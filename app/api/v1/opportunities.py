"""
Opportunities API endpoints.

Provides REST API for managing LinkedIn opportunities:
- Create (process recruiter message)
- List (with pagination and filters)
- Get by ID
- Delete
- Statistics
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas import (
    OpportunityCreate,
    OpportunityListResponse,
    OpportunityResponse,
    OpportunityStats,
    OpportunityUpdate,
)
from app.core.exceptions import DatabaseError, OpportunityNotFoundError, PipelineError
from app.core.logging import get_logger
from app.database.dependencies import get_db
from app.database.models import Opportunity
from app.database.repositories import OpportunityRepository
from app.dspy_modules.pipeline import get_pipeline
from app.dspy_modules.profile_loader import get_profile

logger = get_logger(__name__)

router = APIRouter(prefix="/opportunities", tags=["opportunities"])


# ============================================================================
# Helper Functions
# ============================================================================


def _opportunity_to_response(opportunity: Opportunity) -> OpportunityResponse:
    """Convert Opportunity model to OpportunityResponse schema."""
    return OpportunityResponse(
        id=opportunity.id,
        recruiter_name=opportunity.recruiter_name,
        raw_message=opportunity.raw_message,
        company=opportunity.company,
        role=opportunity.role,
        seniority=opportunity.seniority,
        tech_stack=opportunity.tech_stack or [],
        salary_min=opportunity.salary_min,
        salary_max=opportunity.salary_max,
        currency=opportunity.currency,
        remote_policy=opportunity.remote_policy,
        tech_stack_score=opportunity.tech_stack_score,
        salary_score=opportunity.salary_score,
        seniority_score=opportunity.seniority_score,
        company_score=opportunity.company_score,
        total_score=opportunity.total_score,
        tier=opportunity.tier,
        ai_response=opportunity.ai_response,
        status=opportunity.status,
        processing_time_ms=opportunity.processing_time_ms,
        created_at=opportunity.created_at,
        updated_at=opportunity.updated_at,
    )


# ============================================================================
# Endpoints
# ============================================================================


@router.post(
    "",
    response_model=OpportunityResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create and process opportunity",
    description="Process a recruiter message through the AI pipeline and store results",
)
async def create_opportunity(
    opportunity_in: OpportunityCreate,
    db: AsyncSession = Depends(get_db),
) -> OpportunityResponse:
    """
    Create and process a new opportunity.

    This endpoint:
    1. Runs the message through the DSPy pipeline
    2. Extracts structured data
    3. Scores the opportunity
    4. Generates an AI response
    5. Stores everything in the database

    Args:
        opportunity_in: Opportunity creation data
        db: Database session

    Returns:
        Created opportunity with AI analysis

    Raises:
        HTTPException 500: If pipeline or database fails
    """
    logger.info(
        "create_opportunity_request",
        recruiter=opportunity_in.recruiter_name,
        message_length=len(opportunity_in.raw_message),
    )

    try:
        # Get pipeline and profile
        pipeline = get_pipeline()
        profile = get_profile()

        # Process message through pipeline
        result = pipeline.forward(
            message=opportunity_in.raw_message,
            recruiter_name=opportunity_in.recruiter_name,
            profile=profile,
        )

        # Create opportunity in database
        repo = OpportunityRepository(db)
        opportunity = await repo.create(
            recruiter_name=result.recruiter_name,
            raw_message=result.raw_message,
            # Extracted data
            company=result.extracted.company,
            role=result.extracted.role,
            seniority=result.extracted.seniority,
            tech_stack=result.extracted.tech_stack,
            salary_min=result.extracted.salary_min,
            salary_max=result.extracted.salary_max,
            currency=result.extracted.currency,
            remote_policy=result.extracted.remote_policy,
            location=result.extracted.location,
            # Scores
            tech_stack_score=result.scoring.tech_stack_score,
            salary_score=result.scoring.salary_score,
            seniority_score=result.scoring.seniority_score,
            company_score=result.scoring.company_score,
            total_score=result.scoring.total_score,
            tier=result.scoring.tier,
            # AI Response
            ai_response=result.ai_response,
            # Metadata
            status=result.status,
            processing_time_ms=result.processing_time_ms,
        )

        logger.info(
            "opportunity_created",
            opportunity_id=opportunity.id,
            tier=opportunity.tier,
            score=opportunity.total_score,
        )

        return _opportunity_to_response(opportunity)

    except PipelineError as e:
        logger.error("pipeline_error", error=str(e), details=e.details)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Pipeline processing failed: {e.message}",
        ) from e

    except DatabaseError as e:
        logger.error("database_error", error=str(e), details=e.details)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database operation failed: {e.message}",
        ) from e

    except Exception as e:
        logger.error("unexpected_error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred",
        ) from e


@router.get(
    "",
    response_model=OpportunityListResponse,
    summary="List opportunities",
    description="List opportunities with pagination and filtering",
)
async def list_opportunities(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(10, ge=1, le=100, description="Number of items to return"),
    tier: Optional[str] = Query(
        None,
        description="Filter by tier (HIGH_PRIORITY, INTERESANTE, POCO_INTERESANTE, NO_INTERESA)",
    ),
    status: Optional[str] = Query(None, description="Filter by status"),
    min_score: Optional[int] = Query(None, ge=0, le=100, description="Minimum score"),
    company: Optional[str] = Query(None, description="Filter by company name"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order"),
    db: AsyncSession = Depends(get_db),
) -> OpportunityListResponse:
    """
    List opportunities with pagination and filtering.

    Args:
        skip: Number of items to skip (offset)
        limit: Number of items to return (max 100)
        tier: Filter by opportunity tier
        status: Filter by status
        min_score: Filter by minimum score
        company: Filter by company name (partial match)
        sort_by: Field to sort by
        sort_order: Sort order (asc/desc)
        db: Database session

    Returns:
        Paginated list of opportunities
    """
    logger.debug(
        "list_opportunities_request",
        skip=skip,
        limit=limit,
        tier=tier,
        status=status,
        min_score=min_score,
    )

    try:
        repo = OpportunityRepository(db)

        # Get opportunities
        opportunities = await repo.get_all(
            skip=skip,
            limit=limit,
            tier=tier,
            status=status,
            min_score=min_score,
            company=company,
            sort_by=sort_by,
            sort_order=sort_order,
        )

        # Get total count
        total = await repo.count(
            tier=tier,
            status=status,
            min_score=min_score,
            company=company,
        )

        # Convert to response models
        items = [_opportunity_to_response(opp) for opp in opportunities]

        return OpportunityListResponse(
            items=items,
            total=total,
            skip=skip,
            limit=limit,
            has_more=(skip + len(items)) < total,
        )

    except DatabaseError as e:
        logger.error("database_error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database operation failed: {e.message}",
        ) from e


@router.get(
    "/stats",
    response_model=OpportunityStats,
    summary="Get opportunity statistics",
    description="Get statistics about opportunities",
)
async def get_stats(
    db: AsyncSession = Depends(get_db),
) -> OpportunityStats:
    """
    Get opportunity statistics.

    Returns:
        Statistics including counts by tier, status, and score metrics
    """
    logger.debug("get_stats_request")

    try:
        repo = OpportunityRepository(db)
        stats = await repo.get_stats()

        return OpportunityStats(**stats)

    except DatabaseError as e:
        logger.error("database_error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database operation failed: {e.message}",
        ) from e


@router.get(
    "/{opportunity_id}",
    response_model=OpportunityResponse,
    summary="Get opportunity by ID",
    description="Retrieve a single opportunity by its ID",
)
async def get_opportunity(
    opportunity_id: int,
    db: AsyncSession = Depends(get_db),
) -> OpportunityResponse:
    """
    Get a single opportunity by ID.

    Args:
        opportunity_id: Opportunity ID
        db: Database session

    Returns:
        Opportunity details

    Raises:
        HTTPException 404: If opportunity not found
    """
    logger.debug("get_opportunity_request", opportunity_id=opportunity_id)

    try:
        repo = OpportunityRepository(db)
        opportunity = await repo.get_by_id(opportunity_id)

        if not opportunity:
            raise OpportunityNotFoundError(opportunity_id=opportunity_id)

        return _opportunity_to_response(opportunity)

    except OpportunityNotFoundError as e:
        logger.warning("opportunity_not_found", opportunity_id=opportunity_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Opportunity {opportunity_id} not found",
        ) from e

    except DatabaseError as e:
        logger.error("database_error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database operation failed: {e.message}",
        ) from e


@router.delete(
    "/{opportunity_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete opportunity",
    description="Delete an opportunity by its ID",
)
async def delete_opportunity(
    opportunity_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Delete an opportunity.

    Args:
        opportunity_id: Opportunity ID to delete
        db: Database session

    Raises:
        HTTPException 404: If opportunity not found
    """
    logger.info("delete_opportunity_request", opportunity_id=opportunity_id)

    try:
        repo = OpportunityRepository(db)
        deleted = await repo.delete(opportunity_id)

        if not deleted:
            raise OpportunityNotFoundError(opportunity_id=opportunity_id)

        logger.info("opportunity_deleted", opportunity_id=opportunity_id)

    except OpportunityNotFoundError as e:
        logger.warning("opportunity_not_found", opportunity_id=opportunity_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Opportunity {opportunity_id} not found",
        ) from e

    except DatabaseError as e:
        logger.error("database_error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database operation failed: {e.message}",
        ) from e


@router.patch(
    "/{opportunity_id}",
    response_model=OpportunityResponse,
    summary="Update opportunity",
    description="Update opportunity metadata (status, notes)",
)
async def update_opportunity(
    opportunity_id: int,
    opportunity_update: OpportunityUpdate,
    db: AsyncSession = Depends(get_db),
) -> OpportunityResponse:
    """
    Update an opportunity's metadata.

    Only status and notes can be updated. AI analysis results are immutable.

    Args:
        opportunity_id: Opportunity ID
        opportunity_update: Update data
        db: Database session

    Returns:
        Updated opportunity

    Raises:
        HTTPException 404: If opportunity not found
    """
    logger.info("update_opportunity_request", opportunity_id=opportunity_id)

    try:
        repo = OpportunityRepository(db)

        # Check if exists
        opportunity = await repo.get_by_id(opportunity_id)
        if not opportunity:
            raise OpportunityNotFoundError(opportunity_id=opportunity_id)

        # Update
        update_data = opportunity_update.model_dump(exclude_unset=True)
        updated = await repo.update(opportunity_id, **update_data)

        logger.info("opportunity_updated", opportunity_id=opportunity_id)

        return _opportunity_to_response(updated)

    except OpportunityNotFoundError as e:
        logger.warning("opportunity_not_found", opportunity_id=opportunity_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Opportunity {opportunity_id} not found",
        ) from e

    except DatabaseError as e:
        logger.error("database_error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database operation failed: {e.message}",
        ) from e