from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    chroma_persist_dir: str = "./chroma_data"
    chroma_collection_name: str = "documents"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2:3b"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_url: str = "http://127.0.0.1:53014/embed"
    embedding_server_host: str = "http://127.0.0.1:53014"
    data_dir: str = "./data"
    chunk_size: int = 500
    chunk_overlap: int = 50
    top_k: int = 5
    similarity_threshold: float = 0.7
    llm_temperature: float = 0.2
    llm_max_tokens: int = 1500
    llm_timeout_seconds: int = 30

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
