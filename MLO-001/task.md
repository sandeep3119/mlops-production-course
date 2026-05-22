Sprint 1 — Ticket MLO-001
Title: Containerize a Hugging Face inference model as a production-ready FastAPI service
Context: A Data Scientist has trained a sentence-transformer model (all-MiniLM-L6-v2 from HuggingFace) for semantic search. It works in their notebook. You need to ship it as a REST API.
Acceptance Criteria:

FastAPI app with a POST /embed endpoint
Accepts {"text": "some sentence"}, returns the embedding vector
Runs inside Docker, not just locally
Container starts in under 10 seconds
Model is not downloaded at request time — it loads on startup

What to submit:

main.py — FastAPI app
Dockerfile
requirements.txt
A curl command that tests your endpoint

You are NOT allowed to:

Use a tutorial verbatim
Skip the Dockerfile and just run locally
Download the model inside the request handler