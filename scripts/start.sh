#!/bin/bash
# ============================================================================
# LinkedIn AI Agent - Startup Script
# ============================================================================

set -e  # Exit on error

echo "🚀 LinkedIn AI Agent - Starting..."
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  .env file not found. Creating from .env.example...${NC}"
    cp .env.example .env
    echo -e "${GREEN}✅ Created .env file. Please review and update if needed.${NC}"
    echo ""
fi

# Build images
echo "📦 Building Docker images..."
docker-compose build

# Start services
echo "🐳 Starting services..."
docker-compose up -d

# Wait for services
echo "⏳ Waiting for services to be healthy..."
sleep 15

# Check health
echo "🏥 Checking service health..."
until curl -sf http://localhost:8000/health > /dev/null 2>&1; do
    echo "   Waiting for app to be ready..."
    sleep 5
done

echo -e "${GREEN}✅ All services are healthy!${NC}"
echo ""

# Show status
echo "📊 Service Status:"
docker-compose ps

echo ""
echo -e "${GREEN}🎉 LinkedIn AI Agent is running!${NC}"
echo ""
echo "📚 Access points:"
echo "   - API:        http://localhost:8000"
echo "   - API Docs:   http://localhost:8000/docs"
echo "   - Health:     http://localhost:8000/health"
echo ""
echo "📝 Useful commands:"
echo "   - View logs:   docker-compose logs -f app"
echo "   - Stop:        docker-compose down"
echo "   - Restart:     docker-compose restart"
echo ""
