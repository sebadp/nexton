"""
MessageAnalyzer - DSPy module to extract structured data from recruiter messages.

Uses LLM to parse unstructured text and extract key job information.
"""
import re
from typing import Optional

import dspy

from app.core.logging import get_logger
from app.dspy_modules.models import ExtractedData
from app.dspy_modules.signatures import MessageAnalysisSignature

logger = get_logger(__name__)


class MessageAnalyzer(dspy.Module):
    """
    Analyzes LinkedIn recruiter messages and extracts structured information.

    Uses DSPy's ChainOfThought to ensure LLM thinks through the extraction
    process step by step.
    """

    def __init__(self):
        """Initialize the message analyzer."""
        super().__init__()
        self.analyze = dspy.ChainOfThought(MessageAnalysisSignature)

    def forward(self, message: str) -> ExtractedData:
        """
        Analyze message and extract structured data.

        Args:
            message: Raw recruiter message

        Returns:
            ExtractedData: Extracted and validated data

        Example:
            analyzer = MessageAnalyzer()
            result = analyzer(message="Hola! Tenemos una posición...")
        """
        logger.debug("message_analyzer_start", message_length=len(message))

        try:
            # Call LLM with signature
            prediction = self.analyze(message=message)

            # Extract salary info
            salary_min, salary_max, currency = self._parse_salary(
                prediction.salary_range
            )

            # Parse tech stack
            tech_stack = self._parse_tech_stack(prediction.tech_stack)

            # Create structured result
            extracted = ExtractedData(
                company=prediction.company or "Unknown",
                role=prediction.role or "Unknown Role",
                seniority=self._normalize_seniority(prediction.seniority),
                tech_stack=tech_stack,
                salary_min=salary_min,
                salary_max=salary_max,
                currency=currency,
                remote_policy=self._normalize_remote_policy(prediction.remote_policy),
                location=prediction.location or "Not specified",
            )

            logger.info(
                "message_analyzer_success",
                company=extracted.company,
                role=extracted.role,
                tech_count=len(extracted.tech_stack),
            )

            return extracted

        except Exception as e:
            logger.error("message_analyzer_failed", error=str(e))
            # Return minimal valid data
            return ExtractedData(
                company="Unknown",
                role="Unknown Role",
                seniority="Unknown",
                tech_stack=[],
            )

    def _parse_salary(self, salary_str: str) -> tuple[Optional[int], Optional[int], str]:
        """
        Parse salary range from string.

        Args:
            salary_str: Salary string (e.g., "100000-150000 USD")

        Returns:
            tuple: (min_salary, max_salary, currency)

        Examples:
            "100000-150000 USD" -> (100000, 150000, "USD")
            "5000 USD/month" -> (5000, None, "USD")
            "Not mentioned" -> (None, None, "USD")
        """
        if not salary_str or "not mentioned" in salary_str.lower():
            return None, None, "USD"

        # Try to extract currency
        currency = "USD"
        if "EUR" in salary_str.upper():
            currency = "EUR"
        elif "ARS" in salary_str.upper() or "PESOS" in salary_str.upper():
            currency = "ARS"

        # Extract numbers (handles ranges like "100000-150000" or single values)
        numbers = re.findall(r'\d+', salary_str.replace(',', '').replace('.', ''))

        if len(numbers) >= 2:
            # Range found
            return int(numbers[0]), int(numbers[1]), currency
        elif len(numbers) == 1:
            # Single value
            salary = int(numbers[0])
            return salary, None, currency

        return None, None, currency

    def _parse_tech_stack(self, tech_stack_str: str) -> list[str]:
        """
        Parse tech stack from comma-separated string.

        Args:
            tech_stack_str: Technologies string

        Returns:
            list: List of technology names

        Examples:
            "Python, FastAPI, PostgreSQL" -> ["Python", "FastAPI", "PostgreSQL"]
            "Python,FastAPI,PostgreSQL" -> ["Python", "FastAPI", "PostgreSQL"]
        """
        if not tech_stack_str:
            return []

        # Split by comma and clean
        technologies = [
            tech.strip()
            for tech in tech_stack_str.split(",")
            if tech.strip()
        ]

        return technologies

    def _normalize_seniority(self, seniority: str) -> str:
        """
        Normalize seniority level to standard values.

        Args:
            seniority: Raw seniority string

        Returns:
            str: Normalized seniority
        """
        if not seniority:
            return "Unknown"

        seniority_lower = seniority.lower()

        if any(word in seniority_lower for word in ["junior", "jr", "trainee"]):
            return "Junior"
        elif any(word in seniority_lower for word in ["senior", "sr"]):
            return "Senior"
        elif any(word in seniority_lower for word in ["staff", "lead"]):
            return "Staff"
        elif any(word in seniority_lower for word in ["principal", "architect"]):
            return "Principal"
        elif any(word in seniority_lower for word in ["mid", "semi"]):
            return "Mid"
        else:
            return "Unknown"

    def _normalize_remote_policy(self, remote_policy: str) -> str:
        """
        Normalize remote work policy to standard values.

        Args:
            remote_policy: Raw remote policy string

        Returns:
            str: Normalized remote policy
        """
        if not remote_policy:
            return "Unknown"

        policy_lower = remote_policy.lower()

        if any(word in policy_lower for word in ["remote", "remoto", "100%"]):
            return "Remote"
        elif any(word in policy_lower for word in ["hybrid", "híbrido", "mixto"]):
            return "Hybrid"
        elif any(word in policy_lower for word in ["onsite", "presencial", "office"]):
            return "Onsite"
        else:
            return "Unknown"