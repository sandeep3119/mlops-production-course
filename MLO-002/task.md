Ticket MLO-002
Title: Make this service production-observable
Context: Your embedding service is running. Now the platform team needs to deploy it to Kubernetes. Before that happens, the service needs three things every production service must have.
Task 1 — Health endpoints
Add two endpoints:
GET /health/live   → liveness probe
GET /health/ready  → readiness probe
These are not the same thing. You need to understand the difference before you implement them. The readiness probe must return 503 if the model isn't loaded yet. The liveness probe just confirms the process is alive.

Task 2 — Request logging
Every request to /embed must log:

Timestamp
Input text length (not the text itself — why?)
Response time in milliseconds
HTTP status code

Use Python's logging module, not print. Format as JSON. Why JSON? Because log aggregators like Loki and ELK parse JSON automatically.

Task 3 — Fix the async issue
Convert embed_endpoint to async def and offload the model inference to a threadpool so the event loop isn't blocked.
Acceptance criteria:

GET /health/live returns 200 {"status": "alive"}
GET /health/ready returns 200 when model is loaded, 503 when it isn't
Every /embed request produces a JSON log line
Endpoint is now async def

