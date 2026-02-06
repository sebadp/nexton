"""
Response Generator using DSPy.

Generates personalized responses to LinkedIn messages based on opportunity analysis.
"""

import dspy
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.logging import get_logger
from app.core.profile import get_user_profile
from app.dspy_pipeline.llm_factory import get_llm
from app.dspy_pipeline.opportunity_analyzer import OpportunityAnalysis

logger = get_logger(__name__)


class ResponseOutput(BaseModel):
    """Structured output for generated response."""

    response_text: str = Field(..., description="The generated response message")
    tone: str = Field(
        ..., description="Tone of the response (e.g., professional_interested, polite_decline)"
    )
    length: int = Field(..., description="Length of response in characters")
    key_points: list[str] = Field(
        default_factory=list, description="Key points addressed in response"
    )
    reasoning: str = Field("", description="Reasoning behind the response style")


class GenerateResponse(dspy.Signature):
    """Generate a personalized, human response to a LinkedIn recruiter message.

    CRITICAL RULES:
    1. LANGUAGE MIRRORING: Respond in the SAME language as the recruiter (Spanish → Spanish, English → English)
    2. NO AI-ISMS: Never start with "As a...", "I'm intrigued by...", or robotic phrases
    3. BE DIRECT: Senior dev tone - busy, polite, professional but casual
    4. ONGOING THREADS: If message is short/continuation ("Dale", "Buenísimo"), keep response brief, don't repeat bio
    5. ACKNOWLEDGE LINKS: If recruiter shared Calendly/Ashby link, say you'll check it, don't ask to schedule
    6. SALARY: Use USD 3,500 - 4,500 monthly if asked
    7. CV: Mention you'll attach/send it if asked
    8. AVAILABILITY: Offer "esta semana por la tarde" / "this week in the afternoon"
    """

    # Input
    message: str = dspy.InputField(desc="Original message from recruiter")
    sender: str = dspy.InputField(desc="Sender's name (first name only)")
    tier: str = dspy.InputField(desc="Opportunity tier: A, B, C, or D")
    company: str = dspy.InputField(desc="Company name")
    role: str = dspy.InputField(desc="Job role/title")
    summary: str = dspy.InputField(desc="Brief summary of opportunity")
    tech_stack: str = dspy.InputField(desc="Technologies mentioned")
    is_short_message: str = dspy.InputField(
        desc="'yes' if message is short/ongoing thread, 'no' otherwise"
    )
    has_calendar_link: str = dspy.InputField(
        desc="'yes' if message contains Calendly/Ashby/calendar link, 'no' otherwise"
    )
    message_language: str = dspy.InputField(desc="'es' for Spanish, 'en' for English")

    # User context
    user_first_name: str = dspy.InputField(desc="User's first name only")
    salary_range: str = dspy.InputField(desc="User's salary expectation")

    # Output
    response: str = dspy.OutputField(
        desc="""Natural, human response (2-3 sentences for normal, 1 sentence for short messages).
    MUST be in the SAME language as input.
    For Spanish: Use casual tone with 'Hola [name]', end with '¡Abrazo!' or 'Saludos'
    For English: Use professional casual tone, end naturally
    NO AI-isms like 'I'm intrigued', 'As a Senior Engineer', etc.
    Senior dev tone: direct, busy but interested."""
    )
    tone: str = dspy.OutputField(desc="Tone used: interested, polite, brief, declining")
    key_points: str = dspy.OutputField(desc="Comma-separated key points addressed")
    reasoning: str = dspy.OutputField(desc="Brief reasoning for this response style")


class ResponseGenerator:
    """Generates personalized LinkedIn responses using DSPy."""

    def __init__(
        self,
        provider: str | None = None,
        model: str | None = None,
    ):
        """
        Initialize the generator.

        Args:
            provider: LLM provider (uses settings if None)
            model: Model name (uses settings if None)
        """
        # Get LLM
        self.lm = get_llm(
            provider=provider or settings.RESPONSE_LLM_PROVIDER,
            model=model or settings.RESPONSE_LLM_MODEL,
        )

        # Configure DSPy to use this LLM
        dspy.configure(lm=self.lm)

        # Create DSPy module
        self.generator = dspy.ChainOfThought(GenerateResponse)

        logger.info("response_generator_initialized")

    def generate(
        self,
        message: str,
        sender: str,
        analysis: OpportunityAnalysis,
    ) -> ResponseOutput:
        """
        Generate a personalized response.

        Args:
            message: Original message text
            sender: Sender name
            analysis: Opportunity analysis result

        Returns:
            ResponseOutput with generated response
        """
        logger.info(
            "generating_response",
            sender=sender,
            tier=analysis.tier,
        )

        try:
            # Load user profile
            try:
                profile = get_user_profile()
                user_first_name = profile.first_name
                # Monthly salary range for contractors/freelancers
                salary_range = "USD 3,500 - 4,500 monthly"
                logger.debug("user_profile_loaded", first_name=user_first_name)
            except Exception as e:
                logger.warning("failed_to_load_profile_for_response", error=str(e))
                user_first_name = "Sebastian"
                salary_range = "USD 3,500 - 4,500 monthly"

            # Detect language (simple heuristic)
            message_lower = message.lower()
            spanish_indicators = [
                "hola",
                "gracias",
                "estoy",
                "busco",
                "interesado",
                "posición",
                "salario",
                "¿",
            ]
            is_spanish = any(indicator in message_lower for indicator in spanish_indicators)
            message_language = "es" if is_spanish else "en"

            # Detect if it's a short/ongoing thread message
            message_words = message.split()
            is_short = len(message_words) < 20
            short_responses = [
                "dale",
                "buenísimo",
                "perfecto",
                "ok",
                "okay",
                "genial",
                "great",
                "sounds good",
            ]
            is_ongoing_thread = any(resp in message_lower for resp in short_responses)
            is_short_message = "yes" if (is_short or is_ongoing_thread) else "no"

            # Detect calendar links
            calendar_indicators = [
                "calendly",
                "ashby",
                "calendar",
                "cal.com",
                "schedule",
                "agendar",
            ]
            has_calendar_link = (
                "yes"
                if any(indicator in message_lower for indicator in calendar_indicators)
                else "no"
            )

            # Extract first name from sender
            sender_first_name = sender.split()[0] if sender else "there"

            logger.debug(
                "response_context",
                language=message_language,
                is_short=is_short_message,
                has_calendar_link=has_calendar_link,
                sender_first_name=sender_first_name,
            )

            # Generate response
            result = self.generator(
                message=message,
                sender=sender_first_name,
                tier=analysis.tier,
                company=analysis.company_name or "the company",
                role=analysis.role_title or "the position",
                summary=analysis.summary,
                tech_stack=(
                    ", ".join(analysis.tech_stack) if analysis.tech_stack else "Not specified"
                ),
                is_short_message=is_short_message,
                has_calendar_link=has_calendar_link,
                message_language=message_language,
                user_first_name=user_first_name,
                salary_range=salary_range,
            )

            # Parse key points
            key_points_str = result.key_points
            if key_points_str:
                key_points = [kp.strip() for kp in key_points_str.split(",")]
            else:
                key_points = []

            # Create output
            output = ResponseOutput(
                response_text=result.response,
                tone=result.tone,
                length=len(result.response),
                key_points=key_points,
                reasoning=result.reasoning,
            )

            logger.info(
                "response_generated",
                sender=sender,
                tone=output.tone,
                length=output.length,
            )

            return output

        except Exception as e:
            logger.error("response_generation_failed", error=str(e), exc_info=True)

            # Return fallback response
            fallback = self._get_fallback_response(analysis.tier, sender, message)
            return ResponseOutput(
                response_text=fallback,
                tone="polite",
                length=len(fallback),
                key_points=["acknowledgment"],
                reasoning="Fallback response due to generation error",
            )

    def _get_fallback_response(self, tier: str, sender: str, message: str = "") -> str:
        """Get a fallback response if generation fails.

        Args:
            tier: Opportunity tier (A, B, C, D)
            sender: Sender name
            message: Original message text (for language detection)
        """
        first_name = sender.split()[0] if sender else "there"

        # Detect language
        if message:
            message_lower = message.lower()
            spanish_indicators = [
                "hola",
                "gracias",
                "estoy",
                "busco",
                "interesado",
                "posición",
                "salario",
                "¿",
            ]
            is_spanish = any(indicator in message_lower for indicator in spanish_indicators)
        else:
            is_spanish = False

        # Get responses based on tier and language
        if tier == "A":
            if is_spanish:
                return (
                    f"Hola {first_name}, gracias por contactarme. "
                    f"Me interesa saber más sobre la posición. "
                    f"¿Podemos hablar esta semana por la tarde?\n\n"
                    f"¡Abrazo!"
                )
            else:
                return (
                    f"Hi {first_name}, thanks for reaching out. "
                    f"I'd like to learn more about this opportunity. "
                    f"Can we chat this week in the afternoon?"
                )
        elif tier == "B":
            if is_spanish:
                return (
                    f"Hola {first_name}, gracias por escribir. "
                    f"¿Podrías compartir más detalles sobre el rol?\n\n"
                    f"Saludos"
                )
            else:
                return (
                    f"Hi {first_name}, thanks for your message. "
                    f"Could you share more details about the role?"
                )
        elif tier == "C":
            if is_spanish:
                return (
                    f"Hola {first_name}, gracias por pensar en mí. "
                    f"No estoy buscando activamente por ahora, pero puedo "
                    f"conectar para futuras oportunidades.\n\n"
                    f"Saludos"
                )
            else:
                return (
                    f"Hi {first_name}, thanks for thinking of me. "
                    f"Not actively looking right now, but happy to "
                    f"connect for future opportunities."
                )
        else:  # D
            if is_spanish:
                return (
                    f"Hola {first_name}, gracias por contactar. "
                    f"Lamentablemente esto no se alinea con lo que busco ahora. "
                    f"¡Éxitos con la búsqueda!"
                )
            else:
                return (
                    f"Hi {first_name}, thanks for reaching out. "
                    f"Unfortunately this doesn't align with what I'm looking for right now. "
                    f"Best of luck with your search!"
                )
