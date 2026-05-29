# MLO-001: Containerized ML Inference Service

## What This Is
A production-grade embedding service built with FastAPI and sentence-transformers, containerized with Docker. Exposes a `POST /embed` endpoint that returns a 384-dimensional vector for any input text using the `all-MiniLM-L6-v2` model.

---

## Prerequisites
- Python 3.10+
- Docker Desktop
- Basic understanding of REST APIs
- `pip install fastapi sentence-transformers uvicorn`

---

## Project Structure
```
MLO-001/
├── app/
│   ├── main.py          # FastAPI app, lifespan event, endpoints
│   ├── model.py         # Model loading logic, embed_text()
│   └── utility/
│       └── logger.py    # JSON structured logger
├── tests/
│   └── test_api.py      # API unit tests
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

---

## What You Will Learn
- How to build a production FastAPI service with proper lifespan model loading
- Why models must load at startup, not per-request
- How to containerize a Python ML application with Docker
- How Docker layers work and why layer order affects build speed
- How to write async endpoints and use `run_in_executor` for CPU-bound tasks
- The difference between sync and async FastAPI endpoints
- How to use build arguments (`ARG`) to control model download at build time

---

## Run It

```bash
# Build and run with Docker Compose
docker compose up --build

# Test the endpoint
curl -X POST http://localhost:8000/embed \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello world!"}'

# Expected: {"embedding": [0.023, -0.041, ...]} — 384 floats
```

---

## Key Design Decisions

| Decision | Why |
|---|---|
| `lifespan` event for model loading | Model loads once at startup, not per request |
| `DOWNLOAD_MODEL=true` build arg | Bakes model into image at build time — no runtime internet dependency |
| `local_files_only=True` | Prevents HuggingFace Hub ping on every startup |
| `asyncio.run_in_executor` | Keeps event loop non-blocking for CPU-bound inference |
| CPU-only torch install | Reduces image size by ~1.5GB without GPU hardware |

---

## What You Learned
- Model loading in FastAPI belongs in `lifespan`, not `startup` events or per-request
- Docker image layers cache — put infrequently changing steps (pip install) before frequently changing ones (COPY app/)
- `COPY app/ ./` flattens the package structure inside the container — affects Python imports
- `ARG DOWNLOAD_MODEL=true` at build time bakes the model in; `false` skips it (for CI where tests mock the model)
- An async FastAPI endpoint with a synchronous CPU operation blocks the event loop — always use `run_in_executor`
- CPU-only torch: `pip install torch --index-url https://download.pytorch.org/whl/cpu`

---

## Interview Questions

**FastAPI & Python**
1. What is the difference between FastAPI's `lifespan` context manager and `@app.on_event("startup")`? Why was `on_event` deprecated?
2. You have an async FastAPI endpoint calling a synchronous CPU-bound function. What happens to the event loop, and how do you fix it?
3. What does `asyncio.run_in_executor(None, func, arg)` do? What does `None` mean as the first argument?
4. Why would you use Pydantic `BaseModel` for request/response schemas instead of plain dicts?
5. What is the difference between `uvicorn main:app` and `python -m uvicorn main:app`?

**Docker & Containerization**
6. Explain how Docker layer caching works. Why does the order of instructions in a Dockerfile matter for build performance?
7. What is the difference between `COPY app/ ./` and `COPY app/ ./app/`? How does each affect Python imports inside the container?
8. What is a Docker build argument (`ARG`) vs an environment variable (`ENV`)? When would you use each?
9. Your Docker image is 3GB. Name three ways to reduce its size for an ML serving container.
10. Why would you use a multi-stage Dockerfile for an ML service? What would go in each stage?

**ML Serving**
11. Why should an ML model load at service startup and not per request? What would happen to P99 latency if you loaded per request?
12. What is `all-MiniLM-L6-v2`? What does it output, and what is the output used for?
13. Your embedding service needs to handle 500 requests/second. What are the first three bottlenecks you would investigate?
14. What does `local_files_only=True` do in sentence-transformers? What error does it throw if the model is not found locally?
15. How would you verify that the model baked into your Docker image is identical to the one in your model registry?
