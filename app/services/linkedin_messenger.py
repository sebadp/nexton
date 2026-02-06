"""
LinkedIn message sending service.

Handles sending responses to LinkedIn conversations using Playwright.
"""

import structlog
from playwright.async_api import Page
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from app.core.config import settings
from app.core.exceptions import ScraperError
from app.database.models import PendingResponse
from app.database.repositories import PendingResponseRepository
from app.scraper.session_manager import SessionManager

logger = structlog.get_logger(__name__)


class LinkedInMessenger:
    """Service for sending messages to LinkedIn."""

    def __init__(
        self, email: str | None = None, password: str | None = None, headless: bool = True
    ):
        """
        Initialize LinkedIn messenger.

        Args:
            email: LinkedIn email (uses settings if not provided)
            password: LinkedIn password (uses settings if not provided)
            headless: Run browser in headless mode
        """
        self.email = email or settings.LINKEDIN_EMAIL
        self.password = password or settings.LINKEDIN_PASSWORD
        self.session_manager = SessionManager(headless=headless)
        self._is_initialized = False

        logger.info("linkedin_messenger_initialized", email=self.email, headless=headless)

    async def initialize(self) -> None:
        """
        Initialize the messenger (start browser, login).

        Raises:
            ScraperError: If initialization fails
        """
        if self._is_initialized:
            logger.debug("linkedin_messenger_already_initialized")
            return

        try:
            logger.info("initializing_linkedin_messenger")

            # Start browser session
            await self.session_manager.start()
            page = await self.session_manager.get_page()

            # Login to LinkedIn
            await self._login(page)

            self._is_initialized = True
            logger.info("linkedin_messenger_initialized_successfully")

        except Exception as e:
            logger.error("linkedin_messenger_initialization_failed", error=str(e), exc_info=True)
            await self.cleanup()
            raise ScraperError(
                message="Failed to initialize LinkedIn messenger", details={"error": str(e)}
            ) from e

    async def _login(self, page: Page) -> None:
        """
        Login to LinkedIn.

        Args:
            page: Playwright page

        Raises:
            ScraperError: If login fails
        """
        try:
            logger.info("logging_into_linkedin", email=self.email)

            # Navigate to LinkedIn login
            await page.goto("https://www.linkedin.com/login", wait_until="load", timeout=60000)

            # Fill credentials
            await page.fill('input[id="username"]', self.email)
            await page.fill('input[id="password"]', self.password)

            # Click login button
            await page.click('button[type="submit"]')

            # Wait for navigation (either to feed or checkpoint)
            await page.wait_for_load_state("load", timeout=60000)
            await page.wait_for_timeout(3000)  # Give time for post-login scripts

            # Check if login was successful
            current_url = page.url
            if "checkpoint" in current_url or "challenge" in current_url:
                raise ScraperError(
                    message="LinkedIn login requires additional verification",
                    details={"url": current_url},
                )

            if "feed" not in current_url and "mynetwork" not in current_url:
                raise ScraperError(
                    message="LinkedIn login failed",
                    details={"url": current_url},
                )

            logger.info("linkedin_login_successful")

        except PlaywrightTimeoutError as e:
            logger.error("linkedin_login_timeout", error=str(e))
            raise ScraperError(message="LinkedIn login timeout", details={"error": str(e)}) from e

        except Exception as e:
            logger.error("linkedin_login_failed", error=str(e), exc_info=True)
            raise ScraperError(
                message="Failed to login to LinkedIn", details={"error": str(e)}
            ) from e

    async def send_message(self, conversation_url: str, message: str) -> bool:
        """
        Send a message to a LinkedIn conversation.

        Args:
            conversation_url: URL of the conversation
            message: Message text to send

        Returns:
            bool: True if sent successfully

        Raises:
            ScraperError: If not initialized or sending fails
        """
        if not self._is_initialized:
            raise ScraperError(
                message="Messenger not initialized. Call initialize() first.",
                details={"method": "send_message"},
            )

        try:
            logger.info(
                "sending_linkedin_message",
                conversation_url=conversation_url,
                message_length=len(message),
            )

            page = await self.session_manager.get_page()

            # Navigate to conversation
            await page.goto(conversation_url, wait_until="load", timeout=60000)
            await page.wait_for_timeout(2000)  # Give time for page to initialize

            # Wait for message box to load
            await page.wait_for_selector('div[role="textbox"]', timeout=10000)

            # Fill message box
            message_box = page.locator('div[role="textbox"]').first
            await message_box.click()
            await message_box.fill(message)

            # Wait a bit for the message to be recognized
            await page.wait_for_timeout(500)

            # Find and click send button
            send_button = page.locator('button[type="submit"]').first
            await send_button.click()

            # Wait for message to be sent
            await page.wait_for_timeout(2000)

            logger.info("linkedin_message_sent_successfully", conversation_url=conversation_url)

            return True

        except PlaywrightTimeoutError as e:
            logger.error(
                "linkedin_message_send_timeout", conversation_url=conversation_url, error=str(e)
            )
            raise ScraperError(
                message="Timeout while sending LinkedIn message",
                details={"conversation_url": conversation_url, "error": str(e)},
            ) from e

        except Exception as e:
            logger.error(
                "linkedin_message_send_failed",
                conversation_url=conversation_url,
                error=str(e),
                exc_info=True,
            )
            raise ScraperError(
                message="Failed to send LinkedIn message",
                details={"conversation_url": conversation_url, "error": str(e)},
            ) from e

    async def cleanup(self) -> None:
        """Cleanup resources (close browser)."""
        try:
            await self.session_manager.close()
            self._is_initialized = False
            logger.info("linkedin_messenger_cleaned_up")
        except Exception as e:
            logger.warning("linkedin_messenger_cleanup_failed", error=str(e))


class LinkedInResponseService:
    """Service for sending approved responses to LinkedIn."""

    def __init__(self, messenger: LinkedInMessenger | None = None):
        """
        Initialize response service.

        Args:
            messenger: LinkedIn messenger (creates new if not provided)
        """
        self.messenger = messenger or LinkedInMessenger()

    async def send_pending_response(
        self,
        pending_response: PendingResponse,
        repository: PendingResponseRepository,
    ) -> bool:
        """
        Send a pending response to LinkedIn.

        Args:
            pending_response: Pending response to send
            repository: Repository for updating status

        Returns:
            bool: True if sent successfully
        """
        if pending_response.status != "approved":
            logger.warning(
                "cannot_send_non_approved_response",
                response_id=pending_response.id,
                status=pending_response.status,
            )
            return False

        try:
            # Initialize messenger if needed
            if not self.messenger._is_initialized:
                await self.messenger.initialize()

            # Get the conversation URL from the opportunity
            # TODO: Store conversation URL in Opportunity model
            # For now, we'll need to construct it or store it
            conversation_url = (
                f"https://www.linkedin.com/messaging/thread/{pending_response.opportunity_id}/"
            )

            # Send the message
            message_to_send = pending_response.final_response or pending_response.original_response
            await self.messenger.send_message(conversation_url, message_to_send)

            # Mark as sent
            await repository.mark_as_sent(pending_response.id)

            logger.info(
                "pending_response_sent_successfully",
                response_id=pending_response.id,
                opportunity_id=pending_response.opportunity_id,
            )

            return True

        except Exception as e:
            # Mark as failed
            await repository.mark_as_failed(pending_response.id, error_message=str(e))

            logger.error(
                "pending_response_send_failed",
                response_id=pending_response.id,
                opportunity_id=pending_response.opportunity_id,
                error=str(e),
                exc_info=True,
            )

            return False

    async def cleanup(self) -> None:
        """Cleanup messenger resources."""
        await self.messenger.cleanup()
