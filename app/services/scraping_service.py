"""
Scraping service for lite mode.

Provides synchronous scraping without Celery/Redis dependencies.
"""

from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import get_logger
from app.scraper import LinkedInScraper, ScraperConfig

logger = get_logger(__name__)


class ScrapingService:
    """
    Scraping service for lite mode.

    Runs LinkedIn scraping synchronously without Celery background tasks.
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize scraping service.

        Args:
            db: Database session
        """
        self.db = db
        self._scraper: LinkedInScraper | None = None

    async def scrape_sync(
        self,
        limit: int = 10,
        unread_only: bool = True,
    ) -> dict[str, Any]:
        """
        Run scraping synchronously (for lite mode).

        Args:
            limit: Maximum messages to scrape
            unread_only: Only scrape unread messages

        Returns:
            Dictionary with scraping results
        """
        logger.info(
            "lite_mode_scraping_started",
            limit=limit,
            unread_only=unread_only,
        )

        start_time = datetime.utcnow()
        results: dict[str, Any] = {
            "status": "started",
            "messages_found": 0,
            "messages_processed": 0,
            "opportunities_created": 0,
            "errors": [],
        }
        errors: list[str] = results["errors"]

        try:
            # Initialize scraper
            config = ScraperConfig(
                email=settings.LINKEDIN_EMAIL,
                password=settings.LINKEDIN_PASSWORD,
                headless=settings.SCRAPER_HEADLESS,
            )

            self._scraper = LinkedInScraper(config)
            await self._scraper.initialize()

            # Scrape messages
            logger.info("lite_mode_scraping_messages")
            messages = await self._scraper.scrape_messages(
                limit=limit,
                unread_only=unread_only,
            )

            results["messages_found"] = len(messages)
            logger.info("lite_mode_messages_found", count=len(messages))

            if not messages:
                results["status"] = "completed"
                results["message"] = "No new messages found"
                return results

            # Process each message through the pipeline
            from app.services.opportunity_service import OpportunityService

            service = OpportunityService(self.db, cache=None)  # No cache in lite mode

            for msg in messages:
                try:
                    logger.info(
                        "lite_mode_processing_message",
                        sender=msg.sender_name,
                    )

                    opportunity = await service.create_opportunity(
                        recruiter_name=msg.sender_name,
                        raw_message=msg.message_text,
                        message_timestamp=msg.timestamp,
                        use_cache=False,  # No Redis cache in lite mode
                    )

                    results["messages_processed"] = int(results["messages_processed"]) + 1
                    results["opportunities_created"] = int(results["opportunities_created"]) + 1

                    logger.info(
                        "lite_mode_opportunity_created",
                        opportunity_id=opportunity.id,
                        score=opportunity.total_score,
                        tier=opportunity.tier,
                    )

                except Exception as e:
                    error_msg = f"Failed to process message from {msg.sender_name}: {str(e)}"
                    logger.error("lite_mode_processing_error", error=error_msg)
                    errors.append(error_msg)

            # Calculate duration
            duration = (datetime.utcnow() - start_time).total_seconds()
            results["status"] = "completed"
            results["duration_seconds"] = duration
            results[
                "message"
            ] = f"Processed {results['messages_processed']} of {results['messages_found']} messages"

            logger.info(
                "lite_mode_scraping_completed",
                messages_found=results["messages_found"],
                messages_processed=results["messages_processed"],
                opportunities_created=results["opportunities_created"],
                duration_seconds=duration,
            )

            return results

        except Exception as e:
            logger.error("lite_mode_scraping_failed", error=str(e))
            results["status"] = "failed"
            results["error"] = str(e)
            return results

        finally:
            # Cleanup scraper
            if self._scraper:
                await self._scraper.cleanup()
                self._scraper = None
