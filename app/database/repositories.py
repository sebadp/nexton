"""
Repository pattern for database operations.

Provides abstraction layer between business logic and database.
"""
from datetime import datetime
from typing import Optional, Sequence

from fastapi import Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DatabaseError, OpportunityNotFoundError
from app.core.logging import get_logger
from app.database.dependencies import get_db
from app.database.models import Opportunity, PendingResponse

logger = get_logger(__name__)


class BaseRepository:
    """Base repository with common database operations."""

    def __init__(self, session: AsyncSession):
        """
        Initialize repository with database session.

        Args:
            session: Async SQLAlchemy session
        """
        self.session = session


class OpportunityRepository(BaseRepository):
    """Repository for Opportunity model operations."""

    async def create(self, **kwargs) -> Opportunity:
        """
        Create a new opportunity.

        Args:
            **kwargs: Opportunity attributes

        Returns:
            Opportunity: Created opportunity

        Raises:
            DatabaseError: If creation fails
        """
        try:
            opportunity = Opportunity(**kwargs)
            self.session.add(opportunity)
            await self.session.flush()
            await self.session.refresh(opportunity)

            logger.info(
                "opportunity_created",
                opportunity_id=opportunity.id,
                company=opportunity.company,
                role=opportunity.role,
            )

            return opportunity

        except Exception as e:
            logger.error("opportunity_create_failed", error=str(e))
            raise DatabaseError(
                message="Failed to create opportunity",
                details={"error": str(e)},
            ) from e

    async def get_by_id(self, opportunity_id: int) -> Opportunity:
        """
        Get opportunity by ID.

        Args:
            opportunity_id: Opportunity ID

        Returns:
            Opportunity: Found opportunity

        Raises:
            OpportunityNotFoundError: If not found
        """
        try:
            result = await self.session.execute(
                select(Opportunity).where(Opportunity.id == opportunity_id)
            )
            opportunity = result.scalar_one_or_none()

            if not opportunity:
                raise OpportunityNotFoundError(
                    message=f"Opportunity {opportunity_id} not found",
                    details={"opportunity_id": opportunity_id},
                )

            return opportunity

        except OpportunityNotFoundError:
            raise
        except Exception as e:
            logger.error(
                "opportunity_get_failed",
                opportunity_id=opportunity_id,
                error=str(e),
            )
            raise DatabaseError(
                message="Failed to get opportunity",
                details={"opportunity_id": opportunity_id, "error": str(e)},
            ) from e

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 10,
        tier: Optional[str] = None,
        status: Optional[str] = None,
        company: Optional[str] = None,
        min_score: Optional[int] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> Sequence[Opportunity]:
        """
        Get all opportunities with filters and pagination.

        Args:
            skip: Number of records to skip
            limit: Maximum records to return
            tier: Filter by tier
            status: Filter by status
            company: Filter by company
            min_score: Minimum score filter
            sort_by: Field to sort by
            sort_order: Sort order ('asc' or 'desc')

        Returns:
            Sequence[Opportunity]: List of opportunities
        """
        try:
            query = select(Opportunity)

            # Apply filters
            if tier:
                query = query.where(Opportunity.tier == tier)
            if status:
                query = query.where(Opportunity.status == status)
            if company:
                query = query.where(Opportunity.company.ilike(f"%{company}%"))
            if min_score is not None:
                query = query.where(Opportunity.total_score >= min_score)

            # Apply ordering
            order_column = getattr(Opportunity, sort_by, Opportunity.created_at)
            if sort_order.lower() == "desc":
                query = query.order_by(order_column.desc())
            else:
                query = query.order_by(order_column.asc())

            # Apply pagination
            query = query.offset(skip).limit(limit)

            # Execute
            result = await self.session.execute(query)
            opportunities = result.scalars().all()

            logger.debug(
                "opportunities_retrieved",
                count=len(opportunities),
                skip=skip,
                limit=limit,
                tier=tier,
            )

            return opportunities

        except Exception as e:
            logger.error("opportunities_get_all_failed", error=str(e))
            raise DatabaseError(
                message="Failed to retrieve opportunities",
                details={"error": str(e)},
            ) from e

    async def update(
        self,
        opportunity_id: int,
        **kwargs,
    ) -> Opportunity:
        """
        Update an opportunity.

        Args:
            opportunity_id: Opportunity ID
            **kwargs: Fields to update

        Returns:
            Opportunity: Updated opportunity

        Raises:
            OpportunityNotFoundError: If not found
            DatabaseError: If update fails
        """
        try:
            opportunity = await self.get_by_id(opportunity_id)

            # Update fields
            for key, value in kwargs.items():
                if hasattr(opportunity, key):
                    setattr(opportunity, key, value)

            # Update timestamp
            opportunity.updated_at = datetime.utcnow()

            await self.session.flush()
            await self.session.refresh(opportunity)

            logger.info(
                "opportunity_updated",
                opportunity_id=opportunity_id,
                fields_updated=list(kwargs.keys()),
            )

            return opportunity

        except OpportunityNotFoundError:
            raise
        except Exception as e:
            logger.error(
                "opportunity_update_failed",
                opportunity_id=opportunity_id,
                error=str(e),
            )
            raise DatabaseError(
                message="Failed to update opportunity",
                details={"opportunity_id": opportunity_id, "error": str(e)},
            ) from e

    async def delete(self, opportunity_id: int) -> None:
        """
        Delete an opportunity.

        Args:
            opportunity_id: Opportunity ID

        Raises:
            OpportunityNotFoundError: If not found
            DatabaseError: If delete fails
        """
        try:
            opportunity = await self.get_by_id(opportunity_id)
            await self.session.delete(opportunity)
            await self.session.flush()

            logger.info("opportunity_deleted", opportunity_id=opportunity_id)

        except OpportunityNotFoundError:
            raise
        except Exception as e:
            logger.error(
                "opportunity_delete_failed",
                opportunity_id=opportunity_id,
                error=str(e),
            )
            raise DatabaseError(
                message="Failed to delete opportunity",
                details={"opportunity_id": opportunity_id, "error": str(e)},
            ) from e

    async def count(
        self,
        tier: Optional[str] = None,
        status: Optional[str] = None,
        company: Optional[str] = None,
        min_score: Optional[int] = None,
    ) -> int:
        """
        Count opportunities with filters.

        Args:
            tier: Filter by tier
            status: Filter by status
            company: Filter by company
            min_score: Minimum score filter

        Returns:
            int: Count of opportunities
        """
        try:
            query = select(func.count(Opportunity.id))

            if tier:
                query = query.where(Opportunity.tier == tier)
            if status:
                query = query.where(Opportunity.status == status)
            if company:
                query = query.where(Opportunity.company.ilike(f"%{company}%"))
            if min_score is not None:
                query = query.where(Opportunity.total_score >= min_score)

            result = await self.session.execute(query)
            count = result.scalar_one()

            return count

        except Exception as e:
            logger.error("opportunity_count_failed", error=str(e))
            raise DatabaseError(
                message="Failed to count opportunities",
                details={"error": str(e)},
            ) from e

    async def get_stats(self) -> dict:
        """
        Get aggregate statistics.

        Returns:
            dict: Statistics about opportunities
        """
        try:
            # Total count
            total = await self.count()

            # Count by tier
            tier_stats = {}
            for tier in ["HIGH_PRIORITY", "INTERESANTE", "POCO_INTERESANTE", "NO_INTERESA"]:
                tier_stats[tier] = await self.count(tier=tier)

            # Average, highest, lowest scores
            result = await self.session.execute(
                select(
                    func.avg(Opportunity.total_score),
                    func.max(Opportunity.total_score),
                    func.min(Opportunity.total_score),
                ).where(Opportunity.total_score.is_not(None))
            )
            row = result.one()
            avg_score = row[0] or 0
            highest_score = row[1]
            lowest_score = row[2]

            # Count by status
            status_stats = {}
            for status in ["new", "processing", "processed", "error", "archived"]:
                status_stats[status] = await self.count(status=status)

            # Count by conversation state (NEW)
            conversation_state_stats = {}
            for state in ["NEW_OPPORTUNITY", "FOLLOW_UP", "COURTESY_CLOSE"]:
                query = select(func.count(Opportunity.id)).where(
                    Opportunity.conversation_state == state
                )
                result = await self.session.execute(query)
                conversation_state_stats[state] = result.scalar_one()

            # Count by processing status (NEW)
            processing_status_stats = {}
            for pstatus in ["processed", "ignored", "declined", "manual_review", "auto_responded"]:
                query = select(func.count(Opportunity.id)).where(
                    Opportunity.processing_status == pstatus
                )
                result = await self.session.execute(query)
                processing_status_stats[pstatus] = result.scalar_one()

            # Count pending manual review (NEW)
            manual_review_query = select(func.count(Opportunity.id)).where(
                Opportunity.requires_manual_review == True  # noqa: E712
            )
            manual_review_result = await self.session.execute(manual_review_query)
            pending_manual_review = manual_review_result.scalar_one()

            return {
                "total_count": total,
                "by_tier": tier_stats,
                "average_score": round(float(avg_score), 2),
                "highest_score": highest_score,
                "lowest_score": lowest_score,
                "by_status": status_stats,
                "by_conversation_state": conversation_state_stats,
                "by_processing_status": processing_status_stats,
                "pending_manual_review": pending_manual_review,
            }

        except Exception as e:
            logger.error("opportunity_stats_failed", error=str(e))
            raise DatabaseError(
                message="Failed to get statistics",
                details={"error": str(e)},
            ) from e

    async def get_manual_review_queue(
        self,
        skip: int = 0,
        limit: int = 10,
    ) -> Sequence[Opportunity]:
        """
        Get opportunities that require manual review.

        Args:
            skip: Number of records to skip
            limit: Maximum records to return

        Returns:
            Sequence[Opportunity]: List of opportunities needing manual review
        """
        try:
            query = (
                select(Opportunity)
                .where(Opportunity.requires_manual_review == True)  # noqa: E712
                .order_by(Opportunity.created_at.desc())
                .offset(skip)
                .limit(limit)
            )

            result = await self.session.execute(query)
            return result.scalars().all()

        except Exception as e:
            logger.error("manual_review_queue_failed", error=str(e))
            raise DatabaseError(
                message="Failed to get manual review queue",
                details={"error": str(e)},
            ) from e

    async def count_manual_review(self) -> int:
        """
        Count opportunities requiring manual review.

        Returns:
            int: Count of opportunities needing manual review
        """
        try:
            query = select(func.count(Opportunity.id)).where(
                Opportunity.requires_manual_review == True  # noqa: E712
            )
            result = await self.session.execute(query)
            return result.scalar_one()

        except Exception as e:
            logger.error("manual_review_count_failed", error=str(e))
            raise DatabaseError(
                message="Failed to count manual review queue",
                details={"error": str(e)},
            ) from e


class PendingResponseRepository(BaseRepository):
    """Repository for PendingResponse model operations."""

    async def create(
        self,
        opportunity_id: int,
        original_response: str,
        status: str = "pending",
    ) -> PendingResponse:
        """
        Create a new pending response.

        Args:
            opportunity_id: Associated opportunity ID
            original_response: AI-generated response
            status: Response status

        Returns:
            PendingResponse: Created pending response

        Raises:
            DatabaseError: If creation fails
        """
        try:
            pending_response = PendingResponse(
                opportunity_id=opportunity_id,
                original_response=original_response,
                status=status,
            )
            self.session.add(pending_response)
            await self.session.flush()
            await self.session.refresh(pending_response)

            logger.info(
                "pending_response_created",
                response_id=pending_response.id,
                opportunity_id=opportunity_id,
                status=status,
            )

            return pending_response

        except Exception as e:
            logger.error("pending_response_create_failed", error=str(e))
            raise DatabaseError(
                message="Failed to create pending response",
                details={"error": str(e)},
            ) from e

    async def get_by_id(self, response_id: int) -> Optional[PendingResponse]:
        """
        Get pending response by ID.

        Args:
            response_id: Response ID

        Returns:
            PendingResponse or None
        """
        try:
            result = await self.session.execute(
                select(PendingResponse).where(PendingResponse.id == response_id)
            )
            return result.scalar_one_or_none()

        except Exception as e:
            logger.error("pending_response_get_failed", error=str(e))
            raise DatabaseError(
                message="Failed to get pending response",
                details={"error": str(e)},
            ) from e

    async def get_by_opportunity_id(self, opportunity_id: int) -> Optional[PendingResponse]:
        """
        Get pending response by opportunity ID.

        Args:
            opportunity_id: Opportunity ID

        Returns:
            PendingResponse or None
        """
        try:
            result = await self.session.execute(
                select(PendingResponse)
                .where(PendingResponse.opportunity_id == opportunity_id)
                .where(PendingResponse.status.in_(["pending", "approved"]))
                .order_by(PendingResponse.created_at.desc())
            )
            return result.scalar_one_or_none()

        except Exception as e:
            logger.error("pending_response_get_by_opportunity_failed", error=str(e))
            raise DatabaseError(
                message="Failed to get pending response",
                details={"error": str(e)},
            ) from e

    async def update(self, response_id: int, **kwargs) -> Optional[PendingResponse]:
        """
        Update pending response.

        Args:
            response_id: Response ID
            **kwargs: Fields to update

        Returns:
            Updated PendingResponse or None
        """
        try:
            response = await self.get_by_id(response_id)
            if not response:
                return None

            for key, value in kwargs.items():
                if hasattr(response, key):
                    setattr(response, key, value)

            response.updated_at = datetime.utcnow()
            await self.session.flush()
            await self.session.refresh(response)

            logger.info(
                "pending_response_updated",
                response_id=response_id,
                updates=list(kwargs.keys()),
            )

            return response

        except Exception as e:
            logger.error("pending_response_update_failed", error=str(e))
            raise DatabaseError(
                message="Failed to update pending response",
                details={"error": str(e)},
            ) from e

    async def approve(self, response_id: int, edited_response: Optional[str] = None) -> Optional[PendingResponse]:
        """
        Approve a pending response.

        Args:
            response_id: Response ID
            edited_response: Optional edited response

        Returns:
            Updated PendingResponse or None
        """
        updates = {
            "status": "approved",
            "approved_at": datetime.utcnow(),
        }

        if edited_response:
            updates["edited_response"] = edited_response
            updates["final_response"] = edited_response
        else:
            # Use original if not edited
            response = await self.get_by_id(response_id)
            if response:
                updates["final_response"] = response.original_response

        return await self.update(response_id, **updates)

    async def decline(self, response_id: int) -> Optional[PendingResponse]:
        """
        Decline a pending response.

        Args:
            response_id: Response ID

        Returns:
            Updated PendingResponse or None
        """
        return await self.update(
            response_id,
            status="declined",
            declined_at=datetime.utcnow(),
        )

    async def mark_as_sent(self, response_id: int) -> Optional[PendingResponse]:
        """
        Mark response as sent.

        Args:
            response_id: Response ID

        Returns:
            Updated PendingResponse or None
        """
        return await self.update(
            response_id,
            status="sent",
            sent_at=datetime.utcnow(),
        )

    async def mark_as_failed(self, response_id: int, error_message: str) -> Optional[PendingResponse]:
        """
        Mark response as failed.

        Args:
            response_id: Response ID
            error_message: Error description

        Returns:
            Updated PendingResponse or None
        """
        response = await self.get_by_id(response_id)
        if not response:
            return None

        return await self.update(
            response_id,
            status="failed",
            error_message=error_message,
            send_attempts=response.send_attempts + 1,
        )

    async def list_pending(self, skip: int = 0, limit: int = 10) -> Sequence[PendingResponse]:
        """
        List pending responses.

        Args:
            skip: Offset
            limit: Limit

        Returns:
            List of pending responses
        """
        try:
            result = await self.session.execute(
                select(PendingResponse)
                .where(PendingResponse.status == "pending")
                .order_by(PendingResponse.created_at.desc())
                .offset(skip)
                .limit(limit)
            )
            return result.scalars().all()

        except Exception as e:
            logger.error("pending_response_list_failed", error=str(e))
            raise DatabaseError(
                message="Failed to list pending responses",
                details={"error": str(e)},
            ) from e

    async def count_pending(self) -> int:
        """
        Count pending responses.

        Returns:
            Total count of pending responses
        """
        try:
            result = await self.session.execute(
                select(func.count(PendingResponse.id)).where(
                    PendingResponse.status == "pending"
                )
            )
            return result.scalar_one()

        except Exception as e:
            logger.error("pending_response_count_failed", error=str(e))
            raise DatabaseError(
                message="Failed to count pending responses",
                details={"error": str(e)},
            ) from e


# Dependency for FastAPI
async def get_opportunity_repository(
    session: AsyncSession = Depends(get_db),
) -> OpportunityRepository:
    """
    Dependency to get OpportunityRepository.

    Args:
        session: Database session

    Returns:
        OpportunityRepository: Repository instance
    """
    return OpportunityRepository(session)


async def get_pending_response_repository(
    session: AsyncSession = Depends(get_db),
) -> PendingResponseRepository:
    """
    Dependency to get PendingResponseRepository.

    Args:
        session: Database session

    Returns:
        PendingResponseRepository: Repository instance
    """
    return PendingResponseRepository(session)