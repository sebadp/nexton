"""
API Schemas - Request/Response models for API endpoints.
"""
from datetime import datetime
from typing import List, Optional

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

    status: Optional[str] = Field(None, max_length=50)
    notes: Optional[str] = None

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
    raw_message: str

    # Extracted data
    company: Optional[str] = None
    role: Optional[str] = None
    seniority: Optional[str] = None
    tech_stack: List[str] = Field(default_factory=list)
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    currency: Optional[str] = None
    remote_policy: Optional[str] = None

    # Scoring
    tech_stack_score: Optional[int] = None
    salary_score: Optional[int] = None
    seniority_score: Optional[int] = None
    company_score: Optional[int] = None
    total_score: Optional[int] = None
    tier: Optional[str] = None

    # AI Response
    ai_response: Optional[str] = None

    # Metadata
    status: str
    processing_time_ms: Optional[int] = None
    created_at: datetime
    updated_at: datetime

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
                "status": "processed",
                "processing_time_ms": 1500,
                "created_at": "2024-01-16T10:00:00",
                "updated_at": "2024-01-16T10:00:00",
            }
        }


class OpportunityListResponse(BaseModel):
    """Schema for paginated opportunity list response."""

    items: List[OpportunityResponse]
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
    average_score: Optional[float] = None
    highest_score: Optional[int] = None
    lowest_score: Optional[int] = None

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
                "average_score": 52.5,
                "highest_score": 95,
                "lowest_score": 10,
            }
        }