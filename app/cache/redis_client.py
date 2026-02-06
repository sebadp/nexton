"""
Redis cache client.

Provides caching functionality using Redis with JSON serialization,
TTL support, and cache invalidation.
"""

import json
from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar

import redis.asyncio as aioredis
from redis.asyncio import Redis

from app.core.config import settings
from app.core.exceptions import CacheError
from app.core.logging import get_logger

logger = get_logger(__name__)

# Type variable for generic decorator
F = TypeVar("F", bound=Callable[..., Any])


class RedisCache:
    """
    Redis cache client with async support.

    Provides high-level caching operations with JSON serialization,
    TTL management, and batch operations.
    """

    def __init__(self, redis_url: str | None = None):
        """
        Initialize Redis cache client.

        Args:
            redis_url: Redis connection URL (uses settings if not provided)
        """
        self.redis_url = redis_url or settings.REDIS_URL
        self._client: Redis | None = None
        logger.info("redis_cache_initialized", url=self.redis_url)

    async def connect(self) -> None:
        """
        Connect to Redis.

        Raises:
            CacheError: If connection fails
        """
        try:
            if not self.redis_url:
                raise CacheError("Redus URL not configured")

            self._client = await aioredis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
                max_connections=50,
            )
            # Test connection
            await self._client.ping()
            logger.info("redis_connected")

        except Exception as e:
            logger.error("redis_connection_failed", error=str(e))
            raise CacheError(message="Failed to connect to Redis", details={"error": str(e)}) from e

    async def disconnect(self) -> None:
        """Close Redis connection."""
        if self._client:
            await self._client.close()
            logger.info("redis_disconnected")

    @property
    def client(self) -> Redis:
        """
        Get Redis client.

        Returns:
            Redis client instance

        Raises:
            CacheError: If not connected
        """
        if not self._client:
            raise CacheError(
                message="Redis client not connected. Call connect() first.",
                details={"method": "client"},
            )
        return self._client

    async def get(self, key: str) -> Any | None:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value (deserialized from JSON) or None if not found

        Raises:
            CacheError: If operation fails
        """
        try:
            value = await self.client.get(key)

            if value is None:
                logger.debug("cache_miss", key=key)
                return None

            # Deserialize JSON
            deserialized = json.loads(value)
            logger.debug("cache_hit", key=key)
            return deserialized

        except json.JSONDecodeError as e:
            logger.error("cache_deserialize_error", key=key, error=str(e))
            # Return raw value if not JSON
            return value

        except Exception as e:
            logger.error("cache_get_error", key=key, error=str(e))
            raise CacheError(
                message="Failed to get from cache",
                details={"key": key, "error": str(e)},
            ) from e

    async def set(self, key: str, value: Any, ttl: int | None = None) -> bool:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized)
            ttl: Time to live in seconds (optional)

        Returns:
            True if successful

        Raises:
            CacheError: If operation fails
        """
        try:
            # Serialize to JSON
            serialized = json.dumps(value, default=str)

            # Set with optional TTL
            if ttl:
                await self.client.setex(key, ttl, serialized)
            else:
                await self.client.set(key, serialized)

            logger.debug("cache_set", key=key, ttl=ttl)
            return True

        except (TypeError, ValueError) as e:
            logger.error("cache_serialize_error", key=key, error=str(e))
            raise CacheError(
                message="Failed to serialize value",
                details={"key": key, "error": str(e)},
            ) from e

        except Exception as e:
            logger.error("cache_set_error", key=key, error=str(e))
            raise CacheError(
                message="Failed to set cache",
                details={"key": key, "error": str(e)},
            ) from e

    async def delete(self, key: str) -> bool:
        """
        Delete key from cache.

        Args:
            key: Cache key

        Returns:
            True if key was deleted, False if not found
        """
        try:
            result = await self.client.delete(key)
            deleted = result > 0

            if deleted:
                logger.debug("cache_deleted", key=key)
            else:
                logger.debug("cache_key_not_found", key=key)

            return bool(deleted)

        except Exception as e:
            logger.error("cache_delete_error", key=key, error=str(e))
            raise CacheError(
                message="Failed to delete from cache",
                details={"key": key, "error": str(e)},
            ) from e

    async def delete_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching pattern.

        Args:
            pattern: Redis pattern (e.g., "opportunity:*")

        Returns:
            Number of keys deleted
        """
        try:
            deleted_count = 0
            cursor = 0

            # Use SCAN to find matching keys
            while True:
                cursor, keys = await self.client.scan(cursor=cursor, match=pattern, count=100)

                if keys:
                    deleted = await self.client.delete(*keys)
                    deleted_count += deleted

                if cursor == 0:
                    break

            logger.info("cache_pattern_deleted", pattern=pattern, count=deleted_count)
            return deleted_count

        except Exception as e:
            logger.error("cache_delete_pattern_error", pattern=pattern, error=str(e))
            raise CacheError(
                message="Failed to delete pattern",
                details={"pattern": pattern, "error": str(e)},
            ) from e

    async def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.

        Args:
            key: Cache key

        Returns:
            True if key exists
        """
        try:
            result = await self.client.exists(key)
            return bool(result > 0)

        except Exception as e:
            logger.error("cache_exists_error", key=key, error=str(e))
            return False

    async def get_ttl(self, key: str) -> int:
        """
        Get remaining TTL for key.

        Args:
            key: Cache key

        Returns:
            TTL in seconds, -1 if no TTL, -2 if key doesn't exist
        """
        try:
            ttl = await self.client.ttl(key)
            return int(ttl)

        except Exception as e:
            logger.error("cache_ttl_error", key=key, error=str(e))
            return -2

    async def set_ttl(self, key: str, ttl: int) -> bool:
        """
        Set TTL for existing key.

        Args:
            key: Cache key
            ttl: Time to live in seconds

        Returns:
            True if TTL was set
        """
        try:
            result = await self.client.expire(key, ttl)
            return bool(result)

        except Exception as e:
            logger.error("cache_set_ttl_error", key=key, error=str(e))
            return False

    async def get_many(self, keys: list[str]) -> dict[str, Any]:
        """
        Get multiple values at once.

        Args:
            keys: List of cache keys

        Returns:
            Dictionary mapping keys to values (None if not found)
        """
        try:
            values = await self.client.mget(keys)

            result = {}
            for key, value in zip(keys, values, strict=False):
                if value:
                    try:
                        result[key] = json.loads(value)
                    except json.JSONDecodeError:
                        result[key] = value
                else:
                    result[key] = None

            logger.debug(
                "cache_get_many", key_count=len(keys), found=sum(1 for v in result.values() if v)
            )
            return result

        except Exception as e:
            logger.error("cache_get_many_error", error=str(e))
            raise CacheError(
                message="Failed to get multiple keys",
                details={"error": str(e)},
            ) from e

    async def set_many(self, mapping: dict[str, Any], ttl: int | None = None) -> bool:
        """
        Set multiple values at once.

        Args:
            mapping: Dictionary of key-value pairs
            ttl: Optional TTL for all keys

        Returns:
            True if successful
        """
        try:
            # Serialize all values
            serialized = {k: json.dumps(v, default=str) for k, v in mapping.items()}

            # Use pipeline for atomic operation
            pipe = self.client.pipeline()

            for key, value in serialized.items():
                if ttl:
                    pipe.setex(key, ttl, value)
                else:
                    pipe.set(key, value)

            await pipe.execute()

            logger.debug("cache_set_many", key_count=len(mapping), ttl=ttl)
            return True

        except Exception as e:
            logger.error("cache_set_many_error", error=str(e))
            raise CacheError(
                message="Failed to set multiple keys",
                details={"error": str(e)},
            ) from e

    async def flush_all(self) -> bool:
        """
        Flush entire cache (use with caution!).

        Returns:
            True if successful
        """
        try:
            await self.client.flushdb()
            logger.warning("cache_flushed")
            return True

        except Exception as e:
            logger.error("cache_flush_error", error=str(e))
            return False

    async def get_info(self) -> dict:
        """
        Get Redis server info.

        Returns:
            Dictionary with Redis server information
        """
        try:
            info = await self.client.info()
            return dict(info)

        except Exception as e:
            logger.error("cache_info_error", error=str(e))
            return {}

    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
        return False


# Global cache instance
_cache_instance: RedisCache | None = None


def get_cache() -> RedisCache:
    """
    Get global cache instance (lazy initialization).

    Returns:
        RedisCache instance
    """
    global _cache_instance

    if _cache_instance is None:
        _cache_instance = RedisCache()

    return _cache_instance


def cached(
    key_prefix: str,
    ttl: int = 300,
    key_func: Callable[..., str] | None = None,
):
    """
    Decorator for caching function results.

    Args:
        key_prefix: Prefix for cache key
        ttl: Time to live in seconds
        key_func: Optional function to generate cache key from args

    Returns:
        Decorated function

    Example:
        @cached("pipeline:result", ttl=3600)
        async def process_message(message: str):
            # Expensive operation
            return result
    """

    def decorator(func: F) -> F:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache = get_cache()

            # Generate cache key
            if key_func:
                cache_key = f"{key_prefix}:{key_func(*args, **kwargs)}"
            else:
                # Use function name and args as key
                key_parts = [str(arg) for arg in args] + [f"{k}={v}" for k, v in kwargs.items()]
                cache_key = f"{key_prefix}:{':'.join(key_parts)}"

            # Try to get from cache
            try:
                cached_value = await cache.get(cache_key)
                if cached_value is not None:
                    logger.debug("cache_decorator_hit", key=cache_key)
                    return cached_value
            except Exception as e:
                logger.warning("cache_decorator_get_failed", error=str(e))
                # Continue to execute function if cache fails

            # Execute function
            result = await func(*args, **kwargs)

            # Store in cache
            try:
                await cache.set(cache_key, result, ttl=ttl)
                logger.debug("cache_decorator_set", key=cache_key)
            except Exception as e:
                logger.warning("cache_decorator_set_failed", error=str(e))
                # Don't fail if caching fails

            return result

        return wrapper  # type: ignore

    return decorator
