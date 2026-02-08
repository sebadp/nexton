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
    """Configure DSPy with the environment's LLM provider."""
    # Prioritize Gemini if key is present, or check LLM_PROVIDER
    gemini_key = os.getenv("GEMINI_API_KEY")
    provider = os.getenv("LLM_PROVIDER", settings.LLM_PROVIDER)
    model = os.getenv("LLM_MODEL", settings.LLM_MODEL)

    # Determine which provider to use
    has_openai = bool(os.getenv("OPENAI_API_KEY"))

    use_gemini = False
    if provider == "gemini" and gemini_key:
        use_gemini = True
    elif gemini_key and not has_openai:
        use_gemini = True
    elif gemini_key and provider not in ["openai", "anthropic"]:
        # If provider is unset or unknown, and we have a gemini key, prefer it
        use_gemini = True

    if use_gemini:
        # Sanitize model: if it looks like a GPT model or is missing, default to a safe Gemini model
        target_model = model
        if not target_model or target_model.startswith("gpt") or "gemini" not in target_model:
            target_model = "models/gemini-2.0-flash"

        print(f"Configuring AI Describer with Gemini ({target_model})")

        final_model_name = target_model
        if not final_model_name.startswith("gemini/") and "gemini" in final_model_name:
            final_model_name = "gemini/" + final_model_name.replace("models/", "")

        lm = dspy.LM(model=final_model_name, api_key=gemini_key)
        dspy.settings.configure(lm=lm)
        return

    # Fallback to other providers
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")

    if not api_key:
        print("Warning: No API Key found for AI Describer")

    print(f"Configuring AI Describer with {provider}/{model}")

    if provider == "openai":
        lm = dspy.LM(model=f"openai/{model}", api_key=os.getenv("OPENAI_API_KEY"), max_tokens=2000)
    elif provider == "anthropic":
        lm = dspy.LM(
            model=f"anthropic/{model}", api_key=os.getenv("ANTHROPIC_API_KEY"), max_tokens=2000
        )
    else:
        lm = dspy.LM(model="openai/gpt-4-turbo-preview", max_tokens=2000)

    dspy.settings.configure(lm=lm)


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

    try:
        result = describer(
            diff=diff_content, context="Python project using FastAPI, DSPy, SqlAlchemy"
        )
        content = result.content

        print(f"Generated Title: {content.title}")

        # Update PR
        # Only update if description is empty or user requested it?
        # For now, we will append or just overwrite title + body.
        # Let's overwrite title if strictly better, but maybe just set it if it's default?
        # Safe bet: Update body, suggest title in body?
        # Requirement: "make the agent generate a description".

        pr.edit(title=content.title, body=content.description)
        print("PR updated successfully.")

    except Exception as e:
        print(f"AI Description generation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
