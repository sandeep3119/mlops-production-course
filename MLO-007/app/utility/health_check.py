from ..config import settings
import requests
from ..db import get_chromadb_collection
import logging


logger = logging.getLogger("MLO-007")

def check_ollama():
    """Check if Ollama is running and the model is available"""
    try:
        response = requests.get(f"{settings.ollama_base_url}/api/tags")
        logger.info(f"Ollama check: {response}")
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Ollama check failed: {str(e)}")
        return False


def check_chromadb():
    """Check if ChromaDB is running and accessible"""
    try:
        response = get_chromadb_collection()
        logger.info(f"ChromaDB check: {response}")
        return response is not None
    except Exception as e:
        logger.error(f"ChromaDB check failed: {str(e)}")
        return False


def check_embedding_api():
    """Check if embedding API is reachable"""
    try:
        response = requests.get(settings.embedding_server_host + "/health/live")
        logger.info(f"Embedding API check: {response}")
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Embedding API check failed: {str(e)}")
        return False