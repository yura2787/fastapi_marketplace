import hashlib
import json

import redis.asyncio as aioredis
from settings import settings

_redis: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis


def make_cache_key(prefix: str, params: dict) -> str:
    serialized = json.dumps(params, sort_keys=True, default=str)
    digest = hashlib.md5(serialized.encode()).hexdigest()
    return f"{prefix}:{digest}"


async def cache_get(redis: aioredis.Redis, key: str) -> str | None:
    return await redis.get(key)


async def cache_set(redis: aioredis.Redis, key: str, value: str, ttl: int = 60):
    await redis.setex(key, ttl, value)


async def cache_invalidate_prefix(redis: aioredis.Redis, prefix: str):
    keys = await redis.keys(f"{prefix}:*")
    if keys:
        await redis.delete(*keys)
