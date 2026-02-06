"""
Tests for conversation state analyzer and hard filters.

Tests the following scenarios:
- COURTESY_CLOSE detection for simple acknowledgment messages
- NEW_OPPORTUNITY detection for job offers
- FOLLOW_UP detection for response messages
- Hard filter validation for work week requirements
"""

import pytest

from app.dspy_modules.hard_filters import (
    apply_hard_filters,
    check_salary_requirement,
    check_tech_stack_match,
    check_work_week_requirement,
    get_candidate_status_from_profile,
)
from app.dspy_modules.message_analyzer import ConversationStateAnalyzer
from app.dspy_modules.models import (
    CandidateStatus,
    ConversationState,
    ConversationStateResult,
    ExtractedData,
    HardFilterResult,
    ScoringResult,
)


class TestCourtesyPhraseDetection:
    """Tests for quick courtesy phrase detection."""

    @pytest.mark.parametrize(
        "message",
        [
            "Gracias",
            "gracias",
            "GRACIAS",
            "Muchas gracias",
            "Ok",
            "OK",
            "Dale",
            "Perfecto",
            "Excelente",
            "Genial",
            "Quedamos así",
            "Suerte",
            "Éxitos",
            "Thanks",
            "Thank you",
            "Perfect",
            "Great",
            "Good luck",
            "Sounds good",
            "Got it",
            "Understood",
            "Listo",
            "Entendido",
        ],
    )
    def test_courtesy_phrases_detected(self, message: str):
        """Test that common courtesy phrases are detected."""
        analyzer = ConversationStateAnalyzer()
        result = analyzer._quick_courtesy_check(message)

        assert result is not None, f"Failed to detect courtesy phrase: {message}"
        assert result.state == ConversationState.COURTESY_CLOSE
        assert result.should_process is False
        assert result.confidence == "HIGH"

    @pytest.mark.parametrize(
        "message",
        [
            "Gracias!",
            "gracias.",
            "Ok!",
            "Perfecto!",
            "Thanks!",
            "Great!",
        ],
    )
    def test_courtesy_phrases_with_punctuation(self, message: str):
        """Test that courtesy phrases with punctuation are detected."""
        analyzer = ConversationStateAnalyzer()
        result = analyzer._quick_courtesy_check(message)

        assert result is not None, f"Failed to detect courtesy phrase with punctuation: {message}"
        assert result.state == ConversationState.COURTESY_CLOSE

    @pytest.mark.parametrize(
        "message",
        [
            "Hola, gracias",
            "Hi, thanks",
            "Hey gracias",
        ],
    )
    def test_greeting_with_thanks(self, message: str):
        """Test that greetings with thanks are detected as courtesy."""
        analyzer = ConversationStateAnalyzer()
        result = analyzer._quick_courtesy_check(message)

        assert result is not None, f"Failed to detect greeting with thanks: {message}"
        assert result.state == ConversationState.COURTESY_CLOSE


class TestNotCourtesyMessages:
    """Tests that real job messages are NOT classified as courtesy."""

    @pytest.mark.parametrize(
        "message",
        [
            "Hola! Tenemos una posición de Senior Backend Engineer en TechCorp",
            "Estamos buscando un Python Developer para nuestro equipo",
            "Te contacto porque vi tu perfil y creo que serías ideal para una posición en nuestra empresa",
            "Tenemos una oportunidad en Google para un Staff Engineer",
            "Me gustaría presentarte una posición remota con salario de 150k USD",
        ],
    )
    def test_job_offers_not_courtesy(self, message: str):
        """Test that job offers are NOT detected as courtesy."""
        analyzer = ConversationStateAnalyzer()
        result = analyzer._quick_courtesy_check(message)

        assert result is None, f"Incorrectly classified job offer as courtesy: {message}"


class TestConversationStateResultFactory:
    """Tests for ConversationStateResult factory methods."""

    def test_courtesy_close_factory(self):
        """Test the courtesy_close factory method."""
        result = ConversationStateResult.courtesy_close()

        assert result.state == ConversationState.COURTESY_CLOSE
        assert result.confidence == "HIGH"
        assert result.should_process is False
        assert result.contains_job_details is False

    def test_courtesy_close_with_custom_reasoning(self):
        """Test courtesy_close with custom reasoning."""
        result = ConversationStateResult.courtesy_close(reasoning="Custom test reason")

        assert result.reasoning == "Custom test reason"


class TestHardFilterResultFactory:
    """Tests for HardFilterResult factory methods."""

    def test_all_passed_factory(self):
        """Test the all_passed factory method."""
        result = HardFilterResult.all_passed()

        assert result.passed is True
        assert result.failed_filters == []
        assert result.score_penalty == 0
        assert result.should_decline is False


class TestWorkWeekFilter:
    """Tests for work week requirement filter."""

    def test_four_day_week_confirmed(self):
        """Test when 4-day week is explicitly mentioned."""
        extracted = ExtractedData(
            company="TechCorp",
            role="Engineer",
            work_week="4-days",
        )

        passed, status = check_work_week_requirement(
            extracted, "Tenemos semana laboral de 4 días", "4-days"
        )

        assert passed is True
        assert status == "CONFIRMED"

    def test_four_day_week_not_mentioned(self):
        """Test when 4-day week is NOT mentioned but required."""
        extracted = ExtractedData(
            company="TechCorp",
            role="Engineer",
        )

        passed, status = check_work_week_requirement(
            extracted, "Posición de Senior Engineer", "4-days"
        )

        assert passed is False
        assert status == "NOT_MENTIONED"

    def test_five_day_week_explicit(self):
        """Test when 5-day week is explicitly required."""
        extracted = ExtractedData(
            company="TechCorp",
            role="Engineer",
        )

        passed, status = check_work_week_requirement(
            extracted, "Posición full time de 5 días a la semana", "4-days"
        )

        assert passed is False
        assert status == "FIVE_DAY"

    def test_five_day_not_required_by_candidate(self):
        """Test when candidate doesn't require 4-day week."""
        extracted = ExtractedData(
            company="TechCorp",
            role="Engineer",
        )

        passed, status = check_work_week_requirement(extracted, "Posición full time", "5-days")

        assert passed is True
        assert status == "NOT_REQUIRED"


class TestSalaryFilter:
    """Tests for salary requirement filter."""

    def test_salary_above_minimum(self):
        """Test when salary is above minimum."""
        extracted = ExtractedData(
            company="TechCorp",
            role="Engineer",
            salary_min=100000,
            salary_max=150000,
            currency="USD",
        )

        passed, reason = check_salary_requirement(extracted, minimum_salary_usd=80000)

        assert passed is True
        assert reason is None

    def test_salary_below_minimum(self):
        """Test when salary is below minimum."""
        extracted = ExtractedData(
            company="TechCorp",
            role="Engineer",
            salary_min=50000,
            salary_max=70000,
            currency="USD",
        )

        passed, reason = check_salary_requirement(extracted, minimum_salary_usd=80000)

        assert passed is False
        assert "below minimum" in reason.lower()

    def test_salary_not_mentioned(self):
        """Test when salary is not mentioned (should pass)."""
        extracted = ExtractedData(
            company="TechCorp",
            role="Engineer",
        )

        passed, reason = check_salary_requirement(extracted, minimum_salary_usd=80000)

        assert passed is True
        assert reason is None


class TestTechStackFilter:
    """Tests for tech stack match filter."""

    def test_high_tech_match(self):
        """Test when tech stack match is high."""
        scoring = ScoringResult(
            tech_stack_score=35,  # 87.5% match
            tech_stack_reasoning="Good match",
            salary_score=20,
            salary_reasoning="Good salary",
            seniority_score=15,
            seniority_reasoning="Good fit",
            company_score=8,
            company_reasoning="Good company",
        )

        passed, reason = check_tech_stack_match(scoring, min_tech_match_percent=50)

        assert passed is True
        assert reason is None

    def test_low_tech_match(self):
        """Test when tech stack match is low."""
        scoring = ScoringResult(
            tech_stack_score=15,  # 37.5% match
            tech_stack_reasoning="Partial match",
            salary_score=20,
            salary_reasoning="Good salary",
            seniority_score=15,
            seniority_reasoning="Good fit",
            company_score=8,
            company_reasoning="Good company",
        )

        passed, reason = check_tech_stack_match(scoring, min_tech_match_percent=50)

        assert passed is False
        assert "below threshold" in reason.lower()


class TestCandidateStatus:
    """Tests for candidate status determination."""

    def test_active_search_status(self):
        """Test ACTIVE_SEARCH status determination."""
        profile = {
            "job_search_status": {
                "actively_looking": True,
                "urgency": "urgent",
            }
        }

        status = get_candidate_status_from_profile(profile)

        assert status == CandidateStatus.ACTIVE_SEARCH

    def test_selective_status(self):
        """Test SELECTIVE status determination."""
        profile = {
            "job_search_status": {
                "actively_looking": True,
                "urgency": "selective",
            }
        }

        status = get_candidate_status_from_profile(profile)

        assert status == CandidateStatus.SELECTIVE

    def test_passive_status(self):
        """Test PASSIVE status determination."""
        profile = {
            "job_search_status": {
                "actively_looking": True,
                "urgency": "moderate",
            }
        }

        status = get_candidate_status_from_profile(profile)

        assert status == CandidateStatus.PASSIVE

    def test_not_looking_status(self):
        """Test NOT_LOOKING status determination."""
        profile = {
            "job_search_status": {
                "actively_looking": False,
                "urgency": "not_looking",
            }
        }

        status = get_candidate_status_from_profile(profile)

        assert status == CandidateStatus.NOT_LOOKING


class TestApplyHardFilters:
    """Integration tests for apply_hard_filters function."""

    def test_all_filters_pass(self):
        """Test when all filters pass."""
        extracted = ExtractedData(
            company="TechCorp",
            role="Senior Engineer",
            salary_min=100000,
            salary_max=150000,
            currency="USD",
            remote_policy="Remote",
        )

        scoring = ScoringResult(
            tech_stack_score=35,
            tech_stack_reasoning="Good match",
            salary_score=25,
            salary_reasoning="Good salary",
            seniority_score=18,
            seniority_reasoning="Good fit",
            company_score=8,
            company_reasoning="Good company",
        )

        profile_dict = {
            "preferred_work_week": "5-days",  # Not requiring 4-day
            "minimum_salary_usd": 80000,
            "preferred_remote_policy": "Remote",
            "job_search_status": {
                "reject_if": [],
            },
        }

        result = apply_hard_filters(
            extracted=extracted,
            scoring=scoring,
            raw_message="Great opportunity at TechCorp",
            profile_dict=profile_dict,
        )

        assert result.passed is True
        assert result.failed_filters == []
        assert result.should_decline is False

    def test_four_day_week_not_mentioned_fails(self):
        """Test that missing 4-day week fails filter."""
        extracted = ExtractedData(
            company="TechCorp",
            role="Senior Engineer",
        )

        scoring = ScoringResult(
            tech_stack_score=35,
            tech_stack_reasoning="Good match",
            salary_score=25,
            salary_reasoning="Good salary",
            seniority_score=18,
            seniority_reasoning="Good fit",
            company_score=8,
            company_reasoning="Good company",
        )

        profile_dict = {
            "preferred_work_week": "4-days",  # Requiring 4-day
            "minimum_salary_usd": 80000,
            "preferred_remote_policy": "Remote",
            "job_search_status": {
                "reject_if": [],
            },
        }

        result = apply_hard_filters(
            extracted=extracted,
            scoring=scoring,
            raw_message="Great opportunity",
            profile_dict=profile_dict,
        )

        assert result.passed is False
        assert "4-day work week not mentioned" in result.failed_filters
        assert result.work_week_status == "NOT_MENTIONED"


class TestNoResponseForCourtesy:
    """Tests verifying that no response is generated for courtesy messages."""

    @pytest.mark.parametrize(
        "message",
        [
            "Gracias",
            "Ok, perfecto",
            "Dale",
            "Quedamos así",
        ],
    )
    def test_no_response_for_courtesy(self, message: str):
        """Verify that courtesy messages should not generate a response."""
        analyzer = ConversationStateAnalyzer()
        result = analyzer._quick_courtesy_check(message)

        assert result is not None
        assert result.state == ConversationState.COURTESY_CLOSE
        assert result.should_process is False
        # The pipeline should return empty ai_response for these


class TestEnumValues:
    """Tests for enum definitions."""

    def test_conversation_state_values(self):
        """Test ConversationState enum values."""
        assert ConversationState.NEW_OPPORTUNITY.value == "NEW_OPPORTUNITY"
        assert ConversationState.FOLLOW_UP.value == "FOLLOW_UP"
        assert ConversationState.COURTESY_CLOSE.value == "COURTESY_CLOSE"

    def test_candidate_status_values(self):
        """Test CandidateStatus enum values."""
        assert CandidateStatus.ACTIVE_SEARCH.value == "ACTIVE_SEARCH"
        assert CandidateStatus.PASSIVE.value == "PASSIVE"
        assert CandidateStatus.SELECTIVE.value == "SELECTIVE"
        assert CandidateStatus.NOT_LOOKING.value == "NOT_LOOKING"
