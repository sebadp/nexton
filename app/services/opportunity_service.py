"""
Opportunity service layer.

Business logic for opportunity management, integrating DSPy pipeline,
caching, and database operations.
"""

from collections.abc import Callable, Sequence
from contextvars import copy_context
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from app.cache import CacheKeys, RedisCache, generate_message_hash
from app.core.exceptions import OpportunityNotFoundError, PipelineError
from app.core.logging import get_logger
from app.database.models import Opportunity
from app.database.repositories import OpportunityRepository, PendingResponseRepository
from app.dspy_modules.models import OpportunityResult
from app.dspy_modules.pipeline import get_pipeline
from app.dspy_modules.profile_loader import get_profile
from app.observability import (
    add_span_attributes,
    add_span_event,
    observe,
    track_opportunity_created,
    track_opportunity_processing_time,
    track_opportunity_score,
    track_pipeline_execution,
)

logger = get_logger(__name__)


class OpportunityService:
    """
    Service layer for opportunity management.

    Orchestrates DSPy pipeline, caching, and database operations.
    """

    def __init__(
        self,
        db: AsyncSession,
        cache: RedisCache | None = None,
    ):
        """
        Initialize opportunity service.

        Args:
            db: Database session
            cache: Optional Redis cache (creates new if not provided)
        """
        self.db = db
        self.cache = cache or RedisCache()
        self.repository = OpportunityRepository(db)
        self.response_repository = PendingResponseRepository(db)
        self.pipeline = get_pipeline()
        self.profile = get_profile()

        logger.debug("opportunity_service_initialized")

    @observe(name="opportunity_service.create_opportunity")
    async def create_opportunity(
        self,
        recruiter_name: str,
        raw_message: str,
        message_timestamp: datetime | None = None,
        use_cache: bool = True,
        on_progress: Callable[[str, dict], None] | None = None,
    ) -> Opportunity:
        """
        Create and process a new opportunity.

        This method:
        1. Checks cache for existing pipeline result
        2. Runs DSPy pipeline if not cached
        3. Stores result in database
        4. Caches the result

        Args:
            recruiter_name: Name of the recruiter
            raw_message: Raw message content
            use_cache: Whether to use cache (default: True)
            on_progress: Optional callback for progress updates

        Returns:
            Created opportunity

        Raises:
            PipelineError: If processing fails
        """
        logger.info(
            "creating_opportunity",
            recruiter_name=recruiter_name,
            message_length=len(raw_message),
        )

        start_time = datetime.utcnow()

        try:
            # Generate cache key from message hash
            message_hash = generate_message_hash(raw_message)
            cache_key = CacheKeys.pipeline_result(message_hash)

            pipeline_result: OpportunityResult | None = None

            # Try to get from cache
            if use_cache:
                try:
                    cached_result = await self.cache.get(cache_key)
                    if cached_result:
                        pipeline_result = OpportunityResult(**cached_result)
                        logger.info("pipeline_result_from_cache", message_hash=message_hash)
                        add_span_event("cache_hit", {"message_hash": message_hash})
                        track_pipeline_execution("cached", 0.0)
                except Exception as e:
                    logger.warning("cache_get_failed", error=str(e))

            # Run pipeline if not cached
            if pipeline_result is None:
                pipeline_start = datetime.utcnow()

                # Run blocking DSPy pipeline in threadpool to allow streaming
                # Use copy_context().run to propagate OTel/Langfuse context to the thread
                ctx = copy_context()
                pipeline_result = await run_in_threadpool(
                    ctx.run,
                    self.pipeline,  # Call via __call__ to fix DSPy warning
                    message=raw_message,
                    recruiter_name=recruiter_name,
                    profile=self.profile,
                    on_progress=on_progress,
                )
                assert pipeline_result is not None

                add_span_attributes(
                    score=pipeline_result.scoring.total_score,
                    tier=pipeline_result.scoring.tier,
                    company=pipeline_result.extracted.company,
                )

                # Track pipeline execution metrics
                pipeline_duration = (datetime.utcnow() - pipeline_start).total_seconds()
                track_pipeline_execution("success", pipeline_duration)

                # Cache the result
                if use_cache:
                    try:
                        await self.cache.set(
                            cache_key,
                            pipeline_result.dict(),
                            ttl=CacheKeys.TTL_LONG,
                        )
                        logger.debug("pipeline_result_cached", message_hash=message_hash)
                    except Exception as e:
                        logger.warning("cache_set_failed", error=str(e))

            # Calculate processing time
            processing_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)

            # Create opportunity in database
            # Use to_db_dict to ensure all metadata is correctly mapped
            # (processing_status, conversation_state, hard_filter_results, etc.)
            opp_data = pipeline_result.to_db_dict()

            # Override specific fields
            opp_data["status"] = "processed"  # Lifecycle status is always processed here
            opp_data["processing_time_ms"] = processing_time_ms
            opp_data["message_timestamp"] = message_timestamp

            # Create opportunity with manual tracing attributes if needed,
            # but relying on @observe decorator on the repository method would be better.
            # However, OpportunityRepository.create doesn't seem to be decorated.
            # But the Service method create_opportunity IS decorated.

            opportunity = await self.repository.create(**opp_data)

            await self.db.commit()
            add_span_event("opportunity_created", {"opportunity_id": opportunity.id})

            # Track opportunity metrics
            track_opportunity_created(tier=opportunity.tier or "Unknown", status=opportunity.status)
            track_opportunity_score(float(opportunity.total_score or 0))
            track_opportunity_processing_time(processing_time_ms / 1000.0)

            # Cache the opportunity
            if use_cache:
                try:
                    opp_cache_key = CacheKeys.opportunity_by_id(opportunity.id)
                    await self.cache.set(
                        opp_cache_key,
                        self._opportunity_to_dict(opportunity),
                        ttl=CacheKeys.TTL_MEDIUM,
                    )
                except Exception as e:
                    logger.warning("opportunity_cache_failed", error=str(e))

            # Invalidate stats cache
            await self._invalidate_stats_cache()

            logger.info(
                "opportunity_created",
                opportunity_id=opportunity.id,
                score=opportunity.total_score,
                tier=opportunity.tier,
                processing_time_ms=processing_time_ms,
            )

            # Create pending response if AI response was generated
            if opportunity.ai_response:
                try:
                    pending_response = await self.response_repository.create(
                        opportunity_id=opportunity.id,
                        original_response=opportunity.ai_response,
                        status="pending",
                    )
                    await self.db.commit()

                    logger.info(
                        "pending_response_created",
                        response_id=pending_response.id,
                        opportunity_id=opportunity.id,
                    )
                except Exception as e:
                    # Don't fail opportunity creation if pending response fails
                    logger.warning(
                        "pending_response_creation_failed",
                        opportunity_id=opportunity.id,
                        error=str(e),
                    )

            # Send notification if enabled
            try:
                from app.notifications import notify_opportunity

                await notify_opportunity(opportunity)
            except Exception as e:
                # Don't fail opportunity creation if notification fails
                logger.warning(
                    "opportunity_notification_failed",
                    opportunity_id=opportunity.id,
                    error=str(e),
                )

            return opportunity

        except PipelineError as e:
            await self.db.rollback()
            logger.error("pipeline_processing_failed", error=str(e))
            track_pipeline_execution("error", 0.0)
            raise

        except Exception as e:
            await self.db.rollback()
            logger.error("opportunity_creation_failed", error=str(e))
            track_pipeline_execution("error", 0.0)
            raise PipelineError(
                message="Failed to create opportunity",
                details={"error": str(e)},
            ) from e

    async def get_opportunity(
        self,
        opportunity_id: int,
        use_cache: bool = True,
    ) -> Opportunity:
        """
        Get opportunity by ID.

        Args:
            opportunity_id: Opportunity ID
            use_cache: Whether to use cache

        Returns:
            Opportunity

        Raises:
            OpportunityNotFoundError: If not found
        """
        logger.debug("getting_opportunity", opportunity_id=opportunity_id)

        # Try cache first
        if use_cache:
            try:
                cache_key = CacheKeys.opportunity_by_id(opportunity_id)
                cached = await self.cache.get(cache_key)

                if cached:
                    logger.debug("opportunity_from_cache", opportunity_id=opportunity_id)
                    # Convert dict back to model
                    return Opportunity(**cached)
            except Exception as e:
                logger.warning("cache_get_failed", error=str(e))

        # Get from database
        opportunity = await self.repository.get_by_id(opportunity_id)

        if not opportunity:
            raise OpportunityNotFoundError(
                message=f"Opportunity {opportunity_id} not found",
                details={"opportunity_id": opportunity_id},
            )

        # Cache it
        if use_cache:
            try:
                cache_key = CacheKeys.opportunity_by_id(opportunity_id)
                await self.cache.set(
                    cache_key,
                    self._opportunity_to_dict(opportunity),
                    ttl=CacheKeys.TTL_MEDIUM,
                )
            except Exception as e:
                logger.warning("cache_set_failed", error=str(e))

        return opportunity

    async def list_opportunities(
        self,
        skip: int = 0,
        limit: int = 10,
        tier: str | None = None,
        status: str | None = None,
        min_score: int | None = None,
        company: str | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        use_cache: bool = True,
    ) -> Sequence[Opportunity]:
        """
        List opportunities with filters.

        Args:
            skip: Pagination offset
            limit: Page size
            tier: Filter by tier
            status: Filter by status
            min_score: Minimum score filter
            company: Filter by company name
            sort_by: Sort field
            sort_order: Sort order (asc/desc)
            use_cache: Whether to use cache

        Returns:
            List of opportunities
        """
        logger.debug(
            "listing_opportunities",
            skip=skip,
            limit=limit,
            tier=tier,
            sort_by=sort_by,
        )

        # Try cache for common queries
        if use_cache and not company and not status:
            try:
                cache_key = CacheKeys.opportunity_list(
                    tier=tier,
                    skip=skip,
                    limit=limit,
                    sort_by=sort_by,
                )
                cached = await self.cache.get(cache_key)

                if cached:
                    logger.debug("opportunities_from_cache", count=len(cached))
                    return [Opportunity(**opp) for opp in cached]
            except Exception as e:
                logger.warning("cache_get_failed", error=str(e))

        # Query database
        opportunities = await self.repository.get_all(
            skip=skip,
            limit=limit,
            tier=tier,
            status=status,
            min_score=min_score,
            company=company,
            sort_by=sort_by,
            sort_order=sort_order,
        )

        # Cache simple queries
        if use_cache and not company and not status:
            try:
                cache_key = CacheKeys.opportunity_list(
                    tier=tier,
                    skip=skip,
                    limit=limit,
                    sort_by=sort_by,
                )
                await self.cache.set(
                    cache_key,
                    [self._opportunity_to_dict(opp) for opp in opportunities],
                    ttl=CacheKeys.TTL_SHORT,
                )
            except Exception as e:
                logger.warning("cache_set_failed", error=str(e))

        return opportunities

    async def update_opportunity(
        self,
        opportunity_id: int,
        **updates,
    ) -> Opportunity:
        """
        Update opportunity metadata.

        Args:
            opportunity_id: Opportunity ID
            **updates: Fields to update

        Returns:
            Updated opportunity

        Raises:
            OpportunityNotFoundError: If not found
        """
        logger.info(
            "updating_opportunity", opportunity_id=opportunity_id, updates=list(updates.keys())
        )

        opportunity = await self.repository.update(opportunity_id, **updates)

        if not opportunity:
            raise OpportunityNotFoundError(
                message=f"Opportunity {opportunity_id} not found",
                details={"opportunity_id": opportunity_id},
            )

        await self.db.commit()

        # Invalidate cache
        try:
            cache_key = CacheKeys.opportunity_by_id(opportunity_id)
            await self.cache.delete(cache_key)
            await self._invalidate_stats_cache()
        except Exception as e:
            logger.warning("cache_invalidation_failed", error=str(e))

        logger.info("opportunity_updated", opportunity_id=opportunity_id)

        return opportunity

    async def delete_opportunity(self, opportunity_id: int) -> bool:
        """
        Delete opportunity.

        Args:
            opportunity_id: Opportunity ID

        Returns:
            True if deleted

        Raises:
            OpportunityNotFoundError: If not found
        """
        logger.info("deleting_opportunity", opportunity_id=opportunity_id)

        await self.repository.delete(opportunity_id)
        # Note: repository.delete returns None on success, raises error on failure
        # We assume success if no error raised

        await self.db.commit()

        # Invalidate cache
        try:
            cache_key = CacheKeys.opportunity_by_id(opportunity_id)
            await self.cache.delete(cache_key)
            await self._invalidate_stats_cache()
        except Exception as e:
            logger.warning("cache_invalidation_failed", error=str(e))

        logger.info("opportunity_deleted", opportunity_id=opportunity_id)

        return True

    async def get_stats(self, use_cache: bool = True) -> dict:
        """
        Get opportunity statistics.

        Args:
            use_cache: Whether to use cache

        Returns:
            Statistics dictionary
        """
        logger.debug("getting_stats")

        # Try cache
        if use_cache:
            try:
                cache_key = CacheKeys.opportunity_stats()
                cached = await self.cache.get(cache_key)

                if cached:
                    logger.debug("stats_from_cache")
                    return dict(cached)
            except Exception as e:
                logger.warning("cache_get_failed", error=str(e))

        # Calculate stats
        total_count = await self.repository.count()
        stats_data = await self.repository.get_stats()

        stats = {
            "total_count": total_count,
            "by_tier": stats_data.get("by_tier", {}),
            "average_score": stats_data.get("avg_score", 0),
            "highest_score": stats_data.get("max_score", 0),
            "lowest_score": stats_data.get("min_score", 0),
        }

        # Cache stats
        if use_cache:
            try:
                cache_key = CacheKeys.opportunity_stats()
                await self.cache.set(cache_key, stats, ttl=CacheKeys.TTL_SHORT)
            except Exception as e:
                logger.warning("cache_set_failed", error=str(e))

        return stats

    async def _invalidate_stats_cache(self) -> None:
        """Invalidate statistics cache."""
        try:
            cache_key = CacheKeys.opportunity_stats()
            await self.cache.delete(cache_key)

            # Also invalidate list caches
            pattern = CacheKeys.invalidate_pattern("opportunity:list:*")
            await self.cache.delete_pattern(pattern)

            logger.debug("stats_cache_invalidated")
        except Exception as e:
            logger.warning("cache_invalidation_failed", error=str(e))

    @staticmethod
    def _opportunity_to_dict(opportunity: Opportunity) -> dict:
        """Convert opportunity model to dictionary for caching."""
        return {
            "id": opportunity.id,
            "recruiter_name": opportunity.recruiter_name,
            "raw_message": opportunity.raw_message,
            "company": opportunity.company,
            "role": opportunity.role,
            "seniority": opportunity.seniority,
            "tech_stack": opportunity.tech_stack,
            "salary_min": opportunity.salary_min,
            "salary_max": opportunity.salary_max,
            "currency": opportunity.currency,
            "location": opportunity.location,
            "remote_policy": opportunity.remote_policy,
            "job_type": opportunity.job_type,
            "tech_stack_score": opportunity.tech_stack_score,
            "salary_score": opportunity.salary_score,
            "seniority_score": opportunity.seniority_score,
            "company_score": opportunity.company_score,
            "total_score": opportunity.total_score,
            "tier": opportunity.tier,
            "ai_response": opportunity.ai_response,
            "status": opportunity.status,
            "processing_time_ms": opportunity.processing_time_ms,
            "created_at": opportunity.created_at.isoformat() if opportunity.created_at else None,
            "updated_at": opportunity.updated_at.isoformat() if opportunity.updated_at else None,
            "message_timestamp": opportunity.message_timestamp.isoformat()
            if opportunity.message_timestamp
            else None,
        }
