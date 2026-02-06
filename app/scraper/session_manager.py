"""
Session manager for LinkedIn scraper.

Handles browser sessions, cookie persistence, and authentication state.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from playwright.async_api import Browser, BrowserContext, Page, Playwright, async_playwright

from app.core.exceptions import ScraperError
from app.core.logging import get_logger

logger = get_logger(__name__)


class SessionManager:
    """
    Manages Playwright browser sessions and cookie persistence.

    Handles:
    - Browser context creation
    - Cookie saving/loading
    - Session validation
    - Authentication state
    """

    def __init__(
        self,
        cookies_path: Path | None = None,
        headless: bool = True,
        user_agent: str | None = None,
    ):
        """
        Initialize session manager.

        Args:
            cookies_path: Path to save/load cookies (default: data/cookies.json)
            headless: Run browser in headless mode
            user_agent: Custom user agent string
        """
        self.cookies_path = cookies_path or Path("data/cookies.json")
        self.headless = headless
        self.user_agent = user_agent or self._get_default_user_agent()

        self._playwright: Playwright | None = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None
        self._page: Page | None = None

        # Ensure cookies directory exists
        self.cookies_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info(
            "session_manager_initialized",
            cookies_path=str(self.cookies_path),
            headless=headless,
        )

    @staticmethod
    def _get_default_user_agent() -> str:
        """Get a realistic user agent string."""
        return (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )

    async def start(self) -> None:
        """
        Start the browser and create a new context.

        Raises:
            ScraperError: If browser fails to start
        """
        try:
            logger.info("starting_browser")

            # Start Playwright
            self._playwright = await async_playwright().start()
            assert self._playwright

            # Launch browser
            self._browser = await self._playwright.chromium.launch(
                headless=self.headless,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--disable-dev-shm-usage",
                    "--no-sandbox",
                ],
            )

            # Load cookies if they exist
            storage_state: Any = None
            if self.cookies_path.exists():
                try:
                    cookies = self._load_cookies()
                    if cookies:
                        storage_state = {"cookies": cookies}
                        logger.info("cookies_loaded", cookie_count=len(cookies))
                except Exception as e:
                    logger.warning("failed_to_load_cookies", error=str(e))

            self._context = await self._browser.new_context(
                user_agent=self.user_agent,
                viewport={"width": 1920, "height": 1080},
                locale="es-ES",
                timezone_id="America/Mexico_City",
                storage_state=storage_state,
            )

            # Create initial page
            self._page = await self._context.new_page()

            # Set extra HTTP headers to avoid detection
            await self._page.set_extra_http_headers(
                {
                    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                }
            )

            logger.info("browser_started")

        except Exception as e:
            logger.error("failed_to_start_browser", error=str(e))
            await self.close()
            raise ScraperError(message="Failed to start browser", details={"error": str(e)}) from e

    async def close(self) -> None:
        """Close the browser and cleanup resources."""
        try:
            logger.info("closing_browser")

            if self._page:
                await self._page.close()

            if self._context:
                await self._context.close()

            if self._browser:
                await self._browser.close()

            if self._playwright:
                await self._playwright.stop()

            logger.info("browser_closed")

        except Exception as e:
            logger.error("error_closing_browser", error=str(e))

        finally:
            self._page = None
            self._context = None
            self._browser = None
            self._playwright = None

    async def get_page(self) -> Page:
        """
        Get the current page.

        Returns:
            Current Playwright page

        Raises:
            ScraperError: If browser not started
        """
        if not self._page:
            raise ScraperError(
                message="Browser not started. Call start() first.",
                details={"method": "get_page"},
            )
        return self._page

    async def save_cookies(self) -> None:
        """
        Save current session cookies to disk.

        Raises:
            ScraperError: If failed to save cookies
        """
        try:
            if not self._context:
                logger.warning("no_context_to_save_cookies")
                return

            # Get cookies from context
            storage_state = await self._context.storage_state()
            cookies = storage_state.get("cookies", [])

            # Save to file
            with open(self.cookies_path, "w") as f:
                json.dump(
                    {
                        "cookies": cookies,
                        "saved_at": datetime.now().isoformat(),
                    },
                    f,
                    indent=2,
                )

            logger.info(
                "cookies_saved",
                cookie_count=len(cookies),
                path=str(self.cookies_path),
            )

        except Exception as e:
            logger.error("failed_to_save_cookies", error=str(e))
            raise ScraperError(message="Failed to save cookies", details={"error": str(e)}) from e

    def _load_cookies(self) -> list[dict]:
        """
        Load cookies from disk.

        Returns:
            List of cookie dictionaries

        Raises:
            ScraperError: If failed to load cookies
        """
        try:
            with open(self.cookies_path) as f:
                data = json.load(f)

            # Check if cookies are not too old (30 days)
            saved_at = datetime.fromisoformat(data.get("saved_at", ""))
            age = datetime.now() - saved_at

            if age > timedelta(days=30):
                logger.warning(
                    "cookies_expired",
                    age_days=age.days,
                )
                return []

            cookies = data.get("cookies", [])
            return list(cookies)

        except FileNotFoundError:
            logger.info("no_cookies_file_found")
            return []

        except Exception as e:
            logger.error("failed_to_load_cookies", error=str(e))
            return []

    async def is_logged_in(self) -> bool:
        """
        Check if user is currently logged into LinkedIn.

        Returns:
            True if logged in, False otherwise
        """
        try:
            page = await self.get_page()

            # Navigate to LinkedIn feed to check login status
            # Use 'load' instead of 'networkidle' as LinkedIn keeps making requests
            await page.goto("https://www.linkedin.com/feed/", wait_until="load", timeout=60000)
            await page.wait_for_timeout(2000)  # Give time for redirect if not logged in

            # Check for login indicators
            # If we're on /feed/, we're logged in
            # If we're on /login or /checkpoint, we're not
            current_url = page.url

            is_logged_in = "/feed" in current_url and "/login" not in current_url

            logger.info(
                "login_status_checked",
                is_logged_in=is_logged_in,
                current_url=current_url,
            )

            return is_logged_in

        except Exception as e:
            logger.error("failed_to_check_login_status", error=str(e))
            return False

    async def login(self, email: str, password: str) -> bool:
        """
        Log into LinkedIn.

        Args:
            email: LinkedIn email
            password: LinkedIn password

        Returns:
            True if login successful, False otherwise

        Raises:
            ScraperError: If login fails
        """
        try:
            page = await self.get_page()

            logger.info("attempting_login", email=email)

            # Navigate to login page (increased timeout for slow connections)
            await page.goto(
                "https://www.linkedin.com/login", wait_until="networkidle", timeout=60000
            )

            # Fill in credentials
            await page.fill('input[id="username"]', email)
            await page.fill('input[id="password"]', password)

            # Click login button
            await page.click('button[type="submit"]')

            # Wait for navigation (use 'load' instead of 'networkidle' for LinkedIn)
            # LinkedIn keeps making requests, so networkidle may never happen
            await page.wait_for_load_state("load", timeout=60000)

            # Give extra time for post-login scripts
            await page.wait_for_timeout(3000)

            # Check if login was successful
            is_logged_in = await self.is_logged_in()

            if is_logged_in:
                # Save cookies for future sessions
                await self.save_cookies()
                logger.info("login_successful", email=email)
            else:
                logger.warning("login_failed", email=email)

            return is_logged_in

        except Exception as e:
            logger.error("login_error", error=str(e), email=email)
            raise ScraperError(
                message="Failed to login to LinkedIn",
                details={"error": str(e), "email": email},
            ) from e

    async def __aenter__(self):
        """Context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        await self.close()
        return False
