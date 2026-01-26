"""
Langfuse integration for DSPy observability.

Uses OpenInference instrumentation for automatic trace capture of all DSPy LM calls.
This integration is optional and can be enabled via LANGFUSE_ENABLED=true.

References:
- https://langfuse.com/docs/integrations/dspy
- https://pypi.org/project/openinference-instrumentation-dspy/
"""
import os
from typing import Optional

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_initialized = False
_langfuse_client = None


def setup_langfuse() -> bool:
    """
    Initialize Langfuse instrumentation for DSPy.
    
    This function:
    1. Checks if Langfuse is enabled via settings
    2. Sets up environment variables for the Langfuse client
    3. Initializes the DSPyInstrumentor for automatic trace capture
    
    Returns:
        True if initialized successfully, False if disabled or failed
    
    Example:
        # In your pipeline initialization:
        from app.observability.langfuse_setup import setup_langfuse
        setup_langfuse()  # Now all DSPy calls are traced
    """
    global _initialized, _langfuse_client
    
    if _initialized:
        return True
        
    if not settings.LANGFUSE_ENABLED:
        logger.debug("langfuse_disabled")
        return False
        
    if not settings.LANGFUSE_PUBLIC_KEY or not settings.LANGFUSE_SECRET_KEY:
        logger.warning(
            "langfuse_missing_keys",
            hint="Set LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY to enable Langfuse"
        )
        return False
    
    try:
        # Set environment variables for Langfuse client
        os.environ["LANGFUSE_PUBLIC_KEY"] = settings.LANGFUSE_PUBLIC_KEY
        os.environ["LANGFUSE_SECRET_KEY"] = settings.LANGFUSE_SECRET_KEY
        os.environ["LANGFUSE_HOST"] = settings.LANGFUSE_HOST
        
        # Initialize Langfuse client
        from langfuse import get_client
        _langfuse_client = get_client()
        
        # Verify connection
        if not _langfuse_client.auth_check():
            logger.error(
                "langfuse_auth_failed",
                host=settings.LANGFUSE_HOST,
                hint="Check your API keys and host URL"
            )
            return False
        
        # Instrument DSPy - this captures ALL LM calls automatically
        from openinference.instrumentation.dspy import DSPyInstrumentor
        DSPyInstrumentor().instrument()
        
        _initialized = True
        logger.info(
            "langfuse_initialized",
            host=settings.LANGFUSE_HOST,
        )
        return True
        
    except ImportError as e:
        logger.debug(
            "langfuse_not_installed",
            error=str(e),
            hint="Install with: pip install langfuse openinference-instrumentation-dspy"
        )
        return False
    except Exception as e:
        logger.error("langfuse_setup_failed", error=str(e))
        return False


def get_langfuse_client():
    """
    Get the Langfuse client instance.
    
    Returns:
        Langfuse client or None if not initialized
    """
    global _langfuse_client
    return _langfuse_client


def is_langfuse_enabled() -> bool:
    """Check if Langfuse is enabled and initialized."""
    return _initialized


# ==========================================
# PHASE 2: Trace Enrichment Helpers
# ==========================================

def trace_pipeline_execution(
    recruiter_name: str,
    message_length: int,
    profile_name: str,
    tags: list[str] = None,
):
    """
    Context manager for enriching pipeline traces with metadata.
    
    Args:
        recruiter_name: Name of the recruiter
        message_length: Length of the message
        profile_name: Candidate profile name
        tags: Optional list of tags
    
    Example:
        with trace_pipeline_execution("John Doe", 150, "Sebastian"):
            result = pipeline.forward(...)
    """
    if not _initialized or not _langfuse_client:
        # Return a no-op context manager
        from contextlib import nullcontext
        return nullcontext()
    
    try:
        from langfuse import propagate_attributes
        return propagate_attributes(
            user_id=recruiter_name,
            metadata={
                "message_length": message_length,
                "profile_name": profile_name,
            },
            tags=tags or ["pipeline", "opportunity"],
        )
    except ImportError:
        from contextlib import nullcontext
        return nullcontext()


def score_current_trace(
    name: str,
    value: float,
    comment: str = None,
) -> bool:
    """
    Add a score to the current Langfuse trace.
    
    Args:
        name: Score name (e.g., "opportunity_score", "quality")
        value: Score value (0.0 to 1.0)
        comment: Optional comment explaining the score
    
    Returns:
        True if score was added, False otherwise
    
    Example:
        score_current_trace(
            name="opportunity_score",
            value=0.85,
            comment="Tier: HIGH_PRIORITY"
        )
    """
    if not _initialized or not _langfuse_client:
        return False
    
    try:
        _langfuse_client.score_current_trace(
            name=name,
            value=value,
            comment=comment,
        )
        return True
    except Exception as e:
        logger.debug("langfuse_score_failed", error=str(e))
        return False


def update_current_trace(
    input_data: dict = None,
    output_data: dict = None,
    metadata: dict = None,
) -> bool:
    """
    Update the current trace with additional data.
    
    Args:
        input_data: Input data to add to trace
        output_data: Output data to add to trace
        metadata: Additional metadata
    
    Returns:
        True if updated, False otherwise
    """
    if not _initialized or not _langfuse_client:
        return False
    
    try:
        _langfuse_client.update_current_trace(
            input=input_data,
            output=output_data,
            metadata=metadata,
        )
        return True
    except Exception as e:
        logger.debug("langfuse_update_failed", error=str(e))
        return False


def flush_langfuse() -> bool:
    """
    Flush pending Langfuse events.
    
    Important for short-lived processes or scripts.
    
    Returns:
        True if flushed, False otherwise
    """
    if not _initialized or not _langfuse_client:
        return False
    
    try:
        _langfuse_client.flush()
        return True
    except Exception as e:
        logger.debug("langfuse_flush_failed", error=str(e))
        return False
