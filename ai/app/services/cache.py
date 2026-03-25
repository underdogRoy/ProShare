"""Redis cache helpers."""
import redis

from ai.app.core.config import settings


client = redis.from_url(settings.redis_url, decode_responses=True)


def cache_key(article_id: int, method: str) -> str:
    return f"article:{article_id}:summary:{method}"


def get_cached(article_id: int, method: str) -> str | None:
    return client.get(cache_key(article_id, method))


def set_cached(article_id: int, method: str, value: str) -> None:
    client.setex(cache_key(article_id, method), settings.summary_ttl_seconds, value)
