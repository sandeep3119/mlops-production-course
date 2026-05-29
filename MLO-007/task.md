# MLO-007: Production RAG Pipeline with Local LLM

## Objective
Build a document-ingestion and retrieval-augmented generation service over your existing MLOps project documentation, backed by ChromaDB for vector storage and Ollama (llama3.2:3b) for generation on local GPU.

---

## API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/ingest` | Accept document(s), chunk, embed, store in ChromaDB. Return doc ID + chunk count. |
| POST | `/query` | Accept user question, retrieve top-k relevant chunks, generate answer via Ollama. Return answer + sources + latency breakdown (embed_ms, retrieval_ms, generation_ms). |
| DELETE | `/documents/{doc_id}` | Remove a document and all its chunks from the vector store. |
| GET | `/health/live` | Service is up. |
| GET | `/health/ready` | ChromaDB reachable AND Ollama model loaded. |

---

## Acceptance Criteria

1. Ingest all 6 MLO READMEs (MLO-001 through MLO-006) via the `/ingest` endpoint
2. Query "How does HPA calculate desired replicas?" and get a correct, grounded answer with source references pointing to MLO-006
3. Query something not in any document — service responds saying it doesn't have enough context (not a hallucination)
4. Duplicate ingestion of the same document does NOT create duplicate chunks
5. `/health/ready` returns 503 when Ollama is stopped, 200 when running
6. Latency breakdown is present in every `/query` response — no single number, three separate timings

---

## Tunable Configuration (all via environment variables, no hardcoding)

- `CHROMA_HOST`, `CHROMA_PORT`
- `OLLAMA_BASE_URL`
- `OLLAMA_MODEL`
- `EMBEDDING_MODEL` (sentence-transformers model name)
- `CHUNK_SIZE`, `CHUNK_OVERLAP`
- `TOP_K`
- `SIMILARITY_THRESHOLD`
- `LLM_TEMPERATURE`
- `LLM_MAX_TOKENS`
- `LLM_TIMEOUT_SECONDS`
- `SYSTEM_PROMPT` (or loaded from file)

---

## External Dependencies

| Dependency | Version | Purpose |
|------------|---------|---------|
| Ollama | latest | LLM inference (llama3.2:3b on RTX 4050 GPU) |
| ChromaDB | 1.5.9 | Vector storage + similarity search |
| sentence-transformers | existing from MLO-001 | Embedding for chunks + queries |
| FastAPI | existing | API framework |

---

## Out of Scope

- Streaming responses (MLO-008)
- Prompt versioning (MLO-009)
- Token usage tracking (MLO-010)
- PDF/Word ingestion — plain text and markdown only for this ticket
- Authentication
- Kubernetes deployment (this runs local for now)
- UI/frontend

---

## Definition of Done

- All 5 endpoints working
- README.md with architecture diagram, design decisions, interview questions (same format as MLO-001 through MLO-006)
- All configs driven by env vars with sane defaults
- Tested manually end-to-end with your 6 READMEs as the corpus
