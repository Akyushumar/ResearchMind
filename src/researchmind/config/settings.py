"""Application settings."""
from pathlib import Path
from functools import lru_cache
from typing import Literal

from pydantic import model_validator, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    env: Literal["development", "staging", "production"] = "development"
    debug: bool = True
    log_level: str = "DEBUG"
    database_url: str = "postgresql+asyncpg://researchmind:researchmind@localhost:5432/researchmind"
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_collection: str = "researchmind_evidence"
    
    # Embeddings configuration
    embedding_provider: str = Field("gemini", validation_alias="EMBEDDING_PROVIDER", description="Provider for embeddings: openai, gemini, etc.")
    embedding_model: str = Field("gemini-embedding-2", validation_alias="EMBEDDING_MODEL", description="The embedding model to use")
    embedding_dimension: int = Field(3072, validation_alias="EMBEDDING_DIMENSION", description="The dimension of the embedding vectors")
    
    # Provider API Keys
    openai_api_key: str | None = Field(None, validation_alias="OPENAI_API_KEY")
    gemini_api_key: str | None = Field(None, validation_alias="GEMINI_API_KEY")
    upload_dir: Path = Path("./data/uploads")

    model_config = SettingsConfigDict(env_prefix="RESEARCHMIND_", env_file=".env", extra="ignore")

    @property
    def is_development(self) -> bool:
        """Check if environment is development."""
        return self.env == "development"

    @property
    def is_production(self) -> bool:
        """Check if environment is production."""
        return self.env == "production"

    @model_validator(mode="after")
    def create_upload_dir(self) -> "Settings":
        """Create upload directory if it does not exist."""
        if not self.upload_dir.exists():
            self.upload_dir.mkdir(parents=True, exist_ok=True)
        return self


@lru_cache
def get_settings() -> Settings:
    """Return the cached application settings."""
    return Settings()
