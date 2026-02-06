"""
Unit tests for repository layer.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Opportunity
from app.database.repositories import OpportunityRepository


class TestOpportunityRepository:
    """Test OpportunityRepository."""

    async def test_create_opportunity(
        self, db_session: AsyncSession, sample_opportunity_data: dict
    ):
        """Test creating an opportunity."""
        repo = OpportunityRepository(db_session)

        opportunity = await repo.create(**sample_opportunity_data)

        assert opportunity.id is not None
        assert opportunity.recruiter_name == sample_opportunity_data["recruiter_name"]
        assert opportunity.company == sample_opportunity_data["company"]
        assert opportunity.total_score == sample_opportunity_data["total_score"]

    async def test_get_by_id(self, db_session: AsyncSession, sample_opportunity: Opportunity):
        """Test getting opportunity by ID."""
        repo = OpportunityRepository(db_session)

        opportunity = await repo.get_by_id(sample_opportunity.id)

        assert opportunity is not None
        assert opportunity.id == sample_opportunity.id
        assert opportunity.recruiter_name == sample_opportunity.recruiter_name

    async def test_get_by_id_not_found(self, db_session: AsyncSession):
        """Test getting non-existent opportunity."""
        repo = OpportunityRepository(db_session)

        opportunity = await repo.get_by_id(999999)

        assert opportunity is None

    async def test_get_all(self, db_session: AsyncSession, sample_opportunity: Opportunity):
        """Test listing opportunities."""
        repo = OpportunityRepository(db_session)

        opportunities = await repo.get_all(skip=0, limit=10)

        assert len(opportunities) >= 1
        assert any(opp.id == sample_opportunity.id for opp in opportunities)

    async def test_get_all_with_filters(
        self, db_session: AsyncSession, sample_opportunity: Opportunity
    ):
        """Test filtering opportunities."""
        repo = OpportunityRepository(db_session)

        # Filter by tier
        opportunities = await repo.get_all(tier="HIGH_PRIORITY")
        assert len(opportunities) >= 1
        assert all(opp.tier == "HIGH_PRIORITY" for opp in opportunities)

        # Filter by min_score
        opportunities = await repo.get_all(min_score=80)
        assert len(opportunities) >= 1
        assert all(opp.total_score >= 80 for opp in opportunities if opp.total_score)

    async def test_get_all_pagination(
        self, db_session: AsyncSession, sample_opportunity_data: dict
    ):
        """Test pagination."""
        repo = OpportunityRepository(db_session)

        # Create multiple opportunities
        for i in range(5):
            data = sample_opportunity_data.copy()
            data["recruiter_name"] = f"Recruiter {i}"
            await repo.create(**data)

        # Get first page
        page1 = await repo.get_all(skip=0, limit=2)
        assert len(page1) == 2

        # Get second page
        page2 = await repo.get_all(skip=2, limit=2)
        assert len(page2) == 2

        # Ensure different results
        assert page1[0].id != page2[0].id

    async def test_update_opportunity(
        self, db_session: AsyncSession, sample_opportunity: Opportunity
    ):
        """Test updating an opportunity."""
        repo = OpportunityRepository(db_session)

        updated = await repo.update(sample_opportunity.id, status="contacted")

        assert updated.status == "contacted"
        assert updated.id == sample_opportunity.id

    async def test_delete_opportunity(
        self, db_session: AsyncSession, sample_opportunity: Opportunity
    ):
        """Test deleting an opportunity."""
        repo = OpportunityRepository(db_session)

        deleted = await repo.delete(sample_opportunity.id)
        assert deleted is True

        # Verify it's deleted
        opportunity = await repo.get_by_id(sample_opportunity.id)
        assert opportunity is None

    async def test_delete_nonexistent(self, db_session: AsyncSession):
        """Test deleting non-existent opportunity."""
        repo = OpportunityRepository(db_session)

        deleted = await repo.delete(999999)
        assert deleted is False

    async def test_count(self, db_session: AsyncSession, sample_opportunity: Opportunity):
        """Test counting opportunities."""
        repo = OpportunityRepository(db_session)

        count = await repo.count()
        assert count >= 1

        # Count with filter
        count_filtered = await repo.count(tier="HIGH_PRIORITY")
        assert count_filtered >= 1

    async def test_get_stats(self, db_session: AsyncSession, sample_opportunity: Opportunity):
        """Test getting statistics."""
        repo = OpportunityRepository(db_session)

        stats = await repo.get_stats()

        assert "total_count" in stats
        assert "by_tier" in stats
        assert "by_status" in stats
        assert stats["total_count"] >= 1
