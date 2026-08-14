from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "document-support-rag-chatbot"
    app_env: str = "local"
    log_level: str = "INFO"
    upload_dir: Path = Path("data/uploads")
    max_upload_size_mb: int = Field(default=10, gt=0)
    openai_api_key: str | None = None
    openai_embedding_model: str = "text-embedding-3-small"
    openai_chat_model: str = "gpt-5.6-terra"
    max_retrieval_distance: float = Field(default=1.0, ge=0)
    chroma_persist_dir: Path = Path("data/chroma")
    chroma_collection_name: str = "support_documents"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def max_upload_size_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()
