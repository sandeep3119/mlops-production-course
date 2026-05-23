from sentence_transformers import SentenceTransformer
import os

MODEL_NAME = os.getenv("MODEL_NAME", "all-MiniLM-L6-v2")
MODEL_CACHE = os.getenv("MODEL_CACHE", "models/")

# Load model at startup, cache in models/

model = None
model_ready = False


def load_model():
    global model, model_ready
    model = SentenceTransformer(MODEL_NAME, cache_folder=MODEL_CACHE, local_files_only=True)
    model_ready = True


def embed_text(text: str):
    return model.encode(text)
