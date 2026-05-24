from sentence_transformers import SentenceTransformer
import os
import mlflow
import logging

logger = logging.getLogger("MLO-005")

MODEL_CACHE = os.getenv("MODEL_CACHE", "models/")

# Load model at startup, cache in models/

model = None
model_ready = False


def load_model():
    global model, model_ready
    model_name = get_model_details_from_registry()
    logger.info(f"Loading model: {model_name}...")
    model = SentenceTransformer(
        model_name,
        cache_folder=MODEL_CACHE,
        local_files_only=True,
    )
    model_ready = True


def embed_text(text: str):
    return model.encode(text)


def get_model_details_from_registry() -> str:
    try:
        mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI"))
        client = mlflow.MlflowClient()
        model_version = client.get_model_version_by_alias(
            name="mlo-embed", alias="champion"
        )
        run = mlflow.get_run(model_version.run_id)
        model_name = run.data.params.get("model_name")
    except Exception as e:
        logger.warning(
            f"Failed to fetch model details from registry: {e}"
        )
        model_name = os.getenv("MODEL_NAME", "all-MiniLM-L6-v2")
    return model_name
