"""
API endpoints for managing pending responses.

Handles approve, edit, and decline operations for AI-generated responses.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.database.dependencies import get_db
from app.database.repositories import PendingResponseRepository, get_pending_response_repository

logger = get_logger(__name__)

router = APIRouter(prefix="/responses", tags=["responses"])


# Schemas
class ResponseApproveRequest(BaseModel):
    """Request to approve a response."""

    edited_response: str | None = None


class ResponseDeclineRequest(BaseModel):
    """Request to decline a response."""

    pass


class ResponseData(BaseModel):
    """Response data."""

    id: int
    opportunity_id: int
    original_response: str
    edited_response: str | None = None
    final_response: str | None = None
    status: str
    approved_at: str | None = None
    declined_at: str | None = None
    sent_at: str | None = None
    error_message: str | None = None
    send_attempts: int
    created_at: str
    updated_at: str


class ResponseListResponse(BaseModel):
    """Paginated response list."""

    items: list[ResponseData]
    total: int
    skip: int
    limit: int


@router.post(
    "/{opportunity_id}/approve", response_model=ResponseData, status_code=status.HTTP_200_OK
)
async def approve_response(
    opportunity_id: int,
    request: ResponseApproveRequest | None = None,
    db: AsyncSession = Depends(get_db),
    repository: PendingResponseRepository = Depends(get_pending_response_repository),
):
    """
    Approve an AI-generated response.

    Marks the response as approved and optionally accepts an edited version.
    The response will be queued for sending to LinkedIn.

    Args:
        opportunity_id: Opportunity ID
        request: Optional approval request with edited response
        db: Database session
        repository: Response repository

    Returns:
        Updated response data

    Raises:
        HTTPException: If response not found or already processed
    """
    logger.info("approving_response", opportunity_id=opportunity_id)

    try:
        # Get pending response for this opportunity
        pending_response = await repository.get_by_opportunity_id(opportunity_id)

        if not pending_response:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No pending response found for opportunity {opportunity_id}",
            )

        if pending_response.status not in ["pending"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Response is already {pending_response.status}",
            )

        # Approve the response
        edited_text = request.edited_response if request else None
        updated_response = await repository.approve(
            pending_response.id, edited_response=edited_text
        )

        if not updated_response:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to approve response",
            )

        await db.commit()

        logger.info(
            "response_approved",
            response_id=updated_response.id,
            opportunity_id=opportunity_id,
            edited=bool(edited_text),
        )

        # Queue LinkedIn message sending task
        try:
            from app.tasks.messaging_tasks import send_linkedin_response

            task = send_linkedin_response.apply_async(args=[updated_response.id])
            logger.info(
                "linkedin_response_task_queued",
                response_id=updated_response.id,
                task_id=task.id,
            )
        except Exception as e:
            logger.error(
                "failed_to_queue_linkedin_response",
                response_id=updated_response.id,
                error=str(e),
            )
            # Don't fail the approval if task queueing fails

        return ResponseData(**updated_response.to_dict())

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error("response_approval_failed", opportunity_id=opportunity_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to approve response",
        ) from e


@router.post("/{opportunity_id}/edit", response_model=ResponseData, status_code=status.HTTP_200_OK)
async def edit_response(
    opportunity_id: int,
    request: ResponseApproveRequest,
    db: AsyncSession = Depends(get_db),
    repository: PendingResponseRepository = Depends(get_pending_response_repository),
):
    """
    Edit and approve a response.

    This is an alias for approve_response that requires an edited_response.

    Args:
        opportunity_id: Opportunity ID
        request: Approval request with edited response
        db: Database session
        repository: Response repository

    Returns:
        Updated response data

    Raises:
        HTTPException: If edited_response not provided or response not found
    """
    if not request.edited_response:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="edited_response is required",
        )

    return await approve_response(opportunity_id, request, db, repository)


@router.post(
    "/{opportunity_id}/decline", response_model=ResponseData, status_code=status.HTTP_200_OK
)
async def decline_response(
    opportunity_id: int,
    db: AsyncSession = Depends(get_db),
    repository: PendingResponseRepository = Depends(get_pending_response_repository),
):
    """
    Decline a response.

    Marks the response as declined and will not send any message.

    Args:
        opportunity_id: Opportunity ID
        db: Database session
        repository: Response repository

    Returns:
        Updated response data

    Raises:
        HTTPException: If response not found or already processed
    """
    logger.info("declining_response", opportunity_id=opportunity_id)

    try:
        # Get pending response for this opportunity
        pending_response = await repository.get_by_opportunity_id(opportunity_id)

        if not pending_response:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No pending response found for opportunity {opportunity_id}",
            )

        if pending_response.status not in ["pending"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Response is already {pending_response.status}",
            )

        # Decline the response
        updated_response = await repository.decline(pending_response.id)

        if not updated_response:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to decline response",
            )

        await db.commit()

        logger.info(
            "response_declined", response_id=updated_response.id, opportunity_id=opportunity_id
        )

        return ResponseData(**updated_response.to_dict())

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error("response_decline_failed", opportunity_id=opportunity_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to decline response",
        ) from e


@router.get(
    "/{opportunity_id}",
    response_model=ResponseData | None,
    status_code=status.HTTP_200_OK,
    responses={204: {"description": "No pending response for this opportunity"}},
)
async def get_response(
    opportunity_id: int,
    repository: PendingResponseRepository = Depends(get_pending_response_repository),
):
    """
    Get pending response for an opportunity.

    Args:
        opportunity_id: Opportunity ID
        repository: Response repository

    Returns:
        Response data or 204 if no pending response
    """
    pending_response = await repository.get_by_opportunity_id(opportunity_id)

    if not pending_response:
        from fastapi.responses import Response

        return Response(status_code=status.HTTP_204_NO_CONTENT)

    return ResponseData(**pending_response.to_dict())


@router.get("/", response_model=ResponseListResponse, status_code=status.HTTP_200_OK)
async def list_pending_responses(
    skip: int = 0,
    limit: int = 10,
    repository: PendingResponseRepository = Depends(get_pending_response_repository),
):
    """
    List all pending responses.

    Args:
        skip: Pagination offset
        limit: Page size
        repository: Response repository

    Returns:
        Paginated list of pending responses
    """
    responses = await repository.list_pending(skip=skip, limit=limit)
    total = await repository.count_pending()
    return ResponseListResponse(
        items=[ResponseData(**response.to_dict()) for response in responses],
        total=total,
        skip=skip,
        limit=limit,
    )
