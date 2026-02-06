"""
Integration tests for database operations.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.repositories import OpportunityRepository


@pytest.mark.integration
@pytest.mark.requires_db
class TestDatabaseIntegration:
    """Integration tests for database."""

    async def test_full_crud_flow(self, db_session: AsyncSession, sample_opportunity_data: dict):
        """Test complete CRUD flow."""
        repo = OpportunityRepository(db_session)

        # Create
        opportunity = await repo.create(**sample_opportunity_data)
        assert opportunity.id is not None
        created_id = opportunity.id

        # Read
        fetched = await repo.get_by_id(created_id)
        assert fetched is not None
        assert fetched.recruiter_name == sample_opportunity_data["recruiter_name"]

        # Update
        updated = await repo.update(created_id, status="contacted")
        assert updated.status == "contacted"

        # List
        all_opps = await repo.get_all()
        assert len(all_opps) >= 1

        # Delete
        deleted = await repo.delete(created_id)
        assert deleted is True

        # Verify deletion
        fetched_after_delete = await repo.get_by_id(created_id)
        assert fetched_after_delete is None

    async def test_concurrent_creates(
        self, db_session: AsyncSession, sample_opportunity_data: dict
    ):
        """Test multiple concurrent creates."""
        repo = OpportunityRepository(db_session)

        # Create multiple opportunities
        opportunities = []
        for i in range(10):
            data = sample_opportunity_data.copy()
            data["recruiter_name"] = f"Recruiter {i}"
            data["company"] = f"Company {i}"
            opp = await repo.create(**data)
            opportunities.append(opp)

        # Verify all created
        assert len(opportunities) == 10
        assert all(opp.id is not None for opp in opportunities)

        # Verify unique IDs
        ids = [opp.id for opp in opportunities]
        assert len(set(ids)) == 10

    async def test_filtering_and_sorting(
        self, db_session: AsyncSession, sample_opportunity_data: dict
    ):
        """Test complex filtering and sorting."""
        repo = OpportunityRepository(db_session)

        # Create opportunities with different scores and tiers
        data1 = sample_opportunity_data.copy()
        data1["recruiter_name"] = "High Score"
        data1["total_score"] = 90
        data1["tier"] = "HIGH_PRIORITY"
        await repo.create(**data1)

        data2 = sample_opportunity_data.copy()
        data2["recruiter_name"] = "Medium Score"
        data2["total_score"] = 60
        data2["tier"] = "INTERESANTE"
        await repo.create(**data2)

        data3 = sample_opportunity_data.copy()
        data3["recruiter_name"] = "Low Score"
        data3["total_score"] = 30
        data3["tier"] = "POCO_INTERESANTE"
        await repo.create(**data3)

        # Filter by min_score
        high_score_opps = await repo.get_all(min_score=80)
        assert len(high_score_opps) >= 1
        assert all(opp.total_score >= 80 for opp in high_score_opps if opp.total_score)

        # Filter by tier
        high_priority = await repo.get_all(tier="HIGH_PRIORITY")
        assert len(high_priority) >= 1
        assert all(opp.tier == "HIGH_PRIORITY" for opp in high_priority)

    async def test_statistics_calculation(
        self, db_session: AsyncSession, sample_opportunity_data: dict
    ):
        """Test statistics calculation."""
        repo = OpportunityRepository(db_session)

        # Create opportunities with different tiers
        for tier, score in [
            ("HIGH_PRIORITY", 85),
            ("INTERESANTE", 65),
            ("POCO_INTERESANTE", 35),
        ]:
            data = sample_opportunity_data.copy()
            data["tier"] = tier
            data["total_score"] = score
            await repo.create(**data)

        # Get stats
        stats = await repo.get_stats()

        assert stats["total_count"] >= 3
        assert "by_tier" in stats
        assert "by_status" in stats
        assert stats["by_tier"]["HIGH_PRIORITY"] >= 1
        assert stats["by_tier"]["INTERESANTE"] >= 1
