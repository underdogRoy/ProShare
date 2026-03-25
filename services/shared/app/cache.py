import logging
import time
from threading import Lock

import redis

logger = logging.getLogger(__name__)


class MemoryCache:
    def __init__(self) -> None:
        self._items: dict[str, tuple[float, str]] = {}
        self._lock = Lock()

    def get(self, key: str) -> str | None:
        now = time.time()
        with self._lock:
            item = self._items.get(key)
            if item is None:
                return None
            expires_at, value = item
            if expires_at <= now:
                self._items.pop(key, None)
                return None
            return value

    def setex(self, key: str, ttl_seconds: int, value: str) -> None:
        expires_at = time.time() + ttl_seconds
        with self._lock:
            self._items[key] = (expires_at, value)


def build_cache(cache_url: str):
    if cache_url.startswith("memory://"):
        logger.info("Using in-memory cache for local development")
        return MemoryCache()

    client = redis.Redis.from_url(cache_url, decode_responses=True)
    try:
        client.ping()
        return client
    except redis.RedisError:
        logger.warning("Redis is unavailable at %s, falling back to in-memory cache", cache_url)
        return MemoryCache()
