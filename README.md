# 🤖 LinkedIn AI Agent

> **Intelligent LinkedIn opportunity analysis and automated response generation powered by AI**

Automate your LinkedIn job search with enterprise-grade AI. Analyze recruiter messages, score opportunities, and generate personalized responses - all while you focus on what matters.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com)
[![DSPy](https://img.shields.io/badge/DSPy-latest-orange.svg)](https://github.com/stanfordnlp/dspy)
[![Docker](https://img.shields.io/badge/Docker-ready-blue.svg)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code Coverage](https://img.shields.io/badge/coverage-85%25-brightgreen.svg)](./tests)

---

## 📖 Table of Contents

- [The Problem](#-the-problem)
- [The Solution](#-the-solution)
- [Key Features](#-key-features)
- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Quick Start](#-quick-start)
- [Usage Examples](#-usage-examples)
- [Observability](#-observability)
- [Configuration](#-configuration)
- [Development](#-development)
- [Deployment](#-deployment)
- [Documentation](#-documentation)
- [Contributing](#-contributing)

---

## 🎨 Visual Overview

<div align="center">

### 🖥️ System Dashboards

| Grafana Monitoring | Jaeger Tracing | API Documentation |
|:------------------:|:--------------:|:-----------------:|
| ![Grafana](https://img.shields.io/badge/Grafana-Real--time%20Metrics-orange?style=for-the-badge&logo=grafana) | ![Jaeger](https://img.shields.io/badge/Jaeger-Distributed%20Tracing-purple?style=for-the-badge&logo=jaeger) | ![Swagger](https://img.shields.io/badge/Swagger-Interactive%20API-green?style=for-the-badge&logo=swagger) |
| Track opportunities, pipeline performance | Visualize complete request flows | Test endpoints in the browser |

| Celery Flower | Prometheus | PostgreSQL |
|:-------------:|:----------:|:----------:|
| ![Flower](https://img.shields.io/badge/Flower-Task%20Monitor-success?style=for-the-badge) | ![Prometheus](https://img.shields.io/badge/Prometheus-30+%20Metrics-red?style=for-the-badge&logo=prometheus) | ![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Data%20Store-blue?style=for-the-badge&logo=postgresql) |
| Monitor background jobs | Query custom metrics | Persistent opportunity storage |

</div>

<!-- Screenshots will be added here:
![Grafana Dashboard](docs/images/grafana-dashboard.png)
![Jaeger Traces](docs/images/jaeger-traces.png)
![API Docs](docs/images/api-docs.png)
-->

---

## 🎯 The Problem

Job searching on LinkedIn is time-consuming:
- **50+ recruiter messages per month** that need individual responses
- **Manual analysis** of each opportunity (salary, tech stack, company)
- **Context switching** between LinkedIn, research, and drafting responses
- **Missed opportunities** due to delayed responses
- **Repetitive work** that could be automated

---

## 💡 The Solution

**LinkedIn AI Agent** is an intelligent automation system that:

1. **📥 Scrapes** your LinkedIn messages automatically
2. **🧠 Analyzes** each opportunity using AI (DSPy + LLM)
3. **📊 Scores** opportunities based on your preferences (tech stack, salary, location)
4. **✍️ Generates** personalized responses in your tone
5. **📧 Notifies** you via email for high-priority opportunities
6. **🚀 Sends** approved responses back to LinkedIn

All running on **your infrastructure** with **full observability** and **production-grade reliability**.

---

## ✨ Key Features

### 🤖 Intelligent Analysis Pipeline

- **AI-Powered Extraction**: Automatically extracts company, role, salary, tech stack from messages
- **Smart Scoring**: Multi-dimensional scoring (tech match, salary, seniority, company quality)
- **Tiered Classification**: A/B/C/D tier system for opportunity prioritization
- **Multi-Model Support**: Use OpenAI, Anthropic, or Ollama (local/free) for LLM processing
- **Context-Aware Responses**: Generates human-like responses that mirror language and tone

### 🔄 Complete Automation Workflow

```
LinkedIn Message → Scraper → AI Analysis → Score & Tier → Generate Response
                                                ↓
                                    Notify if High Priority
                                                ↓
                                    Review → Approve → Send
```

### 🎛️ Production-Ready Features

| Feature | Description |
|---------|-------------|
| **Automated Scraping** | Playwright-based LinkedIn scraper with session persistence |
| **Smart Caching** | Redis-based multi-layer caching reduces LLM calls by 60% |
| **Background Jobs** | Celery task queue for async processing and scheduling |
| **Email Notifications** | Beautiful HTML emails for high-priority opportunities |
| **Response Workflow** | Review, edit, approve, and send responses via REST API |
| **Rate Limiting** | Respects LinkedIn limits to avoid account restrictions |
| **Session Management** | Persistent cookies for reliable long-term operation |

### 📊 Enterprise-Grade Observability

| Tool | Purpose | Access |
|------|---------|--------|
| **Prometheus** | Metrics collection (30+ custom metrics) | `:9090` |
| **Grafana** | Pre-configured dashboards | `:3000` |
| **Jaeger** | Distributed tracing (OpenTelemetry) | `:16686` |
| **Loki** | Log aggregation | via Grafana |
| **Flower** | Celery task monitoring | `:5555` |

Track everything:
- Pipeline execution time
- LLM token usage and costs
- Cache hit rates
- Opportunity distribution by tier
- System health metrics

### 🧪 Comprehensive Testing

- **85% code coverage** with 140+ tests
- Unit tests for all core modules
- Integration tests for end-to-end workflows
- Load testing with Locust
- Automated CI/CD pipeline

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         LinkedIn AI Agent                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │                    Application Layer                          │ │
│  │                                                               │ │
│  │   ┌──────────┐      ┌──────────┐      ┌──────────┐          │ │
│  │   │ FastAPI  │◄────►│ Service  │◄────►│   DSPy   │          │ │
│  │   │   API    │      │  Layer   │      │ Pipeline │          │ │
│  │   └────┬─────┘      └────┬─────┘      └────┬─────┘          │ │
│  │        │                 │                  │                │ │
│  │        ▼                 ▼                  ▼                │ │
│  │   ┌──────────┐      ┌──────────┐      ┌──────────┐          │ │
│  │   │PostgreSQL│      │  Redis   │      │  Ollama  │          │ │
│  │   │    DB    │      │  Cache   │      │   LLM    │          │ │
│  │   └──────────┘      └──────────┘      └──────────┘          │ │
│  │                                                               │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │                 Background Processing                         │ │
│  │                                                               │ │
│  │   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌─────────┐  │ │
│  │   │  Celery  │   │Playwright│   │  Email   │   │ Flower  │  │ │
│  │   │ Workers  │   │ Scraper  │   │  Sender  │   │ Monitor │  │ │
│  │   └──────────┘   └──────────┘   └──────────┘   └─────────┘  │ │
│  │                                                               │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │              Observability Stack (Optional)                   │ │
│  │                                                               │ │
│  │   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌─────────┐  │ │
│  │   │Prometheus│───│ Grafana  │───│   Loki   │───│ Jaeger  │  │ │
│  │   │ Metrics  │   │Dashboard │   │   Logs   │   │ Traces  │  │ │
│  │   └──────────┘   └──────────┘   └──────────┘   └─────────┘  │ │
│  │                                                               │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Scraping**: Playwright scrapes LinkedIn messages every 15 minutes
2. **Analysis**: DSPy pipeline analyzes message → extracts info → scores → classifies tier
3. **Caching**: Results cached in Redis (60% cache hit rate)
4. **Storage**: Opportunities stored in PostgreSQL
5. **Notification**: Email sent for A/B tier opportunities
6. **Response**: User reviews/approves → Response sent back to LinkedIn
7. **Monitoring**: All operations tracked with metrics, traces, and logs

---

## 🛠️ Tech Stack

### Core Application
- **[FastAPI](https://fastapi.tiangolo.com/)** - Modern async Python web framework
- **[DSPy](https://github.com/stanfordnlp/dspy)** - Structured LLM programming framework
- **[PostgreSQL 15](https://www.postgresql.org/)** - Primary database with async support
- **[Redis 7](https://redis.io/)** - Caching and Celery broker
- **[Celery 5](https://docs.celeryq.dev/)** - Distributed task queue
- **[Playwright](https://playwright.dev/)** - Browser automation for LinkedIn

### AI/ML
- **[Ollama](https://ollama.ai/)** - Local LLM runtime (free, private)
- **[OpenAI](https://openai.com/)** - GPT-4, GPT-3.5-turbo support
- **[Anthropic](https://www.anthropic.com/)** - Claude 3 support

### Observability
- **[Prometheus](https://prometheus.io/)** - Metrics collection
- **[Grafana](https://grafana.com/)** - Visualization and dashboards
- **[Jaeger](https://www.jaegertracing.io/)** - Distributed tracing
- **[Loki](https://grafana.com/oss/loki/)** - Log aggregation
- **[OpenTelemetry](https://opentelemetry.io/)** - Instrumentation

### Development
- **[pytest](https://pytest.org/)** - Testing framework
- **[Docker](https://www.docker.com/)** - Containerization
- **[Alembic](https://alembic.sqlalchemy.org/)** - Database migrations
- **[Pydantic](https://pydantic-docs.helpmanual.io/)** - Data validation

---

## 🚀 Quick Start

### Prerequisites

- **Docker** and **Docker Compose** (recommended)
- **Python 3.11+** (for local development)
- **LinkedIn credentials** (for scraping)
- **8GB+ RAM** recommended

### Option 1: Docker (Recommended)

```bash
# 1. Clone repository
git clone https://github.com/yourusername/linkedin-ai-agent.git
cd linkedin-ai-agent

# 2. Configure environment
cp .env.example .env
nano .env  # Add your LinkedIn credentials and settings

# 3. Start all services (one command!)
./scripts/start.sh

# 4. Verify deployment
curl http://localhost:8000/health
# Expected: {"status":"healthy","timestamp":"..."}
```

**That's it!** The system is now:
- ✅ Scraping LinkedIn every 15 minutes
- ✅ Analyzing opportunities with AI
- ✅ Caching results in Redis
- ✅ Sending email notifications
- ✅ Ready to generate responses

### Option 2: Local Development

```bash
# 1. Create virtual environment
python3.11 -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# 2. Install dependencies
pip install -r requirements.txt
playwright install chromium

# 3. Start dependencies (Postgres, Redis, Ollama)
docker-compose up -d postgres redis ollama

# 4. Run migrations
alembic upgrade head

# 5. Start FastAPI server
uvicorn app.main:app --reload

# 6. Start Celery worker (separate terminal)
celery -A app.tasks.celery_app worker --loglevel=info
```

---

## 📱 Usage Examples

### Access the API

```bash
# Interactive API documentation
open http://localhost:8000/docs
```

### List Opportunities

```bash
# Get all A-tier opportunities
curl "http://localhost:8000/api/v1/opportunities?tier=A&limit=10"

# Get opportunities above score 80
curl "http://localhost:8000/api/v1/opportunities?min_score=80"
```

### Process a Message

```bash
# Manually process a LinkedIn message
curl -X POST http://localhost:8000/api/v1/opportunities \
  -H "Content-Type: application/json" \
  -d '{
    "recruiter_name": "Jane Smith",
    "raw_message": "Hi! Senior Python Engineer role at Google. $180k-$220k, remote. Interested?"
  }'
```

### Review & Approve Response

```bash
# Get pending response for opportunity
curl http://localhost:8000/api/v1/responses/123

# Approve and send
curl -X POST http://localhost:8000/api/v1/responses/123/approve

# Edit before sending
curl -X POST http://localhost:8000/api/v1/responses/123/edit \
  -H "Content-Type: application/json" \
  -d '{"edited_response": "Thanks Jane! I'd love to learn more..."}'

# Decline (no message sent)
curl -X POST http://localhost:8000/api/v1/responses/123/decline
```

### View Analytics

```bash
# Get opportunity statistics
curl http://localhost:8000/api/v1/opportunities/analytics/stats

# Response:
# {
#   "total": 150,
#   "by_tier": {"A": 12, "B": 45, "C": 68, "D": 25},
#   "avg_score": 62.5,
#   "last_updated": "2024-01-18T..."
# }
```

---

## 📊 Observability

### Access Monitoring Tools

Once the system is running, access these dashboards:

| Service | URL | Credentials | Purpose |
|---------|-----|-------------|---------|
| **API Docs** | http://localhost:8000/docs | - | Interactive API testing |
| **Grafana** | http://localhost:3000 | admin/admin | Metrics dashboards |
| **Prometheus** | http://localhost:9090 | - | Raw metrics queries |
| **Jaeger** | http://localhost:16686 | - | Request tracing |
| **Flower** | http://localhost:5555 | admin/admin | Celery tasks |

### Key Metrics

**Business Metrics**:
- `opportunities_created_total` - Total opportunities by tier
- `opportunity_score_distribution` - Score histogram
- `opportunities_by_tier` - Current distribution

**Performance Metrics**:
- `dspy_pipeline_execution_time_seconds` - Pipeline latency
- `llm_api_latency_seconds` - LLM response time
- `llm_tokens_used_total` - Token usage and costs

**Cache Metrics**:
- `cache_operations_total` - Hit/miss rates
- `cache_hit_rate` - Percentage of cache hits

**System Metrics**:
- `db_query_latency_seconds` - Database performance
- `scraper_operations_total` - Scraping success/failure

### Example Queries

```promql
# Average pipeline execution time (last 1h)
rate(dspy_pipeline_execution_time_seconds_sum[1h]) /
rate(dspy_pipeline_execution_time_seconds_count[1h])

# Cache hit rate
sum(rate(cache_operations_total{status="hit"}[5m])) /
sum(rate(cache_operations_total[5m])) * 100

# Opportunities created per day by tier
sum by (tier) (increase(opportunities_created_total[1d]))
```

### Grafana Dashboards

Pre-configured dashboards available in `monitoring/grafana/dashboards/`:
- **LinkedIn Agent Overview** - Main business metrics
- **System Performance** - CPU, memory, network
- **DSPy Pipeline** - AI/ML performance
- **Database & Cache** - Data layer metrics

---

## ⚙️ Configuration

### Environment Variables

Key configuration options (see [`.env.example`](.env.example) for all options):

```bash
# === Application ===
ENV=development
LOG_LEVEL=INFO

# === LinkedIn Credentials ===
LINKEDIN_EMAIL=your@email.com
LINKEDIN_PASSWORD=your-password

# === Database ===
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/linkedin_agent

# === Redis ===
REDIS_URL=redis://localhost:6379/0

# === AI/ML Configuration ===
# Choose provider: ollama (local/free), openai, anthropic
LLM_PROVIDER=ollama
LLM_MODEL=llama3.2

# Ollama (local)
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2

# OpenAI (paid)
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4-turbo

# Anthropic (paid)
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-3-sonnet-20240229

# Per-module configuration (optional)
ANALYZER_LLM_PROVIDER=ollama
ANALYZER_LLM_MODEL=llama3.2
RESPONSE_LLM_PROVIDER=openai
RESPONSE_LLM_MODEL=gpt-4-turbo

# === Email Notifications ===
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
NOTIFICATION_EMAIL=notifications@example.com

# Only notify for these tiers
NOTIFICATION_TIER_THRESHOLD=["A", "B"]
NOTIFICATION_SCORE_THRESHOLD=60

# === Scraper Settings ===
SCRAPER_HEADLESS=true
SCRAPER_MAX_REQUESTS_PER_MINUTE=10
SCRAPER_MIN_DELAY_SECONDS=3.0

# === Observability (Optional) ===
OTEL_ENABLED=true
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus
```

### User Profile Configuration

Configure your preferences in `config/profile.yaml`:

```yaml
# Personal Information
name: "Your Name"

# Skills and Experience
preferred_technologies:
  - Python
  - FastAPI
  - PostgreSQL
  - Docker
  - React

years_of_experience: 5
current_seniority: "Senior"  # Junior/Mid/Senior/Staff/Principal

# Compensation Expectations (USD)
minimum_salary_usd: 80000
ideal_salary_usd: 120000

# Work Preferences
preferred_remote_policy: "Remote"  # Remote/Hybrid/On-site/Flexible
preferred_locations:
  - "Remote"
  - "United States"

# Company Preferences
preferred_company_size: "Mid-size"  # Startup/Mid-size/Enterprise
industry_preferences:
  - "Technology"
  - "AI/ML"
  - "SaaS"
```

---

## 🧑‍💻 Development

### Local Setup

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Setup pre-commit hooks
pre-commit install

# Run tests
pytest tests/ -v --cov=app

# Run linters
black app/ tests/
ruff check --fix app/ tests/
mypy app/

# Security scan
bandit -r app/
safety check
```

### Project Structure

```
linkedin-ai-agent/
├── app/
│   ├── api/                    # REST API endpoints
│   │   └── v1/
│   │       ├── opportunities.py
│   │       ├── responses.py
│   │       └── health.py
│   ├── cache/                  # Redis caching layer
│   ├── core/                   # Configuration & utilities
│   ├── database/               # SQLAlchemy models & repos
│   ├── dspy_pipeline/          # AI analysis pipeline
│   │   ├── opportunity_analyzer.py
│   │   └── response_generator.py
│   ├── observability/          # Metrics & tracing
│   ├── scraper/                # LinkedIn scraper
│   ├── services/               # Business logic layer
│   ├── tasks/                  # Celery background tasks
│   └── main.py                 # FastAPI application
├── tests/
│   ├── unit/                   # Unit tests
│   ├── integration/            # Integration tests
│   └── performance/            # Load tests
├── monitoring/                 # Observability configs
│   ├── grafana/
│   ├── prometheus/
│   └── loki/
├── infrastructure/
│   └── docker/                 # Dockerfiles
├── scripts/                    # Automation scripts
├── config/                     # Configuration files
├── docs/                       # Documentation
├── docker-compose.yml
└── requirements.txt
```

### Testing

```bash
# Run all tests with coverage
pytest tests/ -v --cov=app --cov-report=html

# Run specific test categories
pytest tests/unit/ -v              # Unit tests only
pytest tests/integration/ -v       # Integration tests
pytest -k "cache" -v               # Cache tests only

# View coverage report
open htmlcov/index.html

# Load testing
locust -f tests/performance/locustfile.py --host=http://localhost:8000
```

**Test Coverage**:
- ✅ 140+ tests
- ✅ 85% code coverage
- ✅ All core modules tested
- ✅ Integration tests for workflows
- ✅ Performance benchmarks

---

## 🚢 Deployment

### Docker Compose (Recommended)

```bash
# Development
docker-compose up -d

# Production
docker-compose -f docker-compose.prod.yml up -d

# With monitoring stack
docker-compose up -d
docker-compose -f docker-compose.monitoring.yml up -d
```

### Manual Deployment

See [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) for:
- Cloud deployment (AWS, GCP, Azure)
- Kubernetes manifests
- CI/CD setup with GitHub Actions
- Secrets management
- Backup/restore procedures
- Scaling strategies

### Resource Requirements

**Minimum**:
- 2 CPU cores
- 4GB RAM
- 20GB disk

**Recommended**:
- 4 CPU cores
- 8GB RAM
- 50GB disk

**Production**:
- 8+ CPU cores
- 16GB+ RAM
- 100GB+ SSD

---

## 📚 Documentation

Comprehensive documentation available in [`docs/`](docs/):

| Document | Description |
|----------|-------------|
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | System design and data flow |
| [API.md](docs/API.md) | Complete API reference |
| [DEPLOYMENT.md](docs/DEPLOYMENT.md) | Production deployment guide |
| [DEVELOPMENT.md](docs/DEVELOPMENT.md) | Development workflow |
| [TESTING_GUIDE.md](docs/TESTING_GUIDE.md) | Testing strategies |
| [MULTI_LLM_GUIDE.md](docs/MULTI_LLM_GUIDE.md) | Multi-model LLM setup |
| [NOTIFICATIONS_AND_RESPONSES.md](docs/NOTIFICATIONS_AND_RESPONSES.md) | Email & response workflow |
| [SCRAPER.md](docs/SCRAPER.md) | LinkedIn scraper details |

### Specialized Guides

- **Getting Started with Ollama**: [`docs/guides/OLLAMA_SETUP.md`](docs/guides/OLLAMA_SETUP.md)
- **User Profile Configuration**: [`docs/guides/PROFILE_CONFIGURATION.md`](docs/guides/PROFILE_CONFIGURATION.md)
- **Scraper Improvements**: [`docs/guides/SCRAPER_IMPROVEMENTS.md`](docs/guides/SCRAPER_IMPROVEMENTS.md)
- **Monitoring Stack**: [`monitoring/README.md`](monitoring/README.md)
- **All Guides**: [`docs/guides/`](docs/guides/)

---

## 🤝 Contributing

Contributions are welcome! Please see [`CONTRIBUTING.md`](docs/CONTRIBUTING.md) for guidelines.

### Development Workflow

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Code Standards

- **Python**: Black formatting, Ruff linting, MyPy type checking
- **Tests**: 80%+ coverage required
- **Commits**: Conventional commits format
- **Documentation**: Update relevant docs with changes

---

## 🐛 Troubleshooting

### Common Issues

**Ollama not responding**:
```bash
docker-compose restart ollama
docker-compose logs ollama
```

**Database connection errors**:
```bash
docker-compose exec postgres pg_isready
# Check DATABASE_URL in .env
```

**Playwright browser issues**:
```bash
playwright install chromium --with-deps
```

**LinkedIn login failing**:
- Check credentials in `.env`
- Verify LinkedIn account isn't locked
- Try with `SCRAPER_HEADLESS=false` to debug

See [`docs/TROUBLESHOOTING.md`](docs/TROUBLESHOOTING.md) for more solutions.

---

## 📈 Performance

### Benchmarks

Based on testing (M1 MacBook Pro, 16GB RAM):

| Metric | Performance |
|--------|-------------|
| API Response Time (no LLM) | p95 < 100ms |
| Pipeline Execution | 2-4s per message |
| Throughput | ~15 messages/min (single worker) |
| Cache Hit Rate | ~60% steady state |
| Database Queries | p95 < 10ms |

### Optimization Tips

1. **Increase workers**: Scale Celery workers for higher throughput
2. **Batch processing**: Process multiple messages in batches
3. **Use cheaper models**: Ollama/Llama for analysis, GPT-4 for responses
4. **Cache aggressively**: Longer TTLs for stable data
5. **Connection pooling**: Reuse DB connections

---

## 🛡️ Security

- ✅ **Secrets Management**: All credentials in environment variables
- ✅ **Input Validation**: Pydantic models for all inputs
- ✅ **SQL Injection**: SQLAlchemy ORM with parameterized queries
- ✅ **Rate Limiting**: Prevents LinkedIn account restrictions
- ✅ **Dependency Scanning**: Automated with `safety` and `trivy`
- ✅ **Container Scanning**: Docker image vulnerability checks
- ✅ **Non-root Containers**: All containers run as non-root users

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

Built with amazing open-source tools:
- [DSPy](https://github.com/stanfordnlp/dspy) - Stanford NLP's structured prompting framework
- [FastAPI](https://fastapi.tiangolo.com) - Modern Python web framework
- [Ollama](https://ollama.ai) - Local LLM runtime
- [Playwright](https://playwright.dev) - Browser automation

Special thanks to the open-source community for making projects like this possible.

---

## 📬 Contact & Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/linkedin-ai-agent/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/linkedin-ai-agent/discussions)
- **Documentation**: [docs/](docs/)

---

<div align="center">

**⭐ Star this repo if you find it useful!**

Built with ❤️ for automating the job search

[Report Bug](https://github.com/yourusername/linkedin-ai-agent/issues) •
[Request Feature](https://github.com/yourusername/linkedin-ai-agent/issues) •
[Documentation](docs/)

</div>
