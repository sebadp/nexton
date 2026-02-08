.PHONY: help setup up down logs test lint format security clean

# Default target
.DEFAULT_GOAL := help

help:  ## Show this help message
	@echo "LinkedIn AI Agent - Available Commands"
	@echo "======================================"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ==========================================
# SETUP & INSTALLATION
# ==========================================

setup:  ## Initial project setup
	@echo "🚀 Setting up LinkedIn Agent..."
	@command -v poetry >/dev/null 2>&1 || { echo "Installing Poetry..."; curl -sSL https://install.python-poetry.org | python3 -; }
	poetry install
	@echo "📦 Pulling Docker images..."
	docker-compose pull
	@echo "🔨 Building Docker images..."
	docker-compose build
	@echo "📁 Creating directories..."
	mkdir -p data logs config docs/diagrams
	@echo "⚙️  Copying environment file..."
	@if [ ! -f .env ]; then cp .env.example .env; echo "Created .env file. Please configure it."; fi
	@echo "✅ Setup complete!"
	@echo ""
	@echo "Next steps:"
	@echo "  1. Edit .env with your configuration"
	@echo "  2. Run 'make up' to start services"
	@echo "  3. Visit http://localhost:8000/docs"

install:  ## Install Python dependencies
	poetry install

install-dev:  ## Install dev dependencies
	poetry install --with dev

# ==========================================
# DOCKER OPERATIONS
# ==========================================

up:  ## Start all services
	@echo "🚀 Starting services..."
	docker-compose up -d
	@echo "✅ Services started!"
	@echo ""
	@echo "📊 Access Points:"
	@echo "  API:        http://localhost:8000"
	@echo "  API Docs:   http://localhost:8000/docs"
	@echo "  Grafana:    http://localhost:3000 (admin/admin)"
	@echo "  Prometheus: http://localhost:9090"
	@echo "  Jaeger:     http://localhost:16686"
	@echo "  PGAdmin:    http://localhost:5050"
	@echo ""
	@echo "Use 'make logs' to view application logs"

down:  ## Stop all services
	@echo "🛑 Stopping services..."
	docker-compose down
	@echo "✅ Services stopped!"

restart:  ## Restart all services
	@echo "🔄 Restarting services..."
	docker-compose restart
	@echo "✅ Services restarted!"

ps:  ## Show running services
	docker-compose ps

# ==========================================
# LOGS & MONITORING
# ==========================================

logs:  ## Show application logs
	docker-compose logs -f app

logs-all:  ## Show all service logs
	docker-compose logs -f

logs-scraper:  ## Show scraper logs
	docker-compose logs -f scraper

logs-celery:  ## Show Celery worker logs
	docker-compose logs -f celery-worker

monitoring:  ## Open monitoring dashboards
	@echo "📊 Opening monitoring dashboards..."
	@echo "  Grafana:    http://localhost:3000"
	@echo "  Jaeger:     http://localhost:16686"
	@echo "  Prometheus: http://localhost:9090"
	@command -v open >/dev/null 2>&1 && open http://localhost:3000 || xdg-open http://localhost:3000 2>/dev/null || echo "Please open http://localhost:3000 manually"

# ==========================================
# DEVELOPMENT
# ==========================================

dev-setup:  ## Setup development environment
	@echo "🛠️  Setting up dev environment..."
	poetry install --with dev
	pre-commit install
	@if [ ! -f .env ]; then cp .env.example .env; fi
	@echo "✅ Dev environment ready!"

dev-run:  ## Run app locally with hot reload
	poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-run-docker:  ## Run in dev mode with Docker (hot reload)
	docker-compose up app --build

shell:  ## Open Python shell in app container
	docker-compose exec app python

bash:  ## Open bash shell in app container
	docker-compose exec app /bin/bash

# ==========================================
# TESTING
# ==========================================

test:  ## Run all tests with coverage
	@echo "🧪 Running tests..."
	docker-compose exec app pytest tests/ -v --cov=app --cov-report=term-missing --cov-report=html
	@echo "📊 Coverage report generated in htmlcov/"

test-unit:  ## Run unit tests only
	docker-compose exec app pytest tests/unit/ -v

test-integration:  ## Run integration tests
	docker-compose exec app pytest tests/integration/ -v

test-e2e:  ## Run end-to-end tests
	docker-compose exec app pytest tests/e2e/ -v

test-watch:  ## Run tests in watch mode
	docker-compose exec app ptw tests/ -- -v

test-local:  ## Run tests locally (no Docker)
	poetry run pytest tests/ -v --cov=app

coverage:  ## Generate coverage report
	docker-compose exec app pytest tests/ --cov=app --cov-report=html
	@echo "📊 Coverage report: htmlcov/index.html"

load-test:  ## Run load tests
	docker-compose exec app locust -f tests/performance/locustfile.py --headless -u 100 -r 10 -t 60s --host http://localhost:8000

# ==========================================
# CODE QUALITY
# ==========================================

lint:  ## Run all linters
	@echo "🔍 Running linters..."
	poetry run black app/ tests/ --check
	poetry run ruff check app/ tests/
	poetry run mypy app/

format:  ## Format code
	@echo "🎨 Formatting code..."
	poetry run black app/ tests/
	poetry run ruff check --fix app/ tests/

format-check:  ## Check code formatting
	poetry run black app/ tests/ --check

type-check:  ## Run type checking
	poetry run mypy app/

check:  ## Run all local validations (lint + format check + test)
	$(MAKE) lint
	$(MAKE) test-unit


security:  ## Run security scans
	@echo "🔒 Running security scans..."
	poetry run bandit -r app/ -ll
	poetry run safety check
	trivy fs . --severity HIGH,CRITICAL

pre-commit:  ## Run pre-commit hooks
	pre-commit run --all-files

# ==========================================
# DATABASE
# ==========================================

db-shell:  ## Open PostgreSQL shell
	docker-compose exec postgres psql -U user -d linkedin_agent

db-dump:  ## Dump database
	docker-compose exec postgres pg_dump -U user linkedin_agent > backup_$$(date +%Y%m%d_%H%M%S).sql

db-restore:  ## Restore database (requires BACKUP_FILE variable)
	@if [ -z "$(BACKUP_FILE)" ]; then echo "Usage: make db-restore BACKUP_FILE=backup.sql"; exit 1; fi
	docker-compose exec -T postgres psql -U user linkedin_agent < $(BACKUP_FILE)

migrate:  ## Run database migrations
	docker-compose exec app alembic upgrade head

migrate-create:  ## Create new migration (requires MESSAGE variable)
	@if [ -z "$(MESSAGE)" ]; then \
		read -p "Migration message: " msg; \
		docker-compose exec app alembic revision --autogenerate -m "$$msg"; \
	else \
		docker-compose exec app alembic revision --autogenerate -m "$(MESSAGE)"; \
	fi

migrate-down:  ## Rollback last migration
	docker-compose exec app alembic downgrade -1

migrate-history:  ## Show migration history
	docker-compose exec app alembic history

migrate-lite:  ## Run database migrations (lite mode)
	docker-compose -f docker-compose.lite.yml exec app alembic upgrade head

migrate-lite-down:  ## Rollback last migration (lite mode)
	docker-compose -f docker-compose.lite.yml exec app alembic downgrade -1

# ==========================================
# REDIS
# ==========================================

redis-cli:  ## Open Redis CLI
	docker-compose exec redis redis-cli

redis-flush:  ## Flush Redis cache
	docker-compose exec redis redis-cli FLUSHALL

redis-monitor:  ## Monitor Redis commands
	docker-compose exec redis redis-cli MONITOR

# ==========================================
# OLLAMA
# ==========================================

ollama-pull:  ## Pull Ollama model (requires MODEL variable)
	@if [ -z "$(MODEL)" ]; then echo "Usage: make ollama-pull MODEL=llama2"; exit 1; fi
	docker-compose exec ollama ollama pull $(MODEL)

ollama-list:  ## List Ollama models
	docker-compose exec ollama ollama list

ollama-run:  ## Run Ollama model interactively (requires MODEL variable)
	@if [ -z "$(MODEL)" ]; then echo "Usage: make ollama-run MODEL=llama2"; exit 1; fi
	docker-compose exec ollama ollama run $(MODEL)

# ==========================================
# CLEANUP
# ==========================================

clean:  ## Clean up generated files and containers
	@echo "🧹 Cleaning up..."
	docker-compose down -v
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov/ .coverage
	@echo "✅ Cleanup complete!"

clean-logs:  ## Clean log files
	rm -rf logs/*.log

clean-docker:  ## Remove all Docker containers, volumes, and images
	@echo "⚠️  This will remove ALL Docker containers, volumes, and images!"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker-compose down -v --rmi all --remove-orphans; \
		echo "✅ Docker cleaned!"; \
	fi

# ==========================================
# CI/CD
# ==========================================

ci-local:  ## Run CI pipeline locally (requires act)
	@command -v act >/dev/null 2>&1 || { echo "act is not installed. Install from: https://github.com/nektos/act"; exit 1; }
	act -j test

ci-test:  ## Run CI test suite
	@echo "🧪 Running CI tests..."
	$(MAKE) lint
	$(MAKE) test
	$(MAKE) security

# ==========================================
# BUILD & DEPLOYMENT
# ==========================================

build:  ## Build Docker images
	docker-compose build

build-prod:  ## Build production images
	docker-compose -f docker-compose.prod.yml build

deploy-staging:  ## Deploy to staging
	@echo "🚀 Deploying to staging..."
	./scripts/deploy.sh staging

deploy-prod:  ## Deploy to production
	@echo "🚀 Deploying to production..."
	./scripts/deploy.sh production

# ==========================================
# DOCUMENTATION
# ==========================================

docs:  ## Generate documentation
	@echo "📚 Generating documentation..."
	@echo "Documentation is in docs/ directory"

docs-serve:  ## Serve documentation locally
	@command -v mkdocs >/dev/null 2>&1 && mkdocs serve || echo "mkdocs not installed. Run: pip install mkdocs"

# ==========================================
# UTILITIES
# ==========================================

health:  ## Check application health
	@echo "🏥 Checking application health..."
	@curl -f http://localhost:8000/health || echo "❌ Application is not healthy"
	@curl -f http://localhost:8000/health/ready || echo "❌ Application is not ready"

health-all:  ## Check all services health
	@echo "🏥 Checking all services..."
	@echo "Application:"
	@curl -sf http://localhost:8000/health && echo "  ✅ Healthy" || echo "  ❌ Unhealthy"
	@echo "PostgreSQL:"
	@docker-compose exec postgres pg_isready -U user && echo "  ✅ Ready" || echo "  ❌ Not ready"
	@echo "Redis:"
	@docker-compose exec redis redis-cli ping | grep -q PONG && echo "  ✅ Ready" || echo "  ❌ Not ready"
	@echo "Ollama:"
	@curl -sf http://localhost:11434/api/tags >/dev/null && echo "  ✅ Ready" || echo "  ❌ Not ready"

backup:  ## Backup database and config
	@echo "💾 Creating backup..."
	@mkdir -p backups
	@docker-compose exec postgres pg_dump -U user linkedin_agent > backups/db_backup_$$(date +%Y%m%d_%H%M%S).sql
	@cp .env backups/env_backup_$$(date +%Y%m%d_%H%M%S)
	@echo "✅ Backup created in backups/"

stats:  ## Show Docker stats
	docker stats --no-stream

info:  ## Show system information
	@echo "LinkedIn AI Agent - System Information"
	@echo "======================================"
	@echo "Docker version:"
	@docker --version
	@echo ""
	@echo "Docker Compose version:"
	@docker-compose --version
	@echo ""
	@echo "Python version:"
	@python --version 2>&1 || python3 --version
	@echo ""
	@echo "Poetry version:"
	@poetry --version 2>&1 || echo "Poetry not installed"
	@echo ""
	@echo "Running containers:"
	@docker-compose ps

# ==========================================
# QUICK ACTIONS
# ==========================================

quick-start:  ## Quick start (setup + up)
	$(MAKE) setup
	$(MAKE) up

quick-test:  ## Quick test (lint + test-unit)
	$(MAKE) lint
	$(MAKE) test-unit

reset:  ## Reset everything (clean + setup + up)
	$(MAKE) clean
	$(MAKE) setup
	$(MAKE) up

# ==========================================
# SIMPLE START COMMANDS
# ==========================================

start:  ## Start full version (all services)
	@if [ ! -f .env ]; then cp .env.example .env && echo "📋 Created .env from .env.example - please edit it"; fi
	@echo "🚀 Starting FULL version..."
	docker-compose up -d
	@echo ""
	@echo "✅ Full version started!"
	@echo "   Frontend:  http://localhost:3000"
	@echo "   API:       http://localhost:8000"
	@echo "   API Docs:  http://localhost:8000/docs"
	@echo "   Mailpit:   http://localhost:8025"
	@echo "   Flower:    http://localhost:5555"

start-lite:  ## Start lite version (backend + frontend + postgres only)
	@if [ ! -f .env ]; then cp .env.example .env && echo "📋 Created .env from .env.example - please edit it"; fi
	@echo "🚀 Starting LITE version..."
	docker-compose -f docker-compose.lite.yml up -d
	@echo ""
	@echo "✅ Lite version started!"
	@echo "   Frontend:  http://localhost:3000"
	@echo "   API:       http://localhost:8000"
	@echo "   API Docs:  http://localhost:8000/docs"

stop:  ## Stop all services (full or lite)
	@echo "🛑 Stopping services..."
	-docker-compose down 2>/dev/null
	-docker-compose -f docker-compose.lite.yml down 2>/dev/null
	@echo "✅ Services stopped!"

start-logs:  ## Start full version with logs (foreground)
	@if [ ! -f .env ]; then cp .env.example .env && echo "📋 Created .env from .env.example - please edit it"; fi
	@echo "🚀 Starting FULL version with logs..."
	docker-compose up

start-lite-logs:  ## Start lite version with logs (foreground)
	@if [ ! -f .env ]; then cp .env.example .env && echo "📋 Created .env from .env.example - please edit it"; fi
	@echo "🚀 Starting LITE version with logs..."
	docker-compose -f docker-compose.lite.yml up

rebuild-lite:  ## Rebuild and restart all lite services
	@echo "🔄 Rebuilding all LITE services..."
	docker-compose -f docker-compose.lite.yml build
	docker-compose -f docker-compose.lite.yml up -d
	@echo "✅ Lite services rebuilt and restarted!"

rebuild-lite-frontend:  ## Rebuild and restart frontend only (lite)
	@echo "🔄 Rebuilding frontend..."
	docker-compose -f docker-compose.lite.yml build frontend
	docker-compose -f docker-compose.lite.yml up -d frontend
	@echo "✅ Frontend rebuilt and restarted!"

rebuild-lite-backend:  ## Rebuild and restart backend only (lite)
	@echo "🔄 Rebuilding backend..."
	docker-compose -f docker-compose.lite.yml build app
	docker-compose -f docker-compose.lite.yml up -d app
	@echo "✅ Backend rebuilt and restarted!"
