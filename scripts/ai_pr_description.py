#!/usr/bin/env python
"""
AI PR Description Generator.
Generates a title and description for the PR based on the diff.
"""

import argparse
import os
import sys

import dspy
from github import Auth, Github
from github.PullRequest import PullRequest
from pydantic import BaseModel

# Ensure app is in python path
sys.path.append(os.getcwd())

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


# =============================================================================
# LLM Configuration Constants
# =============================================================================

# Known OpenAI/GPT model prefixes - used to detect if we need to switch models
# when changing from OpenAI to Gemini provider
OPENAI_MODEL_PREFIXES = (
    "gpt-",
    "gpt3",
    "gpt4",
    "o1-",
    "o3-",
    "text-davinci",
    "text-curie",
    "text-babbage",
    "text-ada",
    "davinci",
    "curie",
    "babbage",
    "ada",
)

DEFAULT_GEMINI_MODEL = "models/gemini-2.0-flash"
DEFAULT_OPENAI_MODEL = "gpt-4-turbo-preview"


class PRContent(BaseModel):
    title: str
    description: str


class PRDescriber(dspy.Signature):
    """
    Generate a Pull Request title and description based on the code changes.
    The description should be structured, concise, and explain the 'why' and 'what'.
    """

    diff: str = dspy.InputField(desc="The git diff of the changes")
    context: str = dspy.InputField(desc="Context about the project")
    content: PRContent = dspy.OutputField(desc="Generated title and description")


def get_pr_diff(pr: PullRequest) -> str:
    """Get the formatted diff of the PR."""
    diffs = []
    for file in pr.get_files():
        if file.status == "removed":
            diffs.append(f"File: {file.filename}\nStatus: {file.status}\n(File deleted)\n")
            continue

        # Limit context for large files? For now just take the patch
        patch = file.patch or "(No patch available)"
        diffs.append(f"File: {file.filename}\nStatus: {file.status}\nPatch:\n{patch}\n")

    return "\n---\n".join(diffs)


def configure_llm():
    """
    Configure DSPy with the environment's LLM provider.

    Provider Selection Priority (in order):
    1. If LLM_PROVIDER=gemini AND GEMINI_API_KEY exists → Use Gemini
    2. If GEMINI_API_KEY exists AND no OPENAI_API_KEY → Use Gemini (auto-detect)
    3. If GEMINI_API_KEY exists AND LLM_PROVIDER is not openai/anthropic → Use Gemini
    4. Otherwise → Fall back to OpenAI or Anthropic based on available keys

    Model Selection for Gemini:
    - If current model looks like a GPT/OpenAI model, switch to Gemini default
    - If model doesn't contain 'gemini', switch to Gemini default
    """
    # Read configuration from environment
    gemini_key = os.getenv("GEMINI_API_KEY")
    provider = os.getenv("LLM_PROVIDER", settings.LLM_PROVIDER)
    model = os.getenv("LLM_MODEL", settings.LLM_MODEL)
    has_openai = bool(os.getenv("OPENAI_API_KEY"))

    # --- Provider Selection Logic ---
    # Determine if we should use Gemini based on priority rules
    use_gemini = False

    # Priority 1: Explicit provider=gemini with valid key
    if provider == "gemini" and gemini_key:
        use_gemini = True
        logger.debug("llm_selection", reason="explicit_gemini_provider")

    # Priority 2: Gemini key exists but no OpenAI key (auto-detect)
    elif gemini_key and not has_openai:
        use_gemini = True
        logger.debug("llm_selection", reason="gemini_key_available_no_openai")

    # Priority 3: Gemini key exists and provider is not explicitly openai/anthropic
    elif gemini_key and provider not in ["openai", "anthropic"]:
        use_gemini = True
        logger.debug("llm_selection", reason="gemini_key_with_unknown_provider")

    # --- Configure Gemini ---
    if use_gemini:
        target_model = model

        # Check if current model is an OpenAI model (needs switching to Gemini)
        is_openai_model = (
            not target_model
            or target_model.lower().startswith(OPENAI_MODEL_PREFIXES)
            or "gemini" not in target_model.lower()
        )

        if is_openai_model:
            logger.debug(
                "llm_model_switch",
                from_model=target_model,
                to_model=DEFAULT_GEMINI_MODEL,
                reason="incompatible_model_for_gemini",
            )
            target_model = DEFAULT_GEMINI_MODEL

        print(f"Configuring AI Describer with Gemini ({target_model})")

        # Normalize model name for DSPy (needs gemini/ prefix)
        final_model_name = target_model
        if not final_model_name.startswith("gemini/") and "gemini" in final_model_name:
            final_model_name = "gemini/" + final_model_name.replace("models/", "")

        lm = dspy.LM(model=final_model_name, api_key=gemini_key)
        dspy.settings.configure(lm=lm)
        logger.info("llm_configured", provider="gemini", model=final_model_name)
        return

    # --- Fallback: OpenAI or Anthropic ---
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")

    if not api_key:
        print("Warning: No API Key found for AI Describer")
        logger.warning("llm_no_api_key", provider=provider)

    print(f"Configuring AI Describer with {provider}/{model}")

    final_model_name = model
    if provider == "openai":
        final_model_name = f"openai/{model}"
        lm = dspy.LM(model=final_model_name, api_key=os.getenv("OPENAI_API_KEY"), max_tokens=2000)
    elif provider == "anthropic":
        final_model_name = f"anthropic/{model}"
        lm = dspy.LM(
            model=final_model_name, api_key=os.getenv("ANTHROPIC_API_KEY"), max_tokens=2000
        )
    else:
        # Final fallback when no valid provider configured
        logger.warning("llm_fallback_to_default", original_provider=provider)
        final_model_name = f"openai/{DEFAULT_OPENAI_MODEL}"
        lm = dspy.LM(model=final_model_name, max_tokens=2000)

    dspy.settings.configure(lm=lm)
    logger.info("llm_configured", provider=provider, model=final_model_name)


def main():
    parser = argparse.ArgumentParser(description="AI PR Description Generator")
    parser.add_argument("--pr", type=int, required=True, help="PR Number")
    parser.add_argument(
        "--repo",
        type=str,
        default=os.getenv("GITHUB_REPOSITORY"),
        help="Repository name (owner/repo)",
    )
    args = parser.parse_args()

    token = os.getenv("GITHUB_TOKEN")
    if not token or not args.repo:
        print("Error: GITHUB_TOKEN or repo name missing")
        sys.exit(1)

    gh = Github(auth=Auth.Token(token))
    try:
        repo = gh.get_repo(args.repo)
        pr = repo.get_pull(args.pr)
    except Exception as e:
        print(f"Error fetching PR: {e}")
        sys.exit(1)

    print(f"Generating description for PR #{args.pr}...")

    diff_content = get_pr_diff(pr)
    if not diff_content:
        print("No changes found to describe.")
        sys.exit(0)

    # Configure AI
    configure_llm()
    describer = dspy.Predict(PRDescriber)

    # Retry logic for RateLimitError
    max_retries = 3
    base_delay = 2

    # Truncate diff if too long to save tokens
    max_diff_length = 20000  # Approx 5k-6k tokens
    if len(diff_content) > max_diff_length:
        print(
            f"Warning: Diff is too large ({len(diff_content)} chars). Truncating to {max_diff_length} chars."
        )
        diff_content = diff_content[:max_diff_length] + "\n... (Diff truncated) ..."

    for attempt in range(max_retries):
        try:
            print(f"Generating description (Attempt {attempt + 1}/{max_retries})...")
            result = describer(
                diff=diff_content, context="Python project using FastAPI, DSPy, SqlAlchemy"
            )
            content = result.content
            break
        except Exception as e:
            # Check for rate limit error in string representation or type
            error_str = str(e).lower()
            if (
                "ratelimit" in error_str
                or "quota" in error_str
                or "429" in error_str
                or "resource_exhausted" in error_str
            ):
                if attempt < max_retries - 1:
                    delay = base_delay * (2**attempt) + (
                        0.1 * attempt
                    )  # Exponential backoff + jitter
                    print(f"Rate limit hit. Retrying in {delay}s...")
                    import time

                    time.sleep(delay)
                    continue

            # If not rate limit or retries exhausted, re-raise
            print(f"AI Description generation failed: {e}")
            sys.exit(1)

    try:
        print(f"Generated Title: {content.title}")

        # Update PR
        pr.edit(title=content.title, body=content.description)
        print("PR updated successfully.")

    except Exception as e:
        print(f"Failed to update PR: {e}")
        print("Continuing without updating PR description (Soft Fail).")
        sys.exit(0)


if __name__ == "__main__":
    main()
