"""
Integration tests for OpportunityService with caching, tracing, and metrics.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from app.cache import RedisCache
from app.database.models import Opportunity
from app.database.repositories import OpportunityRepository
from app.dspy_modules.models import (
    CandidateProfile,
    ExtractedInfo,
    OpportunityResult,
    ScoringResult,
)
from app.services.opportunity_service import OpportunityService


@pytest.fixture
def mock_cache():
    """Create mock Redis cache."""
    cache = AsyncMock(spec=RedisCache)
    cache.get = AsyncMock(return_value=None)
    cache.set = AsyncMock(return_value=True)
    cache.delete = AsyncMock(return_value=True)
    cache.delete_pattern = AsyncMock(return_value=0)
    return cache


@pytest.fixture
def mock_repository():
    """Create mock opportunity repository."""
    repo = MagicMock(spec=OpportunityRepository)
    repo.create = AsyncMock()
    repo.get_by_id = AsyncMock()
    repo.get_all = AsyncMock(return_value=[])
    repo.update = AsyncMock()
    repo.delete = AsyncMock()
    repo.count = AsyncMock(return_value=0)
    repo.count_by_tier = AsyncMock(return_value={})
    repo.get_stats = AsyncMock(return_value={})
    return repo


@pytest.fixture
def mock_pipeline():
    """Create mock DSPy pipeline."""
    pipeline = MagicMock()

    # Create a complete OpportunityResult
    extracted = ExtractedInfo(
        company="TechCorp",
        role="Senior Python Developer",
        seniority="Senior",
        tech_stack=["Python", "FastAPI", "PostgreSQL"],
        salary_min=120000,
        salary_max=150000,
        currency="USD",
        location="Remote",
        remote_policy="Fully Remote",
        job_type="Full-time",
    )

    scoring = ScoringResult(
        tech_stack_score=90,
        salary_score=85,
        seniority_score=95,
        company_score=80,
        total_score=87,
        tier="A",
    )

    result = OpportunityResult(
        recruiter_name="Jane Smith",
        extracted=extracted,
        scoring=scoring,
        ai_response="Great opportunity! Highly recommended.",
    )

    pipeline.forward = MagicMock(return_value=result)
    return pipeline


@pytest.fixture
def mock_profile():
    """Create mock candidate profile."""
    return CandidateProfile(
        name="John Doe",
        current_role="Python Developer",
        years_of_experience=5,
        preferred_tech_stack=["Python", "FastAPI", "Docker"],
        target_salary_min=100000,
        target_salary_max=140000,
        preferred_locations=["Remote"],
        remote_preference="Fully Remote",
    )


@pytest.fixture
async def mock_db_session():
    """Create mock database session."""
    session = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    return session


@pytest.fixture
def service(mock_db_session, mock_cache, mock_repository, mock_pipeline, mock_profile):
    """Create OpportunityService with mocked dependencies."""
    with patch("app.services.opportunity_service.OpportunityRepository", return_value=mock_repository):
        with patch("app.services.opportunity_service.get_pipeline", return_value=mock_pipeline):
            with patch("app.services.opportunity_service.get_profile", return_value=mock_profile):
                service = OpportunityService(db=mock_db_session, cache=mock_cache)
                service.repository = mock_repository
                service.pipeline = mock_pipeline
                service.profile = mock_profile
                yield service


@pytest.mark.asyncio
class TestOpportunityServiceCreate:
    """Test opportunity creation."""

    async def test_create_opportunity_success(self, service, mock_cache, mock_repository):
        """Test successful opportunity creation."""
        # Mock repository response
        created_opportunity = Opportunity(
            id=1,
            recruiter_name="Jane Smith",
            raw_message="Test message",
            company="TechCorp",
            role="Senior Python Developer",
            seniority="Senior",
            tech_stack=["Python", "FastAPI", "PostgreSQL"],
            salary_min=120000,
            salary_max=150000,
            currency="USD",
            location="Remote",
            remote_policy="Fully Remote",
            job_type="Full-time",
            tech_stack_score=90,
            salary_score=85,
            seniority_score=95,
            company_score=80,
            total_score=87,
            tier="A",
            ai_response="Great opportunity!",
            status="processed",
            processing_time_ms=1500,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        mock_repository.create.return_value = created_opportunity

        # Create opportunity
        result = await service.create_opportunity(
            recruiter_name="Jane Smith",
            raw_message="Test message about a Python developer role",
        )

        # Assertions
        assert result.id == 1
        assert result.company == "TechCorp"
        assert result.total_score == 87
        assert result.tier == "A"

        # Verify pipeline was called
        service.pipeline.forward.assert_called_once()

        # Verify cache was updated
        assert mock_cache.set.call_count >= 1

    async def test_create_opportunity_with_cache_hit(self, service, mock_cache):
        """Test opportunity creation with cached pipeline result."""
        # Mock cache hit
        cached_result = {
            "recruiter_name": "Jane Smith",
            "extracted": {
                "company": "TechCorp",
                "role": "Senior Python Developer",
                "seniority": "Senior",
                "tech_stack": ["Python", "FastAPI"],
                "salary_min": 120000,
                "salary_max": 150000,
                "currency": "USD",
                "location": "Remote",
                "remote_policy": "Fully Remote",
                "job_type": "Full-time",
            },
            "scoring": {
                "tech_stack_score": 90,
                "salary_score": 85,
                "seniority_score": 95,
                "company_score": 80,
                "total_score": 87,
                "tier": "A",
            },
            "ai_response": "Great opportunity!",
        }
        mock_cache.get.return_value = cached_result

        # Mock repository
        created_opportunity = Opportunity(
            id=1,
            recruiter_name="Jane Smith",
            raw_message="Test message",
            company="TechCorp",
            tier="A",
            total_score=87,
            status="processed",
            created_at=datetime.utcnow(),
        )
        service.repository.create.return_value = created_opportunity

        result = await service.create_opportunity(
            recruiter_name="Jane Smith",
            raw_message="Test message",
        )

        # Pipeline should not be called (cache hit)
        service.pipeline.forward.assert_not_called()

        assert result.id == 1

    async def test_create_opportunity_without_cache(self, service, mock_cache, mock_repository):
        """Test opportunity creation without using cache."""
        created_opportunity = Opportunity(
            id=1,
            recruiter_name="Jane Smith",
            company="TechCorp",
            tier="A",
            total_score=87,
            status="processed",
            created_at=datetime.utcnow(),
        )
        mock_repository.create.return_value = created_opportunity

        result = await service.create_opportunity(
            recruiter_name="Jane Smith",
            raw_message="Test message",
            use_cache=False,
        )

        # Cache should not be checked
        mock_cache.get.assert_not_called()

        # Pipeline should be called
        service.pipeline.forward.assert_called_once()

    @patch("app.services.opportunity_service.track_pipeline_execution")
    @patch("app.services.opportunity_service.track_opportunity_created")
    async def test_create_opportunity_metrics_tracking(
        self,
        mock_track_created,
        mock_track_pipeline,
        service,
        mock_repository,
    ):
        """Test that metrics are tracked during opportunity creation."""
        created_opportunity = Opportunity(
            id=1,
            recruiter_name="Jane Smith",
            company="TechCorp",
            tier="A",
            total_score=87,
            status="processed",
            created_at=datetime.utcnow(),
        )
        mock_repository.create.return_value = created_opportunity

        await service.create_opportunity(
            recruiter_name="Jane Smith",
            raw_message="Test message",
        )

        # Verify metrics were tracked
        mock_track_pipeline.assert_called()
        mock_track_created.assert_called_once()

    async def test_create_opportunity_error_handling(self, service, mock_db_session):
        """Test error handling during opportunity creation."""
        # Mock pipeline error
        service.pipeline.forward.side_effect = Exception("Pipeline error")

        with pytest.raises(Exception):
            await service.create_opportunity(
                recruiter_name="Jane Smith",
                raw_message="Test message",
            )

        # Verify rollback was called
        mock_db_session.rollback.assert_called_once()


@pytest.mark.asyncio
class TestOpportunityServiceGet:
    """Test opportunity retrieval."""

    async def test_get_opportunity_from_cache(self, service, mock_cache):
        """Test getting opportunity from cache."""
        cached_data = {
            "id": 1,
            "recruiter_name": "Jane Smith",
            "company": "TechCorp",
            "tier": "A",
            "total_score": 87,
            "created_at": datetime.utcnow().isoformat(),
        }
        mock_cache.get.return_value = cached_data

        result = await service.get_opportunity(1, use_cache=True)

        assert result.id == 1
        assert result.company == "TechCorp"

        # Repository should not be called (cache hit)
        service.repository.get_by_id.assert_not_called()

    async def test_get_opportunity_from_database(self, service, mock_cache, mock_repository):
        """Test getting opportunity from database."""
        mock_cache.get.return_value = None

        db_opportunity = Opportunity(
            id=1,
            recruiter_name="Jane Smith",
            company="TechCorp",
            tier="A",
            total_score=87,
            created_at=datetime.utcnow(),
        )
        mock_repository.get_by_id.return_value = db_opportunity

        result = await service.get_opportunity(1, use_cache=True)

        assert result.id == 1
        mock_repository.get_by_id.assert_called_once_with(1)

        # Should cache the result
        mock_cache.set.assert_called_once()

    async def test_get_opportunity_not_found(self, service, mock_cache, mock_repository):
        """Test getting non-existent opportunity."""
        mock_cache.get.return_value = None
        mock_repository.get_by_id.return_value = None

        from app.core.exceptions import OpportunityNotFoundError

        with pytest.raises(OpportunityNotFoundError):
            await service.get_opportunity(999)


@pytest.mark.asyncio
class TestOpportunityServiceList:
    """Test opportunity listing."""

    async def test_list_opportunities(self, service, mock_repository):
        """Test listing opportunities."""
        opportunities = [
            Opportunity(id=1, company="Corp1", tier="A", total_score=90),
            Opportunity(id=2, company="Corp2", tier="B", total_score=75),
        ]
        mock_repository.get_all.return_value = opportunities

        result = await service.list_opportunities(skip=0, limit=10)

        assert len(result) == 2
        assert result[0].company == "Corp1"
        assert result[1].company == "Corp2"

    async def test_list_opportunities_with_filters(self, service, mock_repository):
        """Test listing with filters."""
        opportunities = [Opportunity(id=1, company="Corp1", tier="A", total_score=90)]
        mock_repository.get_all.return_value = opportunities

        result = await service.list_opportunities(
            tier="A",
            min_score=80,
            sort_by="total_score",
            sort_order="desc",
        )

        assert len(result) == 1

        # Verify filters were passed to repository
        mock_repository.get_all.assert_called_once()
        call_kwargs = mock_repository.get_all.call_args[1]
        assert call_kwargs["tier"] == "A"
        assert call_kwargs["min_score"] == 80

    async def test_list_opportunities_with_cache(self, service, mock_cache):
        """Test listing with cache."""
        cached_data = [
            {"id": 1, "company": "Corp1", "tier": "A"},
            {"id": 2, "company": "Corp2", "tier": "B"},
        ]
        mock_cache.get.return_value = cached_data

        result = await service.list_opportunities()

        assert len(result) == 2

        # Repository should not be called
        service.repository.get_all.assert_not_called()


@pytest.mark.asyncio
class TestOpportunityServiceUpdate:
    """Test opportunity updates."""

    async def test_update_opportunity(self, service, mock_repository, mock_cache, mock_db_session):
        """Test updating opportunity."""
        updated_opportunity = Opportunity(
            id=1,
            company="TechCorp",
            tier="A",
            status="archived",
        )
        mock_repository.update.return_value = updated_opportunity

        result = await service.update_opportunity(1, status="archived")

        assert result.status == "archived"
        mock_db_session.commit.assert_called_once()
        mock_cache.delete.assert_called()


@pytest.mark.asyncio
class TestOpportunityServiceDelete:
    """Test opportunity deletion."""

    async def test_delete_opportunity(self, service, mock_repository, mock_cache, mock_db_session):
        """Test deleting opportunity."""
        mock_repository.delete.return_value = True

        result = await service.delete_opportunity(1)

        assert result is True
        mock_db_session.commit.assert_called_once()
        mock_cache.delete.assert_called()


@pytest.mark.asyncio
class TestOpportunityServiceStats:
    """Test opportunity statistics."""

    async def test_get_stats_from_cache(self, service, mock_cache):
        """Test getting stats from cache."""
        cached_stats = {
            "total_count": 100,
            "by_tier": {"A": 10, "B": 30, "C": 40, "D": 20},
            "average_score": 72.5,
        }
        mock_cache.get.return_value = cached_stats

        result = await service.get_stats(use_cache=True)

        assert result["total_count"] == 100
        assert result["by_tier"]["A"] == 10

    async def test_get_stats_from_database(self, service, mock_cache, mock_repository):
        """Test getting stats from database."""
        mock_cache.get.return_value = None
        mock_repository.count.return_value = 100
        mock_repository.count_by_tier.return_value = {"A": 10, "B": 30}
        mock_repository.get_stats.return_value = {
            "avg_score": 75.0,
            "max_score": 95,
            "min_score": 45,
        }

        result = await service.get_stats()

        assert result["total_count"] == 100
        assert result["by_tier"] == {"A": 10, "B": 30}
        assert result["average_score"] == 75.0

        # Should cache the result
        mock_cache.set.assert_called_once()
