"""
FastAPI dependencies for dependency injection.
"""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.base import get_db
from app.database.repositories import OpportunityRepository

# Type aliases for cleaner code
DatabaseSession = Annotated[AsyncSession, Depends(get_db)]


def get_opportunity_repository(
    session: DatabaseSession,
) -> OpportunityRepository:
    """
    Get OpportunityRepository instance.

    Args:
        session: Database session

    Returns:
        OpportunityRepository: Repository instance
    """
    return OpportunityRepository(session)


# Type alias for repository
OpportunityRepo = Annotated[OpportunityRepository, Depends(get_opportunity_repository)]
