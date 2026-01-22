"""
Settings API endpoints for managing application configuration.
"""
import os
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.config import settings

router = APIRouter(prefix="/settings", tags=["settings"])


class SettingsResponse(BaseModel):
    """Public settings response (sensitive data masked)."""
    app_name: str
    app_version: str
    env: str
    log_level: str
    llm_provider: str
    llm_model: str
    llm_temperature: float
    linkedin_email: str
    linkedin_password_set: bool
    smtp_host: str
    smtp_port: int
    profile_path: str
    notification_enabled: bool
    notification_email: str


class UpdateSettingsRequest(BaseModel):
    """Request to update settings."""
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None
    llm_temperature: Optional[float] = None
    linkedin_email: Optional[str] = None
    linkedin_password: Optional[str] = None
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    notification_enabled: Optional[bool] = None
    notification_email: Optional[str] = None


@router.get("", response_model=SettingsResponse)
async def get_settings() -> SettingsResponse:
    """Get current application settings (sensitive data masked)."""
    return SettingsResponse(
        app_name=settings.APP_NAME,
        app_version=settings.APP_VERSION,
        env=settings.ENV,
        log_level=settings.LOG_LEVEL,
        llm_provider=settings.LLM_PROVIDER,
        llm_model=settings.LLM_MODEL,
        llm_temperature=settings.LLM_TEMPERATURE,
        linkedin_email=settings.LINKEDIN_EMAIL,
        linkedin_password_set=bool(settings.LINKEDIN_PASSWORD),
        smtp_host=settings.SMTP_HOST,
        smtp_port=settings.SMTP_PORT,
        profile_path=settings.PROFILE_PATH,
        notification_enabled=settings.NOTIFICATION_ENABLED,
        notification_email=settings.NOTIFICATION_EMAIL,
    )


@router.patch("", response_model=SettingsResponse)
async def update_settings(request: UpdateSettingsRequest) -> SettingsResponse:
    """
    Update application settings at runtime.

    Note: These changes are stored in environment variables and will be
    lost on restart. For persistent changes, update the .env file.
    """
    try:
        # Update settings in memory and environment
        if request.llm_provider is not None:
            os.environ["LLM_PROVIDER"] = request.llm_provider
            settings.LLM_PROVIDER = request.llm_provider

        if request.llm_model is not None:
            os.environ["LLM_MODEL"] = request.llm_model
            settings.LLM_MODEL = request.llm_model

        if request.llm_temperature is not None:
            os.environ["LLM_TEMPERATURE"] = str(request.llm_temperature)
            settings.LLM_TEMPERATURE = request.llm_temperature

        if request.linkedin_email is not None:
            os.environ["LINKEDIN_EMAIL"] = request.linkedin_email
            settings.LINKEDIN_EMAIL = request.linkedin_email

        if request.linkedin_password is not None:
            os.environ["LINKEDIN_PASSWORD"] = request.linkedin_password
            settings.LINKEDIN_PASSWORD = request.linkedin_password

        if request.smtp_host is not None:
            os.environ["SMTP_HOST"] = request.smtp_host
            settings.SMTP_HOST = request.smtp_host

        if request.smtp_port is not None:
            os.environ["SMTP_PORT"] = str(request.smtp_port)
            settings.SMTP_PORT = request.smtp_port

        if request.notification_enabled is not None:
            os.environ["NOTIFICATION_ENABLED"] = str(request.notification_enabled).lower()
            settings.NOTIFICATION_ENABLED = request.notification_enabled

        if request.notification_email is not None:
            os.environ["NOTIFICATION_EMAIL"] = request.notification_email
            settings.NOTIFICATION_EMAIL = request.notification_email

        return await get_settings()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update settings: {str(e)}")
