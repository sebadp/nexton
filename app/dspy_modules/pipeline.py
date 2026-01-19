"""
OpportunityPipeline - Integrates all DSPy modules into a complete workflow.

This is the main entry point for processing LinkedIn recruiter messages.
"""
import time
from typing import Optional

import dspy

from app.core.config import settings
from app.core.exceptions import PipelineError
from app.core.logging import get_logger
from app.dspy_modules.message_analyzer import MessageAnalyzer
from app.dspy_modules.models import CandidateProfile, OpportunityResult
from app.dspy_modules.response_generator import ResponseGenerator
from app.dspy_modules.scorer import Scorer
from app.llm import DSPyLLMAdapter, get_llm_provider

logger = get_logger(__name__)


class OpportunityPipeline(dspy.Module):
    """
    Complete pipeline for processing LinkedIn opportunities.

    Flow:
    1. MessageAnalyzer: Extract structured data from message
    2. Scorer: Calculate relevance scores
    3. ResponseGenerator: Create personalized response

    Example:
        pipeline = OpportunityPipeline()
        result = pipeline(
            message="Hola! Tenemos...",
            recruiter_name="María López",
            profile=candidate_profile,
        )
    """

    def __init__(self):
        """Initialize the pipeline with all modules."""
        super().__init__()

        # Initialize modules
        self.analyzer = MessageAnalyzer()
        self.scorer = Scorer()
        self.generator = ResponseGenerator()

        logger.info("opportunity_pipeline_initialized")

    def forward(
        self,
        message: str,
        recruiter_name: str,
        profile: CandidateProfile,
    ) -> OpportunityResult:
        """
        Process a recruiter message through the complete pipeline.

        Args:
            message: Raw recruiter message
            recruiter_name: Recruiter's name
            profile: Candidate profile

        Returns:
            OpportunityResult: Complete processing result

        Raises:
            PipelineError: If pipeline execution fails
        """
        start_time = time.time()

        logger.info(
            "pipeline_start",
            recruiter=recruiter_name,
            message_length=len(message),
        )

        try:
            # Step 1: Extract structured data
            logger.debug("pipeline_step", step="analyze")
            extracted = self.analyzer(message=message)

            # Step 2: Score the opportunity
            logger.debug("pipeline_step", step="score")
            scoring = self.scorer(extracted=extracted, profile=profile)

            # Step 3: Generate response
            logger.debug("pipeline_step", step="generate_response")

            # Get full profile dict (includes job_search_status)
            from app.dspy_modules.profile_loader import get_profile_dict
            profile_dict = get_profile_dict()

            response = self.generator(
                recruiter_name=recruiter_name,
                extracted=extracted,
                scoring=scoring,
                candidate_name=profile.name,
                profile=profile_dict,
            )

            # Calculate processing time
            processing_time_ms = int((time.time() - start_time) * 1000)

            # Create result
            result = OpportunityResult(
                recruiter_name=recruiter_name,
                raw_message=message,
                extracted=extracted,
                scoring=scoring,
                ai_response=response,
                processing_time_ms=processing_time_ms,
                status="processed",
            )

            logger.info(
                "pipeline_success",
                score=scoring.total_score,
                tier=scoring.tier,
                processing_time_ms=processing_time_ms,
            )

            return result

        except Exception as e:
            processing_time_ms = int((time.time() - start_time) * 1000)

            logger.error(
                "pipeline_failed",
                error=str(e),
                recruiter=recruiter_name,
                processing_time_ms=processing_time_ms,
            )

            raise PipelineError(
                message="Failed to process opportunity",
                details={
                    "recruiter": recruiter_name,
                    "error": str(e),
                    "processing_time_ms": processing_time_ms,
                },
            ) from e


def configure_dspy(
    provider_type: Optional[str] = None,
    model_name: Optional[str] = None,
    max_tokens: Optional[int] = None,
    temperature: Optional[float] = None,
) -> None:
    """
    Configure DSPy with LLM provider.

    Supports multiple providers: OpenAI, Anthropic, Ollama.

    Args:
        provider_type: LLM provider (openai, anthropic, ollama). Defaults to LLM_PROVIDER setting.
        model_name: Model name. Defaults to LLM_MODEL setting.
        max_tokens: Maximum tokens (default from settings)
        temperature: LLM temperature (default from settings)
    """
    provider_type = provider_type or settings.LLM_PROVIDER
    model_name = model_name or settings.LLM_MODEL
    max_tokens = max_tokens or settings.LLM_MAX_TOKENS
    temperature = temperature or settings.LLM_TEMPERATURE

    logger.info(
        "configuring_dspy",
        extra={
            "provider": provider_type,
            "model": model_name,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
    )

    try:
        # Get LLM provider from factory
        llm_provider = get_llm_provider(provider_type=provider_type, model=model_name, cached=True)

        # Wrap provider in DSPy adapter
        lm = DSPyLLMAdapter(
            provider=llm_provider,
            max_tokens=max_tokens,
            temperature=temperature,
        )

        # Set as default LM for DSPy
        dspy.settings.configure(lm=lm)

        logger.info(
            "dspy_configured_successfully",
            extra={
                "provider": provider_type,
                "model": model_name,
            }
        )

    except Exception as e:
        logger.error(
            "dspy_configuration_failed",
            extra={"provider": provider_type, "model": model_name, "error": str(e)}
        )
        raise PipelineError(
            message=f"Failed to configure DSPy with {provider_type}",
            details={"provider": provider_type, "model": model_name, "error": str(e)},
        ) from e


# Singleton instance (lazy initialization)
_pipeline_instance: Optional[OpportunityPipeline] = None


def get_pipeline() -> OpportunityPipeline:
    """
    Get or create pipeline instance (singleton pattern).

    Returns:
        OpportunityPipeline: Pipeline instance
    """
    global _pipeline_instance

    if _pipeline_instance is None:
        # Configure DSPy first
        configure_dspy()

        # Create pipeline
        _pipeline_instance = OpportunityPipeline()
        logger.info("pipeline_instance_created")

    return _pipeline_instance