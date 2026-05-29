from .utility.shared_util import get_embedding
from .db import get_chromadb_collection
import logging
from .config import settings
from pydantic import BaseModel
from typing import List, Dict, Optional, Tuple
from fastapi import APIRouter, HTTPException
logger = logging.getLogger("MLO-007")
from time import time


TOP_K = settings.top_k
RELEVANCE_THRESHOLD = settings.similarity_threshold



class RetrievalQuery(BaseModel):
    query: str

router = APIRouter(prefix="/retrieve", tags=["retrieval"])

def embed_user_query(query: str) -> Optional[List[float]]:
    """
    Get embedding for user query.
    """
    embedding = get_embedding(query)
    if embedding is None:
        logger.error("Failed to get embedding for user query.")
    return embedding

def retrieve_relevant_chunks(query_embedding: List[float], top_k: int = 5) -> List[Dict]:
    """
    Retrieve relevant chunks from ChromaDB based on query embedding.
    """
    try:
        collection = get_chromadb_collection()
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
        )
        return results if results else []
    except Exception as e:
        logger.error(f"Error occurred while retrieving chunks: {str(e)}")
        return []

def filter_retrieved_chunks(retrieved_chunks: List[Dict], relevance_threshold: float = 0.5) -> List[Dict]:
    """
    Filter retrieved chunks based on relevance score.
    """
    filtered_chunks = []
    thresholds = retrieved_chunks["distances"][0]
    for idx, score in enumerate(thresholds):
        if score <= relevance_threshold:
            filtered_chunks.append({
                "id": retrieved_chunks["ids"][0][idx],
                "content": retrieved_chunks["documents"][0][idx],
                "source_file": retrieved_chunks["metadatas"][0][idx]["source_file"],
                "similarity_score": score
            })
    return filtered_chunks

def perform_retrieval(query: str) -> Tuple[List[Dict], float]:
    """
    Perform retrieval for user query.
    """
    start_time = time()
    query_embedding = embed_user_query(query)
    total_embedding_time = time() - start_time
    if query_embedding is None:
        return []
    
    retrieved_chunks = retrieve_relevant_chunks(query_embedding, top_k=TOP_K)
    filtered_chunks = filter_retrieved_chunks(retrieved_chunks, relevance_threshold=RELEVANCE_THRESHOLD)
    
    return filtered_chunks,total_embedding_time


@router.post("/", tags=["retrieval"])
async def retrieve(query: RetrievalQuery):
    """
    Endpoint to trigger document retrieval.
    """
    try:
        results = perform_retrieval(query.query)
        return {
            "status": "success",
            "results": results,
            "query": query.query
        }
    except Exception as e:
        logger.error(f"Retrieval error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
