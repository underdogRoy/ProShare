import time

from services.shared.app.cache import MemoryCache, build_cache


def test_memory_cache_set_and_get():
    cache = MemoryCache()
    cache.setex("mykey", 60, "myvalue")
    assert cache.get("mykey") == "myvalue"


def test_memory_cache_miss_returns_none():
    cache = MemoryCache()
    assert cache.get("absent") is None


def test_memory_cache_expires_after_ttl():
    cache = MemoryCache()
    cache.setex("shortlived", 1, "data")
    time.sleep(1.05)
    assert cache.get("shortlived") is None


def test_memory_cache_unexpired_key_survives():
    cache = MemoryCache()
    cache.setex("longlived", 60, "data")
    time.sleep(0.1)
    assert cache.get("longlived") == "data"


def test_memory_cache_overwrite():
    cache = MemoryCache()
    cache.setex("k", 60, "v1")
    cache.setex("k", 60, "v2")
    assert cache.get("k") == "v2"


def test_memory_cache_independent_keys():
    cache = MemoryCache()
    cache.setex("a", 60, "alpha")
    cache.setex("b", 60, "beta")
    assert cache.get("a") == "alpha"
    assert cache.get("b") == "beta"


def test_build_cache_memory_url_returns_memory_cache():
    c = build_cache("memory://local")
    assert isinstance(c, MemoryCache)


def test_build_cache_invalid_redis_falls_back_to_memory():
    c = build_cache("redis://nonexistent-host-xyz:6379/0")
    assert isinstance(c, MemoryCache)


def test_build_cache_memory_cache_is_usable():
    c = build_cache("memory://local")
    c.setex("hello", 60, "world")
    assert c.get("hello") == "world"
