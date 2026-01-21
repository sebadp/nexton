"""
ResponseGenerator - DSPy module to generate personalized responses.

Creates professional, context-aware responses to recruiters based
on the opportunity score and details.
"""
import dspy

from app.core.logging import get_logger
from app.dspy_modules.models import CandidateStatus, ExtractedData, HardFilterResult, ScoringResult
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
        candidate_status: CandidateStatus = CandidateStatus.PASSIVE,
        hard_filter_result: HardFilterResult = None,
    ) -> str:
        """
        Generate a response to the recruiter.

        Args:
            recruiter_name: Recruiter's name
            extracted: Extracted job data
            scoring: Scoring results
            candidate_name: Candidate's name
            profile: Candidate's profile including job_search_status
            candidate_status: Candidate's job search status
            hard_filter_result: Result of hard filter validation

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
                candidate_status=CandidateStatus.SELECTIVE,
                hard_filter_result=filter_result,
            )
        """
        logger.debug(
            "response_generator_start",
            recruiter=recruiter_name,
            tier=scoring.tier,
            score=scoring.total_score,
            candidate_status=candidate_status.value,
            has_hard_filter_result=hard_filter_result is not None,
        )

        # Use default if no hard filter result provided
        if hard_filter_result is None:
            hard_filter_result = HardFilterResult.all_passed()

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

            # Prepare failed filters string
            failed_hard_filters = ", ".join(hard_filter_result.failed_filters) if hard_filter_result.failed_filters else ""

            # Determine work week status
            work_week_mentioned = hard_filter_result.work_week_status
            if work_week_mentioned == "CONFIRMED":
                work_week_mentioned = "YES"
            elif work_week_mentioned in ("NOT_MENTIONED", "FIVE_DAY"):
                work_week_mentioned = "NO"
            else:
                work_week_mentioned = "UNKNOWN"

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
                candidate_status=candidate_status.value,
                failed_hard_filters=failed_hard_filters,
                work_week_mentioned=work_week_mentioned,
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
                candidate_status=candidate_status.value,
                failed_filters_count=len(hard_filter_result.failed_filters),
            )

            return response

        except Exception as e:
            logger.error("response_generator_failed", error=str(e))
            # Return fallback response based on hard filter result
            return self._fallback_response(
                recruiter_name,
                extracted,
                scoring,
                candidate_name,
                candidate_status,
                hard_filter_result,
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
        candidate_status: CandidateStatus = CandidateStatus.PASSIVE,
        hard_filter_result: HardFilterResult = None,
    ) -> str:
        """
        Generate a fallback response when LLM fails.

        Uses template-based responses that respect hard filters and candidate status.

        Args:
            recruiter_name: Recruiter's name
            extracted: Extracted data
            scoring: Scoring results
            candidate_name: Candidate's name
            candidate_status: Candidate's job search status
            hard_filter_result: Result of hard filter validation

        Returns:
            str: Fallback response
        """
        logger.warning(
            "using_fallback_response",
            tier=scoring.tier,
            candidate_status=candidate_status.value,
            has_hard_filter_result=hard_filter_result is not None,
        )

        # Default if not provided
        if hard_filter_result is None:
            hard_filter_result = HardFilterResult.all_passed()

        tier = scoring.tier

        # Priority 1: Check if hard filters failed and we should decline
        if hard_filter_result.should_decline:
            # Generate decline response based on failed filters
            if "4-day work week" in str(hard_filter_result.failed_filters) or "work week" in str(hard_filter_result.failed_filters).lower():
                response = f"""Hola {recruiter_name},

Gracias por pensar en mí para la posición de {extracted.role} en {extracted.company}.

Actualmente solo estoy considerando posiciones con semana laboral de 4 días, que es un requisito indispensable para mí. Si la posición cuenta con esta modalidad, me encantaría conocer más detalles.

Saludos,
{candidate_name}

*Nota: Esta respuesta fue generada con asistencia de IA como herramienta de productividad."""
            else:
                failed_reasons = ", ".join(hard_filter_result.failed_filters[:2]) if hard_filter_result.failed_filters else "mis requisitos actuales"
                response = f"""Hola {recruiter_name},

Gracias por contactarme sobre {extracted.role} en {extracted.company}.

En este momento estoy buscando oportunidades que se alineen más específicamente con mis requisitos. Lamentablemente, esta posición no cumple con: {failed_reasons}.

Te deseo éxito en la búsqueda.

Saludos,
{candidate_name}

*Nota: Esta respuesta fue generada con asistencia de IA como herramienta de productividad."""
            return response

        # Priority 2: Check candidate status for PASSIVE/SELECTIVE responses
        if candidate_status in (CandidateStatus.PASSIVE, CandidateStatus.SELECTIVE):
            if hard_filter_result.work_week_status == "NOT_MENTIONED":
                response = f"""Hola {recruiter_name},

Gracias por contactarme. Actualmente no estoy buscando activamente, pero para posiciones con semana laboral de 4 días podría considerar hacer un espacio.

¿Este rol cuenta con esa modalidad de trabajo?

Saludos,
{candidate_name}

*Nota: Esta respuesta fue generada con asistencia de IA como herramienta de productividad."""
                return response

        # Priority 3: Standard tier-based responses
        if tier == "HIGH_PRIORITY" and candidate_status == CandidateStatus.ACTIVE_SEARCH:
            response = f"""Hola {recruiter_name},

Muchas gracias por contactarme sobre la posición de {extracted.role} en {extracted.company}.

Me interesa mucho esta oportunidad. Mi experiencia con {', '.join(extracted.tech_stack[:3]) if extracted.tech_stack else 'las tecnologías mencionadas'} se alinea bien con lo que buscan, y me gustaría conocer más detalles sobre el proyecto y el equipo.

¿Podríamos agendar una llamada esta semana para conversar?

Saludos,
{candidate_name}

*Nota: Esta respuesta fue generada con asistencia de IA como herramienta de productividad."""

        elif tier == "HIGH_PRIORITY":
            # HIGH_PRIORITY but PASSIVE/SELECTIVE - ask about requirements first
            response = f"""Hola {recruiter_name},

Gracias por pensar en mí para la posición de {extracted.role} en {extracted.company}.

La oportunidad me parece muy interesante. Antes de avanzar, me gustaría confirmar algunos detalles importantes:
- ¿La posición ofrece semana laboral de 4 días?
- ¿Es una posición 100% remota?

Quedo atento a tu respuesta.

Saludos,
{candidate_name}

*Nota: Esta respuesta fue generada con asistencia de IA como herramienta de productividad."""

        elif tier == "INTERESANTE":
            response = f"""Hola {recruiter_name},

Gracias por pensar en mí para la posición de {extracted.role} en {extracted.company}.

La oportunidad me parece interesante. Me gustaría conocer más sobre:
- ¿Cuentan con semana laboral de 4 días?
- El stack tecnológico completo del proyecto
- El tamaño y estructura del equipo

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