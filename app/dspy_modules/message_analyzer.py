"""
MessageAnalyzer - DSPy module to extract structured data from recruiter messages.

Uses LLM to parse unstructured text and extract key job information.
"""

import re

import dspy

from app.core.logging import get_logger
from app.dspy_modules.models import (
    ConversationState,
    ConversationStateResult,
    ExtractedData,
    FollowUpAnalysisResult,
)
from app.dspy_modules.signatures import (
    ConversationStateSignature,
    FollowUpAnalysisSignature,
    MessageAnalysisSignature,
)
from app.observability import observe

logger = get_logger(__name__)


# Common courtesy/closing phrases that indicate no response needed
COURTESY_PHRASES = {
    # Spanish
    "gracias",
    "muchas gracias",
    "ok",
    "dale",
    "perfecto",
    "excelente",
    "genial",
    "quedamos así",
    "quedamos en contacto",
    "suerte",
    "éxitos",
    "buena suerte",
    "saludos",
    "un saludo",
    "hasta pronto",
    "nos vemos",
    "listo",
    "entendido",
    "de acuerdo",
    "vale",
    "bien",
    "bueno",
    "claro",
    "por supuesto",
    "ningún problema",
    "todo bien",
    # English
    "thanks",
    "thank you",
    "okay",
    "perfect",
    "great",
    "good luck",
    "sounds good",
    "got it",
    "understood",
    "noted",
    "will do",
}


class ConversationStateAnalyzer(dspy.Module):
    """
    Analyzes messages to determine conversation state.

    Uses both rule-based detection for obvious cases and LLM
    for more nuanced classification.
    """

    def __init__(self):
        """Initialize the conversation state analyzer."""
        super().__init__()
        self.analyze = dspy.ChainOfThought(ConversationStateSignature)

    @observe(name="dspy.conversation_state_analyzer.forward")
    def forward(self, message: str) -> ConversationStateResult:
        """
        Analyze message to determine conversation state.

        Args:
            message: Raw LinkedIn message

        Returns:
            ConversationStateResult: Classification result
        """
        logger.debug("conversation_state_analyzer_start", message_length=len(message))

        # Step 1: Quick rule-based check for obvious courtesy messages
        quick_result = self._quick_courtesy_check(message)
        if quick_result:
            logger.info(
                "conversation_state_quick_detect",
                state=quick_result.state.value,
                confidence=quick_result.confidence,
            )
            return quick_result

        # Step 2: Use LLM for more nuanced classification
        try:
            prediction = self.analyze(message=message)

            # Parse the state
            state = self._parse_state(prediction.conversation_state)
            contains_job_details = prediction.contains_job_details.upper() == "YES"

            # Determine if we should process
            should_process = state != ConversationState.COURTESY_CLOSE

            result = ConversationStateResult(
                state=state,
                confidence=prediction.confidence.upper(),
                reasoning=prediction.reasoning,
                contains_job_details=contains_job_details,
                should_process=should_process,
            )

            logger.info(
                "conversation_state_analyzed",
                state=result.state.value,
                confidence=result.confidence,
                should_process=result.should_process,
            )

            return result

        except Exception as e:
            logger.error("conversation_state_analyzer_failed", error=str(e))
            # Default to NEW_OPPORTUNITY to avoid missing real opportunities
            return ConversationStateResult(
                state=ConversationState.NEW_OPPORTUNITY,
                confidence="LOW",
                reasoning=f"Analysis failed, defaulting to NEW_OPPORTUNITY: {str(e)}",
                contains_job_details=True,
                should_process=True,
            )

    def _quick_courtesy_check(self, message: str) -> ConversationStateResult | None:
        """
        Quick rule-based check for obvious courtesy messages.

        Args:
            message: Raw message

        Returns:
            ConversationStateResult if obviously courtesy, None otherwise
        """
        # Clean and normalize the message
        cleaned = message.strip().lower()

        # Remove common punctuation
        cleaned = re.sub(r"[!?.,;:]+$", "", cleaned)
        cleaned = cleaned.strip()

        # Check if entire message is a courtesy phrase
        if cleaned in COURTESY_PHRASES:
            return ConversationStateResult.courtesy_close(
                reasoning=f"Message is a known courtesy phrase: '{cleaned}'"
            )

        # Check for very short messages (< 20 chars) that are likely acknowledgments
        if len(cleaned) < 20:
            # Check if it contains any courtesy phrase
            for phrase in COURTESY_PHRASES:
                if phrase in cleaned:
                    return ConversationStateResult.courtesy_close(
                        reasoning=f"Short message containing courtesy phrase: '{phrase}'"
                    )

        # Check for messages that are just greetings + thanks
        greeting_thanks_pattern = r"^(hola|hi|hey)?\s*(,|\.)?\s*(gracias|thanks|thank you)\.?$"
        if re.match(greeting_thanks_pattern, cleaned, re.IGNORECASE):
            return ConversationStateResult.courtesy_close(
                reasoning="Message is a simple greeting with thanks"
            )

        return None

    def _parse_state(self, state_str: str) -> ConversationState:
        """
        Parse conversation state from LLM output.

        Args:
            state_str: State string from LLM

        Returns:
            ConversationState enum value
        """
        state_upper = state_str.upper().strip()

        if "COURTESY" in state_upper or "CLOSE" in state_upper:
            return ConversationState.COURTESY_CLOSE
        elif "FOLLOW" in state_upper:
            return ConversationState.FOLLOW_UP
        else:
            return ConversationState.NEW_OPPORTUNITY


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

    @observe(name="dspy.message_analyzer.forward")
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
            salary_min, salary_max, currency = self._parse_salary(prediction.salary_range)

            # Parse tech stack
            tech_stack = self._parse_tech_stack(prediction.tech_stack)

            # Create structured result
            extracted = ExtractedData(
                company=self._normalize_company(prediction.company),
                role=self._normalize_role(prediction.role),
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

    def _parse_salary(self, salary_str: str) -> tuple[int | None, int | None, str]:
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
        numbers = re.findall(r"\d+", salary_str.replace(",", "").replace(".", ""))

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
        technologies = [tech.strip() for tech in tech_stack_str.split(",") if tech.strip()]

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

    def _normalize_company(self, company: str) -> str:
        """
        Normalize company name, handling N/A or unknown values.

        Args:
            company: Raw company string

        Returns:
            str: Normalized company name
        """
        if not company:
            return "Unknown Company"

        company_clean = company.strip()
        company_lower = company_clean.lower()

        # List of strings that indicate unknown company
        unknown_indicators = [
            "n/a",
            "unknown",
            "not mentioned",
            "not specified",
            "none",
            "no company",
            "confidential",
            # Common false positives from meeting links/tools
            "microsoft",  # from teams.microsoft.com
            "google",  # from meet.google.com
            "zoom",  # from zoom.us
            "calendly",  # from calendly.com
        ]

        if company_lower in unknown_indicators:
            return "Unknown Company"

        return company_clean

    def _normalize_role(self, role: str) -> str:
        """
        Normalize role name, handling N/A or unknown values.

        Args:
            role: Raw role string

        Returns:
            str: Normalized role name
        """
        if not role:
            return "Unknown Role"

        role_clean = role.strip()
        role_lower = role_clean.lower()

        # List of strings that indicate unknown role
        unknown_indicators = [
            "n/a",
            "unknown",
            "not mentioned",
            "not specified",
            "none",
            "no role",
        ]

        if role_lower in unknown_indicators:
            return "Unknown Role"

        return role_clean


class FollowUpAnalyzer(dspy.Module):
    """
    Analyzes FOLLOW_UP messages to determine if they can be auto-responded.

    Only allows auto-response for clear, profile-answerable questions.
    """

    # Questions that CAN be auto-answered with profile data
    AUTO_RESPONDABLE_TYPES = {"SALARY", "AVAILABILITY", "EXPERIENCE"}

    def __init__(self):
        """Initialize the follow-up analyzer."""
        super().__init__()
        self.analyze = dspy.ChainOfThought(FollowUpAnalysisSignature)

    @observe(name="dspy.follow_up_analyzer.forward")
    def forward(self, message: str, profile_dict: dict) -> FollowUpAnalysisResult:
        """
        Analyze a follow-up message to determine if it can be auto-responded.

        Args:
            message: The follow-up message
            profile_dict: Candidate's profile dictionary

        Returns:
            FollowUpAnalysisResult: Analysis result
        """
        logger.debug("follow_up_analyzer_start", message_length=len(message))

        # Build profile summary for the LLM
        profile_summary = self._build_profile_summary(profile_dict)

        try:
            prediction = self.analyze(
                message=message,
                candidate_profile_summary=profile_summary,
            )

            # Parse results
            question_type = prediction.question_type.upper().strip()
            can_auto_respond = prediction.can_auto_respond.upper() == "YES"
            requires_context = prediction.requires_context.upper() == "YES"
            detected_question = (
                prediction.detected_question if prediction.detected_question != "N/A" else None
            )

            # Double-check: only allow auto-respond for specific question types
            if can_auto_respond and question_type not in self.AUTO_RESPONDABLE_TYPES:
                can_auto_respond = False

            # Generate suggested response if auto-respond is allowed
            suggested_response = None
            if can_auto_respond:
                suggested_response = self._generate_auto_response(
                    question_type, profile_dict, detected_question
                )

            result = FollowUpAnalysisResult(
                can_auto_respond=can_auto_respond,
                question_type=question_type,
                detected_question=detected_question,
                suggested_response=suggested_response,
                reasoning=prediction.reasoning,
                requires_context=requires_context,
            )

            logger.info(
                "follow_up_analysis_complete",
                question_type=question_type,
                can_auto_respond=can_auto_respond,
                requires_context=requires_context,
            )

            return result

        except Exception as e:
            logger.error("follow_up_analyzer_failed", error=str(e))
            return FollowUpAnalysisResult.manual_review(reasoning=f"Analysis failed: {str(e)}")

    def _build_profile_summary(self, profile_dict: dict) -> str:
        """Build a summary of the candidate's profile for the LLM."""
        lines = []

        # Basic info
        lines.append(f"Name: {profile_dict.get('name', 'Unknown')}")
        lines.append(f"Experience: {profile_dict.get('years_of_experience', 'Unknown')} years")
        lines.append(f"Current level: {profile_dict.get('current_seniority', 'Unknown')}")

        # Salary
        min_salary = profile_dict.get("minimum_salary_usd", 0)
        ideal_salary = profile_dict.get("ideal_salary_usd", 0)
        lines.append(f"Salary expectation: ${min_salary:,} - ${ideal_salary:,} USD annually")

        # Technologies
        techs = profile_dict.get("preferred_technologies", [])
        if techs:
            lines.append(f"Key technologies: {', '.join(techs[:10])}")

        # Work preferences
        lines.append(f"Remote preference: {profile_dict.get('preferred_remote_policy', 'Remote')}")
        lines.append(f"Work week preference: {profile_dict.get('preferred_work_week', '4-days')}")

        # Job search status
        job_search = profile_dict.get("job_search_status", {})
        lines.append(f"Currently employed: {job_search.get('currently_employed', 'Unknown')}")
        lines.append(f"Actively looking: {job_search.get('actively_looking', 'Unknown')}")

        return "\n".join(lines)

    def _generate_auto_response(
        self,
        question_type: str,
        profile_dict: dict,
        detected_question: str | None,
    ) -> str | None:
        """Generate an auto-response for answerable questions."""

        # candidate_name = profile_dict.get("name", "").split()[0]  # First name

        if question_type == "SALARY":
            min_salary = profile_dict.get("minimum_salary_usd", 80000)
            ideal_salary = profile_dict.get("ideal_salary_usd", 120000)
            return f"""Gracias por preguntar. Mi expectativa salarial está en el rango de ${min_salary:,} - ${ideal_salary:,} USD anuales, dependiendo de las responsabilidades y beneficios del rol.

*Nota: Esta respuesta fue generada con asistencia de IA como herramienta de productividad."""

        elif question_type == "AVAILABILITY":
            job_search = profile_dict.get("job_search_status", {})
            currently_employed = job_search.get("currently_employed", True)

            if currently_employed:
                return """Actualmente estoy empleado, por lo que necesitaría coordinar una transición. En general, podría estar disponible con un aviso de 2-4 semanas.

*Nota: Esta respuesta fue generada con asistencia de IA como herramienta de productividad."""
            else:
                return """Estoy disponible para comenzar de inmediato o en un plazo corto según las necesidades del proyecto.

*Nota: Esta respuesta fue generada con asistencia de IA como herramienta de productividad."""

        elif question_type == "EXPERIENCE":
            years = profile_dict.get("years_of_experience", 5)
            techs = profile_dict.get("preferred_technologies", [])
            seniority = profile_dict.get("current_seniority", "Senior")

            tech_list = ", ".join(techs[:5]) if techs else "Python, FastAPI, PostgreSQL"
            return f"""Tengo {years} años de experiencia profesional, actualmente en nivel {seniority}. Mis tecnologías principales incluyen: {tech_list}.

Si necesitas más detalles sobre alguna tecnología específica, con gusto te los comparto.

*Nota: Esta respuesta fue generada con asistencia de IA como herramienta de productividad."""

        return None
