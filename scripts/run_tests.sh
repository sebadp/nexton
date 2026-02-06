#!/bin/bash
# ============================================================================
# LinkedIn AI Agent - Test Runner Script
# ============================================================================

set -e  # Exit on error

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "🧪 Running LinkedIn AI Agent Tests..."
echo ""

# Parse arguments
TEST_TYPE="${1:-all}"
COVERAGE="${2:-yes}"

case $TEST_TYPE in
  unit)
    echo "Running unit tests only..."
    if [ "$COVERAGE" = "yes" ]; then
      pytest tests/unit -v --cov=app --cov-report=term-missing --cov-report=html
    else
      pytest tests/unit -v
    fi
    ;;
  integration)
    echo "Running integration tests only..."
    if [ "$COVERAGE" = "yes" ]; then
      pytest tests/integration -v --cov=app --cov-report=term-missing --cov-report=html
    else
      pytest tests/integration -v
    fi
    ;;
  all)
    echo "Running all tests..."
    if [ "$COVERAGE" = "yes" ]; then
      pytest tests/ -v --cov=app --cov-report=term-missing --cov-report=html
    else
      pytest tests/ -v
    fi
    ;;
  *)
    echo -e "${RED}❌ Invalid test type: $TEST_TYPE${NC}"
    echo "Usage: $0 [unit|integration|all] [yes|no]"
    exit 1
    ;;
esac

# Check exit code
if [ $? -eq 0 ]; then
  echo ""
  echo -e "${GREEN}✅ All tests passed!${NC}"

  if [ "$COVERAGE" = "yes" ]; then
    echo ""
    echo "📊 Coverage report generated at htmlcov/index.html"
    echo "   Open with: open htmlcov/index.html"
  fi
else
  echo ""
  echo -e "${RED}❌ Tests failed!${NC}"
  exit 1
fi
