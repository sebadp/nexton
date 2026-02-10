---
name: Walkthrough Best Practices
description: Guidelines for creating high-quality, consistent walkthroughs, emphasizing the use of Makefile commands.
---

# Walkthrough Best Practices

When creating `walkthrough.md` artifacts or explaining steps to the user:

## 1. Prioritize Makefile Commands
Always check the `Makefile` for existing commands before using raw `docker-compose`, `poetry`, or shell commands.
- **Good:** `make up`, `make logs`, `make test`
- **Bad:** `docker-compose up -d`, `docker-compose logs -f app`, `pytest tests/`

## 2. Suggest New Make Commands
If you find yourself writing a complex or repetitive command that isn't in the `Makefile`, you **MUST** suggest adding it to the `Makefile` as part of your task.
- Example: If you need to run a specific eval script often, suggest adding `run-evals: ## Run evals\n\tdocker-compose exec app python scripts/run_evals.py`.

## 3. Structure
- **Prerequisites**: What is needed before starting (env vars, tools).
- **Steps**: Clear, numbered steps using `make` commands.
- **Verification**: How to confirm success.
- **Troubleshooting**: Common issues and fixes.
