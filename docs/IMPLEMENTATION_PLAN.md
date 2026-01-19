# Implementation Plan - LinkedIn AI Agent

> Detailed implementation roadmap with tasks, tests, and validation checkpoints

**Status**: Sprint 1 - 67% Complete ✅
**Start Date**: 2024-01-16
**Last Updated**: 2024-01-16 (Session 1 - End of Day)
**Target Completion**: 3 weeks

---

## 🎯 Current Progress

**Sprint 1**: 8/12 tasks completed (67%) ✅

### ✅ Completed Today (Session 1):
1. ✅ Project dependencies (pyproject.toml + requirements.txt)
2. ✅ Docker Compose setup (PostgreSQL, Redis, Ollama)
3. ✅ Database models and Alembic migrations
4. ✅ FastAPI application structure (main.py, config, logging, exceptions)
5. ✅ Health check endpoints (/health, /health/ready, /health/live, /health/startup)
6. ✅ DSPy signatures and modules (MessageAnalyzer, Scorer, ResponseGenerator)
7. ✅ DSPy pipeline integration (complete workflow)
8. ✅ Repository pattern (OpportunityRepository with CRUD)

### ⏳ Remaining Tasks (33%):
9. ⏳ API endpoints for opportunities (POST, GET, DELETE)
10. ⏳ Dockerfile and update docker-compose
11. ⏳ Tests (unit + integration, 70%+ coverage)
12. ⏳ Documentation updates

### 📊 Code Statistics:
- **Lines of Code**: ~3,100 productive lines
- **Files Created**: 30+ files
- **Modules**: 15+ Python modules
- **Infrastructure**: 5 config files

---

## 📋 Table of Contents

- [Sprint 1: Foundation (Week 1)](#sprint-1-foundation-week-1)
- [Sprint 2: Features & Business Logic (Week 2)](#sprint-2-features--business-logic-week-2)
- [Sprint 3: Production Ready (Week 3)](#sprint-3-production-ready-week-3)
- [Testing Strategy](#testing-strategy)
- [Definition of Done](#definition-of-done)

---

## Sprint 1: Foundation (Week 1)

**Goal**: Establish infrastructure, core services, and basic DSPy pipeline

**Success Metrics**:
- [ ] All services running via Docker Compose
- [ ] Health checks passing
- [ ] Database migrations working
- [ ] Basic DSPy pipeline processing a message
- [ ] 70%+ test coverage on core modules

### Day 1-2: Infrastructure Setup

#### Task 1.1: Project Dependencies Setup ✅ COMPLETED
**Priority**: P0 (Blocker)
**Actual Time**: 1 hour
**Status**: ✅ Complete

- [x] Create `pyproject.toml` with Poetry
  - [x] Add FastAPI + dependencies (FastAPI 0.109+, Uvicorn 0.27+)
  - [x] Add DSPy + Ollama client (dspy-ai 2.4+, ollama 0.1.6+)
  - [x] Add SQLAlchemy + Alembic (SQLAlchemy 2.0+, asyncpg, Alembic 1.13+)
  - [x] Add Redis client (redis 5.0+, aioredis 2.0+)
  - [x] Add testing dependencies (pytest, pytest-cov, pytest-asyncio, factory-boy)
  - [x] Add dev dependencies (black, ruff, mypy, pre-commit, bandit, safety)
  - [x] Add monitoring dependencies (prometheus-client, opentelemetry SDK)

- [x] Created `requirements.txt` and `requirements-dev.txt` as fallback
  - Alternative to Poetry due to version compatibility issues

**Completed Files**:
- `pyproject.toml` (318 lines with full tool configuration)
- `requirements.txt` (55 dependencies)
- `requirements-dev.txt` (40+ dev dependencies)

**Tests**: N/A (infrastructure)

---

#### Task 1.2: Docker Compose - Core Services ✅ COMPLETED
**Priority**: P0 (Blocker)
**Actual Time**: 2 hours
**Status**: ✅ Complete
**Depends On**: Task 1.1

- [x] Create `docker-compose.yml`
  - [x] PostgreSQL service with health check
  - [x] Redis service with health check
  - [x] Ollama service with health check
  - [x] Volume definitions
  - [x] Network configuration
  - [x] Environment variable placeholders

- [x] Create initial `.env` from `.env.example`
  - [x] Configure database credentials
  - [x] Configure Redis URL
  - [x] Configure Ollama URL

- [x] Create health check script (`infrastructure/scripts/health_check.sh`)

**Completed Files**:
- `docker-compose.yml` (150 lines)
  - PostgreSQL 16 with health checks
  - Redis 7 with appendonly persistence
  - Ollama with optional GPU support (NVIDIA runtime)
  - Shared network and volumes
- `.env.example` (environment template)
- `infrastructure/scripts/health_check.sh` (health monitoring script)

**Key Implementation Details**:
- Health checks on all services (pg_isready, redis-cli ping, ollama endpoint)
- Volume persistence for data (postgres_data, redis_data, ollama_models)
- Restart policies (unless-stopped)
- Network isolation with custom bridge network

**Validation**:
```bash
make up
docker-compose ps  # All services should be "healthy"
curl http://localhost:5432  # PostgreSQL responding
redis-cli ping  # Redis responding
curl http://localhost:11434/api/tags  # Ollama responding
```

**Tests**:
- [ ] Write integration test: `tests/integration/test_infrastructure.py`
  - Test PostgreSQL connection
  - Test Redis connection
  - Test Ollama availability

---

#### Task 1.3: PostgreSQL Database Setup ✅ COMPLETED
**Priority**: P0 (Blocker)
**Actual Time**: 2.5 hours
**Status**: ✅ Complete
**Depends On**: Task 1.2

- [x] Create database models (`app/database/models.py`)
  - [x] Opportunity model (all fields per schema)
  - [x] Base model with timestamps
  - [x] Relationships (if any)

- [x] Create database connection (`app/database/base.py`)
  - [x] SQLAlchemy engine setup
  - [x] Async session factory
  - [x] Connection pool configuration

- [x] Setup Alembic
  - [x] Initialize Alembic (`alembic init app/database/migrations`)
  - [x] Configure `alembic.ini`
  - [x] Create initial migration
  - [x] Add indices for performance

**Completed Files**:
- `app/database/models.py` (155 lines)
  - Opportunity model with 25+ fields (id, recruiter_name, company, role, tech_stack, etc.)
  - Check constraints on total_score (0-100) and individual scores
  - Composite indexes on (tier, created_at), (status, created_at), (company, tier)
  - JSON field for tech_stack array
- `app/database/base.py` (database engine and session management)
- `app/database/__init__.py` (package initialization)
- `alembic.ini` (Alembic configuration)
- `app/database/migrations/versions/001_initial_schema.py` (initial migration)

**Key Implementation Details**:
- SQLAlchemy 2.0 with async support (asyncpg driver)
- Mapped columns with type hints for better IDE support
- Automatic created_at and updated_at timestamps
- Performance indexes for common queries (filtering by tier, status, company)

**Validation**:
```bash
make migrate  # Should create tables
make db-shell
# In psql:
\dt  # Should show 'opportunities' table
\d opportunities  # Should show all columns + indices
```

**Tests**:
- [ ] Unit test: `tests/unit/test_database_models.py`
  - Test model creation
  - Test field validations
  - Test timestamp auto-population
- [ ] Integration test: `tests/integration/test_database.py`
  - Test connection
  - Test CRUD operations
  - Test transaction rollback

---

### Day 3-4: Core Application & Configuration

#### Task 1.4: FastAPI Application Structure ✅ COMPLETED
**Priority**: P0 (Blocker)
**Actual Time**: 2.5 hours
**Status**: ✅ Complete
**Depends On**: Task 1.1

- [x] Create `app/main.py` (FastAPI entry point)
  - [x] Initialize FastAPI app
  - [x] Configure CORS
  - [x] Add exception handlers
  - [x] Include routers

- [x] Create `app/core/config.py` (Settings management)
  - [x] Pydantic Settings class
  - [x] Environment variable loading
  - [x] Validation for required vars
  - [x] Database URL builder
  - [x] Redis URL builder

- [x] Create `app/core/logging.py` (Structured logging)
  - [x] Structlog configuration
  - [x] JSON formatter
  - [x] Log levels by environment
  - [x] Contextual logging helpers

- [x] Create `app/core/exceptions.py` (Custom exceptions)
  - [x] OpportunityNotFound
  - [x] DatabaseError
  - [x] LLMError
  - [x] ScraperError

**Completed Files**:
- `app/main.py` (178 lines)
  - FastAPI app with lifespan events
  - CORS middleware configuration
  - Custom exception handlers for all error types
  - Health and API routers included
- `app/core/config.py` (155 lines)
  - Settings class with 40+ configuration options
  - Field validators for DATABASE_URL, CORS_ORIGINS
  - Helper properties (is_development, is_production, is_testing)
- `app/core/logging.py` (115 lines)
  - Structlog with JSON formatting
  - Context manager for temporary log context
  - Environment-based log levels
- `app/core/exceptions.py` (100 lines)
  - Base exceptions with structured details
  - OpportunityNotFound, DatabaseError, ConfigurationError, PipelineError

**Key Implementation Details**:
- Async lifespan management (database initialization and cleanup)
- CORS with configurable allowed origins
- Structured exception handling with proper HTTP status codes
- Production-ready logging with JSON output

**Validation**:
```bash
poetry run uvicorn app.main:app --reload
curl http://localhost:8000  # Should return 404 with JSON
curl http://localhost:8000/openapi.json  # Should return OpenAPI spec
```

**Tests**:
- [ ] Unit test: `tests/unit/test_config.py`
  - Test settings loading
  - Test validation errors
  - Test URL building
- [ ] Unit test: `tests/unit/test_logging.py`
  - Test log formatting
  - Test contextual logging
- [ ] Integration test: `tests/integration/test_app.py`
  - Test app startup
  - Test CORS headers
  - Test exception handling

---

#### Task 1.5: Health Check Endpoints ✅ COMPLETED
**Priority**: P1 (High)
**Actual Time**: 2 hours
**Status**: ✅ Complete
**Depends On**: Task 1.4

- [x] Create `app/api/__init__.py`
- [x] Create `app/api/v1/__init__.py`
- [x] Create `app/api/v1/health.py`
  - [x] GET `/health` - Basic health check
  - [x] GET `/health/ready` - Readiness check
    - Check PostgreSQL connection
    - Check Redis connection
    - Check Ollama availability
  - [x] GET `/health/live` - Liveness check
  - [x] GET `/health/startup` - Startup check

- [x] Add health check middleware (optional)
  - [x] Log health check requests at DEBUG level
  - [x] Add response time metric

**Completed Files**:
- `app/api/__init__.py` (package init)
- `app/api/v1/__init__.py` (v1 router)
- `app/api/v1/health.py` (195 lines)
  - Four health check endpoints
  - Dependency checking (PostgreSQL, Redis, Ollama)
  - Proper status codes (200 for healthy, 503 for unhealthy)

**Key Implementation Details**:
- Kubernetes-ready health probes (liveness, readiness, startup)
- Individual dependency checking with error handling
- Detailed response with check results and timestamps
- Proper HTTP status codes based on health status

**Validation**:
```bash
curl http://localhost:8000/health
# Response: {"status": "healthy"}

curl http://localhost:8000/health/ready
# Response: {"status": "ready", "checks": {"database": true, "redis": true, "ollama": true}}
```

**Tests**:
- [ ] Unit test: `tests/unit/api/test_health.py`
  - Test health endpoint returns 200
  - Test ready endpoint checks dependencies
  - Test ready endpoint returns 503 when deps fail
- [ ] Integration test: `tests/integration/test_health_endpoints.py`
  - Test with real dependencies
  - Test when PostgreSQL is down
  - Test when Redis is down

---

### Day 5-6: DSPy Pipeline Foundation

#### Task 1.6: DSPy Signatures & Base Modules ✅ COMPLETED
**Priority**: P0 (Blocker)
**Actual Time**: 5 hours
**Status**: ✅ Complete
**Depends On**: Task 1.2 (Ollama running)

- [x] Create `app/dspy_modules/__init__.py`
- [x] Create `app/dspy_modules/signatures.py`
  - [x] MessageAnalysisSignature (Input: message, Output: extracted fields)
  - [x] ScoringSignature (Input: extracted data + profile, Output: scores)
  - [x] ResponseGenerationSignature (Input: all data, Output: response)

- [x] Create `app/dspy_modules/message_analyzer.py`
  - [x] MessageAnalyzer class (dspy.Module)
  - [x] Implements extraction logic
  - [x] Validates extracted fields
  - [x] Returns structured data

- [x] Create `app/dspy_modules/scorer.py`
  - [x] Scorer class (dspy.Module)
  - [x] Tech stack scoring (0-40 points)
  - [x] Salary scoring (0-30 points)
  - [x] Seniority scoring (0-20 points)
  - [x] Company scoring (0-10 points)
  - [x] Tier classification logic

- [x] Create `app/dspy_modules/response_generator.py`
  - [x] ResponseGenerator class (dspy.Module)
  - [x] Generates personalized response
  - [x] Includes AI transparency note
  - [x] Word count validation (50-200 words)

**Completed Files**:
- `app/dspy_modules/__init__.py` (package init)
- `app/dspy_modules/signatures.py` (120 lines)
  - Three DSPy signatures with detailed field descriptions
  - Input/output field specifications for LLM
- `app/dspy_modules/message_analyzer.py` (200 lines)
  - MessageAnalyzer with ChainOfThought reasoning
  - Salary parsing with regex
  - Seniority and remote policy normalization
- `app/dspy_modules/scorer.py` (320 lines)
  - Multi-dimensional scoring system
  - Fallback heuristic scoring when LLM fails
  - Company recognition for well-known companies
  - Tier classification (HIGH_PRIORITY, INTERESANTE, POCO_INTERESANTE, NO_INTERESA)
- `app/dspy_modules/response_generator.py` (210 lines)
  - ResponseGenerator with tier-adaptive responses
  - AI transparency note enforcement
  - Word count validation
  - Fallback template responses per tier

**Key Implementation Details**:
- DSPy ChainOfThought for reasoning
- Four-tier classification system: HIGH_PRIORITY (75-100), INTERESANTE (50-74), POCO_INTERESANTE (30-49), NO_INTERESA (0-29)
- Scoring weights: Tech stack (40%), Salary (30%), Seniority (20%), Company (10%)
- Spanish responses with professional tone
- Fallback logic for LLM failures

**Validation**:
```python
# Test in Python shell
from app.dspy_modules.message_analyzer import MessageAnalyzer
analyzer = MessageAnalyzer()
result = analyzer(message="Test recruiter message...")
print(result)  # Should show extracted fields
```

**Tests**:
- [ ] Unit test: `tests/unit/dspy_modules/test_signatures.py`
  - Test signature definitions
  - Test input/output types
- [ ] Unit test: `tests/unit/dspy_modules/test_message_analyzer.py`
  - Test extraction with sample messages
  - Test field validation
  - Test error handling
- [ ] Unit test: `tests/unit/dspy_modules/test_scorer.py`
  - Test scoring calculations
  - Test tier classification
  - Test edge cases (missing data)
- [ ] Unit test: `tests/unit/dspy_modules/test_response_generator.py`
  - Test response generation
  - Test AI transparency note inclusion
  - Test word count validation

---

#### Task 1.7: DSPy Pipeline Integration ✅ COMPLETED
**Priority**: P0 (Blocker)
**Actual Time**: 3 hours
**Status**: ✅ Complete
**Depends On**: Task 1.6

- [x] Create `app/dspy_modules/pipeline.py`
  - [x] OpportunityPipeline class
  - [x] Chains: Analyzer → Scorer → ResponseGenerator
  - [x] Error handling between stages
  - [x] Logging at each stage
  - [x] Return complete OpportunityResult

- [x] Configure DSPy with Ollama
  - [x] Setup Ollama LM in config
  - [x] Configure model name from env
  - [x] Set max tokens, temperature

- [x] Create `app/dspy_modules/models.py` (Pydantic models)
  - [x] ExtractedData model
  - [x] ScoringResult model
  - [x] OpportunityResult model
  - [x] CandidateProfile model

**Completed Files**:
- `app/dspy_modules/pipeline.py` (209 lines)
  - OpportunityPipeline integrating all three modules
  - configure_dspy() function for Ollama setup
  - Singleton pattern with get_pipeline()
  - Processing time tracking
  - Comprehensive error handling
- `app/dspy_modules/models.py` (200 lines)
  - ExtractedData with 15+ fields
  - ScoringResult with total_score and tier properties
  - CandidateProfile with preferences and requirements
  - OpportunityResult with complete pipeline output
- `app/dspy_modules/profile_loader.py` (97 lines)
  - load_profile() function
  - get_profile() with caching
  - YAML configuration support
- `config/profile.yaml` (71 lines)
  - Example candidate profile configuration

**Key Implementation Details**:
- Three-stage pipeline: MessageAnalyzer → Scorer → ResponseGenerator
- Ollama configuration with timeouts and retries
- Pydantic models for data validation
- Processing time tracking per request
- Singleton pattern for efficiency

**Validation**:
```python
# End-to-end test
from app.dspy_modules.pipeline import OpportunityPipeline
pipeline = OpportunityPipeline()
result = pipeline.forward(
    message="Hola! Tenemos una posición de Senior Python Engineer...",
    profile=user_profile
)
print(result.total_score)  # Should be 0-100
print(result.tier)  # Should be HIGH_PRIORITY, etc.
print(result.response)  # Should be generated text
```

**Tests**:
- [ ] Unit test: `tests/unit/dspy_modules/test_pipeline.py`
  - Test pipeline initialization
  - Test forward pass with mock LLM
  - Test error propagation
- [ ] Integration test: `tests/integration/test_dspy_pipeline.py`
  - Test with real Ollama
  - Test with various message types
  - Test performance (should complete in <5s)

---

### Day 7: Testing & Documentation

#### Task 1.8: Repository Pattern ✅ COMPLETED
**Priority**: P1 (High)
**Actual Time**: 2.5 hours
**Status**: ✅ Complete
**Depends On**: Task 1.3

- [x] Create `app/database/repositories.py`
  - [x] BaseRepository class
  - [x] OpportunityRepository class
    - [x] create()
    - [x] get_by_id()
    - [x] get_all(filters, pagination)
    - [x] update()
    - [x] delete()
    - [x] count()
    - [x] get_by_tier()
    - [x] get_by_date_range()
    - [x] get_stats()

- [x] Create `app/database/dependencies.py`
  - [x] get_db() dependency
  - [x] get_opportunity_repository() dependency

**Completed Files**:
- `app/database/repositories.py` (370 lines)
  - BaseRepository with generic CRUD operations
  - OpportunityRepository with full CRUD
  - Advanced filtering (tier, status, min_score, company, date_range)
  - Pagination and sorting support
  - Aggregation methods (count by tier, overall stats)
- `app/database/dependencies.py` (50 lines)
  - Async session dependency
  - Repository dependency injection

**Key Implementation Details**:
- Repository pattern for clean separation of concerns
- Full async/await support
- Advanced query building with filters
- Proper transaction management
- Pagination with skip/limit
- Sorting by multiple fields

**Validation**:
```python
# Test in shell
from app.database.repositories import OpportunityRepository
repo = OpportunityRepository(db_session)
opp = repo.create(data)
assert opp.id is not None
```

**Tests**:
- [ ] Unit test: `tests/unit/test_repositories.py`
  - Test CRUD operations with mock session
  - Test filters and pagination
  - Test error handling
- [ ] Integration test: `tests/integration/test_repositories.py`
  - Test with real database
  - Test transactions
  - Test concurrent access

---

#### Task 1.9: Basic API Endpoints
**Priority**: P1 (High)
**Estimated Time**: 3 hours
**Depends On**: Task 1.8, Task 1.7

- [ ] Create `app/api/v1/opportunities.py`
  - [ ] GET `/api/v1/opportunities` - List opportunities
    - Pagination support
    - Filtering by tier
    - Sorting by score/date
  - [ ] GET `/api/v1/opportunities/{id}` - Get one opportunity
  - [ ] POST `/api/v1/opportunities` - Create opportunity (trigger pipeline)

- [ ] Create Pydantic schemas (`app/api/v1/schemas.py`)
  - [ ] OpportunityCreate (input)
  - [ ] OpportunityResponse (output)
  - [ ] OpportunityList (paginated output)

**Validation**:
```bash
# Create opportunity
curl -X POST http://localhost:8000/api/v1/opportunities \
  -H "Content-Type: application/json" \
  -d '{"recruiter_name": "John Doe", "raw_message": "..."}'
# Response: 201 Created

# List opportunities
curl http://localhost:8000/api/v1/opportunities?tier=HIGH_PRIORITY&limit=10
# Response: 200 OK with array
```

**Tests**:
- [ ] Unit test: `tests/unit/api/test_opportunities.py`
  - Test schema validation
  - Test endpoint logic with mocks
- [ ] Integration test: `tests/integration/test_opportunities_api.py`
  - Test full CRUD flow
  - Test pagination
  - Test filtering
  - Test error responses (404, 422)

---

#### Task 1.10: Docker Compose - Application Service
**Priority**: P0 (Blocker)
**Estimated Time**: 2 hours
**Depends On**: Task 1.4, Task 1.2

- [ ] Create `infrastructure/docker/Dockerfile`
  - [ ] Multi-stage build
  - [ ] Poetry installation
  - [ ] Dependencies layer (cached)
  - [ ] Application layer
  - [ ] Non-root user
  - [ ] Health check

- [ ] Add `app` service to `docker-compose.yml`
  - [ ] Build from Dockerfile
  - [ ] Environment variables from .env
  - [ ] Depends on: postgres, redis, ollama
  - [ ] Volume mounts (code, logs)
  - [ ] Port mapping 8000:8000
  - [ ] Health check
  - [ ] Restart policy

**Validation**:
```bash
make build
make up
docker-compose ps  # app should be healthy
curl http://localhost:8000/health/ready
# All checks should pass
```

**Tests**:
- [ ] Integration test: `tests/integration/test_docker.py`
  - Test container starts
  - Test health checks pass
  - Test API accessible from host

---

#### Task 1.11: Sprint 1 Testing & Coverage
**Priority**: P0 (Blocker)
**Estimated Time**: 3 hours
**Depends On**: All previous tasks

- [ ] Run full test suite
  ```bash
  make test
  ```

- [ ] Check coverage report
  ```bash
  make coverage
  # Target: >70% for Sprint 1
  ```

- [ ] Fix failing tests
- [ ] Add missing tests for uncovered code
- [ ] Update test documentation

**Coverage Targets by Module**:
- [ ] `app/core/`: 80%+
- [ ] `app/database/`: 85%+
- [ ] `app/dspy_modules/`: 70%+ (LLM mocking challenging)
- [ ] `app/api/`: 75%+

**Test Quality Checks**:
- [ ] All tests have docstrings
- [ ] No skipped tests without reason
- [ ] Tests are deterministic (no flakiness)
- [ ] Tests use fixtures properly
- [ ] Integration tests clean up after themselves

---

#### Task 1.12: Sprint 1 Documentation
**Priority**: P1 (High)
**Estimated Time**: 2 hours
**Depends On**: All previous tasks

- [ ] Update `README.md`
  - [ ] Add "Getting Started" with Sprint 1 features
  - [ ] Update architecture diagram if needed

- [ ] Create `docs/API.md`
  - [ ] Document health endpoints
  - [ ] Document opportunity endpoints
  - [ ] Include request/response examples
  - [ ] Add error code documentation

- [ ] Create `docs/TESTING.md`
  - [ ] Explain test structure
  - [ ] How to run tests
  - [ ] How to add new tests
  - [ ] Coverage requirements

- [ ] Create `docs/DEVELOPMENT.md`
  - [ ] Local development setup
  - [ ] Common development tasks
  - [ ] Debugging tips
  - [ ] Code style guide

**Validation**:
- [ ] All links in docs work
- [ ] Code examples in docs are valid
- [ ] Documentation matches implementation

---

### Sprint 1 Completion Checklist

**Functionality**:
- [ ] All services start with `make up`
- [ ] Health checks return green
- [ ] Database migrations apply cleanly
- [ ] Can create opportunity via API
- [ ] DSPy pipeline processes message successfully
- [ ] Can retrieve opportunities via API

**Quality**:
- [ ] All tests passing (`make test`)
- [ ] Coverage >70% (`make coverage`)
- [ ] No linting errors (`make lint`)
- [ ] Type checking passes (`make type-check`)
- [ ] Security scan clean (`make security`)

**Documentation**:
- [ ] README updated
- [ ] API documentation complete
- [ ] Architecture docs match implementation
- [ ] All code has docstrings

**Demo Ready**:
- [ ] Can show end-to-end flow:
  1. Start services
  2. Submit recruiter message
  3. Show DSPy pipeline execution
  4. Show stored opportunity with score
  5. Show generated response

---

## Sprint 2: Features & Business Logic (Week 2)

**Goal**: Add scraper, background jobs, caching, and observability

### Day 1-2: LinkedIn Scraper

#### Task 2.1: Playwright Scraper Setup
- [ ] Create `app/scraper/linkedin_scraper.py`
- [ ] Session management
- [ ] Cookie handling
- [ ] Message detection
- [ ] Rate limiting implementation
- [ ] Retry logic with exponential backoff

**Tests**:
- [ ] Unit tests with mocked Playwright
- [ ] Integration tests with test account

---

#### Task 2.2: Scraper Dockerfile
- [ ] Create `infrastructure/docker/Dockerfile.playwright`
- [ ] Browser dependencies
- [ ] Add to docker-compose.yml

---

### Day 3-4: Background Jobs & Caching

#### Task 2.3: Celery Setup
- [ ] Create `app/tasks/celery_app.py`
- [ ] Task definitions
- [ ] Periodic tasks (scheduled scraping)
- [ ] Add worker to docker-compose

**Tests**:
- [ ] Task execution tests
- [ ] Retry behavior tests

---

#### Task 2.4: Redis Caching
- [ ] Create `app/cache/redis_client.py`
- [ ] Caching strategies
- [ ] Cache invalidation
- [ ] Cache warming

**Tests**:
- [ ] Cache hit/miss tests
- [ ] TTL tests
- [ ] Invalidation tests

---

### Day 5-6: Observability Stack

#### Task 2.5: OpenTelemetry Integration
- [ ] Create `app/core/telemetry.py`
- [ ] Tracing setup
- [ ] Span creation helpers
- [ ] Context propagation

**Tests**:
- [ ] Trace creation tests
- [ ] Span attribute tests

---

#### Task 2.6: Prometheus Metrics
- [ ] Create `app/monitoring/metrics.py`
- [ ] Define custom metrics
- [ ] Add middleware for auto-instrumentation
- [ ] Expose `/metrics` endpoint

**Tests**:
- [ ] Metric increment tests
- [ ] Histogram recording tests

---

#### Task 2.7: Monitoring Stack
- [ ] Add Prometheus to docker-compose
- [ ] Add Grafana to docker-compose
- [ ] Add Loki to docker-compose
- [ ] Add Jaeger to docker-compose
- [ ] Create initial dashboards

**Validation**:
- [ ] Grafana accessible
- [ ] Dashboards showing data
- [ ] Traces visible in Jaeger

---

### Day 7: Service Layer & Testing

#### Task 2.8: Service Layer
- [ ] Create `app/services/opportunity_service.py`
- [ ] Business logic separation
- [ ] Transaction management
- [ ] Error handling

**Tests**:
- [ ] Service method tests
- [ ] Transaction rollback tests

---

#### Task 2.9: Sprint 2 Testing
- [ ] Full test suite
- [ ] Coverage target: >75%
- [ ] Load testing setup

---

### Sprint 2 Completion Checklist

**Functionality**:
- [ ] Scraper detects new messages
- [ ] Background jobs process messages
- [ ] Caching reduces DB load
- [ ] Observability stack operational

**Quality**:
- [ ] Tests passing
- [ ] Coverage >75%
- [ ] No security vulnerabilities

---

## Sprint 3: Production Ready (Week 3)

**Goal**: Production hardening, CI/CD, comprehensive testing

### Day 1-2: E2E Testing

#### Task 3.1: End-to-End Tests
- [ ] Create `tests/e2e/test_full_flow.py`
- [ ] Test complete user journey
- [ ] Test failure scenarios
- [ ] Test concurrent operations

---

#### Task 3.2: Load Testing
- [ ] Create `tests/performance/locustfile.py`
- [ ] Define load scenarios
- [ ] Run load tests
- [ ] Document performance baselines

**Metrics**:
- [ ] API p95 latency < 200ms
- [ ] Pipeline throughput > 10 msg/min
- [ ] No memory leaks under load

---

### Day 3-4: CI/CD Pipeline

#### Task 3.3: GitHub Actions
- [ ] Create `.github/workflows/ci.yml`
  - [ ] Lint
  - [ ] Type check
  - [ ] Unit tests
  - [ ] Integration tests
  - [ ] Coverage report

- [ ] Create `.github/workflows/security.yml`
  - [ ] Bandit scan
  - [ ] Safety check
  - [ ] Trivy container scan

---

#### Task 3.4: Pre-commit Hooks
- [ ] Create `.pre-commit-config.yaml`
- [ ] Setup hooks (black, ruff, mypy)
- [ ] Document in CONTRIBUTING.md

---

### Day 5-6: Production Configuration

#### Task 3.5: Production Docker Compose
- [ ] Create `docker-compose.prod.yml`
- [ ] Production optimizations
- [ ] Security hardening
- [ ] Resource limits

---

#### Task 3.6: Deployment Scripts
- [ ] Create `scripts/deploy.sh`
- [ ] Create `scripts/backup.sh`
- [ ] Create `scripts/rollback.sh`

---

### Day 7: Final Polish

#### Task 3.7: Documentation Completion
- [ ] Update all docs
- [ ] Create deployment guide
- [ ] Create monitoring guide
- [ ] Create troubleshooting guide

---

#### Task 3.8: Demo Preparation
- [ ] Prepare demo script
- [ ] Create sample data
- [ ] Practice presentation
- [ ] Performance benchmarks

---

### Sprint 3 Completion Checklist

**Functionality**:
- [ ] All features complete
- [ ] Production ready

**Quality**:
- [ ] Tests passing
- [ ] Coverage >80%
- [ ] Load tests passing
- [ ] Security scans clean

**Documentation**:
- [ ] All docs complete
- [ ] Deployment guide ready
- [ ] Monitoring runbook ready

**Demo**:
- [ ] Demo environment ready
- [ ] Presentation prepared
- [ ] Q&A prepared

---

## Testing Strategy

### Unit Tests
**Target**: 80% coverage
**Location**: `tests/unit/`

**Coverage**:
- Core utilities (config, logging)
- Database models and repositories
- DSPy modules (with mocked LLM)
- API endpoints (with mocked dependencies)
- Business logic

**Best Practices**:
- Use pytest fixtures
- Mock external dependencies
- Fast execution (<5 seconds total)
- Test edge cases

### Integration Tests
**Target**: Key workflows
**Location**: `tests/integration/`

**Coverage**:
- Database operations
- API endpoints with real DB
- DSPy pipeline with real Ollama
- Redis caching
- Background jobs

**Best Practices**:
- Use test database
- Clean up after tests
- Test realistic scenarios
- Acceptable slower execution (<30 seconds)

### E2E Tests
**Target**: Critical user journeys
**Location**: `tests/e2e/`

**Coverage**:
- Complete message processing flow
- Scraper to database flow
- API to UI flow

**Best Practices**:
- Test production-like environment
- Test failure recovery
- Can be slow (acceptable 1-2 minutes)

### Performance Tests
**Target**: Performance baselines
**Location**: `tests/performance/`

**Metrics**:
- API response times (p50, p95, p99)
- Pipeline throughput
- Database query performance
- Memory usage under load

**Tools**: Locust, pytest-benchmark

---

## Definition of Done

### For Each Task:
- [ ] Code implemented
- [ ] Tests written and passing
- [ ] Documentation updated
- [ ] Code reviewed (self-review minimum)
- [ ] No linting errors
- [ ] No type errors
- [ ] Security check passed

### For Each Sprint:
- [ ] All tasks complete
- [ ] All tests passing
- [ ] Coverage target met
- [ ] Demo prepared
- [ ] Retrospective conducted
- [ ] Next sprint planned

---

## Risk Management

### Identified Risks:

**Risk 1: Ollama Performance**
- **Impact**: High
- **Probability**: Medium
- **Mitigation**: Test with realistic messages early, have OpenAI API as backup

**Risk 2: LinkedIn Scraper Detection**
- **Impact**: High
- **Probability**: High
- **Mitigation**: Rate limiting, session management, manual fallback

**Risk 3: Scope Creep**
- **Impact**: Medium
- **Probability**: High
- **Mitigation**: Strict sprint boundaries, defer nice-to-haves to Sprint 4

**Risk 4: Test Coverage Time**
- **Impact**: Medium
- **Probability**: Medium
- **Mitigation**: Write tests alongside code, not after

---

## Success Criteria

### Technical:
- [ ] All services running reliably
- [ ] <5% error rate
- [ ] <2s pipeline execution time
- [ ] >80% test coverage
- [ ] Zero critical security vulnerabilities

### Business:
- [ ] Can process 100+ messages/day
- [ ] 90% accuracy in scoring
- [ ] Generated responses are usable
- [ ] System is observable and debuggable

### Demo:
- [ ] Can show working end-to-end system
- [ ] Can show observability features
- [ ] Can show test coverage
- [ ] Can show production-ready aspects

---

**Last Updated**: 2024-01-16
**Document Owner**: Engineering Team
**Review Frequency**: End of each sprint