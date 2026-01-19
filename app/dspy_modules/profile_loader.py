"""
Profile loader - Load candidate profile from YAML configuration.
"""
from pathlib import Path
from typing import Optional

import yaml

from app.core.config import settings
from app.core.exceptions import ConfigurationError
from app.core.logging import get_logger
from app.dspy_modules.models import CandidateProfile

logger = get_logger(__name__)


def load_profile(profile_path: Optional[str] = None) -> CandidateProfile:
    """
    Load candidate profile from YAML file.

    Args:
        profile_path: Path to profile YAML file (default from settings)

    Returns:
        CandidateProfile: Loaded and validated profile

    Raises:
        ConfigurationError: If profile cannot be loaded

    Example:
        profile = load_profile()
        profile = load_profile("config/custom_profile.yaml")
    """
    path = profile_path or settings.PROFILE_PATH

    logger.info("loading_profile", path=path)

    try:
        profile_file = Path(path)

        if not profile_file.exists():
            raise ConfigurationError(
                message=f"Profile file not found: {path}",
                details={"path": path},
            )

        # Load YAML
        with open(profile_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        # Validate and create profile
        profile = CandidateProfile(**data)

        logger.info(
            "profile_loaded_successfully",
            name=profile.name,
            technologies_count=len(profile.preferred_technologies),
            min_salary=profile.minimum_salary_usd,
        )

        return profile

    except yaml.YAMLError as e:
        logger.error("profile_yaml_parse_error", error=str(e))
        raise ConfigurationError(
            message="Failed to parse profile YAML",
            details={"error": str(e), "path": path},
        ) from e

    except Exception as e:
        logger.error("profile_load_error", error=str(e))
        raise ConfigurationError(
            message="Failed to load profile",
            details={"error": str(e), "path": path},
        ) from e


# Cached profile instance
_cached_profile: Optional[CandidateProfile] = None


def get_profile(reload: bool = False) -> CandidateProfile:
    """
    Get candidate profile (cached).

    Args:
        reload: Force reload from file

    Returns:
        CandidateProfile: Profile instance
    """
    global _cached_profile

    if _cached_profile is None or reload:
        _cached_profile = load_profile()

    return _cached_profile