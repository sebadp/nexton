"""
Cache key definitions and helpers.

This module provides standardized cache key generation for consistent
caching across the application.
"""


class CacheKeys:
    """Cache key constants and generators."""

    # Prefixes
    PREFIX = "linkedin_agent"
    OPPORTUNITY = f"{PREFIX}:opportunity"
    PIPELINE = f"{PREFIX}:pipeline"
    PROFILE = f"{PREFIX}:profile"
    SCRAPER = f"{PREFIX}:scraper"
    ANALYTICS = f"{PREFIX}:analytics"

    # TTL (seconds)
    TTL_SHORT = 300  # 5 minutes
    TTL_MEDIUM = 1800  # 30 minutes
    TTL_LONG = 3600  # 1 hour
    TTL_DAY = 86400  # 24 hours
    TTL_WEEK = 604800  # 7 days

    @classmethod
    def opportunity_by_id(cls, opportunity_id: int) -> str:
        """
        Generate cache key for opportunity by ID.

        Args:
            opportunity_id: Opportunity ID

        Returns:
            Cache key string
        """
        return f"{cls.OPPORTUNITY}:id:{opportunity_id}"

    @classmethod
    def opportunity_list(
        cls,
        tier: str | None = None,
        skip: int = 0,
        limit: int = 10,
        sort_by: str = "created_at",
    ) -> str:
        """
        Generate cache key for opportunity list query.

        Args:
            tier: Optional tier filter
            skip: Pagination offset
            limit: Page size
            sort_by: Sort field

        Returns:
            Cache key string
        """
        tier_part = f"tier:{tier}" if tier else "all"
        return f"{cls.OPPORTUNITY}:list:{tier_part}:skip:{skip}:limit:{limit}:sort:{sort_by}"

    @classmethod
    def opportunity_stats(cls) -> str:
        """Generate cache key for opportunity statistics."""
        return f"{cls.OPPORTUNITY}:stats"

    @classmethod
    def pipeline_result(cls, message_hash: str) -> str:
        """
        Generate cache key for pipeline result.

        Args:
            message_hash: Hash of the message content

        Returns:
            Cache key string
        """
        return f"{cls.PIPELINE}:result:{message_hash}"

    @classmethod
    def profile_data(cls, profile_name: str = "default") -> str:
        """
        Generate cache key for profile data.

        Args:
            profile_name: Profile identifier

        Returns:
            Cache key string
        """
        return f"{cls.PROFILE}:data:{profile_name}"

    @classmethod
    def scraper_cookies(cls, email: str) -> str:
        """
        Generate cache key for scraper cookies.

        Args:
            email: LinkedIn email

        Returns:
            Cache key string
        """
        return f"{cls.SCRAPER}:cookies:{email}"

    @classmethod
    def scraper_unread_count(cls, email: str) -> str:
        """
        Generate cache key for unread message count.

        Args:
            email: LinkedIn email

        Returns:
            Cache key string
        """
        return f"{cls.SCRAPER}:unread:{email}"

    @classmethod
    def analytics_daily(cls, date: str) -> str:
        """
        Generate cache key for daily analytics.

        Args:
            date: Date in YYYY-MM-DD format

        Returns:
            Cache key string
        """
        return f"{cls.ANALYTICS}:daily:{date}"

    @classmethod
    def invalidate_pattern(cls, pattern: str) -> str:
        """
        Generate pattern for cache invalidation.

        Args:
            pattern: Pattern to match (e.g., "opportunity:*")

        Returns:
            Full pattern for Redis SCAN
        """
        return f"{cls.PREFIX}:{pattern}"


def generate_message_hash(message: str) -> str:
    """
    Generate a hash for a message to use as cache key.

    Args:
        message: Message content

    Returns:
        SHA256 hash of the message
    """
    import hashlib

    return hashlib.sha256(message.encode()).hexdigest()[:16]
