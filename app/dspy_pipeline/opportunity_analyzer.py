"""
Opportunity Analyzer using DSPy.

Analyzes LinkedIn messages to extract opportunity details and calculate match scores.
"""

from typing import Optional
from pydantic import BaseModel, Field
import dspy

from app.core.config import settings
from app.core.logging import get_logger
from app.dspy_pipeline.llm_factory import get_llm

logger = get_logger(__name__)


class OpportunityAnalysis(BaseModel):
    """Structured output for opportunity analysis."""

    # Extracted information
    company_name: Optional[str] = Field(None, description="Company name")
    role_title: Optional[str] = Field(None, description="Job title/role")
    salary_range: Optional[str] = Field(None, description="Salary range (e.g., '$100k-$150k')")
    location: Optional[str] = Field(None, description="Job location")
    work_mode: Optional[str] = Field(None, description="remote, hybrid, or onsite")
    tech_stack: list[str] = Field(default_factory=list, description="Technologies mentioned")
    seniority_level: Optional[str] = Field(None, description="junior, mid, senior, staff, principal")

    # Scores (0-100)
    tech_match_score: int = Field(0, ge=0, le=100, description="Tech stack match score")
    salary_match_score: int = Field(0, ge=0, le=100, description="Salary match score")
    seniority_match_score: int = Field(0, ge=0, le=100, description="Seniority match score")
    company_score: int = Field(0, ge=0, le=100, description="Company attractiveness score")
    total_score: int = Field(0, ge=0, le=100, description="Overall match score")

    # Classification
    tier: str = Field("D", description="A, B, C, or D tier")
    summary: str = Field("", description="Brief summary of the opportunity")
    is_opportunity: bool = Field(True, description="Whether this is actually a job opportunity")


class AnalyzeOpportunity(dspy.Signature):
    """Analyze a LinkedIn message to extract opportunity details and calculate scores."""

    message: str = dspy.InputField(desc="The LinkedIn message text")
    sender: str = dspy.InputField(desc="Sender's name/title")

    # Extracted fields
    company_name: str = dspy.OutputField(desc="Company name (or 'Unknown' if not found)")
    role_title: str = dspy.OutputField(desc="Job title (or 'Unknown' if not found)")
    salary_range: str = dspy.OutputField(desc="Salary range like '$100k-$150k' or 'Not mentioned'")
    location: str = dspy.OutputField(desc="Location or 'Not mentioned'")
    work_mode: str = dspy.OutputField(desc="'remote', 'hybrid', 'onsite', or 'Not mentioned'")
    tech_stack: str = dspy.OutputField(desc="Comma-separated list of technologies or 'None'")
    seniority_level: str = dspy.OutputField(desc="'junior', 'mid', 'senior', 'staff', 'principal', or 'Not mentioned'")

    # Analysis
    is_opportunity: str = dspy.OutputField(desc="'yes' if this is a job opportunity, 'no' otherwise")
    summary: str = dspy.OutputField(desc="One sentence summary of the opportunity")


class ScoreOpportunity(dspy.Signature):
    """Score an opportunity based on match with user profile."""

    # Input
    company_name: str = dspy.InputField()
    role_title: str = dspy.InputField()
    salary_range: str = dspy.InputField()
    tech_stack: str = dspy.InputField()
    seniority_level: str = dspy.InputField()
    work_mode: str = dspy.InputField()

    # User preferences (you would load these from profile)
    preferred_tech: str = dspy.InputField(desc="User's preferred technologies")
    preferred_salary: str = dspy.InputField(desc="User's target salary range")
    preferred_seniority: str = dspy.InputField(desc="User's seniority level")
    preferred_work_mode: str = dspy.InputField(desc="User's preferred work mode")

    # Scores (as strings because DSPy works best with text)
    tech_match_score: str = dspy.OutputField(desc="Tech stack match score 0-100")
    salary_match_score: str = dspy.OutputField(desc="Salary match score 0-100")
    seniority_match_score: str = dspy.OutputField(desc="Seniority match score 0-100")
    company_score: str = dspy.OutputField(desc="Company attractiveness 0-100")
    reasoning: str = dspy.OutputField(desc="Brief explanation of scores")


class OpportunityAnalyzer:
    """Analyzes LinkedIn opportunities using DSPy."""

    def __init__(
        self,
        provider: str | None = None,
        model: str | None = None,
    ):
        """
        Initialize the analyzer.

        Args:
            provider: LLM provider (uses settings if None)
            model: Model name (uses settings if None)
        """
        # Get LLM
        self.lm = get_llm(
            provider=provider or settings.ANALYZER_LLM_PROVIDER,
            model=model or settings.ANALYZER_LLM_MODEL,
        )

        # Configure DSPy to use this LLM
        dspy.configure(lm=self.lm)

        # Create DSPy modules
        self.analyzer = dspy.ChainOfThought(AnalyzeOpportunity)
        self.scorer = dspy.ChainOfThought(ScoreOpportunity)

        logger.info("opportunity_analyzer_initialized")

    def analyze(self, message: str, sender: str) -> OpportunityAnalysis:
        """
        Analyze a LinkedIn message.

        Args:
            message: Message text
            sender: Sender name/title

        Returns:
            OpportunityAnalysis with extracted info and scores
        """
        logger.info("analyzing_opportunity", sender=sender)

        try:
            # Step 1: Extract information
            extraction = self.analyzer(message=message, sender=sender)

            # Parse tech stack
            tech_stack_str = extraction.tech_stack
            if tech_stack_str and tech_stack_str.lower() != "none":
                tech_stack = [t.strip() for t in tech_stack_str.split(",")]
            else:
                tech_stack = []

            # Check if it's an opportunity
            is_opportunity = extraction.is_opportunity.lower() == "yes"

            if not is_opportunity:
                logger.info("not_an_opportunity", sender=sender)
                return OpportunityAnalysis(
                    summary=extraction.summary,
                    is_opportunity=False,
                    tier="D",
                )

            # Step 2: Score the opportunity
            # TODO: Load user preferences from profile
            user_preferences = {
                "preferred_tech": "Python, FastAPI, PostgreSQL, Docker, Kubernetes, React",
                "preferred_salary": "$120k-$180k",
                "preferred_seniority": "Senior",
                "preferred_work_mode": "Remote",
            }

            scoring = self.scorer(
                company_name=extraction.company_name,
                role_title=extraction.role_title,
                salary_range=extraction.salary_range,
                tech_stack=tech_stack_str,
                seniority_level=extraction.seniority_level,
                work_mode=extraction.work_mode,
                **user_preferences,
            )

            # Parse scores
            tech_match_score = self._parse_score(scoring.tech_match_score)
            salary_match_score = self._parse_score(scoring.salary_match_score)
            seniority_match_score = self._parse_score(scoring.seniority_match_score)
            company_score = self._parse_score(scoring.company_score)

            # Calculate total score (weighted average)
            total_score = int(
                (tech_match_score * 0.35)
                + (salary_match_score * 0.30)
                + (seniority_match_score * 0.20)
                + (company_score * 0.15)
            )

            # Determine tier
            if total_score >= 80:
                tier = "A"
            elif total_score >= 60:
                tier = "B"
            elif total_score >= 40:
                tier = "C"
            else:
                tier = "D"

            # Create result
            result = OpportunityAnalysis(
                company_name=extraction.company_name if extraction.company_name != "Unknown" else None,
                role_title=extraction.role_title if extraction.role_title != "Unknown" else None,
                salary_range=extraction.salary_range if extraction.salary_range != "Not mentioned" else None,
                location=extraction.location if extraction.location != "Not mentioned" else None,
                work_mode=extraction.work_mode if extraction.work_mode != "Not mentioned" else None,
                tech_stack=tech_stack,
                seniority_level=extraction.seniority_level if extraction.seniority_level != "Not mentioned" else None,
                tech_match_score=tech_match_score,
                salary_match_score=salary_match_score,
                seniority_match_score=seniority_match_score,
                company_score=company_score,
                total_score=total_score,
                tier=tier,
                summary=extraction.summary,
                is_opportunity=is_opportunity,
            )

            logger.info(
                "opportunity_analyzed",
                sender=sender,
                tier=tier,
                total_score=total_score,
            )

            return result

        except Exception as e:
            logger.error("analysis_failed", error=str(e), exc_info=True)
            # Return minimal analysis on error
            return OpportunityAnalysis(
                summary=f"Failed to analyze: {str(e)}",
                is_opportunity=True,  # Assume it is to be safe
                tier="C",  # Medium priority on error
                total_score=50,
            )

    def _parse_score(self, score_str: str) -> int:
        """
        Parse a score string to int.

        Args:
            score_str: Score as string (e.g., "85", "85/100", "Score: 85")

        Returns:
            Score as integer 0-100
        """
        try:
            # Extract first number from string
            import re

            numbers = re.findall(r"\d+", score_str)
            if numbers:
                score = int(numbers[0])
                # Clamp to 0-100
                return max(0, min(100, score))
            return 50  # Default to medium if can't parse
        except Exception:
            return 50
