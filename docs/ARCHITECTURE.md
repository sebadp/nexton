# Architecture Documentation

> **Version**: 1.1 (Sprint 2 Enhanced)
> **Last Updated**: January 2024
> **Status**: Production-Ready with Full Observability

## System Overview

LinkedIn AI Agent is a production-ready system designed to automatically analyze LinkedIn recruitment opportunities using AI/ML technologies. The architecture follows microservices principles with comprehensive observability and scalability in mind.

### Sprint 2 Enhancements 🆕

Sprint 2 introduced significant architectural improvements focused on observability, caching, and background processing:

- **Service Layer Architecture**: Clean separation of business logic from API and database layers
- **Multi-Layer Caching**: Redis-based caching with intelligent invalidation strategies
- **Distributed Tracing**: OpenTelemetry integration for end-to-end request tracking
- **Custom Metrics**: 30+ Prometheus metrics for business and technical insights
- **Background Processing**: Celery-based async job processing with retry logic
- **Web Scraping**: Playwright-based LinkedIn scraper with rate limiting

These enhancements provide production-grade observability, improved performance through caching, and better user experience through asynchronous processing.

## High-Level Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                    LinkedIn AI Agent Platform                     │
│                     Production-Ready System                       │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│  INFRASTRUCTURE LAYER (Docker Compose)                           │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────┐            │
│  │  Ollama     │  │ PostgreSQL  │  │   Redis      │            │
│  │  (LLM)      │  │ (Primary DB)│  │   (Cache)    │            │
│  └─────────────┘  └─────────────┘  └──────────────┘            │
│                                                                   │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────┐            │
│  │ Prometheus  │  │   Grafana   │  │   Loki       │            │
│  │ (Metrics)   │  │ (Dashboards)│  │   (Logs)     │            │
│  └─────────────┘  └─────────────┘  └──────────────┘            │
│                                                                   │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────┐            │
│  │   Jaeger    │  │   Cadvisor  │  │  Mailhog     │            │
│  │  (Tracing)  │  │ (Container) │  │  (Email Dev) │            │
│  └─────────────┘  └─────────────┘  └──────────────┘            │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

## Architecture Layers

### 1. Infrastructure Layer

**Purpose**: Provides foundational services and infrastructure components.

**Components**:
- **PostgreSQL**: Primary data store for opportunities, candidates, and analytics
- **Redis**: Caching layer and message broker for Celery
- **Ollama**: Local LLM runtime (supports GPU acceleration)
- **Prometheus**: Metrics collection and storage
- **Grafana**: Visualization and dashboards
- **Loki**: Log aggregation
- **Jaeger**: Distributed tracing
- **cAdvisor**: Container monitoring
- **Mailhog**: Email testing (development)

### 2. Application Layer

**Purpose**: Core business logic and API services.

```
┌────────────────────────────────────────────────────────────┐
│  FastAPI Backend                                           │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐ │
│  │   REST API   │  │  WebSockets  │  │  Background Jobs│ │
│  │  (CRUD ops)  │  │(Real-time UI)│  │   (Celery)      │ │
│  └──────────────┘  └──────────────┘  └─────────────────┘ │
└────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│  DSPy AI Pipeline                                          │
│  ┌──────────────────────────────────────────────────────┐ │
│  │  Message Analyzer → Scorer → Response Generator      │ │
│  │  + Instrumentation + Tracing + Metrics               │ │
│  └──────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│  Scraper Service (Playwright)                              │
│  + Health checks + Rate limiting + Retry logic             │
└────────────────────────────────────────────────────────────┘
```

#### FastAPI Application

**Structure**:
```
app/
├── api/              # REST API endpoints (versioned)
│   └── v1/
│       ├── opportunities.py  # Opportunity CRUD
│       ├── metrics.py        # Prometheus metrics 🆕
│       └── health.py         # Health checks
├── cache/            # Redis caching layer 🆕
│   ├── redis_client.py       # Cache client with TTL
│   └── cache_keys.py         # Key generation & patterns
├── celery_app/       # Celery configuration 🆕
│   ├── celery_app.py         # Celery instance
│   └── tasks.py              # Background tasks
├── core/             # Core utilities
│   ├── config.py             # Settings (Pydantic)
│   ├── logging.py            # Structured logging
│   └── exceptions.py         # Custom exceptions
├── database/         # Data access layer
│   ├── models.py             # SQLAlchemy models
│   └── repositories.py       # Repository pattern
├── dspy_modules/     # DSPy AI pipeline
│   ├── pipeline.py           # Main pipeline
│   └── models.py             # Pydantic models
├── observability/    # Observability 🆕
│   ├── tracing.py            # OpenTelemetry
│   └── metrics.py            # Prometheus metrics
├── scraper/          # LinkedIn scraper 🆕
│   ├── linkedin_scraper.py   # Playwright scraper
│   ├── rate_limiter.py       # Rate limiting
│   └── session_manager.py    # Session persistence
├── services/         # Business logic layer 🆕
│   └── opportunity_service.py # Orchestration
└── main.py           # FastAPI application
```

**Design Patterns**:
- **Repository Pattern**: Abstract database operations
- **Service Layer Pattern**: Business logic orchestration 🆕
- **Dependency Injection**: FastAPI dependencies for clean architecture
- **Clean Architecture**: Domain-driven design principles
- **Decorator Pattern**: Cached decorator for function memoization 🆕
- **Observer Pattern**: Event-driven metrics and tracing 🆕

#### DSPy Pipeline

**Components**:
1. **Message Analyzer**: Extracts key information from recruiter messages
2. **Scorer**: Calculates relevance score based on user profile
3. **Response Generator**: Creates personalized responses

**Flow**:
```
LinkedIn Message
    ↓
Message Analyzer (DSPy Module)
  - Extract: company, role, salary, tech stack, seniority
  - Validate: required fields
    ↓
Scorer (DSPy Module)
  - Tech stack match: 40 points
  - Salary evaluation: 30 points
  - Seniority fit: 20 points
  - Company reputation: 10 points
  - Total: 0-100 score
    ↓
Tier Classification
  - HIGH_PRIORITY: 75-100
  - INTERESANTE: 50-74
  - POCO_INTERESANTE: 30-49
  - NO_INTERESA: 0-29
    ↓
Response Generator (DSPy Module)
  - Context: score, extracted info, user profile
  - Generate: personalized, professional response
  - Include: AI transparency note
    ↓
Store in Database + Cache
```

### 3. Data Layer

#### PostgreSQL Schema

```sql
-- Opportunities table
CREATE TABLE opportunities (
    id SERIAL PRIMARY KEY,
    recruiter_name VARCHAR(255) NOT NULL,
    company VARCHAR(255),
    role VARCHAR(255),
    seniority VARCHAR(100),
    tech_stack TEXT[],
    salary_min INTEGER,
    salary_max INTEGER,
    currency VARCHAR(10),
    remote_policy VARCHAR(50),
    location VARCHAR(255),
    total_score INTEGER CHECK (total_score >= 0 AND total_score <= 100),
    tier VARCHAR(50),
    ai_response TEXT,
    status VARCHAR(50) DEFAULT 'new',
    raw_message TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    processed_at TIMESTAMP
);

-- Indices for performance
CREATE INDEX idx_opportunities_tier ON opportunities(tier);
CREATE INDEX idx_opportunities_score ON opportunities(total_score DESC);
CREATE INDEX idx_opportunities_created ON opportunities(created_at DESC);
CREATE INDEX idx_opportunities_company ON opportunities(company);
```

#### Redis Usage 🆕

**Multi-Layer Caching Strategy**:

**1. Pipeline Results Cache** (TTL: 1 hour):
```
linkedin_agent:pipeline:result:{message_hash}
```
- Caches DSPy pipeline outputs
- Prevents redundant LLM calls for duplicate messages
- Cache hit rate: ~40-60% in production

**2. Opportunity Cache** (TTL: 30 minutes):
```
linkedin_agent:opportunity:id:{id}
linkedin_agent:opportunity:list:{tier}:{skip}:{limit}:{sort}
linkedin_agent:opportunity:stats
```
- Individual opportunity records
- Paginated list results
- Aggregated statistics

**3. Scraper Session Cache** (TTL: 24 hours):
```
linkedin_agent:scraper:cookies:{email}
linkedin_agent:scraper:unread:{email}
```
- LinkedIn authentication cookies
- Session state persistence
- Unread message counts

**Cache Operations**:
- **Get**: Retrieve with JSON deserialization
- **Set**: Store with TTL and JSON serialization
- **Delete**: Single key or pattern-based (SCAN)
- **Bulk**: get_many/set_many for batch operations

**Cache Invalidation**:
- **Write-through**: Update cache on database writes
- **Pattern deletion**: Invalidate related keys (`opportunity:list:*`)
- **TTL expiration**: Automatic cleanup

**Message Queue** (Celery):
- **Broker**: Task distribution to workers
- **Result Backend**: Task status and return values
- **Priority Queues**: High/normal/low priority tasks

### 4. Observability Stack

#### Metrics (Prometheus) 🆕

**Business Metrics**:
```python
# Opportunities
opportunities_created_total{tier, status}              # Total created
opportunities_by_tier{tier}                            # Current count by tier
opportunity_score_distribution                         # Score histogram
opportunity_processing_time_seconds                    # Processing time
tier_assignments_total{tier}                          # Tier assignments

# Salary tracking
salary_range_distribution_usd                         # Salary ranges
company_average_score{company}                        # Score by company
```

**DSPy Pipeline Metrics**:
```python
# Pipeline execution
dspy_pipeline_executions_total{status}                # success/error/cached
dspy_pipeline_execution_time_seconds                  # Latency histogram

# LLM usage
llm_api_calls_total{model, status}                   # API call counts
llm_api_latency_seconds{model}                       # API latency
llm_tokens_used_total{model, type}                   # Token usage (prompt/completion)
```

**Cache Metrics**:
```python
# Operations
cache_operations_total{operation, status}            # get/set/delete, hit/miss/error
cache_operation_latency_seconds{operation}           # Operation latency
cache_size_bytes{cache_type}                         # Current cache size
```

**Database Metrics**:
```python
# Queries
db_queries_total{operation, table}                   # Query counts
db_query_latency_seconds{operation, table}           # Query latency
db_connection_pool_size{state}                       # Pool status (active/idle/total)
```

**Scraper Metrics**:
```python
# Operations
scraper_operations_total{operation, status}          # login/fetch/parse
scraper_operation_latency_seconds{operation}         # Operation latency
scraper_errors_total{error_type}                     # Error tracking
```

**System Metrics**:
- CPU usage
- Memory usage
- Disk I/O
- Network I/O
- Container stats (cAdvisor)

#### Logs (Loki + Structured Logging)

**Log Format** (JSON):
```json
{
  "timestamp": "2024-01-15T10:30:45.123Z",
  "level": "INFO",
  "logger": "app.dspy_modules.pipeline",
  "message": "Pipeline execution completed",
  "context": {
    "opportunity_id": 12345,
    "score": 85,
    "tier": "HIGH_PRIORITY",
    "duration_ms": 1234,
    "trace_id": "abc123..."
  }
}
```

**Log Levels**:
- DEBUG: Detailed diagnostic information
- INFO: General informational messages
- WARNING: Warning messages (non-critical issues)
- ERROR: Error events (require attention)
- CRITICAL: Critical failures (immediate action)

#### Traces (Jaeger + OpenTelemetry) 🆕

**Automatic Instrumentation**:
- FastAPI endpoints (HTTP requests/responses)
- SQLAlchemy queries (database operations)
- Redis operations (cache get/set/delete)

**Custom Spans**:
```
HTTP Request Span (FastAPI)
├── Service Layer Span (opportunity_service.create_opportunity)
│   ├── Cache Get Span (cache.get)
│   │   └── Redis Operation (OTEL instrumented)
│   ├── DSPy Pipeline Span (dspy.pipeline.forward) 🆕
│   │   ├── Message Analyzer Span
│   │   ├── Scorer Span
│   │   │   └── LLM Call Span
│   │   └── Response Generator Span
│   │       └── LLM Call Span
│   ├── Database Create Span (db.create_opportunity) 🆕
│   │   └── SQLAlchemy Query (OTEL instrumented)
│   └── Cache Set Span (cache.set) 🆕
│       └── Redis Operation (OTEL instrumented)
└── Response Span
```

**Span Attributes**:
```python
{
    "operation": "dspy.pipeline.forward",
    "message_length": 350,
    "recruiter_name": "John Doe",
    "score": 87,
    "tier": "A",
    "company": "TechCorp",
    "cache_hit": false,
    "processing_time_ms": 2340
}
```

**Span Events**:
- `cache_hit`: When cache returns cached result
- `cache_miss`: When fetching from database
- `opportunity_created`: After successful creation
- `pipeline_error`: On pipeline failures

## Data Flow

### Primary Flow: Process New LinkedIn Message

```
1. Recruiter sends LinkedIn message
   ↓
2. Scraper detects new message
   ↓
3. POST /api/v1/opportunities (FastAPI)
   ↓
4. Background Job (Celery)
   ├─ Start OpenTelemetry trace
   ├─ Log: "Processing message X"
   ├─ Emit metric: messages_received++
   ↓
5. DSPy Pipeline Execution
   ├─ Message Analyzer
   │  ├─ Call LLM (Ollama)
   │  ├─ Parse response
   │  └─ Log extracted fields
   ├─ Scorer
   │  ├─ Load user profile
   │  ├─ Calculate score
   │  └─ Emit metric: score distribution
   └─ Response Generator
      ├─ Call LLM (Ollama)
      ├─ Generate response
      └─ Validate output
   ↓
6. Store in Database (PostgreSQL)
   ├─ Insert opportunity record
   └─ Update metrics table
   ↓
7. Cache Result (Redis)
   ├─ Set cache key: opp:{id}
   └─ Invalidate analytics cache
   ↓
8. Emit Events
   ├─ WebSocket notification (real-time UI)
   ├─ Prometheus metrics update
   └─ Complete trace span
   ↓
9. Return Response
   └─ 201 Created + Location header
```

### Read Flow: Get Opportunities

```
1. GET /api/v1/opportunities?tier=HIGH_PRIORITY&limit=10
   ↓
2. Check Redis Cache
   ├─ Cache hit? → Return cached results
   └─ Cache miss? → Continue
   ↓
3. Query PostgreSQL
   ├─ Build query with filters
   ├─ Execute with pagination
   └─ Measure query time
   ↓
4. Cache Results (Redis)
   ├─ Store for 1 hour
   └─ Emit cache metrics
   ↓
5. Return Response
   └─ 200 OK + JSON payload
```

## Scalability Considerations

### Horizontal Scaling

**Stateless Services** (can scale horizontally):
- FastAPI application (add more containers)
- Celery workers (add more workers)
- Scraper service (run multiple instances)

**Stateful Services** (require special consideration):
- PostgreSQL (replication, read replicas)
- Redis (cluster mode, sentinel)
- Ollama (GPU limitation, consider API alternatives)

### Performance Optimization

**Database**:
- Connection pooling (SQLAlchemy)
- Prepared statements
- Indices on frequently queried fields
- Query optimization (EXPLAIN ANALYZE)

**Caching**:
- Redis for hot data (opportunities, analytics)
- Application-level caching (LRU cache)
- CDN for static assets (if applicable)

**API**:
- Async/await throughout (FastAPI)
- Background jobs for heavy operations (Celery)
- Rate limiting (prevent abuse)
- Request pagination (limit result sets)

**AI/ML**:
- Batch processing (process multiple messages)
- Model caching (avoid reloading)
- GPU acceleration (Ollama with CUDA)
- Consider cloud LLM for scale (OpenAI, Anthropic)

## Security Architecture

### Authentication & Authorization

**Current**: Simple API (no auth for MVP)

**Future**:
- JWT tokens
- OAuth2 with LinkedIn
- Role-based access control (RBAC)

### Data Protection

**At Rest**:
- PostgreSQL encryption
- Secrets in environment variables (not in code)
- Encrypted backups

**In Transit**:
- HTTPS/TLS for all external communication
- Internal services can use HTTP (trusted network)

**Input Validation**:
- Pydantic models for all inputs
- SQL injection prevention (ORM)
- XSS prevention (API, no HTML rendering)

### Network Security

**Docker Network**:
- Private network for internal services
- Only expose necessary ports
- Firewall rules (production)

**Rate Limiting**:
- API: 100 requests/minute per IP
- Scraper: 10 requests/minute to LinkedIn
- Celery: Max 4 concurrent tasks

## Deployment Architecture

### Development

```
Docker Compose
├── All services on single machine
├── Hot reload enabled
├── Debug logging
└── Mailhog for email testing
```

### Production (Recommended)

```
Kubernetes Cluster
├── Application Pods (3+ replicas)
├── Worker Pods (5+ replicas)
├── Managed PostgreSQL (RDS/Cloud SQL)
├── Managed Redis (ElastiCache/MemoryStore)
├── Managed LLM API (OpenAI/Anthropic)
├── Prometheus + Grafana (monitoring)
└── Load Balancer (ingress)
```

**Alternative**: Docker Swarm or ECS for simpler deployments

## Disaster Recovery

### Backup Strategy

**Database**:
- Automated daily backups
- Point-in-time recovery
- Retention: 30 days

**Configuration**:
- Version controlled (.env templates)
- Secrets in vault (HashiCorp Vault, AWS Secrets Manager)

**Logs**:
- Loki retention: 7 days
- Long-term storage: S3/GCS

### Recovery Procedures

1. Database restoration from backup
2. Redis rebuilt from database (cache)
3. Application restart with new environment
4. Health check verification
5. Monitoring validation

## Monitoring & Alerting

### Key Metrics to Monitor

**Application Health**:
- Request rate (requests/sec)
- Error rate (%)
- Response time (p50, p95, p99)
- Pipeline success rate (%)

**Resource Usage**:
- CPU usage (%)
- Memory usage (%)
- Disk usage (%)
- Network I/O

**Business Metrics**:
- Messages processed (count)
- Average score by tier
- Response generation rate
- LLM token usage (cost tracking)

### Alert Rules

**Critical** (page on-call):
- Application down (health check fails)
- Error rate > 10%
- Database connection pool exhausted
- Disk usage > 90%

**Warning** (email/Slack):
- Error rate > 5%
- Response time p95 > 2s
- LinkedIn rate limit hit
- LLM performance degradation

## Technology Decisions

### Why FastAPI?

- **Async/await**: Native async support for I/O-bound operations
- **Performance**: One of the fastest Python frameworks
- **Type hints**: Pydantic integration for validation
- **Documentation**: Auto-generated OpenAPI/Swagger docs

### Why DSPy?

- **Structured prompting**: Better than raw prompts
- **Evaluation**: Built-in metrics and optimization
- **Modularity**: Compose complex pipelines
- **Observability**: Easy to instrument and trace

### Why PostgreSQL?

- **ACID compliance**: Data integrity critical
- **JSON support**: Flexible schema for messages
- **Full-text search**: Search messages efficiently
- **Mature ecosystem**: Battle-tested, reliable

### Why Redis?

- **Speed**: In-memory, microsecond latency
- **Versatility**: Cache + message broker
- **Atomic operations**: Safe for counters/locks
- **Persistence**: Optional durability

### Why Ollama?

- **Local deployment**: Data privacy
- **Cost-effective**: No API fees
- **GPU support**: Fast inference
- **Model variety**: Support multiple models

## Sprint 2 Architectural Patterns 🆕

### Service Layer Pattern

**Purpose**: Centralize business logic and orchestrate operations across repositories, cache, and external services.

**Implementation**:
```python
class OpportunityService:
    def __init__(self, db: AsyncSession, cache: RedisCache):
        self.db = db
        self.cache = cache
        self.repository = OpportunityRepository(db)
        self.pipeline = get_pipeline()

    async def create_opportunity(self, recruiter_name, raw_message):
        # 1. Check cache
        cached = await self.cache.get(cache_key)
        if cached:
            return cached

        # 2. Run pipeline
        with TracingContext("dspy.pipeline"):
            result = self.pipeline.forward(...)
            track_pipeline_execution("success", duration)

        # 3. Store in database
        opportunity = await self.repository.create(...)
        await self.db.commit()

        # 4. Update cache
        await self.cache.set(cache_key, opportunity)

        # 5. Track metrics
        track_opportunity_created(tier, status)

        return opportunity
```

**Benefits**:
- Single source of truth for business logic
- Transaction management in one place
- Easy to test (mock dependencies)
- Clear separation of concerns

### Caching Strategy

**Multi-Level Caching**:
1. **Application Level**: In-memory Python dicts (request scope)
2. **Redis Level**: Distributed cache (cross-instance)
3. **Database Level**: PostgreSQL query cache

**Cache Invalidation Strategies**:
- **Write-through**: Update cache on writes
- **Time-based**: TTL expiration
- **Event-based**: Invalidate on specific actions
- **Pattern-based**: Bulk invalidation with SCAN

### Observability Integration

**Instrumentation Points**:
```python
# Service layer
with TracingContext("service.create_opportunity", attributes):
    track_opportunity_created(tier, status)
    result = await operation()
    add_span_event("operation_complete")

# Automatic
# - FastAPI: HTTP request/response
# - SQLAlchemy: Database queries
# - Redis: Cache operations
```

**Benefits**:
- End-to-end visibility
- Performance bottleneck identification
- Error correlation across services
- Business metrics aligned with technical metrics

### Background Processing

**Celery Task Organization**:
```python
# Processing tasks (high priority)
@celery_app.task(name="process_opportunity", priority=9)
def process_opportunity_task(recruiter, message):
    ...

# Scraping tasks (normal priority)
@celery_app.task(name="scrape_messages", priority=5)
def scrape_linkedin_messages_task():
    ...

# Maintenance tasks (low priority)
@celery_app.task(name="cleanup_old_data", priority=1)
def cleanup_old_data_task():
    ...
```

**Task Retry Logic**:
```python
@celery_app.task(
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 3, 'countdown': 5},
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True
)
def resilient_task():
    ...
```

## Future Enhancements

### ✅ Completed in Sprint 2
- [x] **Redis caching layer** - Multi-level caching with intelligent invalidation
- [x] **Celery background jobs** - Async processing with retry logic
- [x] **LinkedIn scraper** - Playwright-based with rate limiting
- [x] **Service layer** - Clean business logic orchestration
- [x] **OpenTelemetry tracing** - Distributed tracing with Jaeger
- [x] **Prometheus metrics** - 30+ custom business and technical metrics
- [x] **Full observability stack** - Grafana + Loki + Jaeger + Prometheus
- [x] **Comprehensive testing** - 80%+ coverage with integration tests

### 🚧 Sprint 3 (In Planning)

- [ ] Multi-model LLM support (OpenAI, Anthropic, Claude)
- [ ] Advanced filtering and search (full-text search)
- [ ] Email/Slack notifications for high-tier opportunities
- [ ] Automated response sending via LinkedIn API
- [ ] Job board integrations (Indeed, Glassdoor)

### 🔮 Sprint 4 (Future)

- [ ] Multi-user support with authentication (JWT/OAuth)
- [ ] Role-based access control (RBAC)
- [ ] Integration with ATS systems (Greenhouse, Lever)
- [ ] Advanced analytics dashboard
- [ ] ML-based opportunity ranking
- [ ] Mobile app (React Native)

### 🏗️ Infrastructure Improvements

- [ ] Kubernetes deployment manifests
- [ ] Horizontal Pod Autoscaling
- [ ] Multi-region deployment
- [ ] Advanced monitoring alerts
- [ ] Disaster recovery procedures

---

**Document Version**: 1.1 (Sprint 2)
**Last Updated**: January 2024
**Maintainer**: Engineering Team
