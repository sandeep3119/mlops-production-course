from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import torch
from sentence_transformers import SentenceTransformer

app = FastAPI()

class TextRequest(BaseModel):
    text: str

class EmbeddingResponse(BaseModel):
    embedding: List[float]

# Load model at startup (not per request)
model = SentenceTransformer("all-MiniLM-L6-v2")

@app.post("/embed", response_model=EmbeddingResponse)
def embed_text(request: TextRequest):
    if not request.text:
        raise HTTPException(status_code=400, detail="Text is required.")
    with torch.no_grad():
        embedding = model.encode(request.text)
    return {"embedding": embedding.tolist()}
