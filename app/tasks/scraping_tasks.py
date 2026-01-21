"""
Celery tasks for LinkedIn scraping.

Background tasks for scraping LinkedIn messages and processing them
through the DSPy pipeline.
"""

import asyncio
import os
from typing import Dict, List

from celery import Task

from app.core.exceptions import ScraperError
from app.core.logging import get_logger
from app.scraper import LinkedInScraper, ScraperConfig
from app.tasks.celery_app import celery_app
from app.tasks.processing_tasks import process_message

logger = get_logger(__name__)


class ScraperTask(Task):
    """
    Base task for scraping with cleanup.

    Ensures scraper resources are properly cleaned up after task execution.
    """

    _scraper = None

    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        """Cleanup after task completes."""
        if self._scraper:
            try:
                asyncio.run(self._scraper.cleanup())
            except Exception as e:
                logger.error("failed_to_cleanup_scraper", error=str(e))
            finally:
                self._scraper = None


@celery_app.task(
    name="app.tasks.scraping_tasks.scrape_linkedin_messages",
    base=ScraperTask,
    bind=True,
    max_retries=3,
    default_retry_delay=300,  # 5 minutes
)
def scrape_linkedin_messages(
    self, limit: int = 10, unread_only: bool = True
) -> Dict:
    """
    Scrape LinkedIn messages and queue them for processing.

    Args:
        limit: Maximum number of messages to scrape
        unread_only: Only scrape unread messages

    Returns:
        Dictionary with scraping results

    Raises:
        ScraperError: If scraping fails
    """
    logger.info(
        "scraping_task_started",
        task_id=self.request.id,
        limit=limit,
        unread_only=unread_only,
    )

    try:
        # Get credentials from environment
        email = os.getenv("LINKEDIN_EMAIL")
        password = os.getenv("LINKEDIN_PASSWORD")

        if not email or not password:
            raise ScraperError(
                message="LinkedIn credentials not configured",
                details={"missing": "LINKEDIN_EMAIL or LINKEDIN_PASSWORD"},
            )

        # Create scraper config
        config = ScraperConfig(
            email=email,
            password=password,
            headless=os.getenv("SCRAPER_HEADLESS", "true").lower() == "true",
            max_requests_per_minute=int(
                os.getenv("SCRAPER_MAX_REQUESTS_PER_MINUTE", "10")
            ),
            min_delay_seconds=float(os.getenv("SCRAPER_MIN_DELAY_SECONDS", "3.0")),
        )

        # Run scraper
        async def run_scraper():
            async with LinkedInScraper(config) as scraper:
                self._scraper = scraper  # Store for cleanup
                messages = await scraper.scrape_messages(
                    limit=limit, unread_only=unread_only
                )
                return messages

        # Execute async scraper
        messages = asyncio.run(run_scraper())

        logger.info(
            "scraping_completed",
            task_id=self.request.id,
            message_count=len(messages),
        )

        # Queue each message for processing
        queued_tasks = []
        for msg in messages:
            task = process_message.delay(
                recruiter_name=msg.sender_name,
                raw_message=msg.message_text,
                conversation_url=msg.conversation_url,
            )
            queued_tasks.append(task.id)

        logger.info(
            "messages_queued_for_processing",
            task_id=self.request.id,
            queued_count=len(queued_tasks),
        )

        return {
            "status": "success",
            "task_id": self.request.id,
            "messages_scraped": len(messages),
            "messages_queued": len(queued_tasks),
            "queued_task_ids": queued_tasks,
        }

    except ScraperError as e:
        logger.error(
            "scraping_failed",
            task_id=self.request.id,
            error=str(e),
            details=e.details,
        )

        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=60 * (2**self.request.retries))

    except Exception as e:
        logger.error(
            "unexpected_scraping_error", task_id=self.request.id, error=str(e)
        )
        raise


@celery_app.task(
    name="app.tasks.scraping_tasks.scrape_unread_messages",
    base=ScraperTask,
    bind=True,
)
def scrape_unread_messages(self) -> Dict:
    """
    Scrape only unread messages (utility task).

    This task can be called manually. For scheduled scraping,
    use scrape_and_send_daily_summary which runs daily at 9 AM.

    Returns:
        Dictionary with scraping results
    """
    logger.info("periodic_scraping_started", task_id=self.request.id)

    # Call main scraping task with unread_only=True
    return scrape_linkedin_messages(limit=20, unread_only=True)


@celery_app.task(
    name="app.tasks.scraping_tasks.scrape_and_send_daily_summary",
    base=ScraperTask,
    bind=True,
)
def scrape_and_send_daily_summary(self) -> Dict:
    """
    Daily task: Scrape LinkedIn, process new messages, and send ONE summary email.

    This runs once per day at 9 AM and:
    1. Scrapes unread LinkedIn messages
    2. Processes each through DSPy pipeline
    3. Generates AI responses for each
    4. Sends ONE email with summary of all new opportunities

    Returns:
        Dictionary with summary results
    """
    import asyncio
    from app.database.base import AsyncSessionLocal
    from app.database.repositories import OpportunityRepository
    from app.dspy_modules.pipeline import get_pipeline
    from app.dspy_modules.profile_loader import get_profile
    from app.notifications.service import NotificationService

    logger.info("daily_scraping_started", task_id=self.request.id)

    # 1. Scrape unread messages and process them
    async def scrape_and_process_messages():
        # Get credentials from environment
        email = os.getenv("LINKEDIN_EMAIL")
        password = os.getenv("LINKEDIN_PASSWORD")

        if not email or not password:
            raise ScraperError(
                message="LinkedIn credentials not configured",
                details={"missing": "LINKEDIN_EMAIL or LINKEDIN_PASSWORD"},
            )

        # Create scraper config
        from app.scraper import LinkedInScraper, ScraperConfig
        config = ScraperConfig(
            email=email,
            password=password,
            headless=os.getenv("SCRAPER_HEADLESS", "true").lower() == "true",
            max_requests_per_minute=int(
                os.getenv("SCRAPER_MAX_REQUESTS_PER_MINUTE", "10")
            ),
            min_delay_seconds=float(os.getenv("SCRAPER_MIN_DELAY_SECONDS", "3.0")),
        )

        # Scrape messages
        async with LinkedInScraper(config) as scraper:
            messages = await scraper.scrape_messages(limit=50, unread_only=True)

        logger.info(
            "messages_scraped",
            task_id=self.request.id,
            message_count=len(messages),
        )

        if not messages:
            return []

        # Process each message through pipeline and create opportunities
        async with AsyncSessionLocal() as session:
            repo = OpportunityRepository(session)
            pipeline = get_pipeline()
            profile = get_profile()

            opportunities = []

            for msg in messages:
                try:
                    # Process through pipeline
                    result = pipeline.forward(
                        message=msg.message_text,
                        recruiter_name=msg.sender_name,
                        profile=profile,
                    )

                    # Create opportunity
                    opportunity = await repo.create(
                        recruiter_name=result.recruiter_name,
                        raw_message=msg.message_text,
                        company=result.extracted.company,
                        role=result.extracted.role,
                        seniority=result.extracted.seniority,
                        tech_stack=result.extracted.tech_stack,
                        salary_min=result.extracted.salary_min,
                        salary_max=result.extracted.salary_max,
                        currency=result.extracted.currency,
                        remote_policy=result.extracted.remote_policy,
                        location=result.extracted.location,
                        tech_stack_score=result.scoring.tech_stack_score,
                        salary_score=result.scoring.salary_score,
                        seniority_score=result.scoring.seniority_score,
                        company_score=result.scoring.company_score,
                        total_score=result.scoring.total_score,
                        tier=result.scoring.tier,
                        ai_response=result.ai_response,
                        status="processed",
                        processing_time_ms=result.processing_time_ms or 0,
                    )

                    await session.commit()
                    opportunities.append(opportunity)

                    logger.info(
                        "opportunity_created_from_scrape",
                        opportunity_id=opportunity.id,
                        score=opportunity.total_score,
                        tier=opportunity.tier,
                    )

                except Exception as e:
                    logger.error("failed_to_process_message", error=str(e), sender=msg.sender_name)
                    await session.rollback()
                    continue

            return opportunities

    try:
        opportunities = asyncio.run(scrape_and_process_messages())
    except Exception as e:
        logger.error("scraping_and_processing_failed", error=str(e))
        return {
            "status": "error",
            "error": str(e),
            "messages_found": 0,
            "opportunities_created": 0,
        }

    # Check if any opportunities were created
    if not opportunities:
        logger.info("no_new_messages")
        return {
            "status": "no_new_messages",
            "messages_found": 0,
            "opportunities_created": 0,
        }

    # 3. Send ONE summary email with all opportunities
    if opportunities:
        try:
            notification_service = NotificationService()

            # Send daily summary email (async call)
            asyncio.run(notification_service.send_daily_summary(opportunities))

            logger.info(
                "daily_summary_sent",
                opportunities_count=len(opportunities),
                task_id=self.request.id,
            )
        except Exception as e:
            logger.error("failed_to_send_summary", error=str(e))

    return {
        "status": "success",
        "messages_found": len(opportunities),
        "opportunities_created": len(opportunities),
        "summary_sent": len(opportunities) > 0,
    }


@celery_app.task(
    name="app.tasks.scraping_tasks.get_unread_count",
    base=ScraperTask,
    bind=True,
)
def get_unread_count(self) -> Dict:
    """
    Get count of unread messages without scraping content.

    Returns:
        Dictionary with unread count

    Raises:
        ScraperError: If check fails
    """
    logger.info("checking_unread_count", task_id=self.request.id)

    try:
        email = os.getenv("LINKEDIN_EMAIL")
        password = os.getenv("LINKEDIN_PASSWORD")

        if not email or not password:
            raise ScraperError(
                message="LinkedIn credentials not configured",
                details={"missing": "LINKEDIN_EMAIL or LINKEDIN_PASSWORD"},
            )

        config = ScraperConfig(
            email=email,
            password=password,
            headless=True,
        )

        async def check_unread():
            async with LinkedInScraper(config) as scraper:
                self._scraper = scraper
                count = await scraper.get_unread_count()
                return count

        count = asyncio.run(check_unread())

        logger.info("unread_count_retrieved", task_id=self.request.id, count=count)

        return {"status": "success", "unread_count": count, "task_id": self.request.id}

    except Exception as e:
        logger.error("failed_to_get_unread_count", task_id=self.request.id, error=str(e))
        raise


@celery_app.task(
    name="app.tasks.scraping_tasks.mark_conversation_as_read",
    bind=True,
)
def mark_conversation_as_read(self, conversation_url: str) -> Dict:
    """
    Mark a LinkedIn conversation as read.

    Args:
        conversation_url: URL of the conversation to mark as read

    Returns:
        Dictionary with operation result
    """
    logger.info(
        "marking_conversation_as_read",
        task_id=self.request.id,
        url=conversation_url,
    )

    try:
        email = os.getenv("LINKEDIN_EMAIL")
        password = os.getenv("LINKEDIN_PASSWORD")

        if not email or not password:
            raise ScraperError(
                message="LinkedIn credentials not configured",
                details={"missing": "LINKEDIN_EMAIL or LINKEDIN_PASSWORD"},
            )

        config = ScraperConfig(email=email, password=password, headless=True)

        async def mark_read():
            async with LinkedInScraper(config) as scraper:
                success = await scraper.mark_as_read(conversation_url)
                return success

        success = asyncio.run(mark_read())

        logger.info(
            "conversation_marked_as_read",
            task_id=self.request.id,
            url=conversation_url,
            success=success,
        )

        return {
            "status": "success" if success else "failed",
            "conversation_url": conversation_url,
            "task_id": self.request.id,
        }

    except Exception as e:
        logger.error(
            "failed_to_mark_as_read",
            task_id=self.request.id,
            url=conversation_url,
            error=str(e),
        )
        raise


# Monitoring task
@celery_app.task(name="app.tasks.scraping_tasks.test_scraper_health")
def test_scraper_health() -> Dict:
    """
    Test scraper health by checking login status.

    Returns:
        Dictionary with health status
    """
    logger.info("testing_scraper_health")

    try:
        email = os.getenv("LINKEDIN_EMAIL")
        password = os.getenv("LINKEDIN_PASSWORD")

        if not email or not password:
            return {
                "status": "unhealthy",
                "reason": "credentials_not_configured",
            }

        config = ScraperConfig(email=email, password=password, headless=True)

        async def check_health():
            async with LinkedInScraper(config) as scraper:
                # Just check if we can initialize
                return True

        healthy = asyncio.run(check_health())

        return {
            "status": "healthy" if healthy else "unhealthy",
            "scraper": "available",
        }

    except Exception as e:
        logger.error("scraper_health_check_failed", error=str(e))
        return {"status": "unhealthy", "error": str(e)}
