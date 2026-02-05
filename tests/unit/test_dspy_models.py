"""
Unit tests for DSPy models (Pydantic).
"""

import pytest

from app.dspy_modules.models import (
    CandidateProfile,
    ExtractedData,
    OpportunityResult,
    ScoringResult,
)


class TestExtractedData:
    """Test ExtractedData model."""

    def test_create_extracted_data(self):
        """Test creating ExtractedData."""
        data = ExtractedData(
            company="TechCorp",
            role="Senior Engineer",
            seniority="Senior",
            tech_stack=["Python", "FastAPI"],
            salary_min=100000,
            salary_max=120000,
            currency="USD",
            remote_policy="Remote",
            location="Remote",
            description="Test job",
        )

        assert data.company == "TechCorp"
        assert data.role == "Senior Engineer"
        assert len(data.tech_stack) == 2
        assert data.salary_min == 100000

    def test_extracted_data_defaults(self):
        """Test ExtractedData defaults."""
        data = ExtractedData()

        assert data.company is None
        assert data.role is None
        assert data.tech_stack == []
        assert data.salary_min is None


class TestScoringResult:
    """Test ScoringResult model."""

    def test_create_scoring_result(self):
        """Test creating ScoringResult."""
        scoring = ScoringResult(
            tech_stack_score=35,
            salary_score=25,
            seniority_score=18,
            company_score=8,
        )

        assert scoring.tech_stack_score == 35
        assert scoring.salary_score == 25
        assert scoring.seniority_score == 18
        assert scoring.company_score == 8

    def test_total_score_calculation(self):
        """Test total_score property."""
        scoring = ScoringResult(
            tech_stack_score=35,
            salary_score=25,
            seniority_score=18,
            company_score=8,
        )

        assert scoring.total_score == 86

    def test_tier_classification_high_priority(self):
        """Test HIGH_PRIORITY tier (75-100)."""
        scoring = ScoringResult(
            tech_stack_score=35,
            salary_score=25,
            seniority_score=15,
            company_score=10,
        )

        assert scoring.total_score == 85
        assert scoring.tier == "HIGH_PRIORITY"

    def test_tier_classification_interesante(self):
        """Test INTERESANTE tier (50-74)."""
        scoring = ScoringResult(
            tech_stack_score=25,
            salary_score=20,
            seniority_score=10,
            company_score=5,
        )

        assert scoring.total_score == 60
        assert scoring.tier == "INTERESANTE"

    def test_tier_classification_poco_interesante(self):
        """Test POCO_INTERESANTE tier (30-49)."""
        scoring = ScoringResult(
            tech_stack_score=15,
            salary_score=10,
            seniority_score=8,
            company_score=2,
        )

        assert scoring.total_score == 35
        assert scoring.tier == "POCO_INTERESANTE"

    def test_tier_classification_no_interesa(self):
        """Test NO_INTERESA tier (0-29)."""
        scoring = ScoringResult(
            tech_stack_score=10,
            salary_score=5,
            seniority_score=5,
            company_score=0,
        )

        assert scoring.total_score == 20
        assert scoring.tier == "NO_INTERESA"

    def test_score_validation_max(self):
        """Test score validation (max values)."""
        with pytest.raises(ValueError):
            ScoringResult(
                tech_stack_score=50,  # Max is 40
                salary_score=25,
                seniority_score=18,
                company_score=8,
            )

    def test_score_validation_min(self):
        """Test score validation (min values)."""
        with pytest.raises(ValueError):
            ScoringResult(
                tech_stack_score=-5,  # Min is 0
                salary_score=25,
                seniority_score=18,
                company_score=8,
            )


class TestCandidateProfile:
    """Test CandidateProfile model."""

    def test_create_profile(self, sample_profile_data: dict):
        """Test creating CandidateProfile."""
        profile = CandidateProfile(**sample_profile_data)

        assert profile.name == "Test User"
        assert len(profile.preferred_technologies) == 3
        assert profile.years_of_experience == 5
        assert profile.minimum_salary_usd == 80000

    def test_profile_defaults(self):
        """Test CandidateProfile defaults."""
        profile = CandidateProfile(
            name="Test",
            years_of_experience=5,
            current_seniority="Senior",
        )

        assert profile.preferred_technologies == []
        assert profile.preferred_locations == []
        assert profile.industry_preferences == []


class TestOpportunityResult:
    """Test OpportunityResult model."""

    def test_create_opportunity_result(self):
        """Test creating OpportunityResult."""
        extracted = ExtractedData(company="TechCorp", role="Engineer")
        scoring = ScoringResult(
            tech_stack_score=30,
            salary_score=20,
            seniority_score=15,
            company_score=5,
        )

        result = OpportunityResult(
            recruiter_name="Test Recruiter",
            raw_message="Test message",
            extracted=extracted,
            scoring=scoring,
            ai_response="Test response",
            processing_time_ms=1000,
            status="processed",
        )

        assert result.recruiter_name == "Test Recruiter"
        assert result.extracted.company == "TechCorp"
        assert result.scoring.total_score == 70
        assert result.ai_response == "Test response"
        assert result.processing_time_ms == 1000
