from fastapi import FastAPI, HTTPException
import logging
from .utility.logger import JSONFormatter
from pydantic import BaseModel
from contextlib import asynccontextmanager
from .ingestion import router as ingestion_router
from .retrieval import router as retrieval_router, perform_retrieval
from .generation import router as generation_router, perform_generation
from .utility.health_check import check_embedding_api, check_ollama, check_chromadb
from .db import get_chromadb_collection, initialize_chromadb

from time import time

logger = logging.getLogger("MLO-007")
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())  # formatter goes ON the handler
logger.addHandler(handler)
logger.setLevel(logging.INFO)


class UserQuery(BaseModel):
    query: str

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Placeholder for any startup logic, e.g., loading models, initializing resources
    logger.info(msg="Application startup: loading models and initializing resources.")
    initialize_chromadb()
    yield
    # Placeholder for any shutdown logic, e.g., closing database connections
    logger.info(msg="Application shutdown: cleaning up resources.")


# Create FastAPI app
app = FastAPI(
    title="MLO-007 API",
    description="RAG Pipeline API for MLO-007 project",
    version="1.0.0",
    lifespan=lifespan,
    redirect_slashes=False
)

# Include routers
app.include_router(ingestion_router)
app.include_router(retrieval_router)
app.include_router(generation_router)

# Health check endpoint
@app.get("/health/live")
async def health_check():
    """Health check endpoint"""
    logger.info(msg="Health check requested.")
    return {
        "status": "healthy",
        "service": "MLO-007"
    }


@app.get("/health/ready")
async def readiness_check():
    """Readiness check endpoint"""
    logger.info(msg="Readiness check requested.")
    # Placeholder for actual readiness logic, e.g., checking database connections
    if not check_ollama() or not check_chromadb() or not check_embedding_api():
        raise HTTPException(status_code=503, detail="Service not ready")
    else:
        return {
            "status": "ready",
            "service": "MLO-007"
        }

@app.post("/query")
async def query(user_query: UserQuery):
    """Query endpoint"""
    start_time_query_request = time()
    logger.info(msg=f"Query requested: {user_query.query}")
    start_time_retrieval = time()
    retrieved_chunks, embedding_time = perform_retrieval(user_query.query)
    retrieval_time = time() - start_time_retrieval
    sources = [chunk['source_file'] for chunk in retrieved_chunks]
    start_time_generation = time()
    answer = perform_generation(retrieved_chunks, user_query.query)
    generation_time = time() - start_time_generation
    total_time = time() - start_time_query_request
    return {"answer": answer,
            "sources": list(dict.fromkeys(sources)),
            "embedding_time_ms": round(embedding_time*1000, 4),
            "retrieval_time_ms": round(retrieval_time*1000, 4),
            "generation_time_ms": round(generation_time*1000, 4),
            "total_time_ms": round(total_time*1000, 4)
            }

@app.delete("/document/{document_id}")
async def delete_document(document_id: str):
    """Endpoint to delete a document from ChromaDB by its ID."""
    try:
        collection = get_chromadb_collection()
        before_count = collection.count()
        collection.delete(where={"source_file": document_id})
        after_count = collection.count()
        if before_count == after_count:
            logger.warning(f"No document with ID {document_id} found to delete.")
            raise HTTPException(status_code=404, detail=f"No document with ID {document_id} found.")
        logger.info(f"Document with ID {document_id} deleted successfully.")
        return {"status": "success", "message": f"Document with ID {document_id} deleted."}
    except Exception as e:
        logger.error(f"Error deleting document with ID {document_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)