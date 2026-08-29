import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    LOG_LEVEL: str = "INFO"

    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ]
    JWT_SECRET: str = "change-this-in-production-super-secret-key-32-chars"

    STORAGE_DIR: str = os.path.join(os.getcwd(), "storage")
    VECTOR_STORE_DIR: str = os.path.join(os.getcwd(), "vector_indices")

    EMBEDDING_PROVIDER: str = "sentence-transformers"
    EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"

    LLM_PROVIDER: str = "mock"
    LLM_MODEL_NAME: str = "gpt-4o-mini"
    LLM_TEMPERATURE: float = 0.0
    LLM_MAX_TOKENS: int = 1024
    OPENAI_API_KEY: str = ""
    OLLAMA_BASE_URL: str = "http://localhost:11434"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
