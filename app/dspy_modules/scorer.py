"""
Scorer - DSPy module to score opportunities based on candidate profile.

Evaluates how well an opportunity matches candidate's preferences
and requirements.
"""

import json

import dspy

from app.core.logging import get_logger
from app.dspy_modules.models import CandidateProfile, ExtractedData, ScoringResult
from app.dspy_modules.signatures import ScoringSignature
from app.observability import observe

logger = get_logger(__name__)


class Scorer(dspy.Module):
    """
    Scores opportunities based on extracted data and candidate profile.

    Evaluates multiple dimensions:
    - Tech stack match (0-40 points)
    - Salary adequacy (0-30 points)
    - Seniority fit (0-20 points)
    - Company attractiveness (0-10 points)

    Total: 0-100 points
    """

    def __init__(self):
        """Initialize the scorer."""
        super().__init__()
        self.score = dspy.ChainOfThought(ScoringSignature)

    @observe(name="dspy.scorer.forward")
    def forward(
        self,
        extracted: ExtractedData,
        profile: CandidateProfile,
    ) -> ScoringResult:
        """
        Score an opportunity.

        Args:
            extracted: Extracted job data
            profile: Candidate profile

        Returns:
            ScoringResult: Scores and reasoning

        Example:
            scorer = Scorer()
            result = scorer(extracted=data, profile=profile)
        """
        logger.debug(
            "scorer_start",
            company=extracted.company,
            role=extracted.role,
        )

        try:
            # Prepare inputs as JSON
            extracted_json = json.dumps(
                {
                    "company": extracted.company,
                    "role": extracted.role,
                    "seniority": extracted.seniority,
                    "tech_stack": extracted.tech_stack,
                    "salary_min": extracted.salary_min,
                    "salary_max": extracted.salary_max,
                    "remote_policy": extracted.remote_policy,
                    "location": extracted.location,
                },
                indent=2,
            )

            profile_json = json.dumps(
                {
                    "name": profile.name,
                    "preferred_technologies": profile.preferred_technologies,
                    "years_of_experience": profile.years_of_experience,
                    "current_seniority": profile.current_seniority,
                    "minimum_salary_usd": profile.minimum_salary_usd,
                    "preferred_remote_policy": profile.preferred_remote_policy,
                },
                indent=2,
            )

            # Call LLM
            prediction = self.score(
                extracted_data=extracted_json,
                candidate_profile=profile_json,
            )

            # Parse and validate scores
            scoring = ScoringResult(
                tech_stack_score=self._clamp(prediction.tech_stack_score, 0, 40),
                tech_stack_reasoning=prediction.tech_stack_reasoning,
                salary_score=self._clamp(prediction.salary_score, 0, 30),
                salary_reasoning=prediction.salary_reasoning,
                seniority_score=self._clamp(prediction.seniority_score, 0, 20),
                seniority_reasoning=prediction.seniority_reasoning,
                company_score=self._clamp(prediction.company_score, 0, 10),
                company_reasoning=prediction.company_reasoning,
            )

            logger.info(
                "scorer_success",
                total_score=scoring.total_score,
                tier=scoring.tier,
                tech=scoring.tech_stack_score,
                salary=scoring.salary_score,
                seniority=scoring.seniority_score,
                company=scoring.company_score,
            )

            return scoring

        except Exception as e:
            logger.error("scorer_failed", error=str(e))
            # Return fallback scoring
            return self._fallback_scoring(extracted, profile)

    def _clamp(self, value: int, min_val: int, max_val: int) -> int:
        """
        Clamp value between min and max.

        Args:
            value: Value to clamp
            min_val: Minimum allowed value
            max_val: Maximum allowed value

        Returns:
            int: Clamped value
        """
        try:
            val = int(value)
            return max(min_val, min(val, max_val))
        except (ValueError, TypeError):
            return min_val

    def _fallback_scoring(
        self,
        extracted: ExtractedData,
        profile: CandidateProfile,
    ) -> ScoringResult:
        """
        Fallback scoring logic when LLM fails.

        Uses simple heuristics to score the opportunity.

        Args:
            extracted: Extracted data
            profile: Candidate profile

        Returns:
            ScoringResult: Fallback scores
        """
        logger.warning("using_fallback_scoring")

        # Tech stack score (0-40)
        tech_stack_score = self._score_tech_stack(
            extracted.tech_stack,
            profile.preferred_technologies,
        )

        # Salary score (0-30)
        salary_score = self._score_salary(
            extracted.salary_min,
            extracted.salary_max,
            profile.minimum_salary_usd,
        )

        # Seniority score (0-20)
        seniority_score = self._score_seniority(
            extracted.seniority,
            profile.current_seniority,
        )

        # Company score (0-10)
        company_score = self._score_company(extracted.company)

        return ScoringResult(
            tech_stack_score=tech_stack_score,
            tech_stack_reasoning="Fallback: Basic tech stack matching",
            salary_score=salary_score,
            salary_reasoning="Fallback: Salary comparison",
            seniority_score=seniority_score,
            seniority_reasoning="Fallback: Seniority matching",
            company_score=company_score,
            company_reasoning="Fallback: Company evaluation",
        )

    def _score_tech_stack(
        self,
        job_tech: list[str],
        preferred_tech: list[str],
    ) -> int:
        """Score tech stack match (0-40)."""
        if not job_tech or not preferred_tech:
            return 20  # Neutral score

        # Calculate overlap
        job_set = {t.lower() for t in job_tech}
        pref_set = {t.lower() for t in preferred_tech}
        matches = len(job_set & pref_set)
        total = len(pref_set)

        if total == 0:
            return 20

        # Score based on percentage match
        match_ratio = matches / total
        return int(40 * match_ratio)

    def _score_salary(
        self,
        salary_min: int | None,
        salary_max: int | None,
        minimum_required: int,
    ) -> int:
        """Score salary (0-30)."""
        if not salary_min:
            return 15  # Neutral score when salary not mentioned

        # Use max if available, otherwise min
        offered = salary_max or salary_min

        if offered >= minimum_required * 1.5:
            return 30  # Excellent
        elif offered >= minimum_required * 1.2:
            return 25  # Very good
        elif offered >= minimum_required:
            return 20  # Acceptable
        elif offered >= minimum_required * 0.8:
            return 10  # Below expectations
        else:
            return 0  # Too low

    def _score_seniority(
        self,
        job_seniority: str,
        current_seniority: str,
    ) -> int:
        """Score seniority match (0-20)."""
        seniority_levels = {
            "Junior": 1,
            "Mid": 2,
            "Senior": 3,
            "Staff": 4,
            "Principal": 5,
            "Unknown": 0,
        }

        job_level = seniority_levels.get(job_seniority, 0)
        current_level = seniority_levels.get(current_seniority, 0)

        if job_level == 0 or current_level == 0:
            return 10  # Neutral

        # Perfect match
        if job_level == current_level:
            return 20

        # One level up (promotion)
        if job_level == current_level + 1:
            return 18

        # Same level or one down
        if job_level == current_level - 1:
            return 15

        # Too junior
        if job_level < current_level - 1:
            return 5

        # Too senior
        if job_level > current_level + 1:
            return 10

        return 10

    def _score_company(self, company: str) -> int:
        """Score company attractiveness (0-10)."""
        # Simple heuristic - can be enhanced with company database
        well_known = [
            "google",
            "microsoft",
            "amazon",
            "apple",
            "meta",
            "netflix",
            "uber",
            "airbnb",
            "stripe",
            "spotify",
            "mercadolibre",
            "mercadolibre",
            "globant",
            "auth0",
        ]

        company_lower = company.lower()
        for known in well_known:
            if known in company_lower:
                return 10

        # Unknown company gets neutral score
        return 5
