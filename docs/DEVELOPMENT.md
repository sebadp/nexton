# Development Guide - LinkedIn AI Agent

Complete guide for developers working on the LinkedIn AI Agent platform.

## Table of Contents

- [Getting Started](#getting-started)
- [Development Environment](#development-environment)
- [Project Structure](#project-structure)
- [Development Workflow](#development-workflow)
- [Code Style](#code-style)
- [Testing](#testing)
- [Debugging](#debugging)
- [Common Tasks](#common-tasks)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

---

## Getting Started

### Prerequisites

- **Python 3.11+**
- **Docker & Docker Compose**
- **Git**
- **IDE**: VSCode (recommended) or PyCharm
- **8GB+ RAM** recommended

### Initial Setup

1. **Clone repository**
```bash
git clone https://github.com/yourusername/linkedin-agent.git
cd linkedin-agent
```

2. **Install dependencies**

Option A: Using requirements.txt (recommended)
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

Option B: Using Poetry
```bash
poetry install
poetry shell
```

3. **Setup environment**
```bash
cp .env.example .env
# Edit .env with your local settings
```

4. **Start services**
```bash
docker-compose up -d postgres redis ollama
```

5. **Run migrations**
```bash
alembic upgrade head
```

6. **Verify setup**
```bash
python -m pytest tests/
```

---

## Development Environment

### Recommended VSCode Extensions

```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.vscode-pylance",
    "ms-python.black-formatter",
    "charliermarsh.ruff",
    "ms-azuretools.vscode-docker",
    "tamasfe.even-better-toml",
    "redhat.vscode-yaml"
  ]
}
```

### VSCode Settings

`.vscode/settings.json`:
```json
{
  "python.defaultInterpreterPath": "./venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  },
  "[python]": {
    "editor.defaultFormatter": "ms-python.black-formatter",
    "editor.formatOnSave": true
  }
}
```

### Environment Variables

Key variables for development:

```bash
# Application
ENV=development
LOG_LEVEL=DEBUG

# Database (local)
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/linkedin_agent

# Redis (local)
REDIS_URL=redis://localhost:6379/0

# Ollama (local)
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama2

# Celery (NEW)
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
CELERY_WORKER_CONCURRENCY=4

# LinkedIn Scraper (NEW)
LINKEDIN_EMAIL=your@email.com
LINKEDIN_PASSWORD=your-password
SCRAPER_HEADLESS=true
SCRAPER_MAX_REQUESTS_PER_MINUTE=10
SCRAPER_MIN_DELAY_SECONDS=3.0
COOKIES_PATH=data/cookies.json

# Profile
PROFILE_PATH=config/profile.yaml
```

---

## Project Structure

```
linkedin-agent/
├── app/                          # Application code
│   ├── __init__.py
│   ├── main.py                  # FastAPI entry point
│   ├── api/                     # REST API
│   │   ├── __init__.py
│   │   ├── dependencies.py      # API dependencies
│   │   └── v1/                  # API version 1
│   │       ├── __init__.py
│   │       ├── health.py        # Health check endpoints
│   │       ├── opportunities.py # Opportunity endpoints
│   │       └── schemas.py       # Pydantic schemas
│   ├── core/                    # Core utilities
│   │   ├── __init__.py
│   │   ├── config.py            # Settings (Pydantic)
│   │   ├── logging.py           # Structured logging
│   │   └── exceptions.py        # Custom exceptions
│   ├── database/                # Database layer
│   │   ├── __init__.py
│   │   ├── base.py              # SQLAlchemy setup
│   │   ├── models.py            # ORM models
│   │   ├── repositories.py      # Repository pattern
│   │   ├── dependencies.py      # DB dependencies
│   │   └── migrations/          # Alembic migrations
│   ├── dspy_modules/            # DSPy AI pipeline
│   │   ├── __init__.py
│   │   ├── models.py            # Pydantic models
│   │   ├── signatures.py        # DSPy signatures
│   │   ├── message_analyzer.py  # Extraction module
│   │   ├── scorer.py            # Scoring module
│   │   ├── response_generator.py# Response generation
│   │   ├── pipeline.py          # Pipeline orchestration
│   │   └── profile_loader.py    # Profile loading
│   ├── scraper/                 # LinkedIn scraper (NEW)
│   │   ├── __init__.py
│   │   ├── linkedin_scraper.py  # Main scraper with Playwright
│   │   ├── session_manager.py   # Session & cookie management
│   │   └── rate_limiter.py      # Rate limiting (adaptive)
│   └── tasks/                   # Background jobs (NEW)
│       ├── __init__.py
│       ├── celery_app.py        # Celery configuration
│       ├── scraping_tasks.py    # Scraping tasks
│       ├── processing_tasks.py  # Message processing tasks
│       └── monitoring_tasks.py  # Health check tasks
├── tests/                       # Test suite
│   ├── __init__.py
│   ├── conftest.py             # Pytest fixtures
│   ├── unit/                   # Unit tests
│   └── integration/            # Integration tests
├── config/                      # Configuration files
│   └── profile.yaml            # Candidate profile
├── infrastructure/              # Infrastructure as Code
│   ├── docker/
│   │   ├── Dockerfile           # Main app Dockerfile
│   │   └── Dockerfile.playwright# Scraper Dockerfile (NEW)
│   └── scripts/
│       └── health_check.sh
├── scripts/                     # Utility scripts
│   ├── start.sh
│   ├── run_tests.sh
│   └── scrape_linkedin.py       # Scraper script (NEW)
├── docs/                        # Documentation
│   ├── README.md
│   ├── API.md
│   ├── DEVELOPMENT.md
│   └── SCRAPER.md               # Scraper guide (NEW)
├── pyproject.toml              # Project metadata
├── requirements.txt            # Python dependencies
├── requirements-dev.txt        # Dev dependencies
├── pytest.ini                  # Pytest configuration
├── alembic.ini                 # Alembic configuration
├── docker-compose.yml          # Docker orchestration
├── Makefile                    # Common commands
└── README.md                   # Project overview
```

---

## Development Workflow

### 1. Create Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Develop Locally

**Option A: Without Docker (faster iteration)**
```bash
# Start dependencies only
docker-compose up -d postgres redis ollama

# Run app locally with hot reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Option B: With Docker (full environment)**
```bash
docker-compose up -d
docker-compose logs -f app
```

### 3. Make Changes

- Edit code in your IDE
- Hot reload applies changes automatically
- Check logs for errors

### 4. Write Tests

```bash
# Run tests continuously
pytest -v --looponfail
```

### 5. Check Code Quality

```bash
# Format code
black app/ tests/
ruff check --fix app/ tests/

# Type check
mypy app/

# Security scan
bandit -r app/
```

### 6. Commit Changes

```bash
git add .
git commit -m "feat: add new feature"
git push origin feature/your-feature-name
```

### 7. Create Pull Request

- Open PR on GitHub
- CI will run tests automatically
- Request review from team

---

## Code Style

### Python Style Guide

We follow **PEP 8** with some modifications:

- **Line length**: 88 characters (Black default)
- **Quotes**: Double quotes for strings
- **Imports**: Sorted with `isort`
- **Docstrings**: Google style

### Example

```python
"""
Module docstring.

This module does something important.
"""
from typing import List, Optional

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.database.dependencies import get_db

logger = get_logger(__name__)

router = APIRouter()


@router.get("/endpoint")
async def endpoint_function(
    param: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Endpoint function docstring.

    Args:
        param: Parameter description
        db: Database session

    Returns:
        Dictionary with result

    Raises:
        ValueError: When param is invalid
    """
    logger.info("processing_request", param=param)

    # Implementation
    result = {"status": "success"}

    logger.debug("request_completed", result=result)

    return result
```

### Tools

**Black** - Code formatter
```bash
black app/ tests/
```

**Ruff** - Linter (faster than flake8/pylint)
```bash
ruff check app/ tests/
ruff check --fix app/ tests/  # Auto-fix
```

**mypy** - Type checker
```bash
mypy app/
```

**isort** - Import sorter
```bash
isort app/ tests/
```

### Pre-commit Hooks

Install pre-commit hooks:
```bash
pre-commit install
```

`.pre-commit-config.yaml`:
```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black

  - repo: https://github.com/charliermarsh/ruff-pre-commit
    rev: v0.0.270
    hooks:
      - id: ruff
        args: [--fix]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.3.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
```

---

## Testing

### Test Structure

```
tests/
├── conftest.py           # Shared fixtures
├── unit/                 # Unit tests (fast, isolated)
│   ├── test_config.py
│   ├── test_models.py
│   └── test_repositories.py
└── integration/          # Integration tests (slower)
    └── test_database.py
```

### Running Tests

```bash
# All tests
pytest

# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/

# Specific test file
pytest tests/unit/test_config.py

# Specific test
pytest tests/unit/test_config.py::TestSettings::test_default_settings

# With coverage
pytest --cov=app --cov-report=html

# Watch mode (re-run on changes)
pytest -f

# Parallel execution
pytest -n auto
```

### Writing Tests

**Unit Test Example:**
```python
async def test_create_opportunity(db_session: AsyncSession):
    """Test creating an opportunity."""
    repo = OpportunityRepository(db_session)

    opportunity = await repo.create(
        recruiter_name="Test",
        raw_message="Message",
        status="processed"
    )

    assert opportunity.id is not None
    assert opportunity.recruiter_name == "Test"
```

**Integration Test Example:**
```python
@pytest.mark.integration
async def test_api_create_opportunity(client: AsyncClient):
    """Test creating opportunity via API."""
    response = await client.post(
        "/api/v1/opportunities",
        json={
            "recruiter_name": "Test",
            "raw_message": "Message here"
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert data["recruiter_name"] == "Test"
```

### Test Coverage

**Target**: 70%+ for Sprint 1

Check coverage:
```bash
pytest --cov=app --cov-report=term-missing
```

View HTML report:
```bash
pytest --cov=app --cov-report=html
open htmlcov/index.html
```

---

## Debugging

### VSCode Debugger

`.vscode/launch.json`:
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "app.main:app",
        "--reload",
        "--host",
        "0.0.0.0",
        "--port",
        "8000"
      ],
      "jinja": true,
      "justMyCode": false
    },
    {
      "name": "Pytest",
      "type": "python",
      "request": "launch",
      "module": "pytest",
      "args": [
        "-v",
        "-s"
      ]
    }
  ]
}
```

### Logging

```python
from app.core.logging import get_logger

logger = get_logger(__name__)

# Structured logging
logger.info("processing_request", user_id=123, action="create")
logger.error("request_failed", error=str(e), details={"...": "..."})
logger.debug("debug_info", data=data)
```

### Python Debugger

```python
# Add breakpoint
import pdb; pdb.set_trace()

# Or use built-in
breakpoint()
```

### Docker Logs

```bash
# App logs
docker-compose logs -f app

# All services
docker-compose logs -f

# Specific service
docker-compose logs -f postgres
```

---

## Common Tasks

### Database

**Create migration:**
```bash
alembic revision --autogenerate -m "Add new field"
```

**Apply migrations:**
```bash
alembic upgrade head
```

**Rollback migration:**
```bash
alembic downgrade -1
```

**Reset database:**
```bash
docker-compose down -v postgres
docker-compose up -d postgres
alembic upgrade head
```

**Access database:**
```bash
docker-compose exec postgres psql -U user -d linkedin_agent
```

### API Development

**Test endpoint:**
```bash
# With curl
curl http://localhost:8000/api/v1/opportunities

# With httpie
http http://localhost:8000/api/v1/opportunities

# With Python
python -c "import httpx; print(httpx.get('http://localhost:8000/health').json())"
```

**View API docs:**
```bash
open http://localhost:8000/docs
```

### DSPy Pipeline

**Test pipeline:**
```python
from app.dspy_modules.pipeline import get_pipeline
from app.dspy_modules.profile_loader import get_profile

pipeline = get_pipeline()
profile = get_profile()

result = pipeline.forward(
    message="Test message",
    recruiter_name="Test",
    profile=profile
)

print(f"Score: {result.scoring.total_score}")
print(f"Tier: {result.scoring.tier}")
```

### LinkedIn Scraper

**Run scraper manually:**
```bash
# Set credentials
export LINKEDIN_EMAIL="your@email.com"
export LINKEDIN_PASSWORD="your-password"

# Run scraper
python scripts/scrape_linkedin.py
```

**Test scraper in Python:**
```python
import asyncio
from app.scraper import LinkedInScraper, ScraperConfig

async def main():
    config = ScraperConfig(
        email="your@email.com",
        password="your-password",
        headless=True,
    )

    async with LinkedInScraper(config) as scraper:
        # Get unread count
        count = await scraper.get_unread_count()
        print(f"Unread: {count}")

        # Scrape messages
        messages = await scraper.scrape_messages(limit=5)
        print(f"Scraped: {len(messages)} messages")

asyncio.run(main())
```

**Debug scraper (see browser):**
```python
# Set headless=False to see the browser
config = ScraperConfig(
    email="...",
    password="...",
    headless=False,  # See what's happening
)
```

See [SCRAPER.md](SCRAPER.md) for complete scraper documentation.

### Celery Background Jobs

**Start Celery worker locally:**
```bash
# Start worker
celery -A app.tasks.celery_app worker --loglevel=info

# With specific queues
celery -A app.tasks.celery_app worker -Q scraping,processing --loglevel=info

# With concurrency
celery -A app.tasks.celery_app worker --concurrency=4 --loglevel=info
```

**Start Celery Beat (scheduler):**
```bash
celery -A app.tasks.celery_app beat --loglevel=info
```

**Monitor with Flower:**
```bash
# Start Flower UI
celery -A app.tasks.celery_app flower --port=5555

# Access at http://localhost:5555
```

**Trigger tasks manually:**
```python
from app.tasks.scraping_tasks import scrape_linkedin_messages
from app.tasks.processing_tasks import process_message

# Trigger scraping task
result = scrape_linkedin_messages.delay(limit=10, unread_only=True)
print(f"Task ID: {result.id}")

# Check task status
print(f"Status: {result.status}")
print(f"Result: {result.get(timeout=60)}")

# Trigger processing task
result = process_message.delay(
    recruiter_name="John Doe",
    raw_message="We have a position..."
)
```

**Inspect Celery:**
```bash
# Show active tasks
celery -A app.tasks.celery_app inspect active

# Show scheduled tasks
celery -A app.tasks.celery_app inspect scheduled

# Show registered tasks
celery -A app.tasks.celery_app inspect registered

# Purge all tasks
celery -A app.tasks.celery_app purge
```

**Periodic tasks:**
- Scraping: Every 15 minutes (`scrape_unread_messages`)
- Cleanup: Daily at 2 AM (`cleanup_old_opportunities`)
- Health check: Every 5 minutes (`health_check`)

### Docker Services

**Start all services:**
```bash
docker-compose up -d
```

**Start specific services:**
```bash
# Core services only
docker-compose up -d postgres redis ollama

# Add app
docker-compose up -d app

# Add Celery workers
docker-compose up -d celery-worker celery-beat flower

# Add scraper
docker-compose up -d scraper
```

**View logs:**
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f celery-worker
docker-compose logs -f scraper

# Last 100 lines
docker-compose logs --tail=100 celery-worker
```

**Access services:**
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Flower (Celery): http://localhost:5555
- PostgreSQL: localhost:5432
- Redis: localhost:6379

**Restart services:**
```bash
# Restart specific service
docker-compose restart celery-worker

# Rebuild and restart
docker-compose up -d --build app
```

---

## Best Practices

### Code Organization

1. **Separation of Concerns**: Keep API, business logic, and data access separate
2. **Dependency Injection**: Use FastAPI's Depends()
3. **Type Hints**: Always use type hints
4. **Docstrings**: Document all public functions/classes
5. **Constants**: Use config.py, not hardcoded values

### Error Handling

```python
from app.core.exceptions import DatabaseError

try:
    result = await repo.create(data)
except Exception as e:
    logger.error("operation_failed", error=str(e))
    raise DatabaseError(
        message="Failed to create record",
        details={"error": str(e)}
    ) from e
```

### Async/Await

```python
# Good
async def process_data(db: AsyncSession):
    result = await db.execute(query)
    return result

# Bad - blocking operation in async function
async def process_data_bad(db: AsyncSession):
    result = db.execute(query)  # Missing await!
    return result
```

### Logging

```python
# Good - structured logging
logger.info("user_created", user_id=user.id, email=user.email)

# Bad - string formatting
logger.info(f"Created user {user.id} with email {user.email}")
```

---

## Troubleshooting

### Import Errors

```bash
# Add project root to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:${PWD}"

# Or in VSCode settings.json
"python.analysis.extraPaths": ["${workspaceFolder}"]
```

### Database Connection Issues

```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# Check DATABASE_URL
echo $DATABASE_URL

# Test connection
docker-compose exec postgres pg_isready -U user
```

### Ollama Not Working

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Restart Ollama
docker-compose restart ollama

# Pull model
docker-compose exec ollama ollama pull llama2
```

### Port Already in Use

```bash
# Find process using port 8000
lsof -i :8000

# Kill process
kill -9 <PID>

# Or use different port
uvicorn app.main:app --port 8001
```

---

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com)
- [DSPy Documentation](https://github.com/stanfordnlp/dspy)
- [SQLAlchemy 2.0 Tutorial](https://docs.sqlalchemy.org/en/20/tutorial/)
- [Pytest Documentation](https://docs.pytest.org/)
- [Python Type Hints](https://docs.python.org/3/library/typing.html)

---

## Getting Help

- **Documentation**: Check docs/ folder
- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions
- **Code Reviews**: Request review on PR
