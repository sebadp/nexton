"""
API Schemas - Request/Response models for API endpoints.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator

# ============================================================================
# Request Schemas
# ============================================================================


class OpportunityCreate(BaseModel):
    """Schema for creating a new opportunity."""

    recruiter_name: str = Field(..., min_length=1, max_length=255)
    raw_message: str = Field(..., min_length=10, description="Raw recruiter message")

    @field_validator("recruiter_name")
    @classmethod
    def validate_recruiter_name(cls, v: str) -> str:
        """Validate and clean recruiter name."""
        return v.strip()

    @field_validator("raw_message")
    @classmethod
    def validate_raw_message(cls, v: str) -> str:
        """Validate and normalize raw message (preserve newlines and formatting)."""
        # Strip leading/trailing whitespace but preserve internal formatting
        return v.strip()

    class Config:
        json_schema_extra = {
            "example": {
                "recruiter_name": "María González",
                "raw_message": "Hola! Tenemos una posición de Senior Python Engineer en una startup de IA.\\n\\nRequisitos:\\n- 5+ años Python\\n- FastAPI/Django\\n- PostgreSQL\\n\\nSalario: $80k-$120k USD\\nRemoto 100%",
            }
        }


class OpportunityUpdate(BaseModel):
    """Schema for updating an opportunity."""

    status: str | None = Field(None, max_length=50)
    notes: str | None = None

    class Config:
        json_schema_extra = {
            "example": {
                "status": "contacted",
                "notes": "Scheduled interview for next week",
            }
        }


# ============================================================================
# Response Schemas
# ============================================================================


class OpportunityResponse(BaseModel):
    """Schema for opportunity response."""

    # Identifiers
    id: int
    recruiter_name: str
    raw_message: str | None = None

    # Extracted data
    company: str | None = None
    role: str | None = None
    seniority: str | None = None
    tech_stack: list[str] = Field(default_factory=list)
    salary_min: int | None = None
    salary_max: int | None = None
    currency: str | None = None
    remote_policy: str | None = None

    # Scoring
    tech_stack_score: int | None = None
    salary_score: int | None = None
    seniority_score: int | None = None
    company_score: int | None = None
    total_score: int | None = None
    tier: str | None = None

    # AI Response
    ai_response: str | None = None

    # Conversation Classification (NEW)
    conversation_state: str | None = Field(
        None,
        description="Conversation state: NEW_OPPORTUNITY, FOLLOW_UP, COURTESY_CLOSE",
    )
    processing_status: str | None = Field(
        None,
        description="Processing status: processed, ignored, declined, manual_review, auto_responded",
    )

    # Manual Review (NEW)
    requires_manual_review: bool = Field(
        False,
        description="Whether this opportunity needs manual human review",
    )
    manual_review_reason: str | None = Field(
        None,
        description="Reason why manual review is required",
    )

    # Detailed Results (NEW - JSON)
    hard_filter_results: dict[str, Any] | None = Field(
        None,
        description="Results from hard filter checks (work_week, salary, tech_match, etc.)",
    )
    follow_up_analysis: dict[str, Any] | None = Field(
        None,
        description="Analysis for follow-up messages (question_type, can_auto_respond, etc.)",
    )

    # Metadata
    status: str
    processing_time_ms: int | None = None
    created_at: datetime
    updated_at: datetime
    message_timestamp: datetime | None = Field(
        None,
        description="Original timestamp from LinkedIn message",
    )

    @field_validator("message_timestamp")
    @classmethod
    def validate_message_timestamp(cls, v: datetime | None) -> datetime | None:
        """Ensure message_timestamp is not a future date."""
        if v is not None and v > datetime.now():
            # If somehow a future date slipped through, cap it to now
            return datetime.now()
        return v

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "recruiter_name": "María González",
                "raw_message": "Hola! Tenemos una posición...",
                "company": "TechCorp",
                "role": "Senior Python Engineer",
                "seniority": "Senior",
                "tech_stack": ["Python", "FastAPI", "PostgreSQL"],
                "salary_min": 100000,
                "salary_max": 120000,
                "currency": "USD",
                "remote_policy": "Remote",
                "tech_stack_score": 35,
                "salary_score": 25,
                "seniority_score": 18,
                "company_score": 8,
                "total_score": 86,
                "tier": "HIGH_PRIORITY",
                "ai_response": "Hola María, muchas gracias por contactarme...",
                "conversation_state": "NEW_OPPORTUNITY",
                "processing_status": "processed",
                "requires_manual_review": False,
                "manual_review_reason": None,
                "hard_filter_results": {
                    "passed": True,
                    "failed_filters": [],
                    "work_week_status": "NOT_MENTIONED",
                },
                "follow_up_analysis": None,
                "status": "processed",
                "processing_time_ms": 1500,
                "created_at": "2024-01-16T10:00:00",
                "updated_at": "2024-01-16T10:00:00",
                "message_timestamp": "2024-01-15T15:30:00",
            }
        }


class OpportunityListResponse(BaseModel):
    """Schema for paginated opportunity list response."""

    items: list[OpportunityResponse]
    total: int
    skip: int
    limit: int
    has_more: bool

    class Config:
        json_schema_extra = {
            "example": {
                "items": [
                    {
                        "id": 1,
                        "recruiter_name": "María González",
                        "company": "TechCorp",
                        "role": "Senior Python Engineer",
                        "total_score": 86,
                        "tier": "HIGH_PRIORITY",
                        "status": "processed",
                        "created_at": "2024-01-16T10:00:00",
                        "updated_at": "2024-01-16T10:00:00",
                    }
                ],
                "total": 100,
                "skip": 0,
                "limit": 10,
                "has_more": True,
            }
        }


class OpportunityStats(BaseModel):
    """Schema for opportunity statistics."""

    total_count: int
    by_tier: dict
    by_status: dict

    # New classification stats
    by_conversation_state: dict | None = Field(
        None,
        description="Count by conversation state: NEW_OPPORTUNITY, FOLLOW_UP, COURTESY_CLOSE",
    )
    by_processing_status: dict | None = Field(
        None,
        description="Count by processing status: processed, ignored, declined, manual_review, auto_responded",
    )
    pending_manual_review: int = Field(
        0,
        description="Count of opportunities requiring manual review",
    )

    # Score metrics
    average_score: float | None = None
    highest_score: int | None = None
    lowest_score: int | None = None

    class Config:
        json_schema_extra = {
            "example": {
                "total_count": 100,
                "by_tier": {
                    "HIGH_PRIORITY": 15,
                    "INTERESANTE": 35,
                    "POCO_INTERESANTE": 30,
                    "NO_INTERESA": 20,
                },
                "by_status": {
                    "processed": 95,
                    "processing": 3,
                    "failed": 2,
                },
                "by_conversation_state": {
                    "NEW_OPPORTUNITY": 80,
                    "FOLLOW_UP": 15,
                    "COURTESY_CLOSE": 5,
                },
                "by_processing_status": {
                    "processed": 70,
                    "declined": 10,
                    "manual_review": 8,
                    "auto_responded": 7,
                    "ignored": 5,
                },
                "pending_manual_review": 8,
                "average_score": 52.5,
                "highest_score": 95,
                "lowest_score": 10,
            }
        }
