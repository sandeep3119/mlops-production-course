from time import time

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from app import model
import logging
import asyncio
from .utility.logger import JSONFormatter
from contextlib import asynccontextmanager

logger = logging.getLogger("MLO-002")
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())  # formatter goes ON the handler
logger.addHandler(handler)
logger.setLevel(logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    model.load_model()
    yield

app = FastAPI(lifespan=lifespan)


class TextRequest(BaseModel):
    text: str


class EmbeddingResponse(BaseModel):
    embedding: List[float]


@app.post("/embed", response_model=EmbeddingResponse)
async def embed_endpoint(request: TextRequest):
    start = time()
    logger.info(
        "Embedding request received.",
        extra={"extra": {"text_length": len(request.text)}},
    )
    if model.model_ready is False:
        raise HTTPException(status_code=400, detail="Model not loaded.")
    if len(request.text) == 0:
        raise HTTPException(status_code=400, detail="Text is required.")
    loop = asyncio.get_event_loop()
    embedding = await loop.run_in_executor(
        None, model.embed_text, request.text
    )
    latency_ms = round((time() - start) * 1000)
    logger.info(
        "Embedding completed.", extra={"extra": {"latency_ms": latency_ms}}
    )

    return {"embedding": embedding.tolist()}


@app.get("/health/live", status_code=200)
async def health_check():
    logger.info("Liveness check requested.")
    return {"status": "alive"}


@app.get("/health/ready", status_code=200)
async def readiness_check():
    if not model.model_ready:
        logger.error("Model not loaded. Readiness check failed.")
        raise HTTPException(status_code=503, detail="Model not loaded.")
    logger.info("Readiness check requested.")
    return {"status": "ready"}
