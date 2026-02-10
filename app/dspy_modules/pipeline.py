"""
OpportunityPipeline - Integrates all DSPy modules into a complete workflow.

This is the main entry point for processing LinkedIn recruiter messages.
"""

import time
from collections.abc import Callable
from typing import cast

import dspy

from app.core.config import settings
from app.core.exceptions import PipelineError
from app.core.logging import get_logger
from app.dspy_modules.hard_filters import apply_hard_filters, get_candidate_status_from_profile
from app.dspy_modules.message_analyzer import (
    ConversationStateAnalyzer,
    FollowUpAnalyzer,
    MessageAnalyzer,
)
from app.dspy_modules.models import (
    CandidateProfile,
    ConversationState,
    ConversationStateResult,
    ExtractedData,
    HardFilterResult,
    OpportunityResult,
    ScoringResult,
)
from app.dspy_modules.response_generator import ResponseGenerator
from app.dspy_modules.scorer import Scorer
from app.observability import observe

logger = get_logger(__name__)


class OpportunityPipeline(dspy.Module):
    """
    Complete pipeline for processing LinkedIn opportunities.

    Enhanced flow with conversation state awareness:
    0. ConversationStateAnalyzer: Classify message type (NEW_OPPORTUNITY, FOLLOW_UP, COURTESY_CLOSE)
    1. MessageAnalyzer: Extract structured data from message (if should_process)
    2. Scorer: Calculate relevance scores
    3. HardFilters: Apply veto filters based on profile requirements
    4. ResponseGenerator: Create personalized response (respecting filters and status)

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
        self.conversation_state_analyzer = ConversationStateAnalyzer()
        self.analyzer = MessageAnalyzer()
        self.scorer = Scorer()
        self.generator = ResponseGenerator()
        self.follow_up_analyzer = FollowUpAnalyzer()

        # Initialize creative LM for response generation
        self.creative_lm = create_lm(temperature=settings.LLM_TEMPERATURE_GENERATION)

        logger.info("opportunity_pipeline_initialized")

    @observe(name="dspy.pipeline.forward")
    def forward(
        self,
        message: str,
        recruiter_name: str,
        profile: CandidateProfile,
        on_progress: Callable[[str, dict], None] | None = None,
    ) -> OpportunityResult:
        """
        Process a recruiter message through the complete pipeline.

        Args:
            message: Raw recruiter message
            recruiter_name: Recruiter's name
            profile: Candidate profile
            on_progress: Optional callback for progress updates

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
            # Lazy import to avoid circular dependency
            from app.dspy_modules.profile_loader import get_profile_dict

            # Get full profile dict (includes job_search_status)
            profile_dict = get_profile_dict()

            # Step 0: Analyze conversation state
            logger.debug("pipeline_step", step="conversation_state")
            if on_progress:
                on_progress("conversation_state", {"status": "analyzing"})

            conversation_state = self.conversation_state_analyzer(message=message)

            if on_progress:
                on_progress(
                    "conversation_state",
                    {
                        "status": "completed",
                        "state": conversation_state.state.value,
                        "reasoning": conversation_state.reasoning,
                    },
                )

            # If COURTESY_CLOSE, return early with minimal processing
            if not conversation_state.should_process:
                processing_time_ms = int((time.time() - start_time) * 1000)

                logger.info(
                    "pipeline_courtesy_close",
                    state=conversation_state.state.value,
                    reasoning=conversation_state.reasoning,
                    processing_time_ms=processing_time_ms,
                )

                # Create minimal result for COURTESY_CLOSE - no response needed
                return OpportunityResult(
                    recruiter_name=recruiter_name,
                    raw_message=message,
                    conversation_state=conversation_state,
                    extracted=ExtractedData(
                        company="N/A",
                        role="N/A",
                        seniority="Unknown",
                        tech_stack=[],
                    ),
                    hard_filter_result=None,
                    scoring=ScoringResult(
                        tech_stack_score=0,
                        tech_stack_reasoning="Not applicable - courtesy message",
                        salary_score=0,
                        salary_reasoning="Not applicable - courtesy message",
                        seniority_score=0,
                        seniority_reasoning="Not applicable - courtesy message",
                        company_score=0,
                        company_reasoning="Not applicable - courtesy message",
                    ),
                    ai_response="",  # No response for courtesy messages
                    processing_time_ms=processing_time_ms,
                    status="ignored",
                )

            # Handle FOLLOW_UP messages differently - skip hard filters, use FollowUpAnalyzer
            if conversation_state.state == ConversationState.FOLLOW_UP:
                return cast(
                    OpportunityResult,
                    self._handle_follow_up(
                        message=message,
                        recruiter_name=recruiter_name,
                        profile=profile,
                        profile_dict=profile_dict,
                        conversation_state=conversation_state,
                        start_time=start_time,
                        on_progress=on_progress,
                    ),
                )

            # --- Normal flow for NEW_OPPORTUNITY ---

            # Step 1: Extract structured data
            logger.debug("pipeline_step", step="analyze")
            if on_progress:
                on_progress("extracting", {"status": "started", "message": "Thinking..."})

            extracted = self.analyzer(message=message)

            if on_progress:
                on_progress("extracted", extracted.dict())

            # Step 2: Score the opportunity
            logger.debug("pipeline_step", step="score")
            if on_progress:
                on_progress("scoring", {"status": "started", "message": "Thinking..."})

            scoring = self.scorer(extracted=extracted, profile=profile)

            if on_progress:
                on_progress(
                    "scored",
                    {
                        **scoring.dict(),
                        "tech_stack_reasoning": scoring.tech_stack_reasoning,
                        "salary_reasoning": scoring.salary_reasoning,
                        "seniority_reasoning": scoring.seniority_reasoning,
                        "company_reasoning": scoring.company_reasoning,
                    },
                )

            # Step 3: Apply hard filters
            logger.debug("pipeline_step", step="hard_filters")
            if on_progress:
                on_progress("filtering", {"status": "started", "message": "Thinking..."})

            hard_filter_result = apply_hard_filters(
                extracted=extracted,
                scoring=scoring,
                raw_message=message,
                profile_dict=profile_dict,
            )

            if on_progress:
                on_progress(
                    "filtered",
                    {
                        **hard_filter_result.dict(),
                        "reasoning": hard_filter_result.reasoning,
                    },
                )

            # Determine candidate status
            candidate_status = get_candidate_status_from_profile(profile_dict)

            # Determine final status
            if hard_filter_result.should_decline:
                status = "declined"
            else:
                status = "processed"

            # Step 4: Generate response
            logger.debug("pipeline_step", step="generate_response")
            if on_progress:
                on_progress("drafting", {"status": "started", "message": "Thinking..."})

            # Use creative LM for response generation
            with dspy.context(lm=self.creative_lm):
                response = self.generator(
                    recruiter_name=recruiter_name,
                    extracted=extracted,
                    scoring=scoring,
                    candidate_name=profile.name,
                    profile=profile_dict,
                    candidate_status=candidate_status,
                    hard_filter_result=hard_filter_result,
                )

            if on_progress:
                on_progress("drafted", {"response_length": len(response)})

            # Calculate processing time
            processing_time_ms = int((time.time() - start_time) * 1000)

            # Create result
            result = OpportunityResult(
                recruiter_name=recruiter_name,
                raw_message=message,
                conversation_state=conversation_state,
                extracted=extracted,
                hard_filter_result=hard_filter_result,
                scoring=scoring,
                ai_response=response,
                processing_time_ms=processing_time_ms,
                status=status,
            )

            logger.info(
                "pipeline_success",
                conversation_state=conversation_state.state.value,
                score=scoring.total_score,
                tier=scoring.tier,
                hard_filters_passed=hard_filter_result.passed,
                failed_filters_count=len(hard_filter_result.failed_filters),
                candidate_status=candidate_status.value,
                status=status,
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

    @observe(name="dspy.pipeline.handle_follow_up")
    def _handle_follow_up(
        self,
        message: str,
        recruiter_name: str,
        profile: CandidateProfile,
        profile_dict: dict,
        conversation_state: ConversationStateResult,
        start_time: float,
        on_progress: Callable[[str, dict], None] | None = None,
    ) -> OpportunityResult:
        """
        Handle FOLLOW_UP messages with special logic.
        """
        logger.debug("pipeline_step", step="follow_up_analysis")
        if on_progress:
            on_progress("follow_up_analysis", {"status": "started"})

        # Analyze the follow-up message
        follow_up_analysis = self.follow_up_analyzer(
            message=message,
            profile_dict=profile_dict,
        )

        # Perform meaningful extraction on follow-up messages too
        logger.debug("pipeline_step", step="follow_up_extraction")
        if on_progress:
            on_progress("extracting", {"status": "started"})

        extracted = self.analyzer(message=message)

        if on_progress:
            on_progress("extracted", extracted.dict())

        # Score the opportunity based on the extracted data
        logger.debug("pipeline_step", step="follow_up_scoring")
        if on_progress:
            on_progress("scoring", {"status": "started"})

        scoring = self.scorer(extracted=extracted, profile=profile)

        if on_progress:
            on_progress("scored", scoring.dict())

        # Calculate processing time
        processing_time_ms = int((time.time() - start_time) * 1000)

        # Determine response and status based on auto-respond capability
        if follow_up_analysis.can_auto_respond and follow_up_analysis.suggested_response:
            # Auto-respond with profile-based answer
            status = "auto_responded"
            ai_response = follow_up_analysis.suggested_response
            requires_manual_review = False
            manual_review_reason = None

            logger.info(
                "pipeline_follow_up_auto_respond",
                question_type=follow_up_analysis.question_type,
                processing_time_ms=processing_time_ms,
            )
        else:
            # Requires manual review - don't generate auto response
            status = "manual_review"
            ai_response = ""  # Empty - human needs to respond
            requires_manual_review = True
            manual_review_reason = (
                f"Follow-up message requires manual review. "
                f"Question type: {follow_up_analysis.question_type or 'UNKNOWN'}. "
                f"Reason: {follow_up_analysis.reasoning}"
            )

            logger.info(
                "pipeline_follow_up_manual_review",
                question_type=follow_up_analysis.question_type,
                requires_context=follow_up_analysis.requires_context,
                reasoning=follow_up_analysis.reasoning,
                processing_time_ms=processing_time_ms,
            )

        # Create result
        result = OpportunityResult(
            recruiter_name=recruiter_name,
            raw_message=message,
            conversation_state=conversation_state,
            follow_up_analysis=follow_up_analysis,
            extracted=extracted,
            hard_filter_result=HardFilterResult.skipped(),  # Hard filters skipped for follow-ups
            scoring=scoring,
            ai_response=ai_response,
            processing_time_ms=processing_time_ms,
            status=status,
            requires_manual_review=requires_manual_review,
            manual_review_reason=manual_review_reason,
        )

        return result

    def refresh_configuration(self) -> None:
        """
        Refresh pipeline configuration from global settings.

        Call this after updating settings to ensure the pipeline uses
        the latest configuration (e.g. temperature, provider).
        """
        logger.info("refreshing_pipeline_configuration")

        # Re-initialize creative LM
        self.creative_lm = create_lm(temperature=settings.LLM_TEMPERATURE_GENERATION)

        logger.info(
            "pipeline_configuration_refreshed", creative_temp=settings.LLM_TEMPERATURE_GENERATION
        )


def create_lm(
    provider_type: str | None = None,
    model_name: str | None = None,
    max_tokens: int | None = None,
    temperature: float | None = None,
) -> dspy.LM:
    """
    Create a DSPy LM instance.

    Args:
        provider_type: LLM provider
        model_name: Model name
        max_tokens: Max tokens
        temperature: Temperature

    Returns:
        dspy.LM: Configured LM instance
    """
    provider_type = provider_type or settings.LLM_PROVIDER
    model_name = model_name or settings.LLM_MODEL
    max_tokens = max_tokens or settings.LLM_MAX_TOKENS
    temperature = temperature if temperature is not None else settings.LLM_TEMPERATURE

    if provider_type == "ollama":
        model_string = f"ollama/{model_name}"
        return dspy.LM(
            model=model_string,
            api_base=settings.OLLAMA_URL,
            api_key="ollama",
            max_tokens=max_tokens,
            temperature=temperature,
        )
    elif provider_type == "openai":
        model_string = f"openai/{model_name}"
        return dspy.LM(
            model=model_string,
            max_tokens=max_tokens,
            temperature=temperature,
        )
    elif provider_type == "anthropic":
        model_string = f"anthropic/{model_name}"
        return dspy.LM(
            model=model_string,
            max_tokens=max_tokens,
            temperature=temperature,
        )
    else:
        raise ValueError(f"Unsupported provider: {provider_type}")


def configure_dspy(
    provider_type: str | None = None,
    model_name: str | None = None,
    max_tokens: int | None = None,
    temperature: float | None = None,
) -> None:
    """
    Configure global DSPy settings.
    """
    try:
        lm = create_lm(provider_type, model_name, max_tokens, temperature)
        dspy.settings.configure(lm=lm)

        logger.info(
            "dspy_configured_successfully",
            extra={
                "provider": lm.model,
            },
        )

    except Exception as e:
        logger.error(
            "dspy_configuration_failed",
            extra={"error": str(e)},
            exc_info=True,
        )
        raise PipelineError(
            message="Failed to configure DSPy",
            details={"error": str(e)},
        ) from e


# Singleton instance (lazy initialization)
_pipeline_instance: OpportunityPipeline | None = None


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
