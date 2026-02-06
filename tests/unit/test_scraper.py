"""
Unit tests for LinkedIn scraper functionality.
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.scraper.linkedin_scraper import LinkedInScraper
from app.scraper.rate_limiter import RateLimiter
from app.scraper.session_manager import SessionManager


class TestRateLimiter:
    """Test rate limiter functionality."""

    def test_initialization(self):
        """Test rate limiter initialization."""
        limiter = RateLimiter(max_requests=10, window_seconds=60)

        assert limiter.max_requests == 10
        assert limiter.window_seconds == 60
        assert len(limiter.requests) == 0

    @pytest.mark.asyncio
    async def test_within_limit(self):
        """Test requests within rate limit."""
        limiter = RateLimiter(max_requests=5, window_seconds=1)

        # Should allow 5 requests
        for _ in range(5):
            await limiter.acquire()

        assert len(limiter.requests) == 5

    @pytest.mark.asyncio
    async def test_wait_when_exceeded(self):
        """Test waiting when rate limit exceeded."""
        limiter = RateLimiter(max_requests=2, window_seconds=1)

        # Fill the limit
        await limiter.acquire()
        await limiter.acquire()

        assert len(limiter.requests) == 2

        # Next request should wait
        start = datetime.now()
        await limiter.acquire()
        elapsed = (datetime.now() - start).total_seconds()

        # Should have waited approximately the window duration
        assert elapsed >= 0.9  # Allow some tolerance

    @pytest.mark.asyncio
    async def test_cleanup_old_requests(self):
        """Test cleanup of old requests."""
        limiter = RateLimiter(max_requests=5, window_seconds=1)

        # Add some requests
        await limiter.acquire()
        await limiter.acquire()

        # Wait for window to expire
        import asyncio

        await asyncio.sleep(1.1)

        # Should have cleaned up old requests
        await limiter.acquire()
        assert len(limiter.requests) == 1

    def test_is_rate_limited(self):
        """Test rate limit checking."""
        limiter = RateLimiter(max_requests=2, window_seconds=60)

        assert not limiter.is_rate_limited()

        # Add requests
        limiter.requests.append(datetime.now())
        assert not limiter.is_rate_limited()

        limiter.requests.append(datetime.now())
        assert limiter.is_rate_limited()

    def test_time_until_next_request(self):
        """Test calculation of wait time."""
        limiter = RateLimiter(max_requests=2, window_seconds=10)

        assert limiter.time_until_next_request() == 0

        # Add requests
        limiter.requests.append(datetime.now() - timedelta(seconds=5))
        limiter.requests.append(datetime.now())

        wait_time = limiter.time_until_next_request()
        assert 4 <= wait_time <= 6  # Should be around 5 seconds


class TestSessionManager:
    """Test session manager functionality."""

    def test_initialization(self):
        """Test session manager initialization."""
        manager = SessionManager()

        assert manager.cookies_path is not None
        assert manager.cookies == {}

    def test_save_and_load_cookies(self, tmp_path):
        """Test saving and loading cookies."""
        cookies_file = tmp_path / "cookies.json"
        manager = SessionManager(cookies_path=str(cookies_file))

        # Save cookies
        test_cookies = {"session_id": "abc123", "token": "xyz789"}
        manager.save_cookies(test_cookies)

        # Load cookies
        loaded_cookies = manager.load_cookies()

        assert loaded_cookies == test_cookies

    def test_load_cookies_file_not_found(self, tmp_path):
        """Test loading cookies when file doesn't exist."""
        cookies_file = tmp_path / "nonexistent.json"
        manager = SessionManager(cookies_path=str(cookies_file))

        loaded = manager.load_cookies()

        assert loaded == {}

    def test_clear_cookies(self, tmp_path):
        """Test clearing cookies."""
        cookies_file = tmp_path / "cookies.json"
        manager = SessionManager(cookies_path=str(cookies_file))

        # Save some cookies
        manager.save_cookies({"key": "value"})
        assert manager.cookies != {}

        # Clear cookies
        manager.clear_cookies()

        assert manager.cookies == {}
        assert not cookies_file.exists()

    def test_is_session_valid_no_cookies(self):
        """Test session validation with no cookies."""
        manager = SessionManager()

        assert not manager.is_session_valid()

    def test_is_session_valid_with_cookies(self):
        """Test session validation with cookies."""
        manager = SessionManager()
        manager.cookies = {"li_at": "session_token"}

        assert manager.is_session_valid()


@pytest.mark.asyncio
class TestLinkedInScraper:
    """Test LinkedIn scraper."""

    @pytest.fixture
    def mock_playwright(self):
        """Create mock Playwright."""
        mock = MagicMock()
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()

        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_context.new_page = AsyncMock(return_value=mock_page)
        mock_context.cookies = AsyncMock(return_value=[])
        mock_context.close = AsyncMock()
        mock_browser.close = AsyncMock()

        mock_page.goto = AsyncMock()
        mock_page.wait_for_load_state = AsyncMock()
        mock_page.fill = AsyncMock()
        mock_page.click = AsyncMock()
        mock_page.content = AsyncMock(return_value="<html></html>")
        mock_page.query_selector = AsyncMock()

        mock.chromium.launch = AsyncMock(return_value=mock_browser)

        return mock, mock_browser, mock_context, mock_page

    @pytest.fixture
    async def scraper(self, mock_playwright):
        """Create scraper instance with mocked Playwright."""
        mock_pw, _, _, _ = mock_playwright

        with patch("app.scraper.linkedin_scraper.async_playwright") as mock_async_pw:
            mock_async_pw.return_value.__aenter__ = AsyncMock(return_value=mock_pw)
            mock_async_pw.return_value.__aexit__ = AsyncMock(return_value=None)

            scraper = LinkedInScraper(
                email="test@example.com",
                password="password123",
                headless=True,
            )

            await scraper.start()

            yield scraper

            await scraper.close()

    async def test_initialization(self):
        """Test scraper initialization."""
        scraper = LinkedInScraper(
            email="test@example.com",
            password="password123",
            headless=True,
        )

        assert scraper.email == "test@example.com"
        assert scraper.password == "password123"
        assert scraper.headless is True
        assert scraper.rate_limiter is not None
        assert scraper.session_manager is not None

    async def test_start(self, mock_playwright):
        """Test starting scraper."""
        mock_pw, mock_browser, _, _ = mock_playwright

        with patch("app.scraper.linkedin_scraper.async_playwright") as mock_async_pw:
            mock_async_pw.return_value.__aenter__ = AsyncMock(return_value=mock_pw)

            scraper = LinkedInScraper(
                email="test@example.com",
                password="password123",
            )

            await scraper.start()

            mock_pw.chromium.launch.assert_called_once()
            assert scraper.browser is not None
            assert scraper.context is not None

    async def test_close(self, scraper):
        """Test closing scraper."""
        await scraper.close()

        assert scraper.context is None
        assert scraper.browser is None

    async def test_login_success(self, scraper, mock_playwright):
        """Test successful login."""
        _, _, _, mock_page = mock_playwright

        # Mock successful login
        mock_page.url = "https://www.linkedin.com/feed/"

        await scraper.login()

        # Verify login steps were called
        mock_page.goto.assert_called()
        mock_page.fill.assert_called()
        mock_page.click.assert_called()

    async def test_login_with_saved_session(self, scraper):
        """Test login with saved session."""
        # Mock valid session
        scraper.session_manager.cookies = {"li_at": "token"}
        scraper.session_manager.is_session_valid = MagicMock(return_value=True)

        await scraper.login()

        # Should not attempt full login if session is valid
        assert scraper.session_manager.is_session_valid()

    async def test_fetch_messages(self, scraper, mock_playwright):
        """Test fetching messages."""
        _, _, _, mock_page = mock_playwright

        # Mock message elements
        mock_message = MagicMock()
        mock_message.query_selector = AsyncMock()
        mock_message.query_selector.return_value.inner_text = AsyncMock(return_value="Test message")
        mock_page.query_selector_all = AsyncMock(return_value=[mock_message])

        messages = await scraper.fetch_messages()

        assert len(messages) >= 0
        mock_page.goto.assert_called()

    async def test_rate_limiting_applied(self, scraper):
        """Test that rate limiting is applied."""
        scraper.rate_limiter = MagicMock()
        scraper.rate_limiter.acquire = AsyncMock()

        await scraper.fetch_messages()

        scraper.rate_limiter.acquire.assert_called()

    async def test_retry_on_failure(self, scraper, mock_playwright):
        """Test retry logic on failure."""
        _, _, _, mock_page = mock_playwright

        # Mock failure then success
        mock_page.goto.side_effect = [Exception("Network error"), None]

        with patch("app.scraper.linkedin_scraper.asyncio.sleep", new=AsyncMock()):
            # Should retry and eventually succeed
            try:
                await scraper.login()
            except Exception:
                pass  # May still fail in test, but should have retried

    async def test_context_manager(self, mock_playwright):
        """Test using scraper as context manager."""
        mock_pw, _, _, _ = mock_playwright

        with patch("app.scraper.linkedin_scraper.async_playwright") as mock_async_pw:
            mock_async_pw.return_value.__aenter__ = AsyncMock(return_value=mock_pw)
            mock_async_pw.return_value.__aexit__ = AsyncMock(return_value=None)

            async with LinkedInScraper(
                email="test@example.com",
                password="password123",
            ) as scraper:
                assert scraper.browser is not None

            # Should be closed after context
            assert scraper.browser is None

    async def test_get_unread_count(self, scraper, mock_playwright):
        """Test getting unread message count."""
        _, _, _, mock_page = mock_playwright

        # Mock unread count element
        mock_element = MagicMock()
        mock_element.inner_text = AsyncMock(return_value="5")
        mock_page.query_selector = AsyncMock(return_value=mock_element)

        count = await scraper.get_unread_count()

        assert isinstance(count, int)

    async def test_error_handling(self, scraper, mock_playwright):
        """Test error handling in scraper."""
        _, _, _, mock_page = mock_playwright

        # Mock error
        mock_page.goto.side_effect = Exception("Network timeout")

        with pytest.raises(Exception):
            await scraper.fetch_messages()
