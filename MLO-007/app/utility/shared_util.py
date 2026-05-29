import requests
from typing import List, Optional
from ..config import settings
import logging
logger = logging.getLogger("MLO-007")

EMBEDDING_API_URL = settings.embedding_url



def get_embedding(text: str) -> Optional[List[float]]:
    """
    Get embedding from the sentence transformer endpoint.
    """
    try:
        response = requests.post(
            EMBEDDING_API_URL,
            json={"text": text},
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        return data.get("embedding") or data.get("embeddings", [None])[0]
    except Exception as e:
        logger.error(f"Error getting embedding: {str(e)}")
        return None
