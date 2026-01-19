# Deployment Guide

Comprehensive deployment guide for the LinkedIn AI Agent Platform with full observability stack.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Deployment Options](#deployment-options)
- [Docker Compose Deployment](#docker-compose-deployment)
- [Production Configuration](#production-configuration)
- [Monitoring Stack Setup](#monitoring-stack-setup)
- [Environment Variables](#environment-variables)
- [Database Setup](#database-setup)
- [Secrets Management](#secrets-management)
- [Health Checks](#health-checks)
- [Backup and Restore](#backup-and-restore)
- [Scaling](#scaling)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements

- **CPU**: 4+ cores recommended
- **RAM**: 8GB minimum, 16GB recommended (with monitoring stack)
- **Disk**: 20GB+ free space
- **OS**: Linux (Ubuntu 20.04+), macOS, Windows with WSL2

### Software Requirements

- Docker 20.10+
- Docker Compose 2.0+
- Git
- (Optional) Make for convenience commands

### Network Requirements

- Outbound HTTPS (443) for:
  - Docker Hub (pulling images)
  - Ollama models (if using remote LLM)
  - LinkedIn API (scraping)
- Inbound ports (configurable):
  - 8000: API
  - 3000: Grafana
  - 9090: Prometheus
  - 16686: Jaeger
  - 5555: Flower

## Deployment Options

### 1. Docker Compose (Recommended)

Best for:
- Development environments
- Small to medium production deployments
- Quick setup and testing

**Pros**: Easy setup, minimal configuration
**Cons**: Single host limitation

### 2. Docker Swarm

Best for:
- Multi-host deployments
- Built-in orchestration needs
- Teams familiar with Docker

**Pros**: Native Docker, easy migration from Compose
**Cons**: Less ecosystem support than Kubernetes

### 3. Kubernetes

Best for:
- Large-scale production
- Multi-region deployments
- Advanced orchestration needs

**Pros**: Industry standard, rich ecosystem
**Cons**: More complex setup and management

## Docker Compose Deployment

### Quick Start

```bash
# 1. Clone repository
git clone https://github.com/yourusername/linkedin-agent.git
cd linkedin-agent

# 2. Configure environment
cp .env.example .env
# Edit .env with your configuration

# 3. Start core services
docker-compose up -d

# 4. Start monitoring stack
docker-compose -f docker-compose.monitoring.yml up -d

# 5. Verify deployment
curl http://localhost:8000/health
open http://localhost:3000  # Grafana dashboard
```

### Step-by-Step Deployment

#### 1. Prepare Environment

```bash
# Create required directories
mkdir -p data/postgres data/redis logs

# Set permissions
chmod -R 755 data logs

# Create network
docker network create linkedin-agent-network
```

#### 2. Configure Environment Variables

```bash
# Copy and edit .env
cp .env.example .env

# Required configurations
nano .env  # or your preferred editor
```

Key variables to configure:
```bash
# Application
ENV=production
DEBUG=false
LOG_LEVEL=INFO

# Database (use strong passwords!)
DATABASE_URL=postgresql://linkedin_user:STRONG_PASSWORD@postgres:5432/linkedin_agent

# Redis
REDIS_URL=redis://:STRONG_PASSWORD@redis:6379/0

# LinkedIn credentials
LINKEDIN_EMAIL=your_email@example.com
LINKEDIN_PASSWORD=your_secure_password

# Observability
OTEL_ENABLED=true
OTEL_EXPORTER_OTLP_ENDPOINT=http://jaeger:4318
```

#### 3. Build Images

```bash
# Build all services
docker-compose build

# Or build specific service
docker-compose build api
docker-compose build worker
```

#### 4. Initialize Database

```bash
# Start database first
docker-compose up -d postgres redis

# Wait for database to be ready
docker-compose exec postgres pg_isready

# Run migrations
docker-compose exec api alembic upgrade head

# (Optional) Seed database
docker-compose exec api python scripts/seed_db.py
```

#### 5. Start Services

```bash
# Start all core services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f
```

#### 6. Start Monitoring Stack

```bash
# Start observability services
docker-compose -f docker-compose.monitoring.yml up -d

# Verify monitoring
open http://localhost:3000  # Grafana (admin/admin)
open http://localhost:9090  # Prometheus
open http://localhost:16686 # Jaeger
```

#### 7. Verify Deployment

```bash
# Health check
curl http://localhost:8000/health

# Check API docs
open http://localhost:8000/docs

# Check metrics
curl http://localhost:8000/api/v1/metrics

# Test endpoint
curl -X POST http://localhost:8000/api/v1/opportunities \
  -H "Content-Type: application/json" \
  -d '{"recruiter_name": "Test", "raw_message": "Test message"}'
```

## Production Configuration

### docker-compose.prod.yml

Create a production-specific compose file:

```yaml
version: '3.8'

services:
  api:
    image: linkedin-agent:latest
    restart: always
    environment:
      - ENV=production
      - DEBUG=false
      - LOG_LEVEL=WARNING
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  worker:
    image: linkedin-agent:latest
    restart: always
    command: celery -A app.celery_app.celery_app worker --loglevel=info
    environment:
      - ENV=production
    deploy:
      replicas: 2

  postgres:
    image: postgres:15-alpine
    restart: always
    volumes:
      - postgres-data:/var/lib/postgresql/data
      - ./backups:/backups
    environment:
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    deploy:
      resources:
        limits:
          memory: 2G

  redis:
    image: redis:7-alpine
    restart: always
    command: redis-server --requirepass ${REDIS_PASSWORD} --maxmemory 1gb --maxmemory-policy allkeys-lru
    volumes:
      - redis-data:/data

volumes:
  postgres-data:
    driver: local
  redis-data:
    driver: local
```

### Resource Limits

Recommended resource allocation:

| Service | CPU | Memory | Purpose |
|---------|-----|--------|---------|
| API | 1-2 cores | 1-2 GB | HTTP requests |
| Worker | 1-2 cores | 1-2 GB | Background jobs |
| Postgres | 2 cores | 2-4 GB | Database |
| Redis | 0.5-1 core | 1-2 GB | Cache |
| Prometheus | 0.5 core | 1 GB | Metrics |
| Grafana | 0.5 core | 512 MB | Dashboards |
| Jaeger | 1 core | 1 GB | Tracing |

### Production Checklist

- [ ] Use strong passwords for all services
- [ ] Enable TLS/SSL for external access
- [ ] Configure firewall rules
- [ ] Set up automated backups
- [ ] Configure log rotation
- [ ] Enable monitoring alerts
- [ ] Set resource limits
- [ ] Configure auto-restart policies
- [ ] Test disaster recovery procedures
- [ ] Document deployment procedures

## Monitoring Stack Setup

### Full Stack Deployment

```bash
# Deploy monitoring services
docker-compose -f docker-compose.monitoring.yml up -d

# Verify services
docker-compose -f docker-compose.monitoring.yml ps

# Check Prometheus targets
open http://localhost:9090/targets

# Import Grafana dashboards
# Dashboards are auto-provisioned from monitoring/grafana/dashboards/
```

### Configure Grafana

```bash
# Access Grafana
open http://localhost:3000

# Default credentials: admin/admin
# Change password on first login

# Verify datasources
# Go to Configuration > Data Sources
# Should see: Prometheus, Loki, Jaeger
```

### Custom Alerts

Create alertmanager configuration:

```yaml
# monitoring/alertmanager/config.yml
global:
  resolve_timeout: 5m

route:
  receiver: 'default'
  group_by: ['alertname']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 12h

receivers:
  - name: 'default'
    email_configs:
      - to: 'alerts@example.com'
        from: 'alertmanager@example.com'
        smarthost: 'smtp.example.com:587'
        auth_username: 'alertmanager@example.com'
        auth_password: 'password'
```

### Alert Rules

```yaml
# monitoring/prometheus/alerts.yml
groups:
  - name: application
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }}%"

      - alert: HighMemoryUsage
        expr: container_memory_usage_bytes / container_spec_memory_limit_bytes > 0.9
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage"
          description: "Memory usage is {{ $value }}%"
```

## Environment Variables

### Required Variables

```bash
# Application
ENV=production
APP_NAME=linkedin-agent
LOG_LEVEL=INFO

# Database
DATABASE_URL=postgresql://user:pass@postgres:5432/linkedin_agent
DATABASE_POOL_SIZE=20

# Redis
REDIS_URL=redis://:password@redis:6379/0

# Celery
CELERY_BROKER_URL=redis://:password@redis:6379/0
CELERY_RESULT_BACKEND=redis://:password@redis:6379/0
```

### Optional Variables

```bash
# Observability
OTEL_ENABLED=true
OTEL_EXPORTER_OTLP_ENDPOINT=http://jaeger:4318
PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus

# LinkedIn
LINKEDIN_EMAIL=your@email.com
LINKEDIN_PASSWORD=your_password
SCRAPER_HEADLESS=true

# Performance
CELERY_WORKER_CONCURRENCY=4
DATABASE_MAX_OVERFLOW=10
```

See [.env.example](../.env.example) for complete list.

## Database Setup

### Initial Setup

```bash
# Create database
docker-compose exec postgres createdb -U postgres linkedin_agent

# Run migrations
docker-compose exec api alembic upgrade head

# Verify
docker-compose exec postgres psql -U postgres -d linkedin_agent -c "\dt"
```

### Backup

```bash
# Create backup
docker-compose exec postgres pg_dump -U postgres linkedin_agent > backup_$(date +%Y%m%d).sql

# Automated backups (cron)
0 2 * * * cd /path/to/linkedin-agent && docker-compose exec -T postgres pg_dump -U postgres linkedin_agent | gzip > backups/backup_$(date +\%Y\%m\%d_\%H\%M\%S).sql.gz
```

### Restore

```bash
# Restore from backup
docker-compose exec -T postgres psql -U postgres linkedin_agent < backup_20240116.sql

# Or from gzipped backup
gunzip -c backups/backup_20240116.sql.gz | docker-compose exec -T postgres psql -U postgres linkedin_agent
```

## Secrets Management

### Using Docker Secrets (Swarm)

```bash
# Create secrets
echo "my_db_password" | docker secret create db_password -
echo "my_redis_password" | docker secret create redis_password -

# Use in compose
services:
  postgres:
    secrets:
      - db_password
    environment:
      - POSTGRES_PASSWORD_FILE=/run/secrets/db_password

secrets:
  db_password:
    external: true
  redis_password:
    external: true
```

### Using Environment Files

```bash
# Create secrets file
cat > .env.secrets <<EOF
POSTGRES_PASSWORD=strong_password_here
REDIS_PASSWORD=another_strong_password
LINKEDIN_PASSWORD=linkedin_password_here
EOF

# Restrict permissions
chmod 600 .env.secrets

# Load in compose
env_file:
  - .env
  - .env.secrets
```

### Using Vault

```bash
# Install Vault CLI
curl -fsSL https://apt.releases.hashicorp.com/gpg | sudo apt-key add -
sudo apt-add-repository "deb [arch=amd64] https://apt.releases.hashicorp.com $(lsb_release -cs) main"
sudo apt-get update && sudo apt-get install vault

# Store secrets
vault kv put secret/linkedin-agent \
  db_password="strong_password" \
  redis_password="another_password"

# Retrieve in deployment script
export DATABASE_PASSWORD=$(vault kv get -field=db_password secret/linkedin-agent)
```

## Health Checks

### API Health Check

```bash
# Basic health
curl http://localhost:8000/health

# Response:
# {"status":"healthy","timestamp":"2024-01-16T12:00:00Z"}

# Readiness check (checks all dependencies)
curl http://localhost:8000/health/ready

# Response:
# {
#   "status": "ready",
#   "checks": {
#     "database": "healthy",
#     "redis": "healthy",
#     "ollama": "healthy"
#   }
# }
```

### Automated Health Monitoring

```bash
# Using Docker Compose healthcheck
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

### Monitoring Dashboard

Access health metrics in Grafana:
```
http://localhost:3000/d/health-dashboard
```

## Backup and Restore

### Automated Backup Script

```bash
#!/bin/bash
# scripts/backup.sh

BACKUP_DIR="./backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup database
docker-compose exec -T postgres pg_dump -U postgres linkedin_agent | gzip > $BACKUP_DIR/db_$TIMESTAMP.sql.gz

# Backup Redis
docker-compose exec redis redis-cli SAVE
docker cp $(docker-compose ps -q redis):/data/dump.rdb $BACKUP_DIR/redis_$TIMESTAMP.rdb

# Backup configuration
tar -czf $BACKUP_DIR/config_$TIMESTAMP.tar.gz .env monitoring/grafana/

# Cleanup old backups (keep last 30 days)
find $BACKUP_DIR -name "*.gz" -mtime +30 -delete
find $BACKUP_DIR -name "*.rdb" -mtime +30 -delete

echo "Backup completed: $TIMESTAMP"
```

### Restore Script

```bash
#!/bin/bash
# scripts/restore.sh

BACKUP_FILE=$1

if [ -z "$BACKUP_FILE" ]; then
  echo "Usage: ./restore.sh <backup_file>"
  exit 1
fi

# Stop services
docker-compose down

# Restore database
gunzip -c $BACKUP_FILE | docker-compose exec -T postgres psql -U postgres linkedin_agent

# Start services
docker-compose up -d

echo "Restore completed"
```

## Scaling

### Horizontal Scaling

```bash
# Scale API instances
docker-compose up -d --scale api=3

# Scale workers
docker-compose up -d --scale worker=5

# Scale with load balancer
# Add nginx.conf for load balancing
```

### Vertical Scaling

Update resource limits in docker-compose.yml:

```yaml
services:
  api:
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 4G
```

### Database Scaling

```yaml
# Read replicas
services:
  postgres-replica:
    image: postgres:15
    environment:
      - POSTGRES_MASTER_HOST=postgres
      - POSTGRES_REPLICATION_MODE=slave
```

## Troubleshooting

### Service Won't Start

```bash
# Check logs
docker-compose logs api

# Check resource usage
docker stats

# Verify configuration
docker-compose config
```

### Database Connection Issues

```bash
# Test connection
docker-compose exec api python -c "from app.database.base import engine; engine.connect()"

# Check postgres logs
docker-compose logs postgres

# Verify credentials
docker-compose exec postgres psql -U postgres -d linkedin_agent
```

### High Memory Usage

```bash
# Identify memory hogs
docker stats --no-stream

# Reduce worker concurrency
# In .env:
CELERY_WORKER_CONCURRENCY=2

# Restart services
docker-compose restart worker
```

### Monitoring Stack Issues

```bash
# Restart monitoring
docker-compose -f docker-compose.monitoring.yml restart

# Check Prometheus targets
open http://localhost:9090/targets

# Verify Grafana datasources
open http://localhost:3000/datasources
```

## Next Steps

- [Configure Alerts](../monitoring/README.md#alerting)
- [Performance Tuning](PERFORMANCE.md)
- [Security Hardening](SECURITY.md)
- [CI/CD Setup](CICD.md)

## Support

- Documentation: [docs/](.)
- Issues: [GitHub Issues](https://github.com/yourusername/linkedin-agent/issues)
- Monitoring: http://localhost:3000 (Grafana)
