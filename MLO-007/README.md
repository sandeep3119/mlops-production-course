# MLO-007: Production RAG Pipeline with Local LLM

## What This Is
A Retrieval-Augmented Generation (RAG) pipeline built over MLOps project documentation (MLO-001 through MLO-006). Ingests markdown documents into ChromaDB (persistent vector store), retrieves relevant chunks via cosine similarity, and generates grounded answers using Ollama (llama3.2:3b) running on a local RTX 4050 GPU. System prompt enforces factual grounding — the LLM refuses to answer if retrieved context is insufficient, preventing hallucination.

---

## Architecture

```
User Query
    │
    ▼
┌──────────┐     ┌───────────────────┐     ┌──────────────┐
│ FastAPI   │────▶│ Embedding Service │────▶│  ChromaDB    │
│ /query    │     │ (MLO-001-006 K8s) │     │ (persistent) │
│           │     └───────────────────┘     └──────┬───────┘
│           │                                      │
│           │◀──── top-k chunks (cosine filtered) ─┘
│           │
│           │────▶ Ollama (llama3.2:3b on RTX 4050 GPU)
│           │◀──── grounded answer
│           │
│           │────▶ Response: answer + sources + latency breakdown
└──────────┘
```

---

## Prerequisites
- MLO-001 through MLO-006 completed (embedding service deployed on minikube)
- Ollama installed with `llama3.2:3b` model pulled (`ollama pull llama3.2:3b`)
- Python 3.10+
- `pip install -r requirements.txt`

---

## Project Structure
```
MLO-007/
├── .env                        # Local config overrides (gitignored)
├── .env.example                # Config template (committed)
├── requirements.txt
├── task.md
├── data/                       # Markdown documents for ingestion
│   ├── MLO-001_README.md
│   ├── MLO-002_README.md
│   ├── MLO-003_README.md
│   ├── MLO-004_README.md
│   ├── MLO-005_README.md
│   └── MLO-006_README.md
└── app/
    ├── __init__.py
    ├── main.py                 # FastAPI app, endpoints, orchestration
    ├── config.py               # Pydantic BaseSettings — all config via env vars
    ├── db.py                   # ChromaDB client lifecycle (init in lifespan)
    ├── ingestion.py            # Load markdown, chunk, embed, store with dedup
    ├── retrieval.py            # Embed query, similarity search, threshold filter
    ├── generation.py           # System prompt + context → Ollama → answer
    ├── prompts/
    │   ├── __init__.py
    │   └── system_prompt.md    # Static LLM grounding rules
    └── utility/
        ├── __init__.py
        ├── logger.py           # JSONFormatter for structured logging
        ├── health_check.py     # Ollama + ChromaDB + embedding API checks
        └── shared_util.py      # get_embedding() — shared by ingestion + retrieval
```

---

## Deploy & Run

```bash
# Ensure Ollama is running with model loaded
ollama run llama3.2:3b

# Ensure embedding service is running (minikube)
minikube service mlo-embed --url

# Start the RAG service
cd MLO-007
uvicorn app.main:app --reload --port 8001

# Ingest documents
curl -X POST http://127.0.0.1:8001/ingest/

# Query
curl -X POST http://127.0.0.1:8001/query \
  -H "Content-Type: application/json" \
  -d '{"query": "How does HPA calculate desired replicas?"}'

# Check ingestion status
curl http://127.0.0.1:8001/ingest/status

# Delete a document
curl -X DELETE http://127.0.0.1:8001/document/MLO-006_README.md

# Health checks
curl http://127.0.0.1:8001/health/live
curl http://127.0.0.1:8001/health/ready
```

---

## API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/ingest/` | Ingest all markdown files from data directory into ChromaDB |
| GET | `/ingest/status` | Return collection name and total chunk count |
| POST | `/query` | RAG query — retrieve + generate with latency breakdown |
| POST | `/retrieve/` | Retrieve relevant chunks only (debug/inspection) |
| DELETE | `/document/{document_id}` | Remove a document and all its chunks by source filename |
| GET | `/health/live` | Liveness — process is running |
| GET | `/health/ready` | Readiness — Ollama, ChromaDB, and embedding API all reachable |

---

## Key Design Decisions

| Decision | Why |
|---|---|
| ChromaDB `PersistentClient` (embedded mode) | Local-first service, no separate DB process. Swap to `HttpClient` for production by changing one env var. |
| Embedding via HTTP to existing MLO-001-006 service | Microservice pattern — one embedding service, many consumers. No model duplication. |
| Cosine distance with threshold filter | `top_k` alone returns k results regardless of relevance. Threshold (0.7) discards garbage matches. |
| `chunk_size=500`, `chunk_overlap=50` | 500 chars captures a meaningful paragraph. 50 char overlap prevents sentence splits at boundaries. |
| `llm_temperature=0.2` | RAG needs factual, grounded responses. Low temperature reduces hallucination. |
| System prompt in separate `.md` file | Versioned, reviewable, editable without code changes. Not hardcoded in Python. |
| `system` vs `prompt` in Ollama API | System instructions go in `system` field (persistent rules). Context + question go in `prompt` (per-request). LLM treats them differently. |
| ChromaDB initialized in FastAPI `lifespan` | Controlled startup, proper logging, fail-fast. Not at module import time. |
| `db.py` with `get_chromadb_collection()` | Single source of truth for DB client. No module-level side effects. All consumers call the same getter. |
| MD5 content hash as chunk ID | Content-addressed storage — same content = same ID. Re-chunking with different chunk_size doesn't create collisions. |
| Deduplication via hash metadata | `collection.get(where={"hash": hash})` before insert. Idempotent ingestion — safe to re-run. |
| Split health checks (live/ready) | Live = process alive (K8s restarts if down). Ready = dependencies reachable (K8s removes from load balancer if not). Different failure responses. |
| Latency breakdown in response | Three separate timings (embed_ms, retrieval_ms, generation_ms) expose bottlenecks. Critical for SLA debugging. |
| Delete by `source_file` metadata | Users think in documents, not chunks. `DELETE /document/MLO-006_README.md` removes all 14 chunks from that file. |

---

## Observed Results

| Metric | Value |
|---|---|
| Documents ingested | 6 files, 75 chunks |
| Duplicate detection | 75/75 skipped on second ingestion |
| HPA query — correct source identified | MLO-006_README.md (all 5 chunks) |
| Out-of-scope query | "I don't have enough context to answer this question" |
| Embedding time | ~133ms |
| Retrieval time (embed + search) | ~135ms |
| Generation time (llama3.2:3b on GPU) | ~2700ms |
| Total query latency | ~2800ms |
| Delete + re-ingest | 14 chunks removed, 14 re-ingested, 61 skipped |

---

## What You Learned
- **RAG has 3 stages**: ingestion (chunk + embed + store), retrieval (embed query + similarity search + filter), generation (prompt construction + LLM call). Each has distinct dependencies and failure modes.
- **Cosine distance vs cosine similarity**: ChromaDB returns distance (0 = identical, 2 = opposite). Lower is better. Threshold filtering needs `<=`, not `>=`.
- **System prompt goes in the `system` field**: Ollama (and all LLM APIs) treat `system` as persistent rules and `prompt` as the user turn. Mixing them in one field lets the LLM ignore your instructions.
- **Pydantic `BaseSettings` for config**: Type validation at startup. `CHUNK_SIZE=banana` crashes immediately, not 20 minutes later. Priority: env var > .env file > default.
- **FastAPI `lifespan` for initialization**: Heavy resources (DB clients, model loading) go here. Fail-fast at startup, not on first request. `@app.on_event("startup")` is deprecated.
- **Module-level code runs at import time**: `chroma_client.get_or_create_collection()` at the top of a file runs before lifespan, when the client is still `None`. Initialize in lifespan, access via getter functions.
- **Relative imports in packages**: `from .config import settings` (same level), `from ..config import settings` (parent level). Absolute imports like `from app.config` break depending on how you run the app.
- **Embedding as a microservice**: The embedding model runs once in its own service (MLO-001-006 on K8s). The RAG service calls it over HTTP. No model duplication, independent scaling. One model serves many consumers.
- **Idempotent ingestion**: Content-hash-based dedup means you can re-run ingestion without duplicating data. Critical for production ETL pipelines where retries are common.
- **LLM temperature for RAG**: 0.2 for factual, grounded answers. 0.7+ for creative tasks. Wrong temperature = hallucination in a system designed to prevent it.
- **Health check split (live vs ready)**: Liveness tells K8s the process isn't crashed. Readiness tells K8s the service can handle requests. A service can be alive but not ready (dependency down). Different probes, different actions.

---

## Interview Questions

**RAG Architecture**
1. Explain the three stages of a RAG pipeline. What external dependencies does each stage have?
2. Why would you use RAG instead of fine-tuning an LLM on your documentation? What are the tradeoffs?
3. Your RAG pipeline returns an answer that's partially wrong. Walk me through how you'd debug it — what do you check at each stage?
4. What is the difference between cosine similarity and cosine distance? If ChromaDB returns a distance of 0.3, is that a good or bad match?
5. Your context window is 4096 tokens. Your retrieval returns 10 chunks of 500 characters each. What happens and how do you prevent it?

**Chunking & Embeddings**
6. Why does chunk overlap matter? What happens if you chunk a document with zero overlap?
7. Your chunk_size is 500 characters. What are the tradeoffs of making it 100 vs 2000?
8. You change your embedding model. What happens to the vectors already stored in ChromaDB? Can you query them with the new model?
9. Why is the embedding service a separate microservice instead of loaded in-process in the RAG service?
10. Your embedding service goes down during ingestion of a 500-page document. 200 chunks are stored, 300 are not. What happens when you re-run ingestion?

**LLM & Generation**
11. What is the difference between the `system` and `prompt` fields in the Ollama API? Why does it matter for RAG?
12. Your LLM ignores the retrieved context and answers from training data. How do you prevent this?
13. What does temperature control? Why would you use 0.2 for RAG but 0.8 for a creative writing assistant?
14. Your LLM takes 30 seconds to respond. What could cause this on a GPU with sufficient VRAM? Name three things to check.
15. What is KV cache in LLM inference? What happens to VRAM usage as the context grows?

**Production & Observability**
16. Why do you track embed_ms, retrieval_ms, and generation_ms separately instead of one total latency?
17. Your total query latency is 3 seconds. The SLA is 1 second. Looking at the breakdown, retrieval is 100ms and generation is 2800ms. Where do you optimize?
18. What is the difference between liveness and readiness health checks? Give an example where a service is alive but not ready.
19. How does your deduplication work? What happens if the same document is ingested twice with different chunk sizes?
20. You need to move from embedded ChromaDB to a managed vector database. What changes in your code? What doesn't change?
