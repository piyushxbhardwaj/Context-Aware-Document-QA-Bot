import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # API Settings
    HOST: str = "127.0.0.1"
    PORT: int = 8000

    # RAG & LLM Settings
    LLM_PROVIDER: str = "gemini"  # 'gemini' or 'openai'
    GEMINI_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"

    # Chunking Configuration
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 100

    # Embedding Configuration
    EMBEDDING_MODEL: str = "BAAI/bge-small-en-v1.5"

    # Retrieval Configuration
    TOP_K: int = 5
    RRF_CONSTANT: int = 60

    # Persistence Paths
    CHROMA_PERSIST_DIR: str = "data/chroma"
    SQLITE_DB_PATH: str = "data/logs.db"

    # Pydantic Configuration
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

# Instantiate settings
settings = Settings()

# Ensure directories exist
os.makedirs(os.path.dirname(settings.SQLITE_DB_PATH) or "data", exist_ok=True)
os.makedirs(settings.CHROMA_PERSIST_DIR, exist_ok=True)
os.makedirs("data/documents", exist_ok=True)
