"""
DSPy Optimizer Module.

This module handles the optimization of DSPy modules using BootstrapFewShot
and MIPROv2 optimizers. It manages the training process and saving/loading
of optimized modules.
"""
import os
import dspy
from dspy.teleprompt import BootstrapFewShot, MIPROv2

from app.core.logging import get_logger
from app.dspy_modules.metrics import (
    validate_conversation_state,
    validate_message_analysis,
    validate_follow_up,
)
from app.dspy_modules.training_data import (
    conversation_state_trainset,
    message_analysis_trainset,
    follow_up_trainset,
)
from app.dspy_modules.pipeline import OpportunityPipeline

logger = get_logger(__name__)

# Directory to save optimized modules
OPTIMIZED_DIR = os.path.join(os.path.dirname(__file__), "optimized_modules")


class PipelineOptimizer:
    """Manages optimization of pipeline modules."""

    def __init__(self):
        """Initialize the optimizer manager."""
        self._ensure_optimized_dir()

    def _ensure_optimized_dir(self):
        """Ensure the optimized modules directory exists."""
        if not os.path.exists(OPTIMIZED_DIR):
            os.makedirs(OPTIMIZED_DIR)

    def optimize_conversation_state(self, method="bootstrap"):
        """
        Optimize the ConversationStateAnalyzer.
        
        Args:
            method: 'bootstrap' (BootstrapFewShot) or 'mipro' (MIPROv2)
        """
        logger.info(f"Optimizing ConversationStateAnalyzer using {method}...")
        
        # Instantiate a fresh pipeline to get the module
        pipeline = OpportunityPipeline()
        module = pipeline.conversation_state_analyzer
        
        if method == "bootstrap":
            optimizer = BootstrapFewShot(
                metric=validate_conversation_state,
                max_bootstrapped_demos=4,
                max_labeled_demos=4,
            )
        elif method == "mipro":
            optimizer = MIPROv2(
                metric=validate_conversation_state,
                auto="light",
                num_threads=4, # Adjust based on rate limits
            )
        else:
            raise ValueError(f"Unknown optimization method: {method}")

        compiled_module = optimizer.compile(
            module,
            trainset=conversation_state_trainset,
        )
        
        save_path = os.path.join(OPTIMIZED_DIR, "conversation_state_analyzer.json")
        compiled_module.save(save_path)
        logger.info(f"Saved optimized ConversationStateAnalyzer to {save_path}")
        return compiled_module

    def optimize_message_analyzer(self, method="bootstrap"):
        """Optimize the MessageAnalyzer."""
        logger.info(f"Optimizing MessageAnalyzer using {method}...")
        
        pipeline = OpportunityPipeline()
        module = pipeline.analyzer
        
        if method == "bootstrap":
            optimizer = BootstrapFewShot(
                metric=validate_message_analysis,
                max_bootstrapped_demos=2, # Less demos for complex extraction
                max_labeled_demos=2,
            )
        elif method == "mipro":
            optimizer = MIPROv2(
                metric=validate_message_analysis,
                auto="light",
            )
        
        compiled_module = optimizer.compile(
            module,
            trainset=message_analysis_trainset,
        )
        
        save_path = os.path.join(OPTIMIZED_DIR, "message_analyzer.json")
        compiled_module.save(save_path)
        logger.info(f"Saved optimized MessageAnalyzer to {save_path}")
        return compiled_module

    def optimize_follow_up(self, method="bootstrap"):
        """Optimize the FollowUpAnalyzer."""
        logger.info(f"Optimizing FollowUpAnalyzer using {method}...")
        
        pipeline = OpportunityPipeline()
        module = pipeline.follow_up_analyzer
        
        if method == "bootstrap":
            optimizer = BootstrapFewShot(
                metric=validate_follow_up,
                max_bootstrapped_demos=4,
                max_labeled_demos=4,
            )
        
        compiled_module = optimizer.compile(
            module,
            trainset=follow_up_trainset,
        )
        
        save_path = os.path.join(OPTIMIZED_DIR, "follow_up_analyzer.json")
        compiled_module.save(save_path)
        logger.info(f"Saved optimized FollowUpAnalyzer to {save_path}")
        return compiled_module

    def optimize_all(self, method="bootstrap"):
        """Optimize all supported modules."""
        self.optimize_conversation_state(method)
        self.optimize_message_analyzer(method)
        self.optimize_follow_up(method)
        logger.info("All modules optimized successfully.")

