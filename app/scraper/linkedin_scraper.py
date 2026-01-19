"""
LinkedIn scraper using Playwright.

Scrapes LinkedIn messages with rate limiting and retry logic.
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError

from app.core.exceptions import ScraperError
from app.core.logging import get_logger
from app.core.profile import get_user_profile
from app.scraper.rate_limiter import AdaptiveRateLimiter, RateLimitConfig
from app.scraper.session_manager import SessionManager

logger = get_logger(__name__)


@dataclass
class LinkedInMessage:
    """Represents a LinkedIn message."""

    sender_name: str
    message_text: str
    timestamp: datetime
    conversation_url: str
    is_read: bool = False
    message_id: Optional[str] = None
    is_from_user: bool = False  # True if the last message is from the user (not recruiter)


@dataclass
class ScraperConfig:
    """Configuration for LinkedIn scraper."""

    # Credentials
    email: str
    password: str

    # Rate limiting
    max_requests_per_minute: int = 10
    min_delay_seconds: float = 3.0

    # Retry configuration
    max_retries: int = 3
    retry_delay: float = 5.0
    exponential_backoff: bool = True

    # Timeouts (seconds)
    page_timeout: int = 30
    navigation_timeout: int = 60

    # Scraping options
    headless: bool = True
    save_cookies: bool = True


class LinkedInScraper:
    """
    LinkedIn scraper with rate limiting and retry logic.

    Scrapes unread messages from LinkedIn inbox.
    """

    def __init__(self, config: ScraperConfig):
        """
        Initialize scraper.

        Args:
            config: Scraper configuration
        """
        self.config = config

        # Initialize session manager
        self.session_manager = SessionManager(headless=config.headless)

        # Initialize rate limiter
        rate_limit_config = RateLimitConfig(
            max_requests=config.max_requests_per_minute,
            time_window=60,
            min_delay=config.min_delay_seconds,
        )
        self.rate_limiter = AdaptiveRateLimiter(rate_limit_config)

        self._is_initialized = False

        logger.info(
            "scraper_initialized",
            email=config.email,
            headless=config.headless,
        )

    async def initialize(self) -> None:
        """
        Initialize the scraper (start browser, login if needed).

        Raises:
            ScraperError: If initialization fails
        """
        try:
            logger.info("initializing_scraper")

            # Start browser session
            await self.session_manager.start()

            # Check if already logged in (from saved cookies)
            is_logged_in = await self.session_manager.is_logged_in()

            if not is_logged_in:
                logger.info("not_logged_in_attempting_login")
                success = await self.session_manager.login(
                    email=self.config.email, password=self.config.password
                )

                if not success:
                    raise ScraperError(
                        message="Failed to login to LinkedIn",
                        details={"email": self.config.email},
                    )

            self._is_initialized = True
            logger.info("scraper_initialized_successfully")

        except Exception as e:
            logger.error("scraper_initialization_failed", error=str(e))
            await self.cleanup()
            raise ScraperError(
                message="Failed to initialize scraper", details={"error": str(e)}
            ) from e

    async def cleanup(self) -> None:
        """Cleanup resources (close browser)."""
        try:
            logger.info("cleaning_up_scraper")

            if self.config.save_cookies and self._is_initialized:
                await self.session_manager.save_cookies()

            await self.session_manager.close()

            logger.info("scraper_cleanup_complete")

        except Exception as e:
            logger.error("cleanup_error", error=str(e))

    async def scrape_messages(
        self, limit: Optional[int] = None, unread_only: bool = True
    ) -> List[LinkedInMessage]:
        """
        Scrape messages from LinkedIn inbox.

        Args:
            limit: Maximum number of messages to scrape (None = all)
            unread_only: Only scrape unread messages

        Returns:
            List of LinkedIn messages

        Raises:
            ScraperError: If scraping fails
        """
        if not self._is_initialized:
            raise ScraperError(
                message="Scraper not initialized. Call initialize() first.",
                details={"method": "scrape_messages"},
            )

        messages: List[LinkedInMessage] = []

        try:
            logger.info(
                "starting_message_scrape", limit=limit, unread_only=unread_only
            )

            page = await self.session_manager.get_page()

            # Navigate to messaging page with rate limiting
            await self._navigate_with_retry(
                page, "https://www.linkedin.com/messaging/"
            )

            # Wait for messages to load - try multiple selectors
            # LinkedIn changes their class names frequently, so we try several
            selectors_to_try = [
                'ul[class*="msg-conversations-container"]',
                'ul.msg-conversations-container__conversations-list',
                'div[role="navigation"] ul',
                'main ul[class*="list"]',
            ]

            conversation_container = None
            for selector in selectors_to_try:
                try:
                    await page.wait_for_selector(selector, timeout=5000)
                    conversation_container = await page.query_selector(selector)
                    if conversation_container:
                        logger.info("conversation_container_found", selector=selector)
                        break
                except Exception as e:
                    logger.debug("selector_not_found", selector=selector, error=str(e))
                    continue

            if not conversation_container:
                # If no container found, try to get conversations directly
                logger.warning("conversation_container_not_found_trying_direct_selector")

            # Get all conversation items - try multiple selectors
            conversation_selectors = [
                'li[class*="msg-conversation-listitem"]',
                'li.msg-conversation-listitem__link',
                'ul li[data-test-id*="conversation"]',
                'main li[class*="conversation"]',
            ]

            conversations = []
            for selector in conversation_selectors:
                conversations = await page.query_selector_all(selector)
                if conversations:
                    logger.info("conversations_found", selector=selector, count=len(conversations))
                    break
                logger.debug("conversation_selector_not_found", selector=selector)

            # If still no conversations found, save debug info
            if not conversations:
                logger.error("no_conversations_found_saving_debug_info")
                try:
                    # Save screenshot
                    screenshot_path = "debug_linkedin_messaging.png"
                    await page.screenshot(path=screenshot_path, full_page=True)
                    logger.info("debug_screenshot_saved", path=screenshot_path)

                    # Save HTML
                    html_path = "debug_linkedin_messaging.html"
                    html_content = await page.content()
                    with open(html_path, "w", encoding="utf-8") as f:
                        f.write(html_content)
                    logger.info("debug_html_saved", path=html_path)

                    raise ScraperError(
                        message="No conversations found. Debug files saved.",
                        details={
                            "screenshot": screenshot_path,
                            "html": html_path,
                            "url": page.url,
                        },
                    )
                except Exception as e:
                    logger.error("failed_to_save_debug_info", error=str(e))
                    raise ScraperError(
                        message="No conversations found and failed to save debug info",
                        details={"error": str(e)},
                    ) from e

            logger.info("conversations_found", count=len(conversations))

            # Process each conversation
            for idx, conversation in enumerate(conversations):
                if limit and len(messages) >= limit:
                    break

                try:
                    # Check if conversation is unread (if filtering)
                    if unread_only:
                        # Try multiple selectors for unread indicator
                        unread_selectors = [
                            '[data-test-icon="unseen-icon"]',
                            '[class*="unseen"]',
                            '[class*="unread"]',
                            'div[class*="notification-badge"]',
                        ]

                        is_unread = False
                        for selector in unread_selectors:
                            unread_indicator = await conversation.query_selector(selector)
                            if unread_indicator:
                                is_unread = True
                                break

                        if not is_unread:
                            continue

                    # Click on conversation to open it
                    await conversation.click()
                    await asyncio.sleep(1)  # Wait for message to load

                    # Extract message details
                    message = await self._extract_message_from_conversation(page)

                    if message:
                        messages.append(message)
                        logger.info(
                            "message_extracted",
                            sender=message.sender_name,
                            message_id=idx,
                        )

                    # Rate limiting between conversations
                    self.rate_limiter.wait_if_needed()

                except Exception as e:
                    logger.warning(
                        "failed_to_process_conversation",
                        conversation_index=idx,
                        error=str(e),
                    )
                    continue

            logger.info("message_scrape_complete", messages_found=len(messages))

            return messages

        except Exception as e:
            logger.error("message_scrape_failed", error=str(e))
            raise ScraperError(
                message="Failed to scrape messages", details={"error": str(e)}
            ) from e

    async def _extract_message_from_conversation(
        self, page: Page
    ) -> Optional[LinkedInMessage]:
        """
        Extract message details from the currently open conversation.

        Args:
            page: Playwright page

        Returns:
            LinkedInMessage or None if extraction fails
        """
        try:
            # Wait for message content to load - try multiple selectors
            message_list_selectors = [
                'div[class*="msg-s-message-list"]',
                'div.msg-s-message-list-container',
                'main div[role="main"]',
            ]

            message_list_found = False
            for selector in message_list_selectors:
                try:
                    await page.wait_for_selector(selector, timeout=5000)
                    message_list_found = True
                    logger.debug("message_list_found", selector=selector)
                    break
                except Exception:
                    continue

            if not message_list_found:
                logger.warning("message_list_not_found_continuing_anyway")

            # Get sender name from header - try multiple selectors
            sender_selectors = [
                'h2[class*="msg-entity-lockup__entity-title"]',
                'h2.msg-entity-lockup__entity-title',
                'header h2',
                'div[class*="thread-details"] h2',
            ]

            sender_name = "Unknown"
            for selector in sender_selectors:
                sender_element = await page.query_selector(selector)
                if sender_element:
                    sender_name = await sender_element.inner_text()
                    logger.debug("sender_found", selector=selector, name=sender_name)
                    break

            # Get the most recent message text - try multiple selectors
            messages_list_selectors = [
                'li[class*="msg-s-message-list__event"]',
                'ul.msg-s-message-list li',
                'div[class*="message-item"]',
                'div[class*="msg-s-event-listitem"]',
            ]

            messages_list = []
            for selector in messages_list_selectors:
                messages_list = await page.query_selector_all(selector)
                if messages_list:
                    logger.debug("messages_list_found", selector=selector, count=len(messages_list))
                    break

            if not messages_list:
                logger.warning("no_messages_found_in_conversation")
                return None

            # Get the last message (most recent)
            last_message = messages_list[-1]

            # Check if the last message is from the user
            # Use multiple detection strategies
            is_from_user = False

            # Strategy 1: Check message classes for "self" indicator
            try:
                class_attr = await last_message.get_attribute("class")
                if class_attr:
                    is_from_user = "self" in class_attr.lower()
                    logger.debug("class_check", is_from_user=is_from_user, classes=class_attr)
            except Exception as e:
                logger.debug("class_check_failed", error=str(e))

            # Strategy 2: Check for "You" indicator in the message
            # LinkedIn sometimes adds text like "You" before user's messages
            if not is_from_user:
                try:
                    # Look for "You" indicator - LinkedIn adds this before user's own messages
                    you_indicator = await last_message.query_selector('[data-test-link-to-profile-for="self"]')
                    if you_indicator:
                        is_from_user = True
                        logger.debug("you_indicator_found", is_from_user=True)
                except Exception as e:
                    logger.debug("you_indicator_check_failed", error=str(e))

            # Strategy 3: Check if sender name contains user's name
            # This is less reliable but can work as fallback
            if not is_from_user:
                try:
                    # Get all message elements to check who sent the last one
                    # Look for message sender info within the message
                    sender_in_message = await last_message.query_selector('[data-test-id*="sender"]')
                    if sender_in_message:
                        sender_text = await sender_in_message.inner_text()
                        # Check if it says "You" or similar
                        is_from_user = sender_text.lower().strip() in ["you", "tú", "tu"]
                        logger.debug("sender_text_check", is_from_user=is_from_user, sender_text=sender_text)
                except Exception as e:
                    logger.debug("sender_text_check_failed", error=str(e))

            # Strategy 4: Analyze message content for user signature/name
            # This is a heuristic approach - look for common patterns in user's own messages
            if not is_from_user:
                try:
                    # Get the message text to check for signature
                    temp_msg_text = await last_message.inner_text()
                    lower_text = temp_msg_text.lower().strip()

                    # Get user profile to extract name variations
                    try:
                        user_profile = get_user_profile()
                        user_name_variations = user_profile.name_variations
                        logger.debug("loaded_user_profile", name=user_profile.name, variations=user_name_variations)
                    except Exception as profile_err:
                        logger.warning("failed_to_load_user_profile", error=str(profile_err))
                        user_name_variations = []

                    # Build signature list: user's name variations + common closing phrases
                    common_closings = [
                        "¡abrazo!", "abrazo!", "saludos", "thanks", "thank you",
                        "regards", "best regards", "cheers", "cordialmente",
                        "un abrazo", "muchas gracias"
                    ]

                    # Combine user's names with common closings
                    user_signatures = user_name_variations + common_closings

                    # Check if message ends with user signature
                    for signature in user_signatures:
                        if signature and lower_text.endswith(signature.lower()):
                            is_from_user = True
                            logger.debug("signature_detected", is_from_user=True, signature=signature)
                            break
                except Exception as e:
                    logger.debug("signature_check_failed", error=str(e))

            logger.info("message_sender_detection_result", is_from_user=is_from_user)

            # DEBUG: Save HTML if detection might be wrong (for debugging)
            # Uncomment this to debug detection issues
            # try:
            #     if not is_from_user:
            #         msg_html = await last_message.inner_html()
            #         with open(f"debug_message_{datetime.now().timestamp()}.html", "w") as f:
            #             f.write(msg_html)
            #         logger.debug("debug_html_saved")
            # except Exception as e:
            #     logger.debug("failed_to_save_debug_html", error=str(e))

            # Extract message text - try multiple selectors
            message_text_selectors = [
                'p[class*="msg-s-event-listitem__body"]',
                'div[class*="msg-s-event-listitem__body"]',
                'div.msg-s-event-listitem__message-body',
                'p[dir="ltr"]',
            ]

            message_text = ""
            for selector in message_text_selectors:
                message_element = await last_message.query_selector(selector)
                if message_element:
                    message_text = await message_element.inner_text()
                    logger.debug("message_text_found", selector=selector)
                    break

            if not message_text:
                # Fallback: get all text from the message element
                message_text = await last_message.inner_text()
                logger.debug("message_text_extracted_from_full_element")

            # Get conversation URL
            conversation_url = page.url

            # Create message object
            message = LinkedInMessage(
                sender_name=sender_name.strip(),
                message_text=message_text.strip(),
                timestamp=datetime.now(),  # LinkedIn doesn't always show exact timestamps
                conversation_url=conversation_url,
                is_read=False,
                is_from_user=is_from_user,
            )

            return message

        except Exception as e:
            logger.error("failed_to_extract_message", error=str(e))
            return None

    async def _navigate_with_retry(
        self, page: Page, url: str, retries: int = 3
    ) -> None:
        """
        Navigate to URL with retry logic.

        Args:
            page: Playwright page
            url: URL to navigate to
            retries: Number of retries

        Raises:
            ScraperError: If navigation fails after all retries
        """
        for attempt in range(retries):
            try:
                logger.debug("navigating_to_url", url=url, attempt=attempt + 1)

                # Rate limiting
                self.rate_limiter.wait_if_needed()

                # Navigate (use 'load' as LinkedIn keeps making requests)
                await page.goto(url, wait_until="load", timeout=60000)
                await page.wait_for_timeout(2000)  # Give time for initial scripts

                # Success
                self.rate_limiter.report_success()
                logger.info("navigation_successful", url=url)
                return

            except PlaywrightTimeoutError as e:
                logger.warning(
                    "navigation_timeout",
                    url=url,
                    attempt=attempt + 1,
                    retries=retries,
                )

                if attempt == retries - 1:
                    raise ScraperError(
                        message="Navigation timed out after retries",
                        details={"url": url, "error": str(e)},
                    ) from e

                # Exponential backoff
                delay = self.config.retry_delay * (2**attempt)
                logger.info("retrying_navigation", delay=delay)
                await asyncio.sleep(delay)

            except Exception as e:
                logger.error("navigation_error", url=url, error=str(e))

                # Report rate limit error if detected
                if "429" in str(e) or "rate limit" in str(e).lower():
                    self.rate_limiter.report_rate_limit_error()

                if attempt == retries - 1:
                    raise ScraperError(
                        message="Navigation failed after retries",
                        details={"url": url, "error": str(e)},
                    ) from e

                # Exponential backoff
                delay = self.config.retry_delay * (2**attempt)
                await asyncio.sleep(delay)

    async def get_unread_count(self) -> int:
        """
        Get the number of unread messages.

        Returns:
            Number of unread messages

        Raises:
            ScraperError: If failed to get count
        """
        if not self._is_initialized:
            raise ScraperError(
                message="Scraper not initialized",
                details={"method": "get_unread_count"},
            )

        try:
            page = await self.session_manager.get_page()

            # Navigate to messaging
            await self._navigate_with_retry(
                page, "https://www.linkedin.com/messaging/"
            )

            # Count unread indicators - try multiple selectors
            unread_selectors = [
                '[data-test-icon="unseen-icon"]',
                '[class*="unseen"]',
                '[class*="unread"]',
                'div[class*="notification-badge"]',
            ]

            count = 0
            for selector in unread_selectors:
                unread_indicators = await page.query_selector_all(selector)
                if unread_indicators:
                    count = len(unread_indicators)
                    logger.debug("unread_indicator_found", selector=selector, count=count)
                    break

            logger.info("unread_count_retrieved", count=count)

            return count

        except Exception as e:
            logger.error("failed_to_get_unread_count", error=str(e))
            raise ScraperError(
                message="Failed to get unread count", details={"error": str(e)}
            ) from e

    async def mark_as_read(self, conversation_url: str) -> bool:
        """
        Mark a conversation as read.

        Args:
            conversation_url: URL of the conversation

        Returns:
            True if successful, False otherwise
        """
        try:
            page = await self.session_manager.get_page()

            # Navigate to conversation
            await self._navigate_with_retry(page, conversation_url)

            # Wait a moment for LinkedIn to register it as read
            await asyncio.sleep(2)

            logger.info("conversation_marked_as_read", url=conversation_url)

            return True

        except Exception as e:
            logger.error("failed_to_mark_as_read", error=str(e), url=conversation_url)
            return False

    async def __aenter__(self):
        """Context manager entry."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        await self.cleanup()
        return False
