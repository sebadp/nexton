# Testing and Validation Guide

Comprehensive guide for testing and validating the LinkedIn AI Agent Platform (Sprint 3 Release).

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Quick Pipeline Testing](#quick-pipeline-testing-no-infrastructure-required)
- [Automated Tests](#automated-tests)
- [Manual Testing](#manual-testing)
- [Sprint 3 Features Testing](#sprint-3-features-testing)
- [Integration Testing](#integration-testing)
- [Performance Testing](#performance-testing)
- [Monitoring Validation](#monitoring-validation)
- [Troubleshooting](#troubleshooting)

---

## Overview

This guide covers both **automated** and **manual** testing procedures to validate all features:

### Sprint 2 Features ✅
- Redis caching layer
- OpenTelemetry distributed tracing
- Prometheus metrics
- Monitoring stack (Grafana, Loki, Jaeger)
- Celery background jobs
- LinkedIn scraper
- Service layer pattern

### Sprint 3 Features 🆕
- Multi-model LLM support (OpenAI, Anthropic, Ollama)
- Email notifications with SMTP
- Automated response workflow (approve/edit/decline)
- LinkedIn message sending
- Pending responses database model
- Response API endpoints

---

## Prerequisites

### System Requirements

```bash
# Check Python version (3.11+)
python --version

# Check Docker and Docker Compose
docker --version
docker-compose --version

# Check available ports (should be free)
lsof -i :8000  # API
lsof -i :5432  # PostgreSQL
lsof -i :6379  # Redis
lsof -i :3000  # Grafana
lsof -i :9090  # Prometheus
lsof -i :16686 # Jaeger
lsof -i :5555  # Flower
```

### Environment Setup

```bash
# 1. Clone and navigate
cd /Users/sebastiandavila/PycharmProjects/nexton

# 2. Verify .env configuration
cat .env | grep -E "(ENV|DEBUG|DATABASE_URL|REDIS_URL)"

# 3. Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 4. Install aiosqlite for tests
pip install aiosqlite
```

---

## Quick Pipeline Testing (No Infrastructure Required)

These scripts let you test the DSPy pipeline without starting the full Docker stack.

### 1. Test with Sample Messages (Offline)

```bash
# Test pipeline with predefined sample messages
# No LinkedIn login required - uses hardcoded test cases
python test_message_generation.py --sample
```

This tests:
- **Conversation state detection**: NEW_OPPORTUNITY, FOLLOW_UP, COURTESY_CLOSE
- **Hard filters**: 4-day work week requirement, salary minimums, tech stack match
- **AI response generation**: Personalized responses based on profile
- **Manual review detection**: Flags ambiguous follow-ups that need human attention

**Expected output for each message:**
- 🆕 NEW_OPPORTUNITY → Full scoring + AI response
- 🔄 FOLLOW_UP → Manual review required OR auto-response (salary/availability questions)
- 👋 COURTESY_CLOSE → Ignored (no response generated)

### 2. Test with Real LinkedIn Messages

```bash
# Scrapes real messages and generates responses (without sending)
python test_message_generation.py
```

**Requires:**
- `LINKEDIN_EMAIL` and `LINKEDIN_PASSWORD` in `.env`
- LLM provider running (Ollama recommended: `ollama serve`)

**What it does:**
1. Logs into LinkedIn
2. Scrapes up to 10 recent messages
3. Processes each through the DSPy pipeline
4. Shows conversation state, scoring, hard filter results
5. Displays generated AI responses (NOT sent to LinkedIn)

### 3. Run Daily Scrape & Email Summary

```bash
# Full pipeline: scrape → process → save to DB → send email summary
python scripts/run_daily_scrape.py
```

**View emails at:** http://localhost:8025 (Mailpit)

**What it does:**
1. Scrapes unread LinkedIn messages
2. Processes each through DSPy pipeline
3. Saves opportunities to database
4. Sends ONE summary email with all new opportunities

This is the same task that runs daily at 9 AM via Celery Beat.

**Requires:**
- PostgreSQL running (`docker-compose up -d postgres`)
- Mailpit running (`docker run -d -p 1025:1025 -p 8025:8025 axllent/mailpit`)
- LinkedIn credentials in `.env`
- LLM provider configured

### 4. Via Celery (Alternative)

```bash
# Trigger the daily task via Celery CLI
celery -A app.tasks.celery_app call app.tasks.scraping_tasks.scrape_and_send_daily_summary
```

---

## Lite Version (No Infrastructure)

The **Lite Version** allows you to run the LinkedIn Agent without any infrastructure (no Database, Redis, Celery, FastAPI, or Docker). Perfect for:
- Quick testing and development
- Running on low-resource machines
- Simple cron-based automation
- Learning how the pipeline works

### Quick Start

```bash
# 1. Install lite dependencies only (~15 packages vs ~60)
pip install -r requirements-lite.txt
playwright install chromium

# 2. Copy the lite environment template
cp env.lite.example .env

# 3. Edit .env with your credentials
# - LINKEDIN_EMAIL / LINKEDIN_PASSWORD
# - LLM_PROVIDER (ollama recommended)
# - NOTIFICATION_EMAIL

# 4. Start Ollama (if using local LLM)
ollama serve
ollama pull llama3.2

# 5. Start Mailpit to view emails locally
docker run -d -p 1025:1025 -p 8025:8025 axllent/mailpit

# 6. Run the lite agent
python scripts/run_lite.py
```

### Usage Options

```bash
# Run with sample messages (no LinkedIn login needed)
python scripts/run_lite.py --sample

# Limit number of messages to process
python scripts/run_lite.py --limit 5

# Skip email sending (just process and print results)
python scripts/run_lite.py --no-email

# Verbose output
python scripts/run_lite.py -v
```

### What the Lite Version Does

1. **Scrapes LinkedIn** - Gets unread messages from your inbox
2. **Processes with DSPy Pipeline** - Runs full analysis:
   - Conversation state detection (NEW_OPPORTUNITY, FOLLOW_UP, COURTESY_CLOSE)
   - Message extraction (company, role, salary, tech stack)
   - Scoring (0-100 with tier classification)
   - Hard filter checks (4-day work week, salary minimums)
   - AI response generation
3. **Sends Email Summary** - Beautiful HTML email with all results

### Sample Output

```
╔═══════════════════════════════════════════════════════════╗
║           LinkedIn Agent Lite                             ║
║           No DB • No Redis • No Docker                    ║
╚═══════════════════════════════════════════════════════════╝

🔧 Configuring DSPy with ollama/llama3.2...
📝 Using 5 sample messages...

📨 Found 5 messages to process

============================================================
Message #1 ✅ 🆕
============================================================
From: María García - Tech Recruiter
State: NEW_OPPORTUNITY
  → New job opportunity with specific details

Extracted Data:
  Company: TechCorp
  Role: Senior Backend Engineer
  Tech Stack: Python, FastAPI, PostgreSQL, Redis, AWS
  Salary: $150,000 - $180,000

Scoring:
  Total: 85/100 (HIGH_PRIORITY)
  Tech Stack: 35/40
  Salary: 25/30
  Seniority: 18/20
  Company: 7/10

💬 AI Response:
----------------------------------------
  Hola María,

  ¡Gracias por contactarme! La posición en TechCorp
  suena muy interesante...
----------------------------------------

Processing time: 2345ms

📧 Email sent to: your_email@gmail.com
   View at: http://localhost:8025

✅ Done!
```

### RAM Usage Comparison

| Component | Full Version | Lite Version |
|-----------|-------------|--------------|
| PostgreSQL | ~200MB | 0 |
| Redis | ~50MB | 0 |
| Celery Worker | ~150MB | 0 |
| FastAPI/Uvicorn | ~100MB | 0 |
| Monitoring stack | ~300MB | 0 |
| **Script** | - | ~100MB |
| Playwright browser | ~200MB | ~200MB |
| Ollama (if local) | ~4GB | ~4GB |
| **Total (without Ollama)** | **~1GB** | **~300MB** |

### Automation with Cron

Run daily at 9 AM:

```bash
# Edit crontab
crontab -e

# Add this line (adjust paths)
0 9 * * * cd /path/to/nexton && /path/to/venv/bin/python scripts/run_lite.py >> /var/log/linkedin-agent.log 2>&1
```

### Troubleshooting Lite Version

**Error: "LINKEDIN_EMAIL and LINKEDIN_PASSWORD must be set"**
```bash
# Use sample messages for testing
python scripts/run_lite.py --sample
```

**Error: "Failed to configure DSPy with ollama"**
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# If not, start it
ollama serve
```

**No email received**
```bash
# Check if Mailpit is running
docker ps | grep mailpit

# If not, start it
docker run -d -p 1025:1025 -p 8025:8025 axllent/mailpit

# Verify SMTP settings in .env
cat .env | grep SMTP
```

---

## Automated Tests

### 1. Run All Tests

```bash
# Run complete test suite
pytest tests/ -v --cov=app --cov-report=html

# Expected: 50+ tests passing
# Coverage: ~80% for Sprint 2 modules
```

### 2. Run Tests by Category

#### Unit Tests
```bash
# Configuration tests
pytest tests/unit/test_config.py -v
# Expected: 7 tests passing

# Cache tests
pytest tests/unit/test_cache.py -v
# Expected: 24 tests passing

# Observability tests
pytest tests/unit/test_observability.py -v
# Expected: 20 tests passing

# Models tests
pytest tests/unit/test_models.py -v
# Expected: 5 tests passing

# Repository tests
pytest tests/unit/test_repositories.py -v
# Expected: 11 tests passing
```

#### Integration Tests
```bash
# Database integration
pytest tests/integration/test_database.py -v
# Expected: Full CRUD flow working

# Service layer integration
pytest tests/integration/test_service_layer.py -v
# Expected: 18 tests passing

# Celery tasks
pytest tests/integration/test_celery_tasks.py -v
# Expected: 20 tests passing

# Metrics API
pytest tests/integration/test_metrics_api.py -v
# Expected: 12 tests passing
```

### 3. Coverage Report

```bash
# Generate HTML coverage report
pytest tests/ --cov=app --cov-report=html

# Open report
open htmlcov/index.html

# Target coverage by module:
# - app/cache/: 85%+
# - app/observability/: 80%+
# - app/services/: 85%+
# - app/core/: 80%+
```

---

## Manual Testing

### Phase 1: Infrastructure Setup

#### 1.1 Start Core Services

```bash
# Start PostgreSQL and Redis
docker-compose up -d postgres redis

# Verify services
docker-compose ps

# Check logs
docker-compose logs postgres
docker-compose logs redis

# Expected: Both services "healthy"
```

#### 1.2 Database Initialization

```bash
# Run migrations
docker-compose exec api alembic upgrade head

# Verify tables
docker-compose exec postgres psql -U postgres -d linkedin_agent -c "\dt"

# Expected tables:
# - opportunities
# - alembic_version
```

#### 1.3 Start Application Services

```bash
# Start API and workers
docker-compose up -d api worker

# Check status
docker-compose ps

# View logs
docker-compose logs -f api
docker-compose logs -f worker

# Expected: Services running without errors
```

### Phase 2: API Testing

#### 2.1 Health Checks

```bash
# Basic health
curl http://localhost:8000/health

# Expected response:
# {
#   "status": "healthy",
#   "timestamp": "2024-01-17T...",
#   "version": "1.0.0",
#   "environment": "development"
# }

# Readiness check (checks all dependencies)
curl http://localhost:8000/health/ready

# Expected response:
# {
#   "status": "ready",
#   "checks": {
#     "database": "healthy",
#     "redis": "healthy",
#     "ollama": "healthy"
#   },
#   "timestamp": "..."
# }
```

#### 2.2 API Documentation

```bash
# Open Swagger UI
open http://localhost:8000/docs

# Verify endpoints:
# - GET /health
# - GET /health/ready
# - GET /api/v1/metrics
# - POST /api/v1/opportunities
# - GET /api/v1/opportunities
# - GET /api/v1/opportunities/{id}
# - DELETE /api/v1/opportunities/{id}
# - GET /api/v1/opportunities/stats
```

#### 2.3 Create Opportunity

```bash
# Create test opportunity
curl -X POST http://localhost:8000/api/v1/opportunities \
  -H "Content-Type: application/json" \
  -d '{
    "recruiter_name": "Jane Smith",
    "raw_message": "Hi! We have an exciting Senior Python Developer role at TechCorp. Salary range: $150k-$180k. Stack: Python, FastAPI, PostgreSQL, Redis, Docker. Looking for 5+ years experience. Interested?"
  }'

# Expected response:
# {
#   "id": 1,
#   "recruiter_name": "Jane Smith",
#   "company": "TechCorp",
#   "position": "Senior Python Developer",
#   "tech_stack": ["Python", "FastAPI", "PostgreSQL", "Redis", "Docker"],
#   "salary_min": 150000,
#   "salary_max": 180000,
#   "tech_stack_score": 30,
#   "salary_score": 25,
#   "seniority_score": 20,
#   "company_score": 15,
#   "total_score": 90,
#   "tier": "A",
#   "status": "processed",
#   ...
# }
```

#### 2.4 List Opportunities

```bash
# List all opportunities
curl http://localhost:8000/api/v1/opportunities

# List with filters
curl "http://localhost:8000/api/v1/opportunities?tier=A&status=processed&limit=10"

# Expected: Paginated list with opportunities
```

#### 2.5 Get Statistics

```bash
# Get stats
curl http://localhost:8000/api/v1/opportunities/stats

# Expected response:
# {
#   "total_opportunities": 1,
#   "by_tier": {
#     "A": 1,
#     "B": 0,
#     "C": 0,
#     "D": 0
#   },
#   "by_status": {
#     "processed": 1,
#     "pending": 0,
#     "contacted": 0,
#     "rejected": 0
#   },
#   "average_score": 90.0
# }
```

### Phase 3: Caching Validation

#### 3.1 Test Cache Hit

```bash
# First request (cache miss)
time curl -X POST http://localhost:8000/api/v1/opportunities \
  -H "Content-Type: application/json" \
  -d '{
    "recruiter_name": "Test Recruiter",
    "raw_message": "Test message for caching"
  }'

# Note the response time (e.g., 2.5s)

# Second request with same message (cache hit)
time curl -X POST http://localhost:8000/api/v1/opportunities \
  -H "Content-Type: application/json" \
  -d '{
    "recruiter_name": "Test Recruiter",
    "raw_message": "Test message for caching"
  }'

# Expected: Much faster response (~0.1s)
# Cache hit should be 10-20x faster
```

#### 3.2 Verify Redis Cache

```bash
# Connect to Redis
docker-compose exec redis redis-cli

# List cache keys
KEYS opportunity:*
KEYS pipeline:*

# Check specific key
GET "pipeline:hash:abc123..."

# Check TTL
TTL "pipeline:hash:abc123..."

# Expected: Keys present with appropriate TTLs
```

### Phase 4: Background Jobs

#### 4.1 Start Celery Services

```bash
# Start worker
docker-compose up -d worker

# Start Flower (monitoring)
docker-compose up -d flower

# Access Flower dashboard
open http://localhost:5555

# Expected: Flower UI showing active workers
```

#### 4.2 Test Background Tasks

```bash
# Trigger opportunity processing task
# (automatically triggered by API, but can test directly)

# Check Flower for task execution
# Navigate to: http://localhost:5555/tasks

# Expected: Tasks appearing and completing
```

#### 4.3 Monitor Worker Logs

```bash
# View worker logs
docker-compose logs -f worker

# Expected log entries:
# - Task received
# - Task started
# - Task succeeded/failed
# - Processing times
```

### Phase 5: Monitoring Stack

#### 5.1 Start Monitoring Services

```bash
# Start full monitoring stack
docker-compose -f docker-compose.monitoring.yml up -d

# Verify all services
docker-compose -f docker-compose.monitoring.yml ps

# Expected services running:
# - prometheus
# - grafana
# - jaeger
# - loki
# - promtail
```

#### 5.2 Prometheus Validation

```bash
# Access Prometheus
open http://localhost:9090

# Check targets
open http://localhost:9090/targets

# Expected targets (all UP):
# - linkedin-agent-api (localhost:8000)
# - redis-exporter (localhost:9121)
# - postgres-exporter (localhost:9187)
# - node-exporter (localhost:9100)

# Run test queries:
# 1. opportunities_created_total
# 2. cache_operations_total
# 3. dspy_pipeline_executions_total
# 4. http_requests_total

# Expected: Metrics data available
```

#### 5.3 Grafana Dashboards

```bash
# Access Grafana
open http://localhost:3000

# Login: admin / admin
# Change password on first login

# Verify datasources:
# Navigation: Configuration > Data Sources
# Expected:
# - Prometheus (default)
# - Loki
# - Jaeger

# Import dashboard:
# 1. Go to Dashboards > Browse
# 2. Check for "LinkedIn Agent Platform" dashboard
# 3. Open and verify panels:
#    - Request Rate
#    - Error Rate
#    - Response Time
#    - Cache Hit Rate
#    - Pipeline Execution Time
#    - Opportunities by Tier
#    - Database Queries
```

#### 5.4 Jaeger Tracing

```bash
# Access Jaeger UI
open http://localhost:16686

# Select service: "linkedin-agent"

# Perform some API requests to generate traces:
curl -X POST http://localhost:8000/api/v1/opportunities \
  -H "Content-Type: application/json" \
  -d '{"recruiter_name": "Test", "raw_message": "Test trace"}'

# In Jaeger:
# 1. Select "linkedin-agent" service
# 2. Click "Find Traces"
# 3. Click on a trace to view details

# Expected trace spans:
# - HTTP POST /api/v1/opportunities
# - cache.get
# - dspy.pipeline.forward
# - db.insert
# - cache.set

# Verify:
# - Span timings
# - Tags/attributes
# - No errors
```

#### 5.5 Loki Logs

```bash
# In Grafana, go to Explore
# Select Loki datasource

# Example queries:
{job="linkedin-agent"} |= "opportunity"
{job="linkedin-agent"} |= "error"
{job="linkedin-agent"} |= "cache"

# Expected: Structured logs visible with filtering
```

### Phase 6: Metrics Validation

#### 6.1 Metrics Endpoint

```bash
# Get Prometheus metrics
curl http://localhost:8000/api/v1/metrics

# Expected output (Prometheus format):
# HELP opportunities_created_total Total opportunities created
# TYPE opportunities_created_total counter
# opportunities_created_total{tier="A",status="processed"} 1.0
# ...

# Verify metric categories:
# - Business metrics (opportunities_*)
# - Pipeline metrics (dspy_pipeline_*)
# - Cache metrics (cache_*)
# - Database metrics (db_*)
# - HTTP metrics (http_*)
```

#### 6.2 Test Metric Updates

```bash
# Create multiple opportunities
for i in {1..5}; do
  curl -X POST http://localhost:8000/api/v1/opportunities \
    -H "Content-Type: application/json" \
    -d "{
      \"recruiter_name\": \"Recruiter $i\",
      \"raw_message\": \"Test message $i\"
    }"
done

# Check metrics again
curl http://localhost:8000/api/v1/metrics | grep opportunities_created_total

# Expected: Counter increased by 5
```

---

## Sprint 3 Features Testing

### Phase 7: Multi-Model LLM Support

#### 7.1 Test LLM Provider Switching

```bash
# Test with Ollama (default)
curl -X POST http://localhost:8000/api/v1/opportunities \
  -H "Content-Type: application/json" \
  -d '{
    "recruiter_name": "Test",
    "raw_message": "Python Developer role. $120k."
  }'

# Configure OpenAI
# Edit .env: LLM_PROVIDER=openai
docker-compose restart api worker

# Test with OpenAI
curl -X POST http://localhost:8000/api/v1/opportunities \
  -H "Content-Type: application/json" \
  -d '{
    "recruiter_name": "Test",
    "raw_message": "Python Developer role. $120k."
  }'

# Check logs for provider
docker-compose logs api | grep llm_provider

# Expected: Log showing provider being used
```

#### 7.2 Verify Cost Tracking

```bash
# Check LLM cost metrics
curl http://localhost:8000/api/v1/metrics | grep llm_cost

# Expected output:
# llm_cost_usd_total{provider="openai",model="gpt-4"} 0.05
# llm_tokens_used_total{provider="openai",model="gpt-4",type="prompt"} 1500
```

### Phase 8: Email Notifications

#### 8.1 Setup Mailpit for Testing

```bash
# Start Mailpit (captures emails without sending)
docker run -d -p 1025:1025 -p 8025:8025 --name mailpit axllent/mailpit

# Configure .env
SMTP_HOST=localhost
SMTP_PORT=1025
SMTP_USE_TLS=false
NOTIFICATION_EMAIL=test@example.com
NOTIFICATION_ENABLED=true
NOTIFICATION_TIER_THRESHOLD=["A", "B"]
NOTIFICATION_SCORE_THRESHOLD=0

# Restart services
docker-compose restart api
```

#### 8.2 Test Email Sending

```bash
# Create opportunity (should trigger email)
curl -X POST http://localhost:8000/api/v1/opportunities \
  -H "Content-Type: application/json" \
  -d '{
    "recruiter_name": "Jane Doe",
    "raw_message": "Senior Python Engineer at TechCorp. $180k. Python, FastAPI, PostgreSQL."
  }'

# Check Mailpit UI
open http://localhost:8025

# Expected:
# - Email received with opportunity details
# - AI-generated response included
# - Action buttons: Approve, Edit, Decline
# - Beautiful HTML template
```

#### 8.3 Test Notification Rules

```bash
# Create low-tier opportunity (should NOT notify)
curl -X POST http://localhost:8000/api/v1/opportunities \
  -H "Content-Type: application/json" \
  -d '{
    "recruiter_name": "Test",
    "raw_message": "Junior PHP Developer. $50k."
  }'

# Check Mailpit - should have NO new email

# Create high-tier opportunity (should notify)
curl -X POST http://localhost:8000/api/v1/opportunities \
  -H "Content-Type: application/json" \
  -d '{
    "recruiter_name": "Google Recruiter",
    "raw_message": "Staff Engineer at Google. $250k. Python, Go, Kubernetes."
  }'

# Check Mailpit - should have new email
```

### Phase 9: Response Workflow

#### 9.1 Test Pending Response Creation

```bash
# Create opportunity
OPP_RESPONSE=$(curl -X POST http://localhost:8000/api/v1/opportunities \
  -H "Content-Type: application/json" \
  -d '{
    "recruiter_name": "Test Recruiter",
    "raw_message": "Backend Engineer position. Python, Docker."
  }')

# Extract opportunity ID
OPP_ID=$(echo $OPP_RESPONSE | jq -r '.id')

# Get pending response
curl http://localhost:8000/api/v1/responses/$OPP_ID | jq '.'

# Expected response:
# {
#   "id": 1,
#   "opportunity_id": 1,
#   "original_response": "Thank you for reaching out...",
#   "status": "pending",
#   "created_at": "..."
# }
```

#### 9.2 Test Response Approval

```bash
# Approve response (no edits)
curl -X POST http://localhost:8000/api/v1/responses/$OPP_ID/approve \
  -H "Content-Type: application/json" | jq '.'

# Expected:
# {
#   "id": 1,
#   "status": "approved",
#   "approved_at": "2026-01-18T...",
#   "final_response": "Thank you for reaching out..."
# }

# Check Celery logs for task
docker-compose logs -f worker

# Expected log:
# Task send_linkedin_response[...] received
# starting_linkedin_response_send_task response_id=1
```

#### 9.3 Test Response Editing

```bash
# Create new opportunity
OPP_ID=2

# Edit and approve
curl -X POST http://localhost:8000/api/v1/responses/$OPP_ID/edit \
  -H "Content-Type: application/json" \
  -d '{
    "edited_response": "Thank you! I am very interested in this opportunity. Could we schedule a call?"
  }' | jq '.'

# Expected:
# {
#   "status": "approved",
#   "edited_response": "Thank you! I am very interested...",
#   "final_response": "Thank you! I am very interested..."
# }
```

#### 9.4 Test Response Decline

```bash
# Decline response
curl -X POST http://localhost:8000/api/v1/responses/$OPP_ID/decline | jq '.'

# Expected:
# {
#   "status": "declined",
#   "declined_at": "2026-01-18T..."
# }

# Verify no LinkedIn task was queued
docker-compose logs worker | grep "response_id=$OPP_ID"
# Should show NO task for declined response
```

#### 9.5 List Pending Responses

```bash
# List all pending responses
curl http://localhost:8000/api/v1/responses?limit=10 | jq '.'

# Expected: Array of pending responses
# [
#   {
#     "id": 1,
#     "opportunity_id": 1,
#     "status": "pending",
#     ...
#   }
# ]
```

### Phase 10: LinkedIn Message Sending

#### 10.1 Test LinkedIn Messenger (Manual)

**Note**: This requires real LinkedIn credentials and should be tested carefully.

```bash
# Configure LinkedIn credentials in .env
LINKEDIN_EMAIL=your_real_email@example.com
LINKEDIN_PASSWORD=your_real_password

# Restart worker
docker-compose restart worker

# Create and approve a response
# (Follow steps from Phase 9.2)

# Watch Celery logs
docker-compose logs -f worker

# Expected logs:
# initializing_linkedin_messenger
# logging_into_linkedin
# linkedin_login_successful
# sending_linkedin_message
# linkedin_message_sent_successfully
# pending_response_sent_successfully
```

#### 10.2 Test Error Handling

```bash
# Use invalid LinkedIn credentials
LINKEDIN_EMAIL=invalid@test.com
LINKEDIN_PASSWORD=wrong_password

# Restart worker
docker-compose restart worker

# Approve a response
curl -X POST http://localhost:8000/api/v1/responses/1/approve

# Check logs for error
docker-compose logs worker

# Expected:
# linkedin_login_failed
# linkedin_response_send_failed
# Response marked as "failed" in database

# Verify in database
curl http://localhost:8000/api/v1/responses/1 | jq '.status'
# Expected: "failed"
```

#### 10.3 Test Retry Logic

```bash
# Check Celery Flower
open http://localhost:5555/tasks

# Find failed task
# Should show:
# - Status: RETRY
# - Retries: 1/3
# - Next retry: +5 minutes

# After 3 retries, status should be FAILURE
```

### Phase 11: Complete Workflow Test

End-to-end test of the full notification + response workflow:

```bash
# 1. Start Mailpit
docker run -d -p 1025:1025 -p 8025:8025 axllent/mailpit

# 2. Configure .env
NOTIFICATION_ENABLED=true
NOTIFICATION_EMAIL=test@example.com
SMTP_HOST=localhost
SMTP_PORT=1025

# 3. Create opportunity
curl -X POST http://localhost:8000/api/v1/opportunities \
  -H "Content-Type: application/json" \
  -d '{
    "recruiter_name": "Sarah Johnson",
    "raw_message": "Senior Python Engineer at TechStartup. $170k. Python, FastAPI, Docker, AWS."
  }' > /tmp/opp_response.json

OPP_ID=$(cat /tmp/opp_response.json | jq -r '.id')

# 4. Check email received
open http://localhost:8025
# Should see email with opportunity details

# 5. Check pending response created
curl http://localhost:8000/api/v1/responses/$OPP_ID | jq '.'

# 6. Approve response
curl -X POST http://localhost:8000/api/v1/responses/$OPP_ID/approve

# 7. Verify status changes
curl http://localhost:8000/api/v1/responses/$OPP_ID | jq '.status'
# Should change: pending → approved → sent

# 8. Check Celery task execution
docker-compose logs worker | grep "response_id=$OPP_ID"

# 9. Verify in database
docker-compose exec postgres psql -U postgres -d linkedin_agent \
  -c "SELECT status, sent_at FROM pending_responses WHERE id = $OPP_ID;"

# Expected:
#  status |          sent_at
# --------+----------------------------
#  sent   | 2026-01-18 10:30:45.123456
```

---

## Integration Testing

### Scenario 1: Complete Opportunity Flow

```bash
# 1. Create opportunity (first time - cache miss)
curl -X POST http://localhost:8000/api/v1/opportunities \
  -H "Content-Type: application/json" \
  -d '{
    "recruiter_name": "Sarah Johnson",
    "raw_message": "Senior Backend Engineer at CloudCorp. $160k-$200k. Python, Go, Kubernetes, AWS. 7+ years exp required."
  }' | jq '.'

# 2. Verify in database
curl http://localhost:8000/api/v1/opportunities | jq '.items[0]'

# 3. Check cache (should be cached now)
docker-compose exec redis redis-cli KEYS "pipeline:*"

# 4. Create same opportunity again (cache hit)
curl -X POST http://localhost:8000/api/v1/opportunities \
  -H "Content-Type: application/json" \
  -d '{
    "recruiter_name": "Sarah Johnson",
    "raw_message": "Senior Backend Engineer at CloudCorp. $160k-$200k. Python, Go, Kubernetes, AWS. 7+ years exp required."
  }' | jq '.'

# 5. Verify tracing in Jaeger
# Should see trace with cache.get hit

# 6. Check metrics in Prometheus
# cache_operations_total{operation="get",status="hit"} should increase

# 7. View in Grafana dashboard
# Cache hit rate should show increase
```

### Scenario 2: Multiple Tier Classification

```bash
# Create A-tier opportunity
curl -X POST http://localhost:8000/api/v1/opportunities \
  -H "Content-Type: application/json" \
  -d '{
    "recruiter_name": "Tech Lead",
    "raw_message": "Staff Engineer at Google. $200k-$250k. Python, Kubernetes, Distributed Systems. 10+ years."
  }'

# Create B-tier opportunity
curl -X POST http://localhost:8000/api/v1/opportunities \
  -H "Content-Type: application/json" \
  -d '{
    "recruiter_name": "Startup Recruiter",
    "raw_message": "Backend Dev at StartupXYZ. $100k-$120k. Python, Flask. 3 years exp."
  }'

# Create C-tier opportunity
curl -X POST http://localhost:8000/api/v1/opportunities \
  -H "Content-Type: application/json" \
  -d '{
    "recruiter_name": "Agency",
    "raw_message": "Junior Developer role. $60k-$80k. PHP, WordPress. 1 year exp."
  }'

# Check statistics
curl http://localhost:8000/api/v1/opportunities/stats | jq '.'

# Expected output:
# {
#   "total_opportunities": 3,
#   "by_tier": {
#     "A": 1,
#     "B": 1,
#     "C": 1,
#     "D": 0
#   },
#   ...
# }

# Verify in Grafana
# "Opportunities by Tier" panel should show distribution
```

### Scenario 3: Error Handling

```bash
# Test invalid input
curl -X POST http://localhost:8000/api/v1/opportunities \
  -H "Content-Type: application/json" \
  -d '{
    "recruiter_name": "",
    "raw_message": ""
  }'

# Expected: 422 Validation Error

# Test missing fields
curl -X POST http://localhost:8000/api/v1/opportunities \
  -H "Content-Type: application/json" \
  -d '{
    "recruiter_name": "Test"
  }'

# Expected: 422 Validation Error

# Verify error metrics
curl http://localhost:8000/api/v1/metrics | grep http_requests_total | grep 422

# Check error logs in Loki
# {job="linkedin-agent"} |= "error"
```

---

## Performance Testing

### 1. Load Testing Setup

```bash
# Install locust
pip install locust

# Create locustfile.py (provided below)
```

**locustfile.py:**
```python
from locust import HttpUser, task, between

class LinkedInAgentUser(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def create_opportunity(self):
        self.client.post("/api/v1/opportunities", json={
            "recruiter_name": "Test Recruiter",
            "raw_message": "Test opportunity message for load testing"
        })

    @task(1)
    def list_opportunities(self):
        self.client.get("/api/v1/opportunities?limit=10")

    @task(1)
    def get_stats(self):
        self.client.get("/api/v1/opportunities/stats")

    @task(1)
    def health_check(self):
        self.client.get("/health")
```

### 2. Run Load Test

```bash
# Start locust
locust -f locustfile.py --host=http://localhost:8000

# Access Locust UI
open http://localhost:8089

# Configure:
# - Number of users: 10
# - Spawn rate: 2 users/second
# - Host: http://localhost:8000

# Run for 5 minutes and observe:
# - Response times
# - Request rate
# - Failure rate
# - Cache hit rate in Grafana
```

### 3. Performance Metrics

Monitor during load test:

```bash
# Grafana Dashboard
open http://localhost:3000

# Check panels:
# - Request Rate: Should handle 50-100 req/s
# - Response Time p95: Should be < 500ms
# - Cache Hit Rate: Should be > 80% after warmup
# - Error Rate: Should be < 1%

# Prometheus queries:
rate(http_requests_total[1m])
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[1m]))
rate(cache_operations_total{status="hit"}[1m]) / rate(cache_operations_total[1m])
```

---

## Monitoring Validation

### Checklist: Prometheus Metrics

- [ ] `opportunities_created_total` - Increments on new opportunities
- [ ] `opportunities_by_tier` - Shows current count by tier
- [ ] `opportunity_score_distribution` - Histogram of scores
- [ ] `dspy_pipeline_executions_total` - Pipeline execution count
- [ ] `dspy_pipeline_execution_time_seconds` - Pipeline duration
- [ ] `cache_operations_total` - Cache ops by operation and status
- [ ] `cache_hit_rate` - Calculated hit rate
- [ ] `db_queries_total` - Database query count
- [ ] `http_requests_total` - HTTP request count by endpoint

### Checklist: Grafana Dashboards

- [ ] Dashboard loads without errors
- [ ] All panels show data
- [ ] Time range selector works
- [ ] Refresh works correctly
- [ ] Annotations visible (if configured)
- [ ] Variables work (if configured)

### Checklist: Jaeger Tracing

- [ ] Traces appear after API requests
- [ ] All spans present:
  - HTTP request span
  - Cache operation spans
  - Pipeline execution span
  - Database operation spans
- [ ] Span timings reasonable
- [ ] No error spans (unless testing errors)
- [ ] Tags/attributes populated correctly

### Checklist: Loki Logs

- [ ] Logs ingested from all services
- [ ] Log labels correct (`job`, `level`, etc.)
- [ ] LogQL queries work
- [ ] Logs correlate with traces (if traceID present)
- [ ] Structured logging fields parseable

---

## Troubleshooting

### Issue: Tests Failing

```bash
# Check Python version
python --version  # Should be 3.11+

# Reinstall dependencies
pip install -r requirements.txt -r requirements-dev.txt

# Check for missing dependencies
pip list | grep -E "(pytest|pydantic|sqlalchemy|redis|celery)"

# Run specific failing test with verbose output
pytest tests/unit/test_config.py::test_name -vv
```

### Issue: Services Won't Start

```bash
# Check Docker status
docker ps

# Check logs for errors
docker-compose logs api
docker-compose logs postgres
docker-compose logs redis

# Restart services
docker-compose down
docker-compose up -d

# Check for port conflicts
lsof -i :8000
lsof -i :5432
lsof -i :6379
```

### Issue: Database Connection Failed

```bash
# Verify PostgreSQL is running
docker-compose ps postgres

# Check PostgreSQL logs
docker-compose logs postgres

# Test connection
docker-compose exec postgres psql -U postgres -d linkedin_agent

# Run migrations
docker-compose exec api alembic upgrade head
```

### Issue: Redis Connection Failed

```bash
# Verify Redis is running
docker-compose ps redis

# Test Redis connection
docker-compose exec redis redis-cli ping
# Expected: PONG

# Check Redis logs
docker-compose logs redis
```

### Issue: Prometheus No Data

```bash
# Check Prometheus targets
open http://localhost:9090/targets

# All targets should be UP
# If DOWN, check service logs

# Verify metrics endpoint
curl http://localhost:8000/api/v1/metrics

# Should return Prometheus format data
```

### Issue: Grafana Datasource Error

```bash
# Check Prometheus connection
# Grafana > Configuration > Data Sources > Prometheus > Test

# Check network connectivity
docker-compose exec grafana ping prometheus

# Restart Grafana
docker-compose -f docker-compose.monitoring.yml restart grafana
```

### Issue: Jaeger No Traces

```bash
# Verify OTEL_ENABLED=true in .env
cat .env | grep OTEL_ENABLED

# Check Jaeger is running
docker-compose -f docker-compose.monitoring.yml ps jaeger

# Verify OTLP endpoint
curl http://localhost:4318/v1/traces -X POST

# Check application logs for tracing initialization
docker-compose logs api | grep -i "tracing\|telemetry"
```

### Issue: Email Not Sending (Sprint 3)

```bash
# Check SMTP configuration
cat .env | grep SMTP

# Test SMTP connection
python -c "
import smtplib
smtp = smtplib.SMTP('localhost', 1025)
smtp.starttls()
print('SMTP connection successful')
smtp.quit()
"

# Check if notifications enabled
cat .env | grep NOTIFICATION_ENABLED

# Check opportunity meets notification criteria
# Must match tier_threshold AND score_threshold

# Check logs
docker-compose logs api | grep notification

# Expected logs:
# notification_email_sent_successfully
# Or: opportunity_does_not_meet_notification_criteria
```

### Issue: Pending Response Not Created (Sprint 3)

```bash
# Check if AI response was generated
curl http://localhost:8000/api/v1/opportunities/1 | jq '.ai_response'

# Check logs
docker-compose logs api | grep pending_response

# Expected log:
# pending_response_created response_id=1
# Or: pending_response_creation_failed

# Verify database
docker-compose exec postgres psql -U postgres -d linkedin_agent \
  -c "SELECT * FROM pending_responses;"
```

### Issue: LinkedIn Message Not Sending (Sprint 3)

```bash
# Check LinkedIn credentials
cat .env | grep LINKEDIN

# Check Celery worker logs
docker-compose logs worker | grep linkedin

# Common issues:
# 1. LinkedIn requires verification (checkpoint/challenge)
#    - Check logs for "checkpoint" or "challenge"
#    - May need to verify manually first

# 2. Invalid credentials
#    - Verify email/password correct
#    - Try logging in manually to LinkedIn

# 3. Playwright not installed
playwright install chromium

# 4. Rate limiting
#    - LinkedIn may rate limit if too many messages
#    - Wait 1 hour and try again

# Check task status in Flower
open http://localhost:5555/tasks
```

### Issue: Response API Endpoint 404 (Sprint 3)

```bash
# Verify endpoint exists
curl http://localhost:8000/docs

# Check if responses router registered
docker-compose logs api | grep "responses"

# Restart API
docker-compose restart api

# Test endpoint
curl http://localhost:8000/api/v1/responses/1

# If still 404, check:
# - app/api/v1/__init__.py includes responses router
# - app/api/v1/responses.py exists
```

### Issue: Mailpit Not Showing Emails (Sprint 3)

```bash
# Check Mailpit is running
docker ps | grep mailpit

# Start Mailpit if not running
docker run -d -p 1025:1025 -p 8025:8025 axllent/mailpit

# Check SMTP configuration points to Mailpit
cat .env | grep SMTP_HOST
# Should be: localhost

cat .env | grep SMTP_PORT
# Should be: 1025

# Test email sending
curl -X POST http://localhost:8000/api/v1/opportunities \
  -H "Content-Type: application/json" \
  -d '{"recruiter_name": "Test", "raw_message": "Test"}'

# Check Mailpit UI
open http://localhost:8025

# Check API logs
docker-compose logs api | grep email
```

---

## Success Criteria

### Automated Tests
- [ ] 50+ unit tests passing
- [ ] 80%+ code coverage for Sprint 2 modules
- [ ] All integration tests passing
- [ ] No critical test failures

### Manual Tests
- [ ] All API endpoints responding correctly
- [ ] Cache hit rate > 80% after warmup
- [ ] Opportunities correctly classified by tier
- [ ] Statistics endpoint accurate

### Sprint 3 Features ✅
- [ ] Email notifications sent successfully
- [ ] Notification rules working (tier/score filtering)
- [ ] HTML email template renders correctly
- [ ] Pending responses created automatically
- [ ] Response approval workflow functional
- [ ] Response edit workflow functional
- [ ] Response decline workflow functional
- [ ] LinkedIn message sending works (with real credentials)
- [ ] Celery tasks execute successfully
- [ ] Retry logic works on failures
- [ ] Multi-LLM provider switching works
- [ ] LLM cost tracking accurate

### Monitoring
- [ ] Prometheus scraping all targets
- [ ] Grafana dashboards displaying data
- [ ] Jaeger showing complete traces
- [ ] Loki ingesting logs from all services
- [ ] LLM cost metrics appearing
- [ ] Notification metrics tracking

### Performance
- [ ] API response time p95 < 500ms
- [ ] Cache hit response time < 100ms
- [ ] System handles 50+ req/s sustained load
- [ ] No memory leaks under load
- [ ] Error rate < 1%
- [ ] Email sending < 2s
- [ ] LinkedIn message sending < 10s

### Documentation
- [ ] All features documented
- [ ] Deployment guide accurate
- [ ] Testing guide complete (this document)
- [ ] Troubleshooting section helpful
- [ ] Multi-LLM guide complete
- [ ] Notifications guide complete

---

## Next Steps

After successful validation:

1. **Tag Release**: Create git tag `v1.3.0` for Sprint 3
2. **Production Deploy**: Follow `docs/DEPLOYMENT.md` for production
3. **Configure Email**: Set up production SMTP (Gmail, SendGrid, etc.)
4. **Test Notifications**: Verify email delivery in production
5. **Monitor Initial Period**: Watch dashboards closely for 48 hours
6. **Test LinkedIn Integration**: Carefully test message sending with real credentials
7. **Gather Feedback**: Document any issues or improvements
8. **Plan Sprint 4**: Review roadmap and prioritize features

---

## Support

- **Documentation**: See `docs/` directory
- **Issues**: GitHub Issues
- **Monitoring**: http://localhost:3000 (Grafana)
- **API Docs**: http://localhost:8000/docs
