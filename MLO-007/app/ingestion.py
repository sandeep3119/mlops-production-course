import hashlib
from pathlib import Path
from typing import List, Dict, Optional
import requests
from fastapi import APIRouter, HTTPException
import logging
from .config import settings
from .db import get_chromadb_collection
from .utility.shared_util import get_embedding

# Get configured logger
logger = logging.getLogger("MLO-007")

# FastAPI router
router = APIRouter(prefix="/ingest", tags=["ingestion"])

# ChromaDB configuration
EMBEDDING_API_URL = settings.embedding_url
DATA_DIR = settings.data_dir
CHROMA_DB_DIR = settings.chroma_persist_dir
COLLECTION_NAME = settings.chroma_collection_name


def load_markdown_files(data_dir: str) -> List[tuple]:
    """
    Load all markdown files from data directory.
    Returns list of (filename, content) tuples.
    """
    md_files = []
    data_path = Path(data_dir)
    
    if not data_path.exists():
        logger.warning(f"Data directory not found: {data_dir}")
        return md_files
    
    for md_file in data_path.glob("*.md"):
        try:
            with open(md_file, "r", encoding="utf-8") as f:
                content = f.read()
                md_files.append((md_file.name, content))
                logger.info(f"Loaded: {md_file.name}")
        except Exception as e:
            logger.error(f"Error loading {md_file.name}: {str(e)}")
    
    return md_files


def chunk_text(text: str, chunk_size: int = None, overlap: int = None) -> List[str]:
    """
    Split text into chunks with overlap.
    """
    if chunk_size is None:
        chunk_size = settings.chunk_size
    if overlap is None:
        overlap = settings.chunk_overlap
    
    chunks = []
    for i in range(0, len(text), chunk_size - overlap):
        chunk = text[i:i + chunk_size]
        if chunk.strip():
            chunks.append(chunk)
    
    return chunks



def compute_hash(text: str) -> str:
    """Compute hash of text for deduplication."""
    return hashlib.md5(text.encode()).hexdigest()


def is_duplicate(text: str, source_file: str, collection) -> bool:
    """
    Check if chunk already exists in ChromaDB.
    """
    try:
        text_hash = compute_hash(text)
        results = collection.get(
            where={"hash": {"$eq": text_hash}}
        )
        return len(results["ids"]) > 0
    except Exception as e:
        logger.warning(f"Error checking duplicates: {str(e)}")
        return False


def ingest_documents() -> Dict:
    """
    Main ingestion pipeline:
    1. Load markdown files
    2. Chunk documents
    3. Get embeddings
    4. Store in ChromaDB with deduplication
    """
    results = {
        "total_files": 0,
        "total_chunks": 0,
        "stored_chunks": 0,
        "skipped_duplicates": 0,
        "errors": []
    }

    collection = get_chromadb_collection()
    
    # Load markdown files
    md_files = load_markdown_files(DATA_DIR)
    results["total_files"] = len(md_files)
    
    if not md_files:
        logger.warning("No markdown files found to ingest")
        return results
    
    # Process each file
    for source_file, content in md_files:
        logger.info(f"Processing: {source_file}")
        
        # Chunk the document
        chunks = chunk_text(content)
        results["total_chunks"] += len(chunks)
        
        # Process each chunk
        for chunk_idx, chunk_content in enumerate(chunks):
            try:
                # Check for duplicates
                if is_duplicate(chunk_content, source_file, collection):
                    results["skipped_duplicates"] += 1
                    logger.info(f"Skipped duplicate chunk from {source_file}")
                    continue
                
                # Get embedding
                embedding = get_embedding(chunk_content)
                if embedding is None:
                    logger.warning(f"Failed to get embedding for chunk {chunk_idx} from {source_file}")
                    continue
                
                # Prepare metadata
                text_hash = compute_hash(chunk_content)
                metadata = {
                    "source_file": source_file,
                    "chunk_index": chunk_idx,
                    "hash": text_hash
                }
                
                # Store in ChromaDB
                doc_id = text_hash
                collection.add(
                    ids=[doc_id],
                    embeddings=[embedding],
                    metadatas=[metadata],
                    documents=[chunk_content]
                )
                
                results["stored_chunks"] += 1
                logger.info(f"Stored chunk {chunk_idx} from {source_file}")
                
            except Exception as e:
                error_msg = f"Error processing chunk {chunk_idx} from {source_file}: {str(e)}"
                logger.error(error_msg)
                results["errors"].append(error_msg)
    
    # Persist ChromaDB
    logger.info("ChromaDB persisted")
    
    return results


# API Endpoints

@router.post("/")
def ingest_endpoint():
    """
    Endpoint to trigger document ingestion.
    """
    try:
        results = ingest_documents()
        return {
            "status": "success",
            "results": results
        }
    except Exception as e:
        logger.error(f"Ingestion error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
def ingest_status_endpoint():
    """
    Get ChromaDB collection statistics.
    """
    try:
        collection = get_chromadb_collection()
        count = collection.count()
        return {
            "collection_name": COLLECTION_NAME,
            "total_documents": count,
            "chroma_db_dir": CHROMA_DB_DIR
        }
    except Exception as e:
        logger.error(f"Status error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))