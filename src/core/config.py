from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    project_name: str = "Document Intelligence API"
    version: str = "0.1.0"
    api_v1_str: str = "/api/v1"

    environment: str = "development"
    log_level: str = "INFO"

    # PostgreSQL
    postgres_user: str = "admin"
    postgres_password: str = "adminpassword"
    postgres_server: str = "localhost"
    postgres_port: str = "5432"
    postgres_db: str = "doc_intel"

    # Qdrant
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333

    @property
    def async_database_uri(self) -> str:
        return f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@{self.postgres_server}:{self.postgres_port}/{self.postgres_db}"

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


settings = Settings()
