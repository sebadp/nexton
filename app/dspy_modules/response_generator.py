"""
ResponseGenerator - DSPy module to generate personalized responses.

Creates professional, context-aware responses to recruiters based
on the opportunity score and details.
"""
import dspy

from app.core.logging import get_logger
from app.dspy_modules.models import ExtractedData, ScoringResult
from app.dspy_modules.signatures import ResponseGenerationSignature

logger = get_logger(__name__)


class ResponseGenerator(dspy.Module):
    """
    Generates personalized responses to LinkedIn recruiters.

    Response tone and content adapts based on:
    - Total score (0-100)
    - Tier (HIGH_PRIORITY, INTERESANTE, POCO_INTERESANTE, NO_INTERESA)
    - Specific job details (company, role, tech stack, salary)
    """

    def __init__(self):
        """Initialize the response generator."""
        super().__init__()
        self.generate = dspy.ChainOfThought(ResponseGenerationSignature)

    def forward(
        self,
        recruiter_name: str,
        extracted: ExtractedData,
        scoring: ScoringResult,
        candidate_name: str = "Sebastián",
        profile: dict = None,
    ) -> str:
        """
        Generate a response to the recruiter.

        Args:
            recruiter_name: Recruiter's name
            extracted: Extracted job data
            scoring: Scoring results
            candidate_name: Candidate's name
            profile: Candidate's profile including job_search_status

        Returns:
            str: Generated response text

        Example:
            generator = ResponseGenerator()
            response = generator(
                recruiter_name="María",
                extracted=data,
                scoring=scores,
                candidate_name="Juan",
                profile=profile_dict,
            )
        """
        logger.debug(
            "response_generator_start",
            recruiter=recruiter_name,
            tier=scoring.tier,
            score=scoring.total_score,
        )

        try:
            # Prepare salary info
            if extracted.salary_min and extracted.salary_max:
                salary_range = (
                    f"{extracted.salary_min}-{extracted.salary_max} {extracted.currency}"
                )
            elif extracted.salary_min:
                salary_range = f"{extracted.salary_min}+ {extracted.currency}"
            else:
                salary_range = "Not mentioned"

            # Build candidate context from profile
            candidate_context = self._build_candidate_context(profile)

            # Generate response
            prediction = self.generate(
                recruiter_name=recruiter_name,
                company=extracted.company,
                role=extracted.role,
                total_score=scoring.total_score,
                tier=scoring.tier,
                salary_range=salary_range,
                tech_stack=", ".join(extracted.tech_stack[:5]),  # Max 5 techs
                candidate_name=candidate_name,
                candidate_context=candidate_context,
            )

            response = prediction.response.strip()

            # Validate response has AI transparency note
            if "*Nota:" not in response:
                response += (
                    "\n\n*Nota: Esta respuesta fue generada con asistencia de IA "
                    "como herramienta de productividad."
                )

            # Validate word count (50-200 words)
            word_count = len(response.split())
            if word_count < 50:
                logger.warning(
                    "response_too_short",
                    word_count=word_count,
                    tier=scoring.tier,
                )
            elif word_count > 200:
                logger.warning(
                    "response_too_long",
                    word_count=word_count,
                    tier=scoring.tier,
                )

            logger.info(
                "response_generator_success",
                word_count=word_count,
                tier=scoring.tier,
                score=scoring.total_score,
            )

            return response

        except Exception as e:
            logger.error("response_generator_failed", error=str(e))
            # Return fallback response
            return self._fallback_response(
                recruiter_name,
                extracted,
                scoring,
                candidate_name,
            )

    def _build_candidate_context(self, profile: dict = None) -> str:
        """
        Build candidate context string from profile.

        Args:
            profile: Candidate's profile dictionary

        Returns:
            str: Formatted context for the LLM
        """
        if not profile:
            return "Candidate is open to opportunities."

        context_parts = []

        # Job search status
        job_status = profile.get("job_search_status", {})

        if job_status:
            # Current situation
            situation = job_status.get("situation", "").strip()
            if situation:
                context_parts.append(f"Current situation: {situation}")

            # Urgency level
            urgency = job_status.get("urgency", "selective")
            actively_looking = job_status.get("actively_looking", False)

            if urgency == "urgent":
                context_parts.append("Actively seeking new opportunities urgently.")
            elif urgency == "moderate" and actively_looking:
                context_parts.append("Actively looking for the right opportunity.")
            elif urgency == "selective":
                context_parts.append("Open to exceptional opportunities that meet specific criteria.")
            else:
                context_parts.append("Currently not looking, but open to outstanding opportunities.")

            # Must-have requirements
            must_haves = job_status.get("must_have", [])
            if must_haves:
                context_parts.append(
                    "MUST-HAVE requirements (deal-breakers): " + ", ".join(must_haves)
                )

            # Nice to have
            nice_to_haves = job_status.get("nice_to_have", [])
            if nice_to_haves:
                context_parts.append(
                    "Nice to have: " + ", ".join(nice_to_haves[:3])  # Limit to 3
                )

            # Automatic rejection criteria
            reject_if = job_status.get("reject_if", [])
            if reject_if:
                context_parts.append(
                    "Will automatically decline: " + ", ".join(reject_if[:3])
                )

        # Additional preferences
        if profile.get("looking_for_change"):
            context_parts.append("Open to changing jobs.")
        else:
            context_parts.append("Happy in current role, only interested in exceptional opportunities.")

        return " ".join(context_parts)

    def _fallback_response(
        self,
        recruiter_name: str,
        extracted: ExtractedData,
        scoring: ScoringResult,
        candidate_name: str,
    ) -> str:
        """
        Generate a fallback response when LLM fails.

        Uses template-based responses.

        Args:
            recruiter_name: Recruiter's name
            extracted: Extracted data
            scoring: Scoring results
            candidate_name: Candidate's name

        Returns:
            str: Fallback response
        """
        logger.warning("using_fallback_response", tier=scoring.tier)

        tier = scoring.tier

        if tier == "HIGH_PRIORITY":
            response = f"""Hola {recruiter_name},

Muchas gracias por contactarme sobre la posición de {extracted.role} en {extracted.company}.

Me interesa mucho esta oportunidad. Mi experiencia con {', '.join(extracted.tech_stack[:3])} se alinea bien con lo que buscan, y me gustaría conocer más detalles sobre el proyecto y el equipo.

¿Podríamos agendar una llamada esta semana para conversar?

Saludos,
{candidate_name}

*Nota: Esta respuesta fue generada con asistencia de IA como herramienta de productividad."""

        elif tier == "INTERESANTE":
            response = f"""Hola {recruiter_name},

Gracias por pensar en mí para la posición de {extracted.role} en {extracted.company}.

La oportunidad me parece interesante. Me gustaría conocer más sobre:
- El stack tecnológico completo del proyecto
- El tamaño y estructura del equipo
- Las responsabilidades específicas del rol

¿Podrías compartir más información?

Saludos,
{candidate_name}

*Nota: Esta respuesta fue generada con asistencia de IA como herramienta de productividad."""

        elif tier == "POCO_INTERESANTE":
            response = f"""Hola {recruiter_name},

Gracias por contactarme sobre {extracted.role} en {extracted.company}.

En este momento estoy enfocado en oportunidades que se alineen más con mi experiencia y objetivos de carrera. Si tuvieras otras posiciones más senior o con un perfil técnico diferente, estaría interesado en conocerlas.

Saludos,
{candidate_name}

*Nota: Esta respuesta fue generada con asistencia de IA como herramienta de productividad."""

        else:  # NO_INTERESA
            response = f"""Hola {recruiter_name},

Agradezco que hayas pensado en mí, pero en este momento no estoy buscando oportunidades que coincidan con este perfil.

Te deseo éxito en la búsqueda del candidato ideal.

Saludos,
{candidate_name}

*Nota: Esta respuesta fue generada con asistencia de IA como herramienta de productividad."""

        return response