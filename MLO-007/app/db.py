import chromadb
from .config import settings

chroma_client = None
collection = None


def initialize_chromadb():
    global chroma_client, collection
    chroma_client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
    collection = chroma_client.get_or_create_collection(
        name=settings.chroma_collection_name,
        metadata={"hnsw:space": "cosine"}
    )


def get_chromadb_collection():
    global collection
    if collection is None:
        initialize_chromadb()
    return collection