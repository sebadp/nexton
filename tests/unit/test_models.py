"""
Unit tests for database models.
"""

from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Opportunity


class TestOpportunityModel:
    """Test Opportunity model."""

    async def test_create_opportunity(self, db_session: AsyncSession):
        """Test creating an opportunity."""
        opportunity = Opportunity(
            recruiter_name="Test Recruiter",
            raw_message="Test message",
            company="TestCorp",
            role="Senior Engineer",
            status="processed",
        )

        db_session.add(opportunity)
        await db_session.commit()
        await db_session.refresh(opportunity)

        assert opportunity.id is not None
        assert opportunity.recruiter_name == "Test Recruiter"
        assert opportunity.company == "TestCorp"
        assert opportunity.status == "processed"

    async def test_opportunity_timestamps(self, db_session: AsyncSession):
        """Test automatic timestamp creation."""
        opportunity = Opportunity(
            recruiter_name="Test Recruiter",
            raw_message="Test message",
            status="processed",
        )

        db_session.add(opportunity)
        await db_session.commit()
        await db_session.refresh(opportunity)

        assert opportunity.created_at is not None
        assert opportunity.updated_at is not None
        assert isinstance(opportunity.created_at, datetime)
        assert isinstance(opportunity.updated_at, datetime)

    async def test_opportunity_tech_stack_json(self, db_session: AsyncSession):
        """Test tech_stack JSON field."""
        tech_stack = ["Python", "FastAPI", "PostgreSQL"]
        opportunity = Opportunity(
            recruiter_name="Test Recruiter",
            raw_message="Test message",
            tech_stack=tech_stack,
            status="processed",
        )

        db_session.add(opportunity)
        await db_session.commit()
        await db_session.refresh(opportunity)

        assert opportunity.tech_stack == tech_stack
        assert isinstance(opportunity.tech_stack, list)

    async def test_opportunity_scores(self, db_session: AsyncSession):
        """Test scoring fields."""
        opportunity = Opportunity(
            recruiter_name="Test Recruiter",
            raw_message="Test message",
            tech_stack_score=35,
            salary_score=25,
            seniority_score=18,
            company_score=8,
            total_score=86,
            tier="HIGH_PRIORITY",
            status="processed",
        )

        db_session.add(opportunity)
        await db_session.commit()
        await db_session.refresh(opportunity)

        assert opportunity.tech_stack_score == 35
        assert opportunity.salary_score == 25
        assert opportunity.seniority_score == 18
        assert opportunity.company_score == 8
        assert opportunity.total_score == 86
        assert opportunity.tier == "HIGH_PRIORITY"

    async def test_opportunity_optional_fields(self, db_session: AsyncSession):
        """Test optional fields can be None."""
        opportunity = Opportunity(
            recruiter_name="Test Recruiter",
            raw_message="Test message",
            status="processed",
        )

        db_session.add(opportunity)
        await db_session.commit()
        await db_session.refresh(opportunity)

        assert opportunity.company is None
        assert opportunity.role is None
        assert opportunity.seniority is None
        assert opportunity.tech_stack is None
        assert opportunity.salary_min is None
        assert opportunity.total_score is None
