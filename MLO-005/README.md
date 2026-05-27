# MLO-005: Experiment Tracking & Model Registry with MLflow

## What This Is
Deploys an MLflow 3.x tracking server inside the Kubernetes cluster with a PersistentVolumeClaim for data durability. Registers the embedding model with measured performance metrics (P50/P95/P99 latency, throughput, size), promotes it to production via the `champion` alias, and wires the embedding service to dynamically load its model name from the registry on startup — with a graceful fallback if MLflow is unreachable.

---

## Prerequisites
- MLO-004 completed
- kubectl and minikube running
- `pip install mlflow==3.x sentence-transformers numpy`
- MLflow and local client versions **must match** (version mismatch → 404 errors)

---

## Project Structure
```
MLO-005/
├── k8s/
│   ├── mlflow.yaml        # PVC + Deployment + NodePort Service
│   └── configmap.yaml     # MLFLOW_TRACKING_URI added
├── mlflow/
│   └── scripts/
│       └── register_model.py   # Benchmark + log + register + alias
└── app/
    └── model.py           # Loads model name from registry on startup
```

---

## What You Will Learn
- The difference between MLflow's backend store (metadata) and artifact store (model files)
- Why a PVC is required for MLflow in Kubernetes — what happens without it
- How to measure P50/P95/P99 latency with warmup runs using numpy
- Why `log_params` and `log_metrics` are different and when to use each
- How model stages (deprecated) differ from model aliases (`champion`/`challenger`)
- How `MlflowClient.get_model_version_by_alias()` enables registry-driven model loading
- Why you catch specific exceptions instead of broad `Exception` in a fallback pattern
- How Kubernetes DNS lets services talk to each other by name

---

## Deploy MLflow Server

```bash
kubectl apply -f k8s/mlflow.yaml
kubectl rollout status deployment/mlflow
minikube service mlflow   # opens UI in browser
```

## Register Model

```bash
export MLFLOW_TRACKING_URI="http://$(minikube ip):$(kubectl get svc mlflow -o jsonpath='{.spec.ports[0].nodePort}')"
python mlflow/scripts/register_model.py
```

---

## Key Design Decisions

| Decision | Why |
|---|---|
| PVC for MLflow storage | Pod filesystem is ephemeral — all runs and artifacts lost on restart without PVC |
| MLflow 3.1.0 (matches local client) | Client-server version mismatch → 404 on new API endpoints |
| P50/P95/P99 with warmup runs | First inference is cold (memory allocation). Average hides tail latency. |
| `champion` alias over `Production` stage | Stages deprecated in MLflow 3.x. Aliases are more flexible (champion/challenger for A/B). |
| `get_model_version_by_alias()` in model.py | Service reads which model is `champion` at startup — no code change needed to swap models |
| Specific exception catch + env var fallback | MLflow downtime must not crash the embedding service |
| `MLFLOW_TRACKING_URI: http://mlflow:5000` in ConfigMap | Short-form Kubernetes DNS — services in same namespace resolve by service name |

---

## What You Learned
- **Backend store** holds run metadata (params, metrics, tags, run IDs). **Artifact store** holds large binary files (model weights, datasets). They can fail independently — knowing which is down tells you what's broken.
- **Experiment tracking** records the relationship between inputs (hyperparameters, code version) and outputs (metrics, artifacts) so runs can be compared and reproduced. Logging records events.
- **Model registry** provides a lifecycle: None → (Staging) → Production → Archived. In MLflow 3.x: use aliases (`champion`, `challenger`) instead of stages.
- **Warmup first**: discard the first 10 inferences before benchmarking. Cold start includes JIT, memory allocation, cache warming.
- **P99 for SLAs**: if your SLA says "99% of requests under 50ms", check P99. Average is meaningless for SLA compliance.
- `mlflow.set_tracking_uri()` and `MlflowClient()` inside `load_model()`, not at module level — module-level calls run at import time before the network is ready.
- Short Kubernetes DNS: `http://mlflow:5000` works within the same namespace. Full form: `http://mlflow.default.svc.cluster.local:5000`.

---

## Interview Questions

**MLflow & Experiment Tracking**
1. What is the difference between `mlflow.log_param()` and `mlflow.log_metric()`? Give an example of each for an embedding model.
2. What is the difference between the MLflow backend store and the artifact store? If the artifact store goes down, what stops working?
3. Why would you use a model registry instead of just storing model files in S3 directly?
4. What is the difference between model stages (Staging/Production) and model aliases (champion/challenger) in MLflow? Why were stages deprecated?
5. How does `mlflow.sentence_transformers.log_model(model, artifact_path="model")` differ from `mlflow.log_artifact()`?

**Model Versioning & Lifecycle**
6. Walk me through how you would promote a new model version to production in MLflow without any service downtime.
7. What does `get_model_version_by_alias("mlo-embed", "champion")` return? How do you use it to load the actual model?
8. Your embedding service reads the model name from the registry at startup. MLflow goes down. What happens to your service?
9. Why is it important that metrics logged to MLflow are measured, not hardcoded? What risk does hardcoding create?
10. You want to A/B test two model versions — 10% of traffic to the new model. How would you use MLflow aliases to support this?

**Infrastructure & Kubernetes**
11. Why does MLflow need a PersistentVolumeClaim when deployed in Kubernetes? What happens to experiment data if you use emptyDir instead?
12. Your MLflow server shows `cpu: <unknown>` in the HPA. What does this mean and how do you fix it?
13. How does `http://mlflow:5000` resolve from another pod in the same namespace? What is the full DNS name?
14. Your local MLflow client is version 3.12 but your server is 2.13. What error will you see and why?
15. How would you migrate MLflow from SQLite (file-based backend store) to PostgreSQL for production? What changes in the server startup command?
