"""Application settings."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed environment settings for backend."""

    model_config = SettingsConfigDict(env_file=".env", env_prefix="BACKEND_")

    app_name: str = "ProShare API"
    database_url: str = "postgresql+psycopg://postgres:postgres@db:5432/proshare"
    secret_key: str = "change-me"
    access_token_expire_minutes: int = 30
    refresh_token_expire_minutes: int = 60 * 24 * 7
    redis_url: str = "redis://redis:6379/0"
    ai_service_url: str = "http://ai:8100"
    cors_origins: str = "http://localhost:3000"


settings = Settings()
