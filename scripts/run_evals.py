import asyncio
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from app.dspy_modules.models import CandidateProfile
from app.dspy_modules.pipeline import get_pipeline
from app.observability import observe

# Sample Data
SAMPLE_PROFILE = CandidateProfile(
    name="Sebastian Davila",
    current_seniority="Senior",
    years_of_experience=8,
    preferred_technologies=["Python", "FastAPI", "React", "AWS", "Docker"],
    minimum_salary_usd=120000,
    preferred_remote_policy="Remote",
    preferred_locations=["Remote"],
)

SAMPLE_MESSAGE = """
Hola Sebastian,

Espero que estés bien. Soy Recruiter en TechCorp.
Vi tu perfil y me impresionó tu experiencia con Python y AWS.
Estamos buscando un Senior Backend Developer para liderar nuestro equipo de plataforma.
El rol es 100% remoto, salario hasta $140k USD.
Te interesa conversar?

Saludos,
Ana
"""


def on_progress(step: str, data: dict):
    print(f"[{step.upper()}] {data}")


async def main():
    # Wrap execution in a Langfuse span using the low-level SDK if straightforward,
    # or just rely on the fact that pipeline is instrumented.
    # But since I exported @observe, let's use it to test nesting.
    await _run_evals()


@observe(name="scripts.run_evals")
async def _run_evals():
    print("Running evals with Langfuse integration...")
    print(f"Langfuse Host: {settings.LANGFUSE_HOST}")
    print(f"Langfuse Public Key: {settings.LANGFUSE_PUBLIC_KEY}")

    # Initialize pipeline (this triggers configure_dspy -> Langfuse setup)
    pipeline = get_pipeline()

    print("\nStarting pipeline execution...")
    try:
        result = pipeline.forward(
            message=SAMPLE_MESSAGE,
            recruiter_name="Ana",
            profile=SAMPLE_PROFILE,
            on_progress=on_progress,
        )

        print("\n--- Result ---")
        print(f"Status: {result.status}")
        print(f"Score: {result.scoring.total_score}")
        print(f"Response: {result.ai_response[:100]}...")

        print("\nCheck Langfuse dashboard for traces!")

    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
