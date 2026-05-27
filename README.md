# MLOps Production Engineering — Hands-On Curriculum

A production-first MLOps curriculum structured as real engineering tickets. Every module mirrors a task a working MLOps engineer would receive on the job — you build it, debug it, and learn to explain every decision at depth.

---

## Curriculum Overview

| Module | Topic | Status | Key Technologies |
|---|---|---|---|
| [MLO-001](./MLO-001/README.md) | Containerized ML Inference Service | ✅ Complete | FastAPI, Docker, sentence-transformers |
| [MLO-002](./MLO-002/README.md) | Observability — Probes, Logging, Latency | ✅ Complete | Python logging, JSON structured logs, health probes |
| [MLO-003](./MLO-003/README.md) | Kubernetes Deployment | ✅ Complete | Kubernetes, ConfigMap, resource limits, probes |
| [MLO-004](./MLO-004/README.md) | CI/CD with GitHub Actions | ✅ Complete | GitHub Actions, Docker Hub, unittest.mock |
| [MLO-005](./MLO-005/README.md) | Experiment Tracking & Model Registry | ✅ Complete | MLflow 3.x, PVC, model aliases |
| [MLO-006](./MLO-006/README.md) | Autoscaling + Load Testing | ✅ Complete | HPA, metrics-server, Locust |
| MLO-007 | RAG Pipeline on Local GPU | 🔄 In Progress | Ollama, ChromaDB, FastAPI |
| MLO-011 | GPU Metrics + Monitoring | ⏳ Upcoming | Prometheus, Grafana, NVIDIA exporter |

---

## What You Build

By the end of this curriculum you will have built and operated a complete ML serving stack:

```
                    ┌─────────────────────────────────────────┐
                    │           Kubernetes Cluster             │
                    │                                          │
  HTTP Request ────►│  Service (NodePort)                      │
                    │       │                                  │
                    │       ▼                                  │
                    │  mlo-embed Deployment (HPA: 2–6 pods)   │
                    │  ┌─────────────┐  ┌─────────────┐       │
                    │  │   Pod 1     │  │   Pod 2     │  ...  │
                    │  │  FastAPI    │  │  FastAPI    │       │
                    │  │  + Model    │  │  + Model    │       │
                    │  └──────┬──────┘  └─────────────┘       │
                    │         │ reads champion alias           │
                    │         ▼                                │
                    │  MLflow Server (NodePort)                │
                    │  ┌─────────────────────────┐            │
                    │  │  Experiment Tracking     │            │
                    │  │  Model Registry          │            │
                    │  │  PVC (persistent)        │            │
                    │  └─────────────────────────┘            │
                    │                                          │
                    │  HPA ──► metrics-server ──► kubelets    │
                    └─────────────────────────────────────────┘

  GitHub ──► GitHub Actions ──► Docker Hub ──► kubectl set image
  (push to main)  (CI/CD)        (registry)    (deploy)
```

---

## Prerequisites

```bash
# Tools
docker --version          # Docker Desktop
kubectl version           # Kubernetes CLI
minikube version          # Local K8s cluster
python --version          # 3.10+

# Python packages (cumulative across modules)
pip install fastapi uvicorn sentence-transformers \
            mlflow numpy locust

# Minikube addons
minikube addons enable metrics-server
```

---

## Production Principles

Every module enforces the same standards expected in production engineering:

- **Measure before setting resource limits** — `docker stats` under real load, then add headroom
- **Never hardcode metrics** — benchmark and measure; hardcoded numbers in a registry are lies
- **P95/P99 over average** — average latency is not an SLA metric
- **Warmup before benchmarking** — discard first N results to avoid cold-start skew
- **Catch specific exceptions** — `except MlflowException` not `except Exception`
- **Structured JSON logs** — every log line must be parseable by aggregation tools
- **Named loggers, single handler** — set up handlers once in the entry point, not in every module
- **Immutable image tags** — `:v42` not `:latest` in production manifests
- **Client-server version alignment** — SDK and server version must match
- **Fallback for dependencies** — downstream failures must not crash the serving layer

---

## Key Learnings by Module

### MLO-001 — Containerized Inference
- Model loads at startup via `lifespan`, never per-request
- `COPY app/ ./` flattens structure — affects Python import resolution inside the container
- `DOWNLOAD_MODEL=true` bakes model at build time — eliminates runtime HuggingFace dependency

### MLO-002 — Observability
- Liveness = is the process alive? Readiness = is it ready to serve traffic? They fail differently.
- `import model; model.model_ready` — not `from model import model_ready` (copies the boolean value at import time)
- `record.getMessage()` not `record.msg` in custom formatters — the latter is a raw template

### MLO-003 — Kubernetes
- `emptyDir` is always empty on pod start — never use it for data that must survive restarts
- `requests` = scheduling guarantee; `limits` = hard cap. Exceeding memory limit = OOMKill
- ConfigMap decouples configuration from images — change config without rebuilding

### MLO-004 — CI/CD
- Tests mock the model so CI uses `DOWNLOAD_MODEL=false`. Production builds bake it in with `true`.
- Relative imports break when a Dockerfile flattens the package structure
- `:latest` tag in K8s manifests = no reliable rollback path

### MLO-005 — MLflow
- Client and server versions must match — version drift causes 404 on new API endpoints
- `transition_model_version_stage` deprecated in MLflow 3.x — use `set_registered_model_alias`
- `champion`/`challenger` pattern for A/B model promotion
- Backend store (metadata) and artifact store (model files) fail independently

### MLO-006 — Autoscaling
- HPA formula: `ceil(currentReplicas × currentMetric / targetMetric)`
- HPA uses `requests` not `limits` for utilisation calculation
- `cpu: <unknown>` = metrics-server cannot scrape kubelets — in minikube, fix with `--kubelet-insecure-tls`
- Stabilisation window prevents flapping — tune based on traffic pattern

---

## Running the Full Stack

```bash
# Start cluster
minikube start

# Deploy all services
kubectl apply -f MLO-005/k8s/mlflow.yaml
kubectl apply -f MLO-005/k8s/configmap.yaml
kubectl apply -f MLO-005/k8s/deployment.yaml
kubectl apply -f MLO-005/k8s/service.yaml
kubectl apply -f MLO-006/k8s/hpa.yaml

# Register model with MLflow
export MLFLOW_TRACKING_URI="http://$(minikube ip):$(kubectl get svc mlflow -o jsonpath='{.spec.ports[0].nodePort}')"
python MLO-005/mlflow/scripts/register_model.py

# Verify everything is running
kubectl get pods
kubectl get hpa

# Run load test
locust -f MLO-006/locust/locustfile.py \
  --host=$(minikube service mlo-embed --url --silent)
```

---

## License

MIT
