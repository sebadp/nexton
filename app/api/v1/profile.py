"""
Profile API endpoints for managing user profile (profile.yaml).
"""
from pathlib import Path
from typing import Any

import yaml
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core.config import settings

router = APIRouter(prefix="/profile", tags=["profile"])


class JobSearchStatus(BaseModel):
    """Job search status configuration."""
    currently_employed: bool = True
    actively_looking: bool = True
    urgency: str = "selective"
    situation: str = ""
    must_have: list[str] = Field(default_factory=list)
    nice_to_have: list[str] = Field(default_factory=list)
    reject_if: list[str] = Field(default_factory=list)


class ProfileSchema(BaseModel):
    """User profile schema."""
    name: str = ""
    preferred_technologies: list[str] = Field(default_factory=list)
    years_of_experience: int = 0
    current_seniority: str = "Senior"
    minimum_salary_usd: int = 0
    ideal_salary_usd: int = 0
    preferred_remote_policy: str = "Remote"
    preferred_work_week: str = "5-days"
    preferred_locations: list[str] = Field(default_factory=list)
    preferred_company_size: str = "Mid-size"
    industry_preferences: list[str] = Field(default_factory=list)
    open_to_relocation: bool = False
    looking_for_change: bool = True
    job_search_status: JobSearchStatus = Field(default_factory=JobSearchStatus)


def _get_profile_path() -> Path:
    """Get the profile file path."""
    return Path(settings.PROFILE_PATH)


def _load_profile() -> dict[str, Any]:
    """Load profile from YAML file."""
    profile_path = _get_profile_path()
    if not profile_path.exists():
        return {}

    with open(profile_path, "r") as f:
        return yaml.safe_load(f) or {}


def _save_profile(data: dict[str, Any]) -> None:
    """Save profile to YAML file."""
    profile_path = _get_profile_path()
    profile_path.parent.mkdir(parents=True, exist_ok=True)

    with open(profile_path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)


@router.get("", response_model=ProfileSchema)
async def get_profile() -> ProfileSchema:
    """Get the current user profile."""
    try:
        data = _load_profile()
        return ProfileSchema(**data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load profile: {str(e)}")


@router.put("", response_model=ProfileSchema)
async def update_profile(profile: ProfileSchema) -> ProfileSchema:
    """Update the user profile."""
    try:
        data = profile.model_dump()
        _save_profile(data)
        return profile
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save profile: {str(e)}")
