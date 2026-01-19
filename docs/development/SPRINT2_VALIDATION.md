# Sprint 2 Validation Checklist

Quick validation guide for Sprint 2 release (v1.1.0).

## 🚀 Quick Start

```bash
# 1. Run automated smoke test
./scripts/smoke_test.sh

# 2. If all tests pass, you're good to go!
# 3. For detailed testing, see docs/TESTING_GUIDE.md
```

---

## ✅ Pre-Flight Checklist

### Environment Setup

- [ ] Python 3.11+ installed
- [ ] Docker and Docker Compose installed
- [ ] All dependencies installed (`pip install -r requirements.txt`)
- [ ] `.env` file configured correctly
- [ ] Ports available (8000, 5432, 6379, 3000, 9090, 16686)

### Services Started

```bash
# Core services
docker-compose up -d postgres redis api worker

# Monitoring stack
docker-compose -f docker-compose.monitoring.yml up -d
```

- [ ] PostgreSQL running (`docker-compose ps postgres`)
- [ ] Redis running (`docker-compose ps redis`)
- [ ] API running (`docker-compose ps api`)
- [ ] Worker running (`docker-compose ps worker`)
- [ ] Monitoring stack running (optional but recommended)

---

## 🧪 Quick Validation (5 minutes)

### 1. API Health

```bash
curl http://localhost:8000/health
# Expected: {"status":"healthy",...}

curl http://localhost:8000/health/ready
# Expected: {"status":"ready","checks":{...}}
```

- [ ] Basic health endpoint working
- [ ] Readiness check shows all dependencies healthy

### 2. Create Test Opportunity

```bash
curl -X POST http://localhost:8000/api/v1/opportunities \
  -H "Content-Type: application/json" \
  -d '{
    "recruiter_name": "Test Recruiter",
    "raw_message": "Senior Python Engineer at TechCorp. $150k-$180k. Python, FastAPI, PostgreSQL, Docker. 5+ years experience."
  }'
```

- [ ] Opportunity created successfully
- [ ] Returned with valid ID, scores, and tier classification
- [ ] Response time reasonable (< 3s for first request)

### 3. Verify Caching

```bash
# Create same opportunity again
curl -X POST http://localhost:8000/api/v1/opportunities \
  -H "Content-Type: application/json" \
  -d '{
    "recruiter_name": "Test Recruiter",
    "raw_message": "Senior Python Engineer at TechCorp. $150k-$180k. Python, FastAPI, PostgreSQL, Docker. 5+ years experience."
  }'
```

- [ ] Second request much faster (< 500ms)
- [ ] Cache hit confirmed

### 4. Check Metrics

```bash
curl http://localhost:8000/api/v1/metrics | grep opportunities_created_total
```

- [ ] Metrics endpoint returns Prometheus format
- [ ] `opportunities_created_total` counter present and accurate

### 5. Verify Monitoring (if stack running)

```bash
# Prometheus
open http://localhost:9090/targets
# Expected: All targets UP

# Grafana
open http://localhost:3000
# Login: admin/admin
# Expected: Dashboard loads with data

# Jaeger
open http://localhost:16686
# Expected: Traces visible for recent requests
```

- [ ] Prometheus scraping metrics
- [ ] Grafana dashboard showing data
- [ ] Jaeger showing distributed traces

---

## 📊 Automated Test Validation

### Run Test Suite

```bash
# Run all tests
pytest tests/ -v --cov=app

# Expected results:
# - 50+ tests passing
# - 80%+ coverage for Sprint 2 modules
# - 0 critical failures
```

### Key Test Categories

```bash
# Configuration (7 tests)
pytest tests/unit/test_config.py -v

# Cache (24 tests)
pytest tests/unit/test_cache.py -v

# Observability (20 tests)
pytest tests/unit/test_observability.py -v

# Service Layer (18 tests)
pytest tests/integration/test_service_layer.py -v
```

**Expected Results:**
- [ ] Configuration tests: 7/7 passing
- [ ] Cache tests: 23+/24 passing
- [ ] Observability tests: 20/20 passing
- [ ] Service layer tests: 18/18 passing

---

## 🎯 Sprint 2 Features Validation

### Feature 1: Redis Caching

**Test:**
```bash
# First request (cache miss)
time curl -X POST http://localhost:8000/api/v1/opportunities \
  -H "Content-Type: application/json" \
  -d '{"recruiter_name":"Cache Test","raw_message":"Test message unique12345"}'

# Second request (cache hit)
time curl -X POST http://localhost:8000/api/v1/opportunities \
  -H "Content-Type: application/json" \
  -d '{"recruiter_name":"Cache Test","raw_message":"Test message unique12345"}'
```

**Success Criteria:**
- [ ] Cache miss takes 1-3 seconds
- [ ] Cache hit takes < 500ms
- [ ] Speedup of 5-10x
- [ ] Redis keys visible: `docker-compose exec redis redis-cli KEYS "pipeline:*"`

### Feature 2: OpenTelemetry Tracing

**Test:**
```bash
# Create opportunity
curl -X POST http://localhost:8000/api/v1/opportunities \
  -H "Content-Type: application/json" \
  -d '{"recruiter_name":"Trace Test","raw_message":"Test for tracing"}'

# View trace in Jaeger
open http://localhost:16686
# Select service: linkedin-agent
# Click "Find Traces"
```

**Success Criteria:**
- [ ] Trace appears in Jaeger UI
- [ ] Spans include:
  - `POST /api/v1/opportunities`
  - `cache.get`
  - `dspy.pipeline.forward`
  - `db.insert`
  - `cache.set`
- [ ] Span timings reasonable
- [ ] No error spans

### Feature 3: Prometheus Metrics

**Test:**
```bash
curl http://localhost:8000/api/v1/metrics | grep -E "(opportunities_created|cache_operations|dspy_pipeline)"
```

**Success Criteria:**
- [ ] Business metrics present:
  - `opportunities_created_total`
  - `opportunities_by_tier`
  - `opportunity_score_distribution`
- [ ] Pipeline metrics present:
  - `dspy_pipeline_executions_total`
  - `dspy_pipeline_execution_time_seconds`
- [ ] Cache metrics present:
  - `cache_operations_total`
  - `cache_hit_rate`

### Feature 4: Grafana Dashboards

**Test:**
```bash
open http://localhost:3000
# Login: admin/admin
# Navigate to Dashboards > LinkedIn Agent Platform
```

**Success Criteria:**
- [ ] Dashboard loads without errors
- [ ] All panels show data
- [ ] Key panels visible:
  - Request Rate
  - Cache Hit Rate
  - Opportunities by Tier
  - Pipeline Execution Time
  - Error Rate

### Feature 5: Celery Background Jobs

**Test:**
```bash
# Check Flower dashboard
open http://localhost:5555

# View worker logs
docker-compose logs worker
```

**Success Criteria:**
- [ ] Flower UI accessible
- [ ] Workers visible and active
- [ ] Tasks executing successfully
- [ ] No failed tasks (unless testing error handling)

### Feature 6: Service Layer

**Test:**
```bash
# Service layer handles caching, metrics, and tracing automatically
curl -X POST http://localhost:8000/api/v1/opportunities \
  -H "Content-Type: application/json" \
  -d '{"recruiter_name":"Service Test","raw_message":"Testing service layer integration"}'
```

**Success Criteria:**
- [ ] Request processed successfully
- [ ] Metrics automatically tracked
- [ ] Trace automatically created
- [ ] Cache automatically used
- [ ] Database transaction handled correctly

---

## 🔍 Common Issues & Quick Fixes

### Issue: API not responding

```bash
# Check if running
docker-compose ps api

# Check logs
docker-compose logs api

# Restart
docker-compose restart api
```

### Issue: Database connection failed

```bash
# Check PostgreSQL
docker-compose ps postgres
docker-compose logs postgres

# Run migrations
docker-compose exec api alembic upgrade head
```

### Issue: Redis connection failed

```bash
# Check Redis
docker-compose ps redis
docker-compose exec redis redis-cli ping
# Expected: PONG
```

### Issue: Tests failing

```bash
# Reinstall dependencies
pip install -r requirements.txt -r requirements-dev.txt

# Install test database
pip install aiosqlite

# Run specific failing test
pytest tests/unit/test_config.py -vv
```

### Issue: Metrics not appearing

```bash
# Check metrics endpoint
curl http://localhost:8000/api/v1/metrics

# Check Prometheus targets
open http://localhost:9090/targets

# Restart Prometheus
docker-compose -f docker-compose.monitoring.yml restart prometheus
```

---

## 📈 Performance Benchmarks

### Expected Performance (Development Environment)

| Metric | Target | Acceptable |
|--------|--------|------------|
| API Health Check | < 50ms | < 100ms |
| Create Opportunity (cache miss) | < 3s | < 5s |
| Create Opportunity (cache hit) | < 500ms | < 1s |
| List Opportunities | < 200ms | < 500ms |
| Cache Hit Rate (after warmup) | > 80% | > 60% |
| P95 Response Time | < 500ms | < 1s |
| Requests/Second | > 50 | > 20 |

### Quick Performance Test

```bash
# Health check (should be very fast)
time curl http://localhost:8000/health

# Create opportunity (first time)
time curl -X POST http://localhost:8000/api/v1/opportunities \
  -H "Content-Type: application/json" \
  -d '{"recruiter_name":"Perf Test","raw_message":"Performance testing message"}'

# Same request (cached)
time curl -X POST http://localhost:8000/api/v1/opportunities \
  -H "Content-Type: application/json" \
  -d '{"recruiter_name":"Perf Test","raw_message":"Performance testing message"}'
```

---

## ✅ Final Validation Checklist

### Core Functionality
- [ ] API health checks passing
- [ ] Opportunities can be created
- [ ] Opportunities can be listed
- [ ] Opportunities can be retrieved by ID
- [ ] Statistics endpoint working
- [ ] API documentation accessible

### Sprint 2 Features
- [ ] Redis caching working (5-10x speedup)
- [ ] OpenTelemetry tracing enabled
- [ ] Prometheus metrics available
- [ ] Grafana dashboards showing data
- [ ] Jaeger traces visible
- [ ] Loki logs ingested
- [ ] Celery workers processing tasks
- [ ] Service layer integrating all features

### Quality Assurance
- [ ] 50+ automated tests passing
- [ ] 80%+ code coverage
- [ ] No critical errors in logs
- [ ] Performance targets met
- [ ] Documentation complete

### Deployment Ready
- [ ] All services start successfully
- [ ] Health checks passing
- [ ] Monitoring stack operational
- [ ] Smoke test script passing
- [ ] Load testing completed (optional)

---

## 🎉 Success!

If all checkboxes are ✅, congratulations! Sprint 2 is fully validated and ready for:

1. **Production Deployment** - Follow `docs/DEPLOYMENT.md`
2. **Git Tagging** - Create release tag `v1.1.0`
3. **Sprint 3 Planning** - Review roadmap and prioritize features

---

## 📚 Additional Resources

- **Detailed Testing**: `docs/TESTING_GUIDE.md`
- **Deployment Guide**: `docs/DEPLOYMENT.md`
- **Architecture**: `docs/ARCHITECTURE.md`
- **Changelog**: `CHANGELOG.md`
- **API Documentation**: http://localhost:8000/docs

---

## 🆘 Need Help?

1. Review **Troubleshooting** section above
2. Check `docs/TESTING_GUIDE.md` for detailed procedures
3. Review service logs: `docker-compose logs <service>`
4. Check monitoring dashboards for insights

---

**Last Updated**: January 17, 2024
**Sprint**: 2 (v1.1.0)
**Status**: ✅ Complete
