#!/usr/bin/env python
"""
Script to optimize DSPy pipeline modules.

Usage:
    python scripts/optimize_pipeline.py --all
    python scripts/optimize_pipeline.py --module conversation_state --method bootstrap
"""
import argparse
import sys
import os

# Ensure app is in python path
sys.path.append(os.getcwd())

from dotenv import load_dotenv
load_dotenv()

from app.core.logging import get_logger
from app.dspy_modules.pipeline import configure_dspy
from app.dspy_modules.optimizer import PipelineOptimizer

logger = get_logger(__name__)


def main():
    """Run optimization pipeline."""
    parser = argparse.ArgumentParser(description="Optimize DSPy modules.")
    parser.add_argument(
        "--module",
        choices=["conversation_state", "message_analyzer", "follow_up", "all"],
        default="all",
        help="Module to optimize"
    )
    parser.add_argument(
        "--method",
        choices=["bootstrap", "mipro"],
        default="bootstrap",
        help="Optimization method"
    )
    
    args = parser.parse_args()
    
    print(f"Starting optimization for {args.module} using {args.method}...")
    
    try:
        # 1. Configure DSPy
        configure_dspy()
        
        # 2. Initialize Optimizer
        optimizer = PipelineOptimizer()
        
        # 3. Run Optimization
        if args.module == "all":
            optimizer.optimize_all(method=args.method)
        elif args.module == "conversation_state":
            optimizer.optimize_conversation_state(method=args.method)
        elif args.module == "message_analyzer":
            optimizer.optimize_message_analyzer(method=args.method)
        elif args.module == "follow_up":
            optimizer.optimize_follow_up(method=args.method)
            
        print("\nOptimization completed successfully! ✨")
        print(f"Optimized modules saved to app/dspy_modules/optimized_modules/")
        
    except Exception as e:
        print(f"\nError during optimization: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
