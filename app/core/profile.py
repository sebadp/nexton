"""
User profile loader.

Loads user preferences and profile information from config/profile.yaml
"""

from pathlib import Path
from typing import Optional
import yaml

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class UserProfile:
    """User profile with preferences and information."""

    def __init__(self, data: dict):
        """Initialize profile from dict."""
        self.name: str = data.get("name", "")
        self.preferred_technologies: list[str] = data.get("preferred_technologies", [])
        self.years_of_experience: int = data.get("years_of_experience", 0)
        self.current_seniority: str = data.get("current_seniority", "Mid")
        self.minimum_salary_usd: int = data.get("minimum_salary_usd", 0)
        self.ideal_salary_usd: int = data.get("ideal_salary_usd", 0)
        self.preferred_remote_policy: str = data.get("preferred_remote_policy", "Remote")
        self.preferred_locations: list[str] = data.get("preferred_locations", [])
        self.preferred_company_size: str = data.get("preferred_company_size", "Mid-size")
        self.industry_preferences: list[str] = data.get("industry_preferences", [])
        self.open_to_relocation: bool = data.get("open_to_relocation", False)
        self.looking_for_change: bool = data.get("looking_for_change", True)
        self.notes: str = data.get("notes", "")

    @property
    def first_name(self) -> str:
        """Get first name."""
        if not self.name:
            return ""
        return self.name.split()[0]

    @property
    def name_variations(self) -> list[str]:
        """
        Get variations of the user's name for signature detection.

        Returns list of name variations to check, including:
        - Full name
        - First name
        - First name without accents
        - Lowercase variations
        """
        variations = []

        if not self.name:
            return variations

        # Add full name
        variations.append(self.name.strip())

        # Add first name
        first_name = self.first_name
        if first_name:
            variations.append(first_name)

            # Add version without accents (e.g., Sebastián -> Sebastian)
            # Simple accent removal for common Spanish characters
            accent_map = {
                'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
                'Á': 'A', 'É': 'E', 'Í': 'I', 'Ó': 'O', 'Ú': 'U',
                'ñ': 'n', 'Ñ': 'N'
            }
            first_name_no_accent = first_name
            for accented, plain in accent_map.items():
                first_name_no_accent = first_name_no_accent.replace(accented, plain)

            if first_name_no_accent != first_name:
                variations.append(first_name_no_accent)

        # Add lowercase versions
        lowercase_variations = [v.lower() for v in variations]
        variations.extend(lowercase_variations)

        # Remove duplicates while preserving order
        seen = set()
        unique_variations = []
        for v in variations:
            if v and v not in seen:
                seen.add(v)
                unique_variations.append(v)

        return unique_variations


def load_user_profile(profile_path: Optional[str] = None) -> UserProfile:
    """
    Load user profile from YAML file.

    Args:
        profile_path: Path to profile YAML file. Uses settings.PROFILE_PATH if None.

    Returns:
        UserProfile instance

    Raises:
        FileNotFoundError: If profile file doesn't exist
        ValueError: If profile file is invalid
    """
    path = Path(profile_path or settings.PROFILE_PATH)

    if not path.exists():
        logger.error("profile_file_not_found", path=str(path))
        raise FileNotFoundError(f"Profile file not found: {path}")

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if not data:
            raise ValueError("Profile file is empty")

        profile = UserProfile(data)
        logger.info(
            "profile_loaded",
            name=profile.name,
            seniority=profile.current_seniority,
            experience_years=profile.years_of_experience,
        )

        return profile

    except yaml.YAMLError as e:
        logger.error("profile_yaml_error", error=str(e), path=str(path))
        raise ValueError(f"Invalid YAML in profile file: {e}") from e

    except Exception as e:
        logger.error("profile_load_error", error=str(e), path=str(path))
        raise


# Global profile instance (loaded on first access)
_profile: Optional[UserProfile] = None


def get_user_profile() -> UserProfile:
    """
    Get the user profile (singleton pattern).

    Returns:
        UserProfile instance

    Raises:
        FileNotFoundError: If profile file doesn't exist
        ValueError: If profile file is invalid
    """
    global _profile

    if _profile is None:
        _profile = load_user_profile()

    return _profile
