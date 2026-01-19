"""
Pydantic models for DSPy pipeline data structures.

These models provide type safety and validation for data
flowing through the pipeline.
"""
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class ExtractedData(BaseModel):
    """Data extracted from recruiter message by MessageAnalyzer."""

    company: str = Field(description="Company name")
    role: str = Field(description="Job role/title")
    seniority: str = Field(
        description="Seniority level",
        default="Unknown",
    )
    tech_stack: List[str] = Field(
        description="List of technologies",
        default_factory=list,
    )
    salary_min: Optional[int] = Field(
        description="Minimum salary in USD",
        default=None,
    )
    salary_max: Optional[int] = Field(
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
        return (
            self.tech_stack_score
            + self.salary_score
            + self.seniority_score
            + self.company_score
        )

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
    preferred_technologies: List[str] = Field(
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
    ideal_salary_usd: Optional[int] = Field(
        description="Ideal salary in USD",
        default=None,
    )

    # Work preferences
    preferred_remote_policy: str = Field(
        description="Preferred work arrangement: Remote, Hybrid, or Flexible",
        default="Remote",
    )
    preferred_locations: List[str] = Field(
        description="Preferred work locations",
        default_factory=list,
    )

    # Company preferences
    preferred_company_size: Optional[str] = Field(
        description="Preferred company size: Startup, Mid-size, Enterprise",
        default=None,
    )
    industry_preferences: List[str] = Field(
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
    notes: Optional[str] = Field(
        description="Additional notes or context",
        default=None,
    )


class OpportunityResult(BaseModel):
    """Complete result from pipeline execution."""

    # Input data
    recruiter_name: str
    raw_message: str

    # Extracted data
    extracted: ExtractedData

    # Scoring results
    scoring: ScoringResult

    # Generated response
    ai_response: str

    # Metadata
    processing_time_ms: Optional[int] = None
    status: str = "processed"
    error_message: Optional[str] = None

    def to_db_dict(self) -> dict:
        """
        Convert to dictionary format for database storage.

        Returns:
            dict: Data ready for Opportunity model
        """
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
            # Metadata
            "status": self.status,
            "processing_time_ms": self.processing_time_ms,
            "error_message": self.error_message,
        }