from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import torch
from model import embed_text

app = FastAPI()

class TextRequest(BaseModel):
    text: str

class EmbeddingResponse(BaseModel):
    embedding: List[float]

@app.post("/embed", response_model=EmbeddingResponse)
def embed_endpoint(request: TextRequest):
    if not request.text:
        raise HTTPException(status_code=400, detail="Text is required.")
    
    embedding = embed_text(request.text)
    return {"embedding": embedding.tolist()}
