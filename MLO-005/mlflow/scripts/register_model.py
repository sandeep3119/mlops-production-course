import time

import mlflow
import os
import mlflow.sentence_transformers
import numpy as np
from sentence_transformers import SentenceTransformer


MODEL_NAME = os.getenv("MODEL_NAME", "all-MiniLM-L6-v2")
MODEL_CACHE = os.getenv("MODEL_CACHE", "models/")
remote_server_uri = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000/")
mlflow.set_tracking_uri(remote_server_uri)
mlflow.set_experiment("/embedding-service-mlo-embed")


def get_dir_size_mb(path):
    total_bytes = 0
    for dirpath, _, files in os.walk(path):
        for filename in files:
            full_path = os.path.join(dirpath, filename)
            total_bytes += os.path.getsize(full_path)
    return round(total_bytes / (1024 * 1024), 2)


# Logging a run
with mlflow.start_run():
    # Log parameters which are known before training the model.
    # In this case, we are just logging the model name and framework used.
    mlflow.log_params({
        "model_name": MODEL_NAME,
        "framework": "sentence-transformers"
    })

    # Log metrics which happens on run time for every new model.
    model = SentenceTransformer(
        MODEL_NAME, cache_folder=MODEL_CACHE
    )
    MODEL_DIM = len(model.encode("This is a test sentence."))
    MODEL_SIZE_MB = get_dir_size_mb(MODEL_CACHE)

    # Warm up the model by encoding some sentences.
    # This is to get a more accurate inference time metric.
    sentences = ["This is a test sentence."] * 100
    model.encode(sentences[:10])
    latencies = []
    for sentence in sentences:
        start = time.time()
        model.encode(sentence)
        # Convert to milliseconds
        latencies.append((time.time() - start) * 1000)

    mlflow.log_metrics({
        "model_size_mb": MODEL_SIZE_MB,
        "model_dimension": MODEL_DIM,
        "latency_p50_ms": np.percentile(latencies, 50),
        "latency_p95_ms": np.percentile(latencies, 95),
        "latency_p99_ms": np.percentile(latencies, 99),
        "throughput_sentences_per_second": (
            1000 / np.percentile(latencies, 50)
        ),
    })

    # Log the model itself as an artifact.
    # This will allow us to easily load the model later
    # for inference or further training.
    try:
        mlflow.sentence_transformers.log_model(
            model=model,
            name="model"
        )
        run_id = mlflow.active_run().info.run_id
        model_uri = f"runs:/{run_id}/model"
    except Exception as e:
        msg = "Failed to log model with sentence_transformers flavor"
        print(f"Warning: {msg}: {e}")
        exit(1)
    # Register the model in MLflow Model Registry.
    # This will allow us to manage different versions of the model
    # and transition them through different stages
    # (e.g., Staging, Production).
    try:
        model_version = mlflow.register_model(
            model_uri=model_uri,
            name="mlo-embed"
        )
    except Exception as e:
        print(f"Warning: Failed to register model: {e}")
        print("Model logged but not registered in model registry.")
        model_version = None

    # Transition the model to Production stage.
    # In a real scenario, you might want to have a manual
    # review process before transitioning to production.
    if model_version is not None:
        client = mlflow.MlflowClient()
        try:
            client.set_registered_model_alias(
                name="mlo-embed",
                alias="champion",
                version=model_version.version
            )
        except Exception as e:
            print(f"Warning: Failed to set model alias: {e}")
