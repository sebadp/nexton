"""
Test configuration and fixtures.
"""

import asyncio
from collections.abc import AsyncGenerator, Generator
from unittest.mock import Mock

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.database.base import Base
from app.database.models import Opportunity
from app.main import app

# Disable observability in tests to prevent:
# 1. Spamming Langfuse with test traces
# 2. slowing down tests with network calls
# 3. Requiring API keys in CI/CD environment
settings.OTEL_ENABLED = False
settings.LANGFUSE_SECRET_KEY = None
settings.DATABASE_URL = (
    "sqlite+aiosqlite:///:memory:"  # Force valid URL format for validation logic if needed
)

# ============================================================================
# Database Fixtures
# ============================================================================


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine():
    """Create test database engine."""
    # Use in-memory SQLite for tests
    from sqlalchemy.pool import StaticPool

    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        poolclass=StaticPool,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create database session for tests."""
    async_session = sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        yield session
        await session.rollback()


# ============================================================================
# API Client Fixtures
# ============================================================================


@pytest.fixture
async def client(
    db_session: AsyncSession, mock_pipeline: Mock
) -> AsyncGenerator[AsyncClient, None]:
    """Create async HTTP client for API tests."""
    from unittest.mock import AsyncMock, patch

    from app.database.dependencies import get_db

    # Override dependency
    app.dependency_overrides[get_db] = lambda: db_session

    from httpx import ASGITransport

    transport = ASGITransport(app=app)

    # Patch database initialization in lifespan and pipeline/profile dependencies
    with patch("app.main.init_db", new_callable=AsyncMock), patch(
        "app.main.close_db", new_callable=AsyncMock
    ), patch("app.api.v1.opportunities.get_pipeline") as mock_get_pipeline, patch(
        "app.api.v1.opportunities.get_profile"
    ) as mock_get_profile:
        # Configure mocks
        from app.dspy_modules.models import CandidateProfile

        mock_get_pipeline.return_value = mock_pipeline

        # Create profile from sample data
        profile_data = {
            "name": "Test User",
            "preferred_technologies": ["Python", "FastAPI"],
            "years_of_experience": 5,
            "current_seniority": "Senior",
            "minimum_salary_usd": 60000,
            "ideal_salary_usd": 120000,
            "preferred_remote_policy": "Remote",
            "preferred_locations": ["Argentina"],
            "preferred_company_size": "Mid-size",
            "industry_preferences": ["Technology"],
            "open_to_relocation": False,
            "looking_for_change": True,
            "notes": "Test notes",
            "id": 1,
        }
        mock_get_profile.return_value = CandidateProfile(**profile_data)

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield client

    app.dependency_overrides.clear()


# ============================================================================
# Mock Fixtures
# ============================================================================


@pytest.fixture
def mock_ollama():
    """Mock Ollama LLM for DSPy tests."""
    mock = Mock()
    mock.generate.return_value = {
        "company": "TechCorp",
        "role": "Senior Python Engineer",
        "seniority": "Senior",
        "tech_stack": "Python, FastAPI, PostgreSQL",
        "salary_min": "100000",
        "salary_max": "120000",
        "currency": "USD",
        "remote_policy": "Remote",
    }
    return mock


@pytest.fixture
def mock_pipeline():
    """Mock DSPy pipeline."""
    from app.dspy_modules.models import (
        ExtractedData,
        OpportunityResult,
        ScoringResult,
    )

    mock = Mock()
    mock.forward.return_value = OpportunityResult(
        recruiter_name="Test Recruiter",
        raw_message="Test message",
        extracted=ExtractedData(
            company="TechCorp",
            role="Senior Python Engineer",
            seniority="Senior",
            tech_stack=["Python", "FastAPI", "PostgreSQL"],
            salary_min=100000,
            salary_max=120000,
            currency="USD",
            remote_policy="Remote",
            location="Remote",
            description="Test job description",
        ),
        scoring=ScoringResult(
            tech_stack_score=35,
            tech_stack_reasoning="Good match",
            salary_score=25,
            salary_reasoning="Above minimum",
            seniority_score=18,
            seniority_reasoning="Matches request",
            company_score=8,
            company_reasoning="Good company",
        ),
        ai_response="Test response",
        processing_time_ms=1000,
        status="processed",
    )
    return mock


# ============================================================================
# Data Fixtures
# ============================================================================


@pytest.fixture
def sample_opportunity_data() -> dict:
    """Sample opportunity data for tests."""
    return {
        "recruiter_name": "María González",
        "raw_message": "Hola! Tenemos una posición de Senior Python Engineer en TechCorp...",
        "company": "TechCorp",
        "role": "Senior Python Engineer",
        "seniority": "Senior",
        "tech_stack": ["Python", "FastAPI", "PostgreSQL", "Docker"],
        "salary_min": 100000,
        "salary_max": 120000,
        "currency": "USD",
        "remote_policy": "Remote",
        "location": "Remote",
        "description": "Buscamos un Senior Python Engineer...",
        "tech_stack_score": 35,
        "salary_score": 25,
        "seniority_score": 18,
        "company_score": 8,
        "total_score": 86,
        "tier": "HIGH_PRIORITY",
        "ai_response": "Hola María, muchas gracias por contactarme...",
        "status": "processed",
        "processing_time_ms": 1500,
    }


@pytest.fixture
async def sample_opportunity(
    db_session: AsyncSession, sample_opportunity_data: dict
) -> Opportunity:
    """Create sample opportunity in database."""
    opportunity = Opportunity(**sample_opportunity_data)
    db_session.add(opportunity)
    await db_session.commit()
    await db_session.refresh(opportunity)
    return opportunity


@pytest.fixture
def sample_profile_data() -> dict:
    """Sample candidate profile data."""
    return {
        "name": "Test User",
        "preferred_technologies": ["Python", "FastAPI", "PostgreSQL"],
        "years_of_experience": 5,
        "current_seniority": "Senior",
        "minimum_salary_usd": 80000,
        "ideal_salary_usd": 120000,
        "preferred_remote_policy": "Remote",
        "preferred_locations": ["Remote", "Argentina"],
        "preferred_company_size": "Mid-size",
        "industry_preferences": ["Technology", "AI/ML"],
        "open_to_relocation": False,
        "looking_for_change": True,
        "notes": "Test notes",
    }
