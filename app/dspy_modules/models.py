"""
Pydantic models for DSPy pipeline data structures.

These models provide type safety and validation for data
flowing through the pipeline.
"""

from enum import Enum

from pydantic import BaseModel, Field, field_validator


class ConversationState(str, Enum):
    """Classification of the conversation/message state."""

    NEW_OPPORTUNITY = "NEW_OPPORTUNITY"  # Recruiter presenting a new job
    FOLLOW_UP = "FOLLOW_UP"  # Recruiter responding to candidate's previous message
    COURTESY_CLOSE = "COURTESY_CLOSE"  # Simple acknowledgment (Gracias, Ok, etc.)


class ProcessingStatus(str, Enum):
    """Final processing status for an opportunity."""

    PROCESSED = "processed"  # Normal processing, response generated
    IGNORED = "ignored"  # Courtesy message, no response needed
    DECLINED = "declined"  # Failed hard filters, polite decline generated
    MANUAL_REVIEW_REQUIRED = "manual_review"  # Follow-up needs human review
    AUTO_RESPONDED = "auto_responded"  # Follow-up with answerable question


class CandidateStatus(str, Enum):
    """Job search status of the candidate."""

    ACTIVE_SEARCH = "ACTIVE_SEARCH"  # Actively looking for opportunities
    PASSIVE = "PASSIVE"  # Not actively looking, but open to exceptional offers
    SELECTIVE = "SELECTIVE"  # Very selective, specific requirements
    NOT_LOOKING = "NOT_LOOKING"  # Not interested in new opportunities


class ConversationStateResult(BaseModel):
    """Result of conversation state analysis."""

    state: ConversationState = Field(description="The classified conversation state")
    confidence: str = Field(
        description="Confidence level: HIGH, MEDIUM, LOW",
        default="MEDIUM",
    )
    reasoning: str = Field(
        description="Why this classification was chosen",
        default="",
    )
    contains_job_details: bool = Field(
        description="Whether the message contains actual job information",
        default=False,
    )
    should_process: bool = Field(
        description="Whether the pipeline should continue processing",
        default=True,
    )

    @classmethod
    def courtesy_close(
        cls, reasoning: str = "Message is a simple courtesy/acknowledgment"
    ) -> "ConversationStateResult":
        """Factory for COURTESY_CLOSE state."""
        return cls(
            state=ConversationState.COURTESY_CLOSE,
            confidence="HIGH",
            reasoning=reasoning,
            contains_job_details=False,
            should_process=False,
        )


class HardFilterResult(BaseModel):
    """Result of hard filter validation."""

    passed: bool = Field(description="Whether all hard filters passed")
    failed_filters: list[str] = Field(
        description="List of filters that failed",
        default_factory=list,
    )
    score_penalty: int = Field(
        description="Score penalty to apply (0-100)",
        default=0,
        ge=0,
        le=100,
    )
    should_decline: bool = Field(
        description="Whether the response should be a polite decline",
        default=False,
    )
    work_week_status: str = Field(
        description="4-day work week status: CONFIRMED, NOT_MENTIONED, FIVE_DAY, UNKNOWN",
        default="UNKNOWN",
    )

    @classmethod
    def all_passed(cls) -> "HardFilterResult":
        """Factory for when all filters pass."""
        return cls(
            passed=True,
            failed_filters=[],
            score_penalty=0,
            should_decline=False,
        )

    @classmethod
    def skipped(cls) -> "HardFilterResult":
        """Factory for when hard filters are skipped (e.g., for FOLLOW_UP)."""
        return cls(
            passed=True,
            failed_filters=[],
            score_penalty=0,
            should_decline=False,
            work_week_status="SKIPPED",
        )


class FollowUpAnalysisResult(BaseModel):
    """Result of analyzing a FOLLOW_UP message for auto-response capability."""

    can_auto_respond: bool = Field(
        description="Whether the system can safely auto-respond to this follow-up",
        default=False,
    )
    question_type: str | None = Field(
        description="Type of question detected: SALARY, AVAILABILITY, TECH_STACK, EXPERIENCE, INTEREST, NONE, OTHER",
        default=None,
    )
    detected_question: str | None = Field(
        description="The specific question detected in the message",
        default=None,
    )
    suggested_response: str | None = Field(
        description="If auto-respond is possible, the suggested response based on profile",
        default=None,
    )
    reasoning: str = Field(
        description="Why this decision was made",
        default="",
    )
    requires_context: bool = Field(
        description="Whether answering requires previous conversation context we don't have",
        default=True,
    )

    @classmethod
    def manual_review(
        cls, reasoning: str = "Follow-up requires manual review"
    ) -> "FollowUpAnalysisResult":
        """Factory for when manual review is needed."""
        return cls(
            can_auto_respond=False,
            question_type="NONE",
            requires_context=True,
            reasoning=reasoning,
        )


class ExtractedData(BaseModel):
    """Data extracted from recruiter message by MessageAnalyzer."""

    company: str = Field(description="Company name")
    role: str = Field(description="Job role/title")
    seniority: str = Field(
        description="Seniority level",
        default="Unknown",
    )
    tech_stack: list[str] = Field(
        description="List of technologies",
        default_factory=list,
    )
    salary_min: int | None = Field(
        description="Minimum salary in USD",
        default=None,
    )
    salary_max: int | None = Field(
        description="Maximum salary in USD",
        default=None,
    )
    currency: str = Field(
        description="Currency code",
        default="USD",
    )
    remote_policy: str = Field(
        description="Remote work policy",
        default="Unknown",
    )
    location: str = Field(
        description="Job location",
        default="Not specified",
    )
    job_type: str = Field(
        description="Job type: Full-time, Part-time, Contract, etc.",
        default="Full-time",
    )
    work_week: str = Field(
        description="Work week mentioned: 4-days, 5-days, flexible, or Unknown",
        default="Unknown",
    )

    @field_validator("tech_stack", mode="before")
    @classmethod
    def parse_tech_stack(cls, v):
        """Parse tech stack from comma-separated string or list."""
        if isinstance(v, str):
            # Split by comma and clean
            return [tech.strip() for tech in v.split(",") if tech.strip()]
        return v or []


class ScoringResult(BaseModel):
    """Scoring results from Scorer module."""

    tech_stack_score: int = Field(
        ge=0,
        le=40,
        description="Tech stack match score (0-40)",
    )
    tech_stack_reasoning: str = Field(
        description="Explanation of tech stack score",
    )

    salary_score: int = Field(
        ge=0,
        le=30,
        description="Salary adequacy score (0-30)",
    )
    salary_reasoning: str = Field(
        description="Explanation of salary score",
    )

    seniority_score: int = Field(
        ge=0,
        le=20,
        description="Seniority match score (0-20)",
    )
    seniority_reasoning: str = Field(
        description="Explanation of seniority score",
    )

    company_score: int = Field(
        ge=0,
        le=10,
        description="Company attractiveness score (0-10)",
    )
    company_reasoning: str = Field(
        description="Explanation of company score",
    )

    @property
    def total_score(self) -> int:
        """Calculate total score (0-100)."""
        return self.tech_stack_score + self.salary_score + self.seniority_score + self.company_score

    @property
    def tier(self) -> str:
        """Determine tier based on total score."""
        score = self.total_score
        if score >= 75:
            return "HIGH_PRIORITY"
        elif score >= 50:
            return "INTERESANTE"
        elif score >= 30:
            return "POCO_INTERESANTE"
        else:
            return "NO_INTERESA"


class CandidateProfile(BaseModel):
    """Candidate profile with preferences and requirements."""

    name: str = Field(description="Candidate's name")

    # Skills and experience
    preferred_technologies: list[str] = Field(
        description="Technologies the candidate prefers to work with",
        default_factory=list,
    )
    years_of_experience: int = Field(
        description="Total years of professional experience",
        ge=0,
    )
    current_seniority: str = Field(
        description="Current seniority level",
    )

    # Compensation expectations
    minimum_salary_usd: int = Field(
        description="Minimum acceptable salary in USD",
        ge=0,
    )
    ideal_salary_usd: int | None = Field(
        description="Ideal salary in USD",
        default=None,
    )

    # Work preferences
    preferred_remote_policy: str = Field(
        description="Preferred work arrangement: Remote, Hybrid, or Flexible",
        default="Remote",
    )
    preferred_work_week: str = Field(
        description="Preferred work week: 4-days, 5-days, or flexible",
        default="5-days",
    )
    preferred_locations: list[str] = Field(
        description="Preferred work locations",
        default_factory=list,
    )

    # Company preferences
    preferred_company_size: str | None = Field(
        description="Preferred company size: Startup, Mid-size, Enterprise",
        default=None,
    )
    industry_preferences: list[str] = Field(
        description="Preferred industries",
        default_factory=list,
    )

    # Additional context
    open_to_relocation: bool = Field(
        description="Whether open to relocating",
        default=False,
    )
    looking_for_change: bool = Field(
        description="Whether actively looking for new opportunities",
        default=True,
    )
    notes: str | None = Field(
        description="Additional notes or context",
        default=None,
    )


class OpportunityResult(BaseModel):
    """Complete result from pipeline execution."""

    # Input data
    recruiter_name: str
    raw_message: str

    # Conversation state analysis
    conversation_state: ConversationStateResult | None = Field(
        description="Result of conversation state analysis",
        default=None,
    )

    # Follow-up analysis (only populated for FOLLOW_UP state)
    follow_up_analysis: FollowUpAnalysisResult | None = Field(
        description="Analysis of follow-up message for auto-response capability",
        default=None,
    )

    # Extracted data
    extracted: ExtractedData

    # Hard filter validation
    hard_filter_result: HardFilterResult | None = Field(
        description="Result of hard filter validation",
        default=None,
    )

    # Scoring results
    scoring: ScoringResult

    # Generated response
    ai_response: str

    # Metadata
    processing_time_ms: int | None = None
    status: str = "processed"  # processed, ignored, declined, manual_review, auto_responded
    requires_manual_review: bool = Field(
        description="Whether this message needs manual human review",
        default=False,
    )
    manual_review_reason: str | None = Field(
        description="Reason why manual review is required",
        default=None,
    )
    error_message: str | None = None

    def to_db_dict(self) -> dict:
        """
        Convert to dictionary format for database storage.

        Returns:
            dict: Data ready for Opportunity model
        """
        # Build hard filter results dict if available
        hard_filter_results = None
        if self.hard_filter_result:
            hard_filter_results = {
                "passed": self.hard_filter_result.passed,
                "failed_filters": self.hard_filter_result.failed_filters,
                "score_penalty": self.hard_filter_result.score_penalty,
                "should_decline": self.hard_filter_result.should_decline,
                "work_week_status": self.hard_filter_result.work_week_status,
            }

        # Build follow-up analysis dict if available
        follow_up_analysis = None
        if self.follow_up_analysis:
            follow_up_analysis = {
                "can_auto_respond": self.follow_up_analysis.can_auto_respond,
                "question_type": self.follow_up_analysis.question_type,
                "detected_question": self.follow_up_analysis.detected_question,
                "suggested_response": self.follow_up_analysis.suggested_response,
                "reasoning": self.follow_up_analysis.reasoning,
                "requires_context": self.follow_up_analysis.requires_context,
            }

        return {
            "recruiter_name": self.recruiter_name,
            "raw_message": self.raw_message,
            # Extracted data
            "company": self.extracted.company,
            "role": self.extracted.role,
            "seniority": self.extracted.seniority,
            "tech_stack": self.extracted.tech_stack,
            "salary_min": self.extracted.salary_min,
            "salary_max": self.extracted.salary_max,
            "currency": self.extracted.currency,
            "remote_policy": self.extracted.remote_policy,
            "location": self.extracted.location,
            # Scoring
            "total_score": self.scoring.total_score,
            "tech_stack_score": self.scoring.tech_stack_score,
            "salary_score": self.scoring.salary_score,
            "seniority_score": self.scoring.seniority_score,
            "company_score": self.scoring.company_score,
            "tier": self.scoring.tier,
            # Response
            "ai_response": self.ai_response,
            # Conversation classification
            "conversation_state": (
                self.conversation_state.state.value if self.conversation_state else None
            ),
            "processing_status": self.status,
            # Manual review
            "requires_manual_review": self.requires_manual_review,
            "manual_review_reason": self.manual_review_reason,
            # Filter and analysis results (JSON)
            "hard_filter_results": hard_filter_results,
            "follow_up_analysis": follow_up_analysis,
            # Metadata
            "status": self.status,
            "processing_time_ms": self.processing_time_ms,
            "error_message": self.error_message,
        }
