from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="AI_")

    redis_url: str = "redis://redis:6379/1"
    backend_api_url: str = "http://backend:8000"
    llm_provider: str = "mock"
    summary_ttl_seconds: int = 604800
    max_chunk_words: int = 1500
    overlap_words: int = 150


settings = Settings()
