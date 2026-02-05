#!/usr/bin/env python
"""
AI PR Reviewer Script.
Analyzes the PR diff and posts comments on GitHub.
"""

import argparse
import os
import sys

import dspy
from github import Github
from github.PullRequest import PullRequest
from pydantic import BaseModel

# Ensure app is in python path
sys.path.append(os.getcwd())

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class PRCorrection(BaseModel):
    file_path: str
    line_number: int
    comment: str
    suggestion: str | None = None
    severity: str  # 'info', 'warning', 'critical'


class ReviewResult(BaseModel):
    summary: str
    corrections: list[PRCorrection]


class CodeReviewer(dspy.Signature):
    """
    Review code changes in a Pull Request.
    Focus on:
    1. Bugs and potential runtime errors
    2. Security vulnerabilities
    3. Performance issues
    4. Code style and best practices (PEP 8, clean code)
    5. Type safety issues

    Provide specific, actionable feedback.
    """

    diff: str = dspy.InputField(desc="The git diff of the changes")
    file_context: str = dspy.InputField(desc="Context about the files being changed")
    review: ReviewResult = dspy.OutputField(desc="Structured review comments")


def get_pr_diff(pr: PullRequest) -> str:
    """Get the formatted diff of the PR."""
    diffs = []
    for file in pr.get_files():
        if file.status == "removed" or not file.filename.endswith(".py"):
            continue

        diffs.append(f"File: {file.filename}\nStatus: {file.status}\nPatch:\n{file.patch}\n")

    return "\n---\n".join(diffs)


def configure_llm():
    """Configure DSPy with the environment's LLM provider."""
    provider = os.getenv("LLM_PROVIDER", settings.LLM_PROVIDER)
    model = os.getenv("LLM_MODEL", settings.LLM_MODEL)
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")

    # Fallback if config.py settings are empty/default in CI env
    if not api_key:
        print("Warning: No API Key found for AI Reviewer")

    print(f"Configuring AI Reviewer with {provider}/{model}")

    if provider == "openai":
        lm = dspy.LM(model=f"openai/{model}", api_key=os.getenv("OPENAI_API_KEY"), max_tokens=2000)
    elif provider == "anthropic":
        lm = dspy.LM(
            model=f"anthropic/{model}", api_key=os.getenv("ANTHROPIC_API_KEY"), max_tokens=2000
        )
    else:
        # Default or fallback
        lm = dspy.LM(model="openai/gpt-4-turbo-preview", max_tokens=2000)

    dspy.settings.configure(lm=lm)


def main():
    parser = argparse.ArgumentParser(description="AI PR Reviewer")
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

    gh = Github(token)
    try:
        repo = gh.get_repo(args.repo)
        pr = repo.get_pull(args.pr)
    except Exception as e:
        print(f"Error fetching PR: {e}")
        sys.exit(1)

    print(f"Analyzing PR #{args.pr}: {pr.title}")

    diff_content = get_pr_diff(pr)
    if not diff_content:
        print("No python changes found to review.")
        sys.exit(0)

    # Configure AI
    configure_llm()
    reviewer = dspy.Predict(CodeReviewer)

    try:
        result = reviewer(
            diff=diff_content, file_context="Python project using FastAPI, DSPy, SqlAlchemy"
        )
        review_data = result.review

        # Post summary comment
        summary_body = f"## 🤖 AI Review Summary\n\n{review_data.summary}\n\n"
        pr.create_issue_comment(summary_body)

        # Post inline comments (this is tricky with just 'patch', need position mapping)
        # For simplicity in V1, we will post all findings as a checklist in the main comment
        # because mapping patch lines to PR position requires more logic.

        findings_body = "### 🔍 Findings\n\n"
        for correction in review_data.corrections:
            icon = (
                "🔴"
                if correction.severity == "critical"
                else "⚠️"
                if correction.severity == "warning"
                else "ℹ️"
            )
            findings_body += f"- {icon} **{correction.file_path}**: {correction.comment}\n"
            if correction.suggestion:
                findings_body += f"  ```python\n  {correction.suggestion}\n  ```\n"

        pr.create_issue_comment(findings_body)
        print("Review posted successfully.")

    except Exception as e:
        print(f"AI Review failed: {e}")
        # Don't fail the CI job, just log error
        sys.exit(0)


if __name__ == "__main__":
    main()
