import asyncio
import os
import sys

import dspy
from dspy.teleprompt import BootstrapFewShot
from sqlalchemy import select

# Add app to path
sys.path.append(os.getcwd())

from app.core.config import settings
from app.database.base import AsyncSessionLocal
from app.database.models import Opportunity
from app.dspy_modules.models import CandidateProfile, ExtractedData
from app.dspy_modules.profile_loader import get_profile
from app.dspy_modules.scorer import Scorer

# Configure DSPy
dspy.settings.configure(
    lm=dspy.OpenAI(model=settings.LLM_MODEL, api_key=settings.OPENAI_API_KEY, max_tokens=2000)
)

OUTPUT_PATH = "app/dspy_modules/settings/scorer_compiled.json"


async def fetch_training_examples() -> list[dspy.Example]:
    """
    Fetch opportunities with positive feedback (score=1) and convert to DSPy examples.
    """
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Opportunity).where(Opportunity.feedback_score == 1))
        opportunities = result.scalars().all()

    print(f"Found {len(opportunities)} positive feedback examples in DB.")

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
        # Reconstruct ExtractedData from DB fields
        # Note: In a real system, we might want the exact ExtractedData payload stored in DB
        # For now, we assume the DB columns reflect the extracted data faithfully.
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
            # Note: We rely on the model generating its own reasoning,
            # or we could use feedback_notes if they contained reasoning.
        ).with_inputs("extracted", "profile")

        examples.append(example)

    return examples


def validate_score(example, pred, trace=None):
    """
    Metric to check if the predicted scores are close to the target scores.
    """
    # Allow a small margin of error or require exact match?
    # For integer scores, exact match or very close is preferred.

    def parse_score(val):
        try:
            return float(val)
        except (ValueError, TypeError):
            return 0.0

    # derived scores from prediction
    # Accessing internal fields of the prediction (which matches Signature)
    # The 'pred' object here is the result of the Scorer.forward(), which returns ScoringResult.
    # WAIT. BootstrapFewShot validation 'pred' is the return value of the module.
    # Scorer returns ScoringResult object.

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
        # print(f"Metric error: {e}")
        return False


def train_scorer(trainset: list[dspy.Example]):
    """
    Train the Scorer module.
    """
    print(f"Starting training Scorer with {len(trainset)} examples...")

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
    # 1. Get Data
    examples = await fetch_training_examples()

    if not examples:
        print("No training data found. skipping training.")
        return

    # 2. Train
    print("Compiling Scorer...")
    try:
        compiled_scorer = train_scorer(examples)

        # 3. Save
        compiled_scorer.save(OUTPUT_PATH)
        print(f"Optimized Scorer saved to {OUTPUT_PATH}")

    except Exception as e:
        print(f"Training failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
