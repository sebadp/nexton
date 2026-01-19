# Tests - LinkedIn AI Agent

Comprehensive test suite for the LinkedIn AI Agent platform.

## 📁 Test Structure

```
tests/
├── conftest.py              # Global fixtures and test configuration
├── unit/                    # Unit tests (fast, isolated)
│   ├── test_config.py       # Configuration tests
│   ├── test_models.py       # Database model tests
│   ├── test_repositories.py # Repository pattern tests
│   ├── test_dspy_models.py  # DSPy Pydantic model tests
│   ├── test_api_health.py   # Health endpoint tests
│   ├── test_cache.py        # Redis cache tests (Sprint 2)
│   ├── test_observability.py # Tracing & metrics tests (Sprint 2)
│   └── test_scraper.py      # LinkedIn scraper tests (Sprint 2)
├── integration/             # Integration tests (slower, database required)
│   ├── test_database.py     # Full CRUD flow tests
│   ├── test_service_layer.py    # OpportunityService integration (Sprint 2)
│   ├── test_celery_tasks.py     # Celery background tasks (Sprint 2)
│   └── test_metrics_api.py      # Metrics API endpoint (Sprint 2)
├── e2e/                     # End-to-end tests
└── fixtures/                # Shared test fixtures
```

## 🚀 Running Tests

### Run All Tests
```bash
# With coverage
pytest

# Without coverage
pytest --no-cov
```

### Run Specific Test Types
```bash
# Unit tests only
pytest tests/unit

# Integration tests only
pytest tests/integration

# Specific test file
pytest tests/unit/test_config.py

# Specific test function
pytest tests/unit/test_config.py::TestSettings::test_default_settings
```

### Using Scripts
```bash
# Run all tests with coverage
./scripts/run_tests.sh all

# Run only unit tests
./scripts/run_tests.sh unit

# Run without coverage
./scripts/run_tests.sh all no
```

### Using Makefile
```bash
# Run all tests
make test

# Run unit tests
make test-unit

# Run integration tests
make test-integration

# Generate coverage report
make coverage

# Open coverage report in browser
make coverage-report
```

## 📊 Coverage Goals

**Sprint 1 Target**: 70%+ ✅ Achieved
**Sprint 2 Target**: 80%+

### Current Coverage by Module:
- `app/core/`: 80%+ (config, logging, exceptions)
- `app/database/`: 85%+ (models, repositories)
- `app/dspy_modules/`: 70%+ (models, pipeline - LLM mocked)
- `app/api/`: 75%+ (endpoints with mocked dependencies)

### Sprint 2 Coverage:
- `app/cache/`: 85%+ (Redis cache, decorators)
- `app/observability/`: 80%+ (tracing, metrics)
- `app/scraper/`: 75%+ (LinkedIn scraper, rate limiting)
- `app/services/`: 85%+ (OpportunityService with integrations)
- `app/celery_app/`: 70%+ (Background tasks)

## 🧪 Test Categories

### Unit Tests
- **Fast**: Run in < 5 seconds total
- **Isolated**: No external dependencies
- **Mocked**: All external services mocked (DB, LLM, APIs)
- **Focus**: Business logic, data models, utilities

### Integration Tests
- **Slower**: May take 10-30 seconds
- **Database**: Uses in-memory SQLite
- **Realistic**: Tests actual flows
- **Focus**: CRUD operations, API endpoints, data flows

## 🏷️ Test Markers

Use markers to run specific test categories:

```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run tests that require database
pytest -m requires_db

# Skip slow tests
pytest -m "not slow"
```

## 🔧 Test Configuration

### pytest.ini
- Test discovery paths
- Coverage configuration
- Output formatting
- Markers definition

### conftest.py
Key fixtures:
- `db_session`: Async database session (in-memory SQLite)
- `client`: Async HTTP client for API tests
- `mock_pipeline`: Mocked DSPy pipeline
- `sample_opportunity_data`: Test data fixtures

## 📝 Writing New Tests

### Unit Test Example
```python
async def test_create_opportunity(self, db_session: AsyncSession):
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

### Integration Test Example
```python
@pytest.mark.integration
@pytest.mark.requires_db
async def test_full_crud_flow(self, db_session: AsyncSession):
    """Test complete CRUD flow."""
    repo = OpportunityRepository(db_session)

    # Create
    opp = await repo.create(**data)

    # Read
    fetched = await repo.get_by_id(opp.id)

    # Update
    updated = await repo.update(opp.id, status="contacted")

    # Delete
    deleted = await repo.delete(opp.id)

    assert deleted is True
```

## 🐛 Debugging Tests

### Run with verbose output
```bash
pytest -vv
```

### Show print statements
```bash
pytest -s
```

### Drop into debugger on failure
```bash
pytest --pdb
```

### Run last failed tests
```bash
pytest --lf
```

## 📈 Continuous Integration

Tests are run automatically on:
- Pull requests
- Commits to main branch
- Scheduled nightly builds

CI configuration: `.github/workflows/ci.yml`

## 🚀 Sprint 2 Test Coverage

### New Test Files Added

#### Unit Tests
1. **test_cache.py** - Redis cache functionality
   - Cache key generation
   - Get/set/delete operations
   - Pattern-based deletion
   - TTL management
   - Bulk operations (get_many, set_many)
   - Cached decorator
   - Error handling

2. **test_observability.py** - Tracing and metrics
   - TracingContext context manager
   - Span attributes and events
   - Error recording in spans
   - Metrics tracking functions (opportunities, pipeline, cache, database)
   - Setup functions for tracing and metrics

3. **test_scraper.py** - LinkedIn scraper
   - RateLimiter functionality
   - SessionManager (cookie persistence)
   - Scraper initialization and lifecycle
   - Login flow with saved sessions
   - Message fetching with rate limiting
   - Retry logic and error handling

#### Integration Tests
1. **test_service_layer.py** - OpportunityService integration
   - Opportunity creation with caching
   - Cache hit/miss scenarios
   - Metrics tracking during operations
   - Tracing integration
   - CRUD operations with cache invalidation
   - Stats aggregation
   - Error handling and rollback

2. **test_celery_tasks.py** - Background task processing
   - Opportunity processing task
   - LinkedIn scraping task
   - Notification sending task
   - Stats update task
   - Task configuration and routing
   - Task chaining and workflows
   - Metrics tracking in tasks
   - Error handling and retries

3. **test_metrics_api.py** - Metrics API endpoint
   - Endpoint availability and response format
   - Prometheus format validation
   - Content type validation
   - Concurrent access handling
   - Performance testing
   - Label validation

### Running Sprint 2 Tests

```bash
# Run all Sprint 2 tests
pytest tests/unit/test_cache.py tests/unit/test_observability.py tests/unit/test_scraper.py tests/integration/test_service_layer.py tests/integration/test_celery_tasks.py tests/integration/test_metrics_api.py

# Run cache tests only
pytest tests/unit/test_cache.py -v

# Run observability tests only
pytest tests/unit/test_observability.py -v

# Run service layer integration tests
pytest tests/integration/test_service_layer.py -v

# Run with coverage for Sprint 2 modules
pytest tests/unit/test_cache.py tests/unit/test_observability.py --cov=app/cache --cov=app/observability --cov-report=html
```

## 🎯 Best Practices

1. **Test Naming**: Use descriptive names starting with `test_`
2. **Arrange-Act-Assert**: Structure tests clearly
3. **One Assertion**: Focus on one thing per test
4. **Fixtures**: Use fixtures for common setup
5. **Mocking**: Mock external services (LLM, external APIs)
6. **Async**: Use `async`/`await` for database tests
7. **Cleanup**: Tests should clean up after themselves
8. **Deterministic**: Tests should not be flaky

## 🚨 Common Issues

### Import Errors
```bash
# Make sure app is in PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:${PWD}"
```

### Database Errors
- Tests use in-memory SQLite
- Each test gets fresh session
- Isolation via transactions

### Async Issues
- Always use `async def` for async tests
- Use `await` for async operations
- Configure `asyncio_mode=auto` in pytest.ini

## 📚 Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://github.com/pytest-dev/pytest-asyncio)
- [pytest-cov](https://pytest-cov.readthedocs.io/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
