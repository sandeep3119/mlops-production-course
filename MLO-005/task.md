## MLO-005: Experiment Tracking + Model Registry

Your embedding service currently has no memory. You deploy a model, it runs, you have no record of: which model version was used, what its performance characteristics were, when it was registered, or how to roll back to a previous version. MLflow solves this.

What you will build:

MLflow tracking server running as a pod in your cluster
A one-time model registration script that logs the all-MiniLM-L6-v2 model to MLflow with metrics and metadata
Your embedding service reads the model name/version from MLflow model registry instead of a hardcoded env var
Deliverables:

k8s/mlflow.yaml — MLflow server deployment + service
scripts/register_model.py — logs model, registers it, adds metrics
Updated model.py — loads model name from MLflow registry stage (Production)
Screenshot of MLflow UI showing registered model