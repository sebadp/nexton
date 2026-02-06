"""
Unit tests for Redis cache functionality.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.cache import CacheKeys, RedisCache, cached, generate_message_hash
from app.core.exceptions import CacheError


class TestCacheKeys:
    """Test cache key generation."""

    def test_opportunity_by_id(self):
        """Test opportunity ID cache key generation."""
        key = CacheKeys.opportunity_by_id(123)
        assert key == "linkedin_agent:opportunity:id:123"

    def test_opportunity_list(self):
        """Test opportunity list cache key generation."""
        key = CacheKeys.opportunity_list(tier="A", skip=0, limit=10, sort_by="created_at")
        assert key == "linkedin_agent:opportunity:list:tier:A:skip:0:limit:10:sort:created_at"

        # Test without tier
        key = CacheKeys.opportunity_list(skip=0, limit=10, sort_by="score")
        assert key == "linkedin_agent:opportunity:list:all:skip:0:limit:10:sort:score"

    def test_pipeline_result(self):
        """Test pipeline result cache key generation."""
        message_hash = "abc123"
        key = CacheKeys.pipeline_result(message_hash)
        assert key == "linkedin_agent:pipeline:result:abc123"

    def test_invalidate_pattern(self):
        """Test cache invalidation pattern."""
        pattern = CacheKeys.invalidate_pattern("opportunity:*")
        assert pattern == "linkedin_agent:opportunity:*"


class TestGenerateMessageHash:
    """Test message hash generation."""

    def test_generate_hash(self):
        """Test hash generation for message."""
        message = "Hello, this is a test message"
        hash1 = generate_message_hash(message)
        hash2 = generate_message_hash(message)

        # Same message produces same hash
        assert hash1 == hash2
        assert len(hash1) == 16  # SHA256 truncated to 16 chars

    def test_different_messages(self):
        """Test different messages produce different hashes."""
        hash1 = generate_message_hash("message 1")
        hash2 = generate_message_hash("message 2")
        assert hash1 != hash2


@pytest.mark.asyncio
class TestRedisCache:
    """Test Redis cache client."""

    @pytest.fixture
    def mock_redis(self):
        """Create mock Redis client."""
        mock = AsyncMock()
        mock.ping = AsyncMock()
        mock.get = AsyncMock()
        mock.set = AsyncMock()
        mock.setex = AsyncMock()
        mock.delete = AsyncMock()
        mock.scan = AsyncMock()
        mock.exists = AsyncMock()
        mock.ttl = AsyncMock()
        mock.expire = AsyncMock()
        mock.mget = AsyncMock()
        mock.pipeline = MagicMock()
        mock.flushdb = AsyncMock()
        mock.info = AsyncMock()
        mock.close = AsyncMock()
        return mock

    @pytest.fixture
    async def cache(self, mock_redis):
        """Create RedisCache instance with mock client."""
        cache = RedisCache(redis_url="redis://localhost:6379/0")
        cache._client = mock_redis
        return cache

    async def test_get_success(self, cache, mock_redis):
        """Test successful cache get."""
        mock_redis.get.return_value = '{"key": "value"}'

        result = await cache.get("test_key")

        assert result == {"key": "value"}
        mock_redis.get.assert_called_once_with("test_key")

    async def test_get_miss(self, cache, mock_redis):
        """Test cache miss returns None."""
        mock_redis.get.return_value = None

        result = await cache.get("missing_key")

        assert result is None

    async def test_get_error(self, cache, mock_redis):
        """Test cache get error handling."""
        mock_redis.get.side_effect = Exception("Redis error")

        with pytest.raises(CacheError) as exc_info:
            await cache.get("test_key")

        assert "Failed to get from cache" in str(exc_info.value.message)

    async def test_set_success(self, cache, mock_redis):
        """Test successful cache set."""
        result = await cache.set("test_key", {"data": "value"}, ttl=300)

        assert result is True
        mock_redis.setex.assert_called_once()

    async def test_set_without_ttl(self, cache, mock_redis):
        """Test cache set without TTL."""
        result = await cache.set("test_key", {"data": "value"})

        assert result is True
        mock_redis.set.assert_called_once()

    async def test_delete_success(self, cache, mock_redis):
        """Test successful cache delete."""
        mock_redis.delete.return_value = 1

        result = await cache.delete("test_key")

        assert result is True
        mock_redis.delete.assert_called_once_with("test_key")

    async def test_delete_not_found(self, cache, mock_redis):
        """Test delete when key not found."""
        mock_redis.delete.return_value = 0

        result = await cache.delete("missing_key")

        assert result is False

    async def test_delete_pattern(self, cache, mock_redis):
        """Test pattern-based deletion."""
        # Mock scan to return keys in batches
        mock_redis.scan.side_effect = [
            (10, ["key1", "key2"]),
            (0, ["key3"]),
        ]
        mock_redis.delete.return_value = 2

        count = await cache.delete_pattern("test:*")

        assert count == 4  # 2 + 2
        assert mock_redis.scan.call_count == 2

    async def test_exists(self, cache, mock_redis):
        """Test key existence check."""
        mock_redis.exists.return_value = 1

        result = await cache.exists("test_key")

        assert result is True

    async def test_get_ttl(self, cache, mock_redis):
        """Test TTL retrieval."""
        mock_redis.ttl.return_value = 300

        ttl = await cache.get_ttl("test_key")

        assert ttl == 300

    async def test_set_ttl(self, cache, mock_redis):
        """Test TTL setting."""
        mock_redis.expire.return_value = True

        result = await cache.set_ttl("test_key", 600)

        assert result is True
        mock_redis.expire.assert_called_once_with("test_key", 600)

    async def test_get_many(self, cache, mock_redis):
        """Test bulk get operation."""
        mock_redis.mget.return_value = ['{"a": 1}', '{"b": 2}', None]

        result = await cache.get_many(["key1", "key2", "key3"])

        assert result == {
            "key1": {"a": 1},
            "key2": {"b": 2},
            "key3": None,
        }

    async def test_set_many(self, cache, mock_redis):
        """Test bulk set operation."""
        pipeline_mock = AsyncMock()
        pipeline_mock.setex = MagicMock()
        pipeline_mock.execute = AsyncMock()
        mock_redis.pipeline.return_value = pipeline_mock

        data = {"key1": {"a": 1}, "key2": {"b": 2}}
        result = await cache.set_many(data, ttl=300)

        assert result is True
        assert pipeline_mock.setex.call_count == 2
        pipeline_mock.execute.assert_called_once()

    async def test_flush_all(self, cache, mock_redis):
        """Test cache flush."""
        mock_redis.flushdb.return_value = True

        result = await cache.flush_all()

        assert result is True
        mock_redis.flushdb.assert_called_once()

    async def test_context_manager(self, mock_redis):
        """Test async context manager."""
        with patch("app.cache.redis_client.aioredis.from_url", return_value=mock_redis):
            async with RedisCache() as cache:
                assert cache._client is not None

            mock_redis.close.assert_called_once()


@pytest.mark.asyncio
class TestCachedDecorator:
    """Test cached decorator."""

    @pytest.fixture
    def mock_cache(self):
        """Create mock cache."""
        cache = AsyncMock(spec=RedisCache)
        cache.get = AsyncMock()
        cache.set = AsyncMock()
        return cache

    async def test_cached_hit(self, mock_cache):
        """Test cached decorator with cache hit."""
        mock_cache.get.return_value = "cached_result"

        with patch("app.cache.redis_client.get_cache", return_value=mock_cache):

            @cached("test", ttl=300)
            async def test_func(arg):
                return f"computed_{arg}"

            result = await test_func("value")

            assert result == "cached_result"
            mock_cache.get.assert_called_once()
            mock_cache.set.assert_not_called()

    async def test_cached_miss(self, mock_cache):
        """Test cached decorator with cache miss."""
        mock_cache.get.return_value = None

        with patch("app.cache.redis_client.get_cache", return_value=mock_cache):

            @cached("test", ttl=300)
            async def test_func(arg):
                return f"computed_{arg}"

            result = await test_func("value")

            assert result == "computed_value"
            mock_cache.get.assert_called_once()
            mock_cache.set.assert_called_once()

    async def test_cached_with_key_func(self, mock_cache):
        """Test cached decorator with custom key function."""
        mock_cache.get.return_value = None

        def custom_key(*args, **kwargs):
            return f"custom_{args[0]}"

        with patch("app.cache.redis_client.get_cache", return_value=mock_cache):

            @cached("test", ttl=300, key_func=custom_key)
            async def test_func(arg):
                return f"result_{arg}"

            await test_func("value")

            # Check that custom key was used
            call_args = mock_cache.get.call_args[0][0]
            assert "custom_value" in call_args
