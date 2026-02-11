import argparse
import asyncio
import os
import sys

import dspy
from dspy.teleprompt import BootstrapFewShot
from sqlalchemy import or_, select

# Add app to path
sys.path.append(os.getcwd())

from app.core.config import settings
from app.database.base import AsyncSessionLocal
from app.database.models import Opportunity
from app.dspy_modules.models import CandidateProfile, ExtractedData
from app.dspy_modules.profile_loader import get_profile
from app.dspy_modules.scorer import Scorer

OUTPUT_PATH = "app/dspy_modules/settings/scorer_compiled.json"


async def fetch_training_examples() -> list[dspy.Example]:
    """
    Fetch opportunities with feedback and convert to DSPy examples.

    Includes:
    - Positive Feedback (score=1): Used as standard examples
    - Negative Feedback (score=-1): Could be used with specific logic, but for BootstrapFewShot,
      we typically provide "correct" examples. If feedback is -1, it means the *system's* previous
      output was wrong.
      To use these for training, we would need the *corrected* values from the user.

      Current strategy:
      - Load POSITIVE examples (Verified Good).
      - If we had a mechanism to store "Corrected Label" along with negative feedback,
        we would use that.
      - For now, we will stick to Positive examples as "Gold Standard".
      - However, per user request, we are fetching them to at least acknowledge existence
        or potentially use them if we implement a "correction" flow later.
    """
    async with AsyncSessionLocal() as db:
        # Fetch positive (1) and explicit negative (-1)
        result = await db.execute(
            select(Opportunity).where(
                or_(Opportunity.feedback_score == 1, Opportunity.feedback_score == -1)
            )
        )
        opportunities = result.scalars().all()

    print(f"Found {len(opportunities)} feedback examples in DB.")

    # helper stats
    pos_count = sum(1 for o in opportunities if o.feedback_score == 1)
    neg_count = sum(1 for o in opportunities if o.feedback_score == -1)
    print(f"  - Positive (Thumbs Up): {pos_count}")
    print(
        f"  - Negative (Thumbs Down): {neg_count} (Skipped for training until correction logic is added)"
    )

    # Load profile (Assuming single user profile for now)
    profile = get_profile()
    if not profile:
        # Fallback mock/warning if no profile found (should not happen in prod)
        print("Warning: No profile found. Using dummy.")
        profile = CandidateProfile(
            name="User",
            preferred_technologies=["Python"],
            years_of_experience=5,
            current_seniority="Senior",
            minimum_salary_usd=50000,
        )

    examples = []
    for opp in opportunities:
        # Only use POSITIVE examples for few-shot demonstrations for now
        # because we don't know what the "Right" answer is for a negative example
        # unless the user provided it in notes (which is unstructured).
        if opp.feedback_score != 1:
            continue

        extracted = ExtractedData(
            company=opp.company,
            role=opp.role,
            seniority=opp.seniority,
            tech_stack=opp.tech_stack or [],
            salary_min=opp.salary_min,
            salary_max=opp.salary_max,
            currency=opp.currency,
            remote_policy=opp.remote_policy,
            location=opp.location,
        )

        # Create Example
        # Inputs: extracted, profile
        # Outputs: The scores we want the model to predict
        example = dspy.Example(
            extracted=extracted,
            profile=profile,
            # Target Labels (what we want the model to output)
            tech_stack_score=str(opp.tech_stack_score),
            salary_score=str(opp.salary_score),
            seniority_score=str(opp.seniority_score),
            company_score=str(opp.company_score),
        ).with_inputs("extracted", "profile")

        examples.append(example)

    return examples


def validate_score(example, pred, trace=None):
    """
    Metric to check if the predicted scores are close to the target scores.
    """

    def parse_score(val):
        try:
            return float(val)
        except (ValueError, TypeError):
            return 0.0

    try:
        # Check total score difference
        target_total = (
            parse_score(example.tech_stack_score)
            + parse_score(example.salary_score)
            + parse_score(example.seniority_score)
            + parse_score(example.company_score)
        )

        pred_total = pred.total_score

        # If total score is within 10% or 10 points
        if abs(target_total - pred_total) <= 10:
            return True

        return False

    except Exception:
        return False


def train_scorer(trainset: list[dspy.Example]):
    """
    Train the Scorer module.
    """
    print(f"Starting training Scorer with {len(trainset)} validated examples...")

    # max_bootstrapped_demos=2 means it will try to generate 2 full few-shot examples (input + thought + output)
    # matching the high quality metric.
    teleprompter = BootstrapFewShot(
        metric=validate_score, max_bootstrapped_demos=2, max_labeled_demos=2
    )

    scorer = Scorer()

    # Compile
    compiled_scorer = teleprompter.compile(scorer, trainset=trainset)

    print("Training complete.")
    return compiled_scorer


async def main():
    parser = argparse.ArgumentParser(description="Optimize DSPy Scorer Module")
    parser.add_argument("--model", type=str, help="LLM Model to use (overrides env)")
    parser.add_argument("--api-key", type=str, help="API Key (overrides env)")
    parser.add_argument("--limit", type=int, default=10, help="Limit examples (mock param for now)")

    args = parser.parse_args()

    # Resolve Configuration
    model = args.model or settings.LLM_MODEL
    api_key = args.api_key or settings.OPENAI_API_KEY

    print(f"Configuring DSPy with model: {model}")

    # Configure DSPy
    dspy.settings.configure(
        lm=dspy.OpenAI(model=model, api_key=api_key, max_tokens=settings.LLM_MAX_TOKENS)
    )

    # 1. Get Data
    examples = await fetch_training_examples()

    if not examples:
        print("No positive training data found. Skipping training.")
        return

    # 2. Train
    print("Compiling Scorer...")
    try:
        compiled_scorer = train_scorer(examples)

        # 3. Save
        # Ensure directory exists
        os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

        compiled_scorer.save(OUTPUT_PATH)
        print(f"Optimized Scorer saved to {OUTPUT_PATH}")

    except Exception as e:
        print(f"Training failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
