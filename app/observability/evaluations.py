"""
LLM output evaluations and dataset management using Langfuse.

This module provides helpers for:
- Scoring LLM outputs for quality evaluation
- Creating datasets for fine-tuning and evaluation
- Running batch evaluations

References:
- https://langfuse.com/docs/scores
- https://langfuse.com/docs/datasets
"""
from typing import Any, Optional

from app.core.config import settings
from app.core.logging import get_logger
from app.observability.langfuse_setup import get_langfuse_client, is_langfuse_enabled

logger = get_logger(__name__)


# ==========================================
# SCORING FUNCTIONS
# ==========================================

async def score_trace(
    trace_id: str,
    name: str,
    value: float,
    comment: Optional[str] = None,
    data_type: str = "NUMERIC",
) -> bool:
    """
    Add a score to a specific Langfuse trace by ID.
    
    Use this for async scoring after pipeline completion.
    
    Args:
        trace_id: Langfuse trace ID
        name: Score name (e.g., "quality", "relevance", "accuracy")
        value: Score value (0.0 to 1.0 for NUMERIC, or any value for other types)
        comment: Optional explanation
        data_type: Score type (NUMERIC, BOOLEAN, CATEGORICAL)
    
    Returns:
        True if score was added, False otherwise
    
    Example:
        await score_trace(
            trace_id="tr-abc123",
            name="user_feedback",
            value=1.0,
            comment="User approved the response"
        )
    """
    if not is_langfuse_enabled():
        return False
        
    langfuse = get_langfuse_client()
    if not langfuse:
        return False
    
    try:
        langfuse.score(
            trace_id=trace_id,
            name=name,
            value=value,
            comment=comment,
            data_type=data_type,
        )
        logger.debug("langfuse_trace_scored", trace_id=trace_id, name=name, value=value)
        return True
    except Exception as e:
        logger.warning("langfuse_score_failed", trace_id=trace_id, error=str(e))
        return False


async def score_opportunity(
    trace_id: str,
    total_score: int,
    tier: str,
    status: str,
) -> bool:
    """
    Score an opportunity trace with standard metrics.
    
    Args:
        trace_id: Langfuse trace ID
        total_score: Opportunity score (0-100)
        tier: Tier classification (HIGH_PRIORITY, INTERESANTE, etc.)
        status: Processing status
    
    Returns:
        True if all scores were added
    """
    if not is_langfuse_enabled():
        return False
    
    success = True
    
    # Score the overall opportunity score (normalized to 0-1)
    success &= await score_trace(
        trace_id=trace_id,
        name="opportunity_score",
        value=total_score / 100.0,
        comment=f"Tier: {tier}, Status: {status}",
    )
    
    # Categorical tier score
    success &= await score_trace(
        trace_id=trace_id,
        name="opportunity_tier",
        value=["NO_INTERESA", "POCO_INTERESANTE", "INTERESANTE", "HIGH_PRIORITY"].index(tier) if tier in ["NO_INTERESA", "POCO_INTERESANTE", "INTERESANTE", "HIGH_PRIORITY"] else 0,
        comment=tier,
        data_type="CATEGORICAL",
    )
    
    return success


# ==========================================
# DATASET FUNCTIONS
# ==========================================

async def create_dataset(
    name: str,
    description: Optional[str] = None,
) -> bool:
    """
    Create a new Langfuse dataset.
    
    Args:
        name: Dataset name (unique identifier)
        description: Optional description
    
    Returns:
        True if created, False otherwise
    """
    if not is_langfuse_enabled():
        return False
    
    langfuse = get_langfuse_client()
    if not langfuse:
        return False
    
    try:
        langfuse.create_dataset(
            name=name,
            description=description,
        )
        logger.info("langfuse_dataset_created", name=name)
        return True
    except Exception as e:
        logger.warning("langfuse_dataset_creation_failed", name=name, error=str(e))
        return False


async def add_dataset_item(
    dataset_name: str,
    input_data: dict,
    expected_output: Optional[dict] = None,
    metadata: Optional[dict] = None,
) -> bool:
    """
    Add an item to a Langfuse dataset.
    
    Use this to build datasets for:
    - Evaluation benchmarks
    - Fine-tuning data
    - Regression testing
    
    Args:
        dataset_name: Name of the dataset
        input_data: Input data (e.g., {"message": "...", "recruiter": "..."})
        expected_output: Expected output (e.g., {"score": 85, "tier": "HIGH_PRIORITY"})
        metadata: Additional metadata
    
    Returns:
        True if added, False otherwise
    
    Example:
        await add_dataset_item(
            dataset_name="opportunity_evaluation",
            input_data={
                "message": "Senior Python role at Google...",
                "recruiter_name": "John Doe",
            },
            expected_output={
                "tier": "HIGH_PRIORITY",
                "score_min": 80,
            },
        )
    """
    if not is_langfuse_enabled():
        return False
    
    langfuse = get_langfuse_client()
    if not langfuse:
        return False
    
    try:
        langfuse.create_dataset_item(
            dataset_name=dataset_name,
            input=input_data,
            expected_output=expected_output,
            metadata=metadata,
        )
        logger.debug("langfuse_dataset_item_added", dataset=dataset_name)
        return True
    except Exception as e:
        logger.warning("langfuse_dataset_item_failed", dataset=dataset_name, error=str(e))
        return False


async def add_opportunity_to_dataset(
    dataset_name: str,
    recruiter_name: str,
    raw_message: str,
    expected_tier: Optional[str] = None,
    expected_score_range: Optional[tuple[int, int]] = None,
) -> bool:
    """
    Add an opportunity example to a dataset for evaluation.
    
    Args:
        dataset_name: Dataset name
        recruiter_name: Recruiter name
        raw_message: Raw LinkedIn message
        expected_tier: Expected tier classification
        expected_score_range: Expected score range (min, max)
    
    Returns:
        True if added, False otherwise
    """
    input_data = {
        "recruiter_name": recruiter_name,
        "raw_message": raw_message,
    }
    
    expected_output = {}
    if expected_tier:
        expected_output["tier"] = expected_tier
    if expected_score_range:
        expected_output["score_min"] = expected_score_range[0]
        expected_output["score_max"] = expected_score_range[1]
    
    return await add_dataset_item(
        dataset_name=dataset_name,
        input_data=input_data,
        expected_output=expected_output if expected_output else None,
    )
