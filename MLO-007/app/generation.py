import logging

from .config import settings
from typing import List, Dict
import requests
from pydantic import BaseModel
from fastapi import APIRouter
import os

logger = logging.getLogger("MLO-007")

OLLAMA_API_URL = settings.ollama_base_url
MODEL_NAME = settings.ollama_model
SYSTEM_PROMPT_FILE = os.path.join(os.path.dirname(__file__), "prompts", "system_prompt.md")

router = APIRouter(prefix="/generate", tags=["generation"])


class GenerationRequest(BaseModel):
    user_query: str
    retrieved_chunks: List[Dict] = []


def load_system_prompt() -> str:
    """
    Load system prompt from configuration or file.
    """
    # For simplicity, we are using a hardcoded system prompt defined in prompts.py
    # In a real implementation, you might want to load this from a file or environment variable
    with open(SYSTEM_PROMPT_FILE, "r") as f:
        system_prompt = f.read()
    logger.info("System prompt loaded successfully.")
    return system_prompt


def build_contextual_prompt(retrieved_chunks: List[Dict], user_query: str) -> str:
    """
    Build system prompt for LLM based on retrieved chunks.
    """
    
    if not retrieved_chunks:
        return "No relevant information found in the knowledge base."
    
    prompt = "Based on the following retrieved information, answer the user's question:\n\n"
    for idx, chunk in enumerate(retrieved_chunks):
        prompt += f"Chunk {idx + 1} (Source: {chunk['source_file']}):\n{chunk['content']}\n\n"
    
    prompt += "Use this information to answer the user's question as accurately as possible."
    logger.info("System prompt built successfully with retrieved chunks.")
    return f"{prompt} \n\nUser's Question: {user_query} \n\nAnswer:"


def generate_answer(system_prompt: str, contextual_prompt: str) -> str:
    """
    Generate answer from Ollama LLM using the system prompt.
    """
    try:
        response = requests.post(
            OLLAMA_API_URL + "/api/generate",
            json={"model": MODEL_NAME,
                  "system": system_prompt,  
                    "prompt": contextual_prompt,
                    "stream": False
                    },
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        logger.info("Answer generated successfully.")
        return data.get("response", "").strip()
    except Exception as e:
        logger.error(f"Error generating answer from Ollama: {str(e)}")
        return "Sorry, I couldn't generate an answer at this time."


def perform_generation(retrieved_chunks: List[Dict], user_query: str) -> str:
    """
    Perform generation by building system prompt and calling LLM.
    """
    system_prompt = load_system_prompt()
    contextual_prompt = build_contextual_prompt(retrieved_chunks, user_query)
    answer = generate_answer(system_prompt, contextual_prompt)
    return answer


@router.post("/")
def generate(user_query: str, retrieved_chunks: List[Dict] = []) -> Dict:
    """
    API endpoint to perform generation for user query.
    """
    answer = perform_generation(retrieved_chunks, user_query)
    return {"answer": answer}
