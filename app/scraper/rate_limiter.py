"""
Rate limiter for LinkedIn scraper.

Implements token bucket algorithm with configurable rates to avoid
LinkedIn's rate limiting and prevent account suspension.
"""

import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional

from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""

    # Maximum number of requests allowed
    max_requests: int = 10

    # Time window in seconds
    time_window: int = 60

    # Minimum delay between requests (seconds)
    min_delay: float = 3.0

    # Maximum delay for jitter (seconds)
    max_delay: float = 6.0


@dataclass
class RateLimiter:
    """
    Token bucket rate limiter.

    Ensures requests don't exceed configured rate limits.
    """

    config: RateLimitConfig = field(default_factory=RateLimitConfig)
    _request_times: list[float] = field(default_factory=list, init=False)
    _last_request_time: Optional[float] = field(default=None, init=False)

    def wait_if_needed(self) -> None:
        """
        Wait if necessary to comply with rate limits.

        This method blocks until it's safe to make the next request.
        """
        now = time.time()

        # Remove old requests outside the time window
        cutoff_time = now - self.config.time_window
        self._request_times = [t for t in self._request_times if t > cutoff_time]

        # Check if we've hit the rate limit
        if len(self._request_times) >= self.config.max_requests:
            # Wait until the oldest request falls out of the window
            oldest_request = self._request_times[0]
            wait_until = oldest_request + self.config.time_window
            wait_time = wait_until - now

            if wait_time > 0:
                logger.warning(
                    "rate_limit_hit",
                    requests_in_window=len(self._request_times),
                    wait_time=wait_time,
                )
                time.sleep(wait_time)
                now = time.time()

        # Enforce minimum delay between requests
        if self._last_request_time is not None:
            time_since_last = now - self._last_request_time
            if time_since_last < self.config.min_delay:
                delay = self.config.min_delay - time_since_last
                logger.debug("enforcing_min_delay", delay=delay)
                time.sleep(delay)
                now = time.time()

        # Record this request
        self._request_times.append(now)
        self._last_request_time = now

        logger.debug(
            "rate_limit_check_passed",
            requests_in_window=len(self._request_times),
            max_requests=self.config.max_requests,
        )

    def get_remaining_requests(self) -> int:
        """
        Get the number of requests remaining in the current window.

        Returns:
            Number of requests that can be made without hitting the rate limit.
        """
        now = time.time()
        cutoff_time = now - self.config.time_window
        recent_requests = [t for t in self._request_times if t > cutoff_time]
        return max(0, self.config.max_requests - len(recent_requests))

    def get_time_until_next_request(self) -> float:
        """
        Get the time in seconds until the next request can be made.

        Returns:
            Seconds until next request is allowed (0 if can make request now).
        """
        if self._last_request_time is None:
            return 0.0

        now = time.time()
        time_since_last = now - self._last_request_time
        if time_since_last < self.config.min_delay:
            return self.config.min_delay - time_since_last

        # Check if we're at the rate limit
        cutoff_time = now - self.config.time_window
        recent_requests = [t for t in self._request_times if t > cutoff_time]
        if len(recent_requests) >= self.config.max_requests:
            oldest_request = recent_requests[0]
            return (oldest_request + self.config.time_window) - now

        return 0.0

    def reset(self) -> None:
        """Reset the rate limiter state."""
        self._request_times.clear()
        self._last_request_time = None
        logger.info("rate_limiter_reset")


class AdaptiveRateLimiter(RateLimiter):
    """
    Adaptive rate limiter that adjusts limits based on errors.

    If we encounter rate limiting errors, automatically reduces the rate.
    """

    def __init__(self, config: Optional[RateLimitConfig] = None):
        super().__init__(config=config or RateLimitConfig())
        self._original_config = RateLimitConfig(
            max_requests=self.config.max_requests,
            time_window=self.config.time_window,
            min_delay=self.config.min_delay,
            max_delay=self.config.max_delay,
        )
        self._error_count = 0
        self._last_error_time: Optional[datetime] = None

    def report_rate_limit_error(self) -> None:
        """
        Report that a rate limit error occurred.

        This will cause the rate limiter to become more conservative.
        """
        self._error_count += 1
        self._last_error_time = datetime.now()

        # Reduce rate by 25% each time we hit an error
        reduction_factor = 0.75**self._error_count
        new_max_requests = max(
            1, int(self._original_config.max_requests * reduction_factor)
        )
        new_min_delay = self._original_config.min_delay / reduction_factor

        self.config.max_requests = new_max_requests
        self.config.min_delay = min(
            new_min_delay, self._original_config.max_delay * 2
        )

        logger.warning(
            "rate_limit_error_reported",
            error_count=self._error_count,
            new_max_requests=new_max_requests,
            new_min_delay=self.config.min_delay,
        )

    def report_success(self) -> None:
        """
        Report a successful request.

        If we haven't had errors recently, gradually restore the original rate.
        """
        # If no errors in the last 5 minutes, start recovering
        if self._last_error_time:
            time_since_error = datetime.now() - self._last_error_time
            if time_since_error > timedelta(minutes=5):
                # Gradually increase back to original rate
                if self._error_count > 0:
                    self._error_count = max(0, self._error_count - 1)

                    recovery_factor = 0.75**self._error_count
                    self.config.max_requests = min(
                        int(self._original_config.max_requests * recovery_factor),
                        self._original_config.max_requests,
                    )
                    self.config.min_delay = max(
                        self._original_config.min_delay / recovery_factor,
                        self._original_config.min_delay,
                    )

                    logger.info(
                        "rate_limit_recovering",
                        error_count=self._error_count,
                        max_requests=self.config.max_requests,
                        min_delay=self.config.min_delay,
                    )
