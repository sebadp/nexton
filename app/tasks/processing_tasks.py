"""
Celery tasks for opportunity processing.

Background tasks for processing scraped messages through the DSPy pipeline
and storing results in the database.
"""

import asyncio
from datetime import datetime, timedelta

from app.core.exceptions import PipelineError
from app.core.logging import get_logger
from app.database.base import AsyncSessionLocal as async_session
from app.database.repositories import OpportunityRepository, PendingResponseRepository
from app.dspy_modules.pipeline import get_pipeline
from app.dspy_modules.profile_loader import get_profile
from app.tasks.celery_app import celery_app

logger = get_logger(__name__)


@celery_app.task(
    name="app.tasks.processing_tasks.process_message",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def process_message(
    self, recruiter_name: str, raw_message: str, conversation_url: str | None = None
) -> dict:
    """
    Process a LinkedIn message through the DSPy pipeline.

    This task:
    1. Runs the DSPy pipeline (extract → score → generate response)
    2. Stores the result in the database
    3. Returns the opportunity details

    Args:
        recruiter_name: Name of the recruiter
        raw_message: Raw message text
        conversation_url: Optional LinkedIn conversation URL

    Returns:
        Dictionary with processing results

    Raises:
        PipelineError: If processing fails
    """
    logger.info(
        "processing_message_started",
        task_id=self.request.id,
        recruiter_name=recruiter_name,
    )

    try:
        # Run async processing
        async def process():
            # Get pipeline and profile
            pipeline = get_pipeline()
            profile = get_profile()

            # Run pipeline
            result = pipeline.forward(
                message=raw_message,
                recruiter_name=recruiter_name,
                profile=profile,
            )

            # Store in database
            async with async_session() as session:
                repo = OpportunityRepository(session)

                # Use to_db_dict for comprehensive field mapping
                db_data = result.to_db_dict()
                opportunity = await repo.create(**db_data)

                await session.commit()

                # Create pending response if AI response was generated
                if opportunity.ai_response:
                    response_repo = PendingResponseRepository(session)
                    await response_repo.create(
                        opportunity_id=opportunity.id,
                        original_response=opportunity.ai_response,
                        status="pending",
                    )
                    await session.commit()

                    logger.info(
                        "pending_response_created",
                        opportunity_id=opportunity.id,
                    )

                return opportunity

        opportunity = asyncio.run(process())

        logger.info(
            "message_processed_successfully",
            task_id=self.request.id,
            opportunity_id=opportunity.id,
            score=opportunity.total_score,
            tier=opportunity.tier,
        )

        return {
            "status": "success",
            "task_id": self.request.id,
            "opportunity_id": opportunity.id,
            "total_score": opportunity.total_score,
            "tier": opportunity.tier,
            "company": opportunity.company,
            "role": opportunity.role,
        }

    except PipelineError as e:
        logger.error(
            "pipeline_error",
            task_id=self.request.id,
            error=str(e),
            details=e.details,
        )

        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=60 * (2**self.request.retries)) from e

    except Exception as e:
        logger.error("processing_failed", task_id=self.request.id, error=str(e))
        raise


@celery_app.task(name="app.tasks.processing_tasks.process_opportunity")
def process_opportunity(opportunity_id: int) -> dict:
    """
    Re-process an existing opportunity through the pipeline.

    Useful for:
    - Updating scores after profile changes
    - Regenerating responses
    - Fixing processing errors

    Args:
        opportunity_id: ID of the opportunity to reprocess

    Returns:
        Dictionary with processing results
    """
    logger.info("reprocessing_opportunity_started", opportunity_id=opportunity_id)

    async def reprocess():
        async with async_session() as session:
            repo = OpportunityRepository(session)

            # Get existing opportunity
            opportunity = await repo.get_by_id(opportunity_id)
            if not opportunity:
                raise ValueError(f"Opportunity {opportunity_id} not found")

            # Run pipeline
            pipeline = get_pipeline()
            profile = get_profile()

            result = pipeline.forward(
                message=opportunity.raw_message or "",
                recruiter_name=opportunity.recruiter_name or "Unknown",
                profile=profile,
            )

            # Update opportunity
            updated = await repo.update(
                opportunity_id=opportunity_id,
                company=result.extracted.company,
                role=result.extracted.role,
                tech_stack=result.extracted.tech_stack,
                tech_stack_score=result.scoring.tech_stack_score,
                salary_score=result.scoring.salary_score,
                seniority_score=result.scoring.seniority_score,
                company_score=result.scoring.company_score,
                total_score=result.scoring.total_score,
                tier=result.scoring.tier,
                ai_response=result.ai_response,
                status="reprocessed",
                processing_time_ms=result.processing_time_ms,
            )

            await session.commit()

            # Create new pending response if AI response was regenerated
            if result.ai_response:
                response_repo = PendingResponseRepository(session)
                await response_repo.create(
                    opportunity_id=opportunity_id,
                    original_response=result.ai_response,
                    status="pending",
                )
                await session.commit()

            return updated

    opportunity = asyncio.run(reprocess())

    logger.info(
        "opportunity_reprocessed",
        opportunity_id=opportunity_id,
        new_score=opportunity.total_score,
        new_tier=opportunity.tier,
    )

    return {
        "status": "success",
        "opportunity_id": opportunity_id,
        "total_score": opportunity.total_score,
        "tier": opportunity.tier,
    }


@celery_app.task(name="app.tasks.processing_tasks.cleanup_old_opportunities")
def cleanup_old_opportunities(days: int = 90) -> dict:
    """
    Clean up old opportunities (periodic task).

    Deletes opportunities older than specified days that are not
    marked as important (tier != HIGH_PRIORITY).

    Args:
        days: Delete opportunities older than this many days

    Returns:
        Dictionary with cleanup results
    """
    logger.info("cleanup_started", days=days)

    async def cleanup():
        async with async_session() as session:
            repo = OpportunityRepository(session)

            # Calculate cutoff date
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            # Get old, low-priority opportunities
            old_opportunities = await repo.get_all(
                min_score=0,  # Get all scores
                status="processed",
            )

            deleted_count = 0
            for opp in old_opportunities:
                # Skip high priority opportunities
                if opp.tier == "HIGH_PRIORITY":
                    continue

                # Skip recent opportunities
                if opp.created_at > cutoff_date:
                    continue

                # Delete
                await repo.delete(opp.id)
                deleted_count += 1

            await session.commit()

            return deleted_count

    deleted_count = asyncio.run(cleanup())

    logger.info("cleanup_completed", deleted_count=deleted_count)

    return {
        "status": "success",
        "deleted_count": deleted_count,
        "cutoff_days": days,
    }


@celery_app.task(name="app.tasks.processing_tasks.batch_process_messages")
def batch_process_messages(messages: list[dict]) -> dict:
    """
    Process multiple messages in a batch.

    Args:
        messages: List of message dictionaries with recruiter_name and raw_message

    Returns:
        Dictionary with batch processing results
    """
    logger.info("batch_processing_started", message_count=len(messages))

    results = []
    errors = []

    for msg in messages:
        try:
            result = process_message(
                recruiter_name=msg["recruiter_name"],
                raw_message=msg["raw_message"],
                conversation_url=msg.get("conversation_url"),
            )
            results.append(result)
        except Exception as e:
            logger.error(
                "batch_processing_item_failed",
                recruiter=msg.get("recruiter_name"),
                error=str(e),
            )
            errors.append({"message": msg, "error": str(e)})

    logger.info(
        "batch_processing_completed",
        total=len(messages),
        successful=len(results),
        failed=len(errors),
    )

    return {
        "status": "completed",
        "total_messages": len(messages),
        "successful": len(results),
        "failed": len(errors),
        "results": results,
        "errors": errors,
    }


@celery_app.task(name="app.tasks.processing_tasks.generate_daily_report")
def generate_daily_report() -> dict:
    """
    Generate a daily report of opportunities (periodic task).

    Returns:
        Dictionary with report statistics
    """
    logger.info("generating_daily_report")

    async def generate_report():
        async with async_session() as session:
            repo = OpportunityRepository(session)

            # Get today's date range
            today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            tomorrow = today + timedelta(days=1)

            # Get opportunities created today
            opportunities = await repo.get_by_date_range(start_date=today, end_date=tomorrow)

            # Calculate statistics
            total_count = len(opportunities)
            by_tier: dict[str, int] = {}
            by_company: dict[str, int] = {}

            for opp in opportunities:
                # Count by tier
                tier = opp.tier or "UNKNOWN"
                by_tier[tier] = by_tier.get(tier, 0) + 1

                # Count by company
                company = opp.company or "Unknown"
                by_company[company] = by_company.get(company, 0) + 1

            # Get average score
            scores = [opp.total_score for opp in opportunities if opp.total_score]
            avg_score = sum(scores) / len(scores) if scores else 0

            return {
                "date": today.isoformat(),
                "total_count": total_count,
                "by_tier": by_tier,
                "top_companies": dict(
                    sorted(by_company.items(), key=lambda x: x[1], reverse=True)[:5]
                ),
                "average_score": round(avg_score, 2),
            }

    report = asyncio.run(generate_report())

    logger.info("daily_report_generated", **report)

    return {"status": "success", "report": report}
