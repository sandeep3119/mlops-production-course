# MLO-002: Observability — Health Probes, Structured Logging & Latency Tracking

## What This Is
Production observability layer added on top of the MLO-001 embedding service. Implements Kubernetes-compatible health probes, JSON structured logging, and per-request latency tracking. A service without observability cannot be operated in production.

---

## Prerequisites
- MLO-001 completed and running
- Understanding of HTTP status codes
- `pip install fastapi uvicorn`

---

## Project Structure
```
MLO-002/
├── app/
│   ├── main.py          # /health/live, /health/ready endpoints, latency tracking
│   ├── model.py         # model_ready flag
│   └── utility/
│       └── logger.py    # JSONFormatter — structured logging
├── tests/
└── Dockerfile
```

---

## What You Will Learn
- The difference between liveness and readiness probes and why both are needed
- How to implement structured JSON logging in Python using a custom `logging.Formatter`
- Why `logger.info()` is not the same as `logging.info()` — named loggers vs root logger
- How `extra={"extra": {...}}` passes structured fields into log records
- How to track per-request latency with `from time import time`
- Why `record.getMessage()` and not `record.msg` in a custom formatter
- The `model_ready` flag pattern — why importing a module attribute as a value is wrong

---

## Endpoints

| Endpoint | Purpose | Returns |
|---|---|---|
| `GET /health/live` | Liveness — is the process alive? | 200 always |
| `GET /health/ready` | Readiness — is the model loaded? | 200 if ready, 503 if not |
| `POST /embed` | Inference with latency logging | `{"embedding": [...]}` |

---

## Key Design Decisions

| Decision | Why |
|---|---|
| Separate live vs ready endpoints | Kubernetes needs both — different failure scenarios |
| `import model` then `model.model_ready` | Boolean imports are value copies; reading from the module reads the live value |
| Named logger (`logging.getLogger("MLO-002")`) | Root logger pollutes all libraries; named loggers are scoped |
| `record.getMessage()` in formatter | Substitutes `%s` args into the message; `record.msg` returns raw template |
| Single handler setup in `main.py` | Multiple handler setups across files cause duplicate log output |

---

## What You Learned
- **Liveness probe** → answers "is the container alive?" — Kubernetes restarts the pod if this fails
- **Readiness probe** → answers "can this pod receive traffic?" — Kubernetes removes pod from Service endpoints if this fails. A pod can be alive but not ready (model still loading).
- `logging.info()` uses the root logger, which includes noise from every imported library. Always use `logging.getLogger("your-app-name")`.
- `import model; model.model_ready` reads the live attribute. `from model import model_ready` copies the boolean at import time — never updates.
- JSON structured logs enable log aggregation tools (ELK, Datadog, CloudWatch) to query by field. Plain text logs require regex parsing.
- `record.getMessage()` = `record.msg % record.args`. If someone calls `logger.info("Processed %s items", 42)`, `record.msg` gives `"Processed %s items"`, `getMessage()` gives `"Processed 42 items"`.

---

## Interview Questions

**Kubernetes Probes**
1. What is the difference between a liveness probe and a readiness probe? Give a concrete scenario where a pod should be alive but not ready.
2. A pod's liveness probe fails. What does Kubernetes do? A readiness probe fails — what does Kubernetes do differently?
3. Why does `initialDelaySeconds` matter for an ML serving pod specifically? What happens if you set it too low?
4. Your pod takes 45 seconds to load a large model. How do you configure probes to avoid being killed before startup completes? What is `startupProbe` and when would you use it?
5. What HTTP status code should `/health/ready` return when the model is not loaded? Why not 200?

**Logging**
6. What is the difference between `logging.info()` and `logger.info()` where `logger = logging.getLogger("myapp")`?
7. Why would you use JSON-formatted logs in production instead of plain text? Name two tools that benefit from structured logs.
8. What does a logging `Handler` do vs a logging `Formatter`? What is the relationship between them?
9. If you add a `StreamHandler` in both `main.py` and `model.py` for the same logger name, what happens to log output?
10. What is `record.getMessage()` and why should a custom `Formatter` use it instead of `record.msg`?

**Latency & Performance**
11. Why is average latency a misleading metric for a production SLA? What should you measure instead?
12. Your `/embed` endpoint shows P50=5ms but P99=800ms. What does this tell you about the service behaviour?
13. How would you add request ID tracking to correlate logs from the same request across multiple services?
14. What is the difference between measuring latency inside the application vs at the load balancer? Which is more accurate for what?
15. Your structured logs show `latency_ms` values but you notice they're always 0. What is the likely bug in the timing code?
