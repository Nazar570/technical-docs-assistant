from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    project_name: str = "Document Intelligence API"
    version: str = "0.1.0"
    api_v1_str: str = "/api/v1"

    environment: str = "development"
    log_level: str = "INFO"

    postgres_user: str = "admin"
    postgres_password: str = "adminpassword"
    postgres_server: str = "localhost"
    postgres_port: str = "5432"
    postgres_db: str = "doc_intel"

    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_collection_name: str = "document_chunks"

    elastic_host: str = "http://localhost:9200"
    elastic_index_name: str = "document_chunks"

    embedding_model_name: str = "BAAI/bge-small-en-v1.5"
    embedding_dim: int = 384
    reranker_model_name: str = "BAAI/bge-reranker-base"

    gemini_api_key: str = ""
    llm_model_name: str = "gemini-flash-latest"
    generation_temperature: float = 0.1

    langfuse_secret_key: str = ""
    langfuse_public_key: str = ""
    langfuse_base_url: str = "https://cloud.langfuse.com"

    redis_url: str = "redis://localhost:6379/0"
    storage_dir: str = "local_data/uploads"

    @property
    def async_database_uri(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@"
            f"{self.postgres_server}:{self.postgres_port}/{self.postgres_db}"
        )

    def model_post_init(self, __context: dict) -> None:
        Path(self.storage_dir).mkdir(parents=True, exist_ok=True)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
