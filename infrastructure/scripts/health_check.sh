#!/bin/bash
# Health check script for all services

set -e

echo "🏥 Checking service health..."
echo "================================"

# Colors for output
GREEN='\033[0.32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check PostgreSQL
echo -n "PostgreSQL: "
if docker-compose exec -T postgres pg_isready -U user -d linkedin_agent > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Healthy${NC}"
    POSTGRES_OK=true
else
    echo -e "${RED}✗ Unhealthy${NC}"
    POSTGRES_OK=false
fi

# Check Redis
echo -n "Redis: "
if docker-compose exec -T redis redis-cli ping 2>/dev/null | grep -q PONG; then
    echo -e "${GREEN}✓ Healthy${NC}"
    REDIS_OK=true
else
    echo -e "${RED}✗ Unhealthy${NC}"
    REDIS_OK=false
fi

# Check Ollama
echo -n "Ollama: "
if curl -sf http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Healthy${NC}"
    OLLAMA_OK=true
else
    echo -e "${YELLOW}⚠ Not responding (may still be starting)${NC}"
    OLLAMA_OK=false
fi

echo "================================"

# Summary
if $POSTGRES_OK && $REDIS_OK; then
    echo -e "${GREEN}Core services are healthy!${NC}"
    if ! $OLLAMA_OK; then
        echo -e "${YELLOW}Note: Ollama may take 1-2 minutes to start${NC}"
    fi
    exit 0
else
    echo -e "${RED}Some services are unhealthy${NC}"
    echo "Run 'docker-compose logs <service>' to see logs"
    exit 1
fi
