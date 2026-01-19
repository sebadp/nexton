"""
Test configuration and fixtures.
"""
import asyncio
from typing import AsyncGenerator, Generator
from unittest.mock import MagicMock, Mock

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from app.core.config import settings
from app.database.base import Base
from app.database.models import Opportunity
from app.main import app

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
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        poolclass=NullPool,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create database session for tests."""
    async_session = sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        yield session
        await session.rollback()


# ============================================================================
# API Client Fixtures
# ============================================================================


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Create async HTTP client for API tests."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


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
            salary_score=25,
            seniority_score=18,
            company_score=8,
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
