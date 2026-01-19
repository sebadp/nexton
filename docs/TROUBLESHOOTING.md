# Troubleshooting Guide

Common issues and solutions for LinkedIn AI Agent.

## Table of Contents

- [Installation Issues](#installation-issues)
- [Docker Issues](#docker-issues)
- [Database Issues](#database-issues)
- [Ollama/LLM Issues](#ollamallm-issues)
- [LinkedIn Scraper Issues](#linkedin-scraper-issues)
- [Performance Issues](#performance-issues)
- [Monitoring Issues](#monitoring-issues)

---

## Installation Issues

### Python Version

**Problem**: `python: command not found` or wrong Python version

**Solution**:
```bash
# Check Python version
python3 --version

# Should be 3.11+
# If not, install Python 3.11:

# macOS
brew install python@3.11

# Ubuntu/Debian
sudo apt update
sudo apt install python3.11 python3.11-venv

# Verify
python3.11 --version
```

### Pip Installation Failures

**Problem**: Packages fail to install

**Solution**:
```bash
# Upgrade pip
pip install --upgrade pip

# Install with verbose output
pip install -r requirements.txt -v

# If specific package fails, try:
pip install package-name --no-cache-dir
```

### Playwright Installation

**Problem**: `playwright install` fails

**Solution**:
```bash
# Install with dependencies
playwright install chromium --with-deps

# If permission denied
sudo playwright install-deps

# Manual browser installation
python -m playwright install chromium
```

---

## Docker Issues

### Docker Compose Fails

**Problem**: `docker-compose` not found

**Solution**:
```bash
# Install Docker Compose
# macOS: Included with Docker Desktop

# Linux
sudo apt install docker-compose-plugin

# Or use docker compose (new syntax)
docker compose up -d
```

### Containers Won't Start

**Problem**: Containers exit immediately

**Solution**:
```bash
# Check logs
docker-compose logs [service-name]

# Common issues:
# 1. Port already in use
docker ps  # Check running containers
lsof -i :8000  # Check specific port

# 2. Volume permission issues
docker-compose down -v  # Remove volumes
docker-compose up -d

# 3. Image build issues
docker-compose build --no-cache
docker-compose up -d
```

### Out of Disk Space

**Problem**: `no space left on device`

**Solution**:
```bash
# Clean up Docker
docker system prune -a --volumes

# Check disk usage
df -h
docker system df

# Remove unused images
docker image prune -a
```

---

## Database Issues

### Connection Refused

**Problem**: `connection refused` to PostgreSQL

**Solution**:
```bash
# Check if Postgres is running
docker-compose ps postgres

# Check logs
docker-compose logs postgres

# Restart Postgres
docker-compose restart postgres

# Verify connection
docker-compose exec postgres pg_isready -U user
```

### Migration Errors

**Problem**: Alembic migration fails

**Solution**:
```bash
# Check current revision
alembic current

# Reset database (CAREFUL: loses data)
alembic downgrade base
alembic upgrade head

# Or drop and recreate
docker-compose down -v
docker-compose up -d postgres
alembic upgrade head
```

### Database Locked

**Problem**: `database is locked`

**Solution**:
```bash
# Check active connections
docker-compose exec postgres psql -U user -d linkedin_agent -c "SELECT * FROM pg_stat_activity;"

# Kill connections if needed
docker-compose exec postgres psql -U user -d linkedin_agent -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'linkedin_agent' AND pid <> pg_backend_pid();"
```

---

## Ollama/LLM Issues

### Ollama Not Responding

**Problem**: Ollama API not reachable

**Solution**:
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Restart Ollama
docker-compose restart ollama

# Check logs
docker-compose logs ollama

# Pull model if missing
docker-compose exec ollama ollama pull llama3.2
```

### Model Not Found

**Problem**: `model 'llama3.2' not found`

**Solution**:
```bash
# List available models
docker-compose exec ollama ollama list

# Pull the model
docker-compose exec ollama ollama pull llama3.2

# Or use a different model in .env
LLM_MODEL=mistral  # or another available model
```

### Slow LLM Responses

**Problem**: LLM responses take too long

**Solution**:
```bash
# 1. Use a smaller model
LLM_MODEL=llama3.2:1b  # Faster, less accurate

# 2. Reduce max tokens
LLM_MAX_TOKENS=200

# 3. Enable GPU (if available)
# Edit docker-compose.yml, uncomment GPU section

# 4. Use OpenAI/Anthropic for critical paths
RESPONSE_LLM_PROVIDER=openai
RESPONSE_LLM_MODEL=gpt-3.5-turbo
```

---

## LinkedIn Scraper Issues

### Login Failures

**Problem**: Scraper can't log into LinkedIn

**Solution**:
```bash
# 1. Verify credentials in .env
LINKEDIN_EMAIL=your@email.com
LINKEDIN_PASSWORD=your_password

# 2. Check if account is locked
# - Log in manually via browser
# - Complete any security challenges

# 3. Run with headless=false to debug
SCRAPER_HEADLESS=false
python scripts/scrape_linkedin.py

# 4. Clear cookies
rm data/cookies.json
```

### Rate Limiting

**Problem**: LinkedIn blocks requests

**Solution**:
```bash
# Increase delays in .env
SCRAPER_MIN_DELAY_SECONDS=5.0
SCRAPER_MAX_REQUESTS_PER_MINUTE=5

# Reduce scraping frequency
# Edit docker-compose.yml celery-beat schedule
```

### Selector Not Found

**Problem**: `Element not found: <selector>`

**Solution**:
```bash
# LinkedIn changed their HTML structure
# Run with debug mode to see current page
SCRAPER_HEADLESS=false
LOG_LEVEL=DEBUG

# Check scraper logs for details
docker-compose logs scraper

# Update selectors in app/scraper/linkedin_scraper.py
```

### Browser Crash

**Problem**: Playwright browser crashes

**Solution**:
```bash
# Increase memory limits in docker-compose.yml
deploy:
  resources:
    limits:
      memory: 4G

# Or reduce concurrency
CELERY_WORKER_CONCURRENCY=2
```

---

## Performance Issues

### High Memory Usage

**Problem**: System using too much memory

**Solution**:
```bash
# Check container stats
docker stats

# Reduce worker count
CELERY_WORKER_CONCURRENCY=2

# Limit container memory
# Edit docker-compose.yml:
deploy:
  resources:
    limits:
      memory: 2G

# Clear Redis cache
docker-compose exec redis redis-cli FLUSHALL
```

### Slow API Responses

**Problem**: API endpoints are slow

**Solution**:
```bash
# 1. Check if caching is enabled
CACHE_ENABLED=true

# 2. Monitor metrics
open http://localhost:3000  # Grafana

# 3. Check database queries
docker-compose logs app | grep "query_latency"

# 4. Add database indexes (if needed)
# See docs/PERFORMANCE.md
```

### High CPU Usage

**Problem**: CPU usage is very high

**Solution**:
```bash
# Check which service is using CPU
docker stats

# Common causes:
# 1. Too many Celery workers
CELERY_WORKER_CONCURRENCY=2

# 2. LLM inference (use GPU or external API)
# 3. Too many concurrent scraping tasks
```

---

## Monitoring Issues

### Grafana Not Loading

**Problem**: Grafana dashboard doesn't load

**Solution**:
```bash
# Check if Grafana is running
docker-compose -f docker-compose.monitoring.yml ps

# Restart Grafana
docker-compose -f docker-compose.monitoring.yml restart grafana

# Check logs
docker-compose -f docker-compose.monitoring.yml logs grafana

# Access Grafana
open http://localhost:3000
# Login: admin/admin
```

### No Metrics in Prometheus

**Problem**: Prometheus not collecting metrics

**Solution**:
```bash
# Check if metrics endpoint is accessible
curl http://localhost:8000/api/v1/metrics

# Verify Prometheus targets
open http://localhost:9090/targets

# Check Prometheus config
cat monitoring/prometheus/prometheus.yml

# Restart Prometheus
docker-compose -f docker-compose.monitoring.yml restart prometheus
```

### Jaeger Not Showing Traces

**Problem**: No traces in Jaeger UI

**Solution**:
```bash
# Verify tracing is enabled in .env
OTEL_ENABLED=true
OTEL_EXPORTER_OTLP_ENDPOINT=http://jaeger:4318

# Check if Jaeger is running
docker-compose -f docker-compose.monitoring.yml ps jaeger

# Generate some traffic
curl -X POST http://localhost:8000/api/v1/opportunities \
  -H "Content-Type: application/json" \
  -d '{"recruiter_name":"Test","raw_message":"Test message"}'

# Check Jaeger UI
open http://localhost:16686
```

---

## General Debugging

### Enable Debug Logging

```bash
# In .env
LOG_LEVEL=DEBUG

# Restart services
docker-compose restart
```

### Check Service Health

```bash
# Health check endpoint
curl http://localhost:8000/health

# Check all services
docker-compose ps

# Detailed logs
docker-compose logs -f [service-name]
```

### Reset Everything

```bash
# Nuclear option: reset everything
docker-compose down -v
docker system prune -a --volumes
docker-compose build --no-cache
docker-compose up -d
alembic upgrade head
```

---

## Getting Help

If you're still stuck:

1. **Check logs**: `docker-compose logs [service]`
2. **Search issues**: [GitHub Issues](https://github.com/yourusername/linkedin-ai-agent/issues)
3. **Ask community**: [GitHub Discussions](https://github.com/yourusername/linkedin-ai-agent/discussions)
4. **Create issue**: Provide logs, environment details, steps to reproduce

---

## Useful Commands

```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f app

# Check service status
docker-compose ps

# Restart service
docker-compose restart [service]

# Rebuild and restart
docker-compose up -d --build

# Shell into container
docker-compose exec app bash

# Database shell
docker-compose exec postgres psql -U user -d linkedin_agent

# Redis CLI
docker-compose exec redis redis-cli

# Check disk usage
docker system df

# Clean up
docker system prune -a --volumes
```
