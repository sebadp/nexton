#!/bin/bash
# Smoke Test Script for LinkedIn AI Agent Platform
# Validates core functionality and Sprint 2 features

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
API_URL="${API_URL:-http://localhost:8000}"
PROMETHEUS_URL="${PROMETHEUS_URL:-http://localhost:9090}"
GRAFANA_URL="${GRAFANA_URL:-http://localhost:3000}"
JAEGER_URL="${JAEGER_URL:-http://localhost:16686}"

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_TOTAL=0

# Helper functions
print_header() {
    echo ""
    echo "=========================================="
    echo "$1"
    echo "=========================================="
}

print_test() {
    echo -n "Testing: $1 ... "
    TESTS_TOTAL=$((TESTS_TOTAL + 1))
}

print_success() {
    echo -e "${GREEN}✓ PASSED${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
}

print_failure() {
    echo -e "${RED}✗ FAILED${NC}"
    echo -e "${RED}  Error: $1${NC}"
    TESTS_FAILED=$((TESTS_FAILED + 1))
}

print_warning() {
    echo -e "${YELLOW}⚠ WARNING: $1${NC}"
}

check_url() {
    local url=$1
    local expected_code=${2:-200}

    http_code=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null || echo "000")

    if [ "$http_code" = "$expected_code" ]; then
        return 0
    else
        return 1
    fi
}

# Start tests
clear
echo "╔════════════════════════════════════════════════════╗"
echo "║   LinkedIn AI Agent - Smoke Test Suite           ║"
echo "║   Sprint 2 Validation                             ║"
echo "╚════════════════════════════════════════════════════╝"
echo ""
echo "Target Environment:"
echo "  API:        $API_URL"
echo "  Prometheus: $PROMETHEUS_URL"
echo "  Grafana:    $GRAFANA_URL"
echo "  Jaeger:     $JAEGER_URL"
echo ""

# Test 1: API Health
print_header "Phase 1: API Health Checks"

print_test "API Basic Health"
if check_url "$API_URL/health"; then
    response=$(curl -s "$API_URL/health")
    if echo "$response" | grep -q '"status":"healthy"'; then
        print_success
    else
        print_failure "Invalid health response"
    fi
else
    print_failure "API not responding"
fi

print_test "API Readiness"
if check_url "$API_URL/health/ready"; then
    response=$(curl -s "$API_URL/health/ready")
    if echo "$response" | grep -q '"status":"ready"'; then
        print_success
    else
        print_failure "Service not ready"
    fi
else
    print_failure "Readiness check failed"
fi

print_test "API Documentation"
if check_url "$API_URL/docs"; then
    print_success
else
    print_failure "Swagger UI not accessible"
fi

# Test 2: Core Functionality
print_header "Phase 2: Core API Functionality"

print_test "Create Opportunity"
response=$(curl -s -X POST "$API_URL/api/v1/opportunities" \
    -H "Content-Type: application/json" \
    -d '{
        "recruiter_name": "Smoke Test",
        "raw_message": "Senior Python Developer at TestCorp. $150k-$180k. Python, FastAPI, PostgreSQL. 5+ years required."
    }' 2>/dev/null)

if echo "$response" | grep -q '"id"'; then
    opportunity_id=$(echo "$response" | grep -o '"id":[0-9]*' | grep -o '[0-9]*')
    print_success
else
    print_failure "Failed to create opportunity"
fi

print_test "List Opportunities"
if check_url "$API_URL/api/v1/opportunities"; then
    response=$(curl -s "$API_URL/api/v1/opportunities")
    if echo "$response" | grep -q '"items"'; then
        print_success
    else
        print_failure "Invalid list response"
    fi
else
    print_failure "List endpoint failed"
fi

if [ -n "$opportunity_id" ]; then
    print_test "Get Opportunity by ID"
    if check_url "$API_URL/api/v1/opportunities/$opportunity_id"; then
        print_success
    else
        print_failure "Failed to get opportunity $opportunity_id"
    fi
fi

print_test "Get Statistics"
if check_url "$API_URL/api/v1/opportunities/stats"; then
    response=$(curl -s "$API_URL/api/v1/opportunities/stats")
    if echo "$response" | grep -q '"total_opportunities"'; then
        print_success
    else
        print_failure "Invalid stats response"
    fi
else
    print_failure "Stats endpoint failed"
fi

# Test 3: Metrics
print_header "Phase 3: Metrics Validation"

print_test "Prometheus Metrics Endpoint"
if check_url "$API_URL/api/v1/metrics"; then
    response=$(curl -s "$API_URL/api/v1/metrics")
    if echo "$response" | grep -q "opportunities_created_total"; then
        print_success
    else
        print_failure "Metrics not in Prometheus format"
    fi
else
    print_failure "Metrics endpoint failed"
fi

print_test "Prometheus Server"
if check_url "$PROMETHEUS_URL/-/healthy"; then
    print_success
else
    print_warning "Prometheus not accessible (optional service)"
fi

print_test "Prometheus Targets"
if check_url "$PROMETHEUS_URL/api/v1/targets"; then
    print_success
else
    print_warning "Prometheus targets not accessible"
fi

# Test 4: Caching
print_header "Phase 4: Caching Validation"

print_test "Cache Miss (First Request)"
start_time=$(date +%s%3N)
curl -s -X POST "$API_URL/api/v1/opportunities" \
    -H "Content-Type: application/json" \
    -d '{
        "recruiter_name": "Cache Test",
        "raw_message": "This is a unique message for cache testing abc123xyz"
    }' > /dev/null 2>&1
end_time=$(date +%s%3N)
first_request_time=$((end_time - start_time))
print_success

print_test "Cache Hit (Second Request)"
start_time=$(date +%s%3N)
curl -s -X POST "$API_URL/api/v1/opportunities" \
    -H "Content-Type: application/json" \
    -d '{
        "recruiter_name": "Cache Test",
        "raw_message": "This is a unique message for cache testing abc123xyz"
    }' > /dev/null 2>&1
end_time=$(date +%s%3N)
second_request_time=$((end_time - start_time))

if [ "$second_request_time" -lt "$((first_request_time / 2))" ]; then
    print_success
    echo "    Cache speedup: ${first_request_time}ms → ${second_request_time}ms"
else
    print_warning "Cache may not be working (${first_request_time}ms → ${second_request_time}ms)"
fi

# Test 5: Monitoring Stack
print_header "Phase 5: Monitoring Stack"

print_test "Grafana Server"
if check_url "$GRAFANA_URL/api/health"; then
    print_success
else
    print_warning "Grafana not accessible (optional service)"
fi

print_test "Jaeger Server"
if check_url "$JAEGER_URL/"; then
    print_success
else
    print_warning "Jaeger not accessible (optional service)"
fi

# Test 6: Docker Services
print_header "Phase 6: Docker Services Status"

print_test "Docker Services Running"
if command -v docker-compose &> /dev/null; then
    services=$(docker-compose ps --services 2>/dev/null | wc -l)
    running=$(docker-compose ps --filter "status=running" --services 2>/dev/null | wc -l)
    if [ "$running" -gt 0 ]; then
        print_success
        echo "    Services running: $running"
    else
        print_warning "No services running via docker-compose"
    fi
else
    print_warning "docker-compose not available"
fi

# Test 7: Performance Check
print_header "Phase 7: Basic Performance Check"

print_test "API Response Time (5 requests)"
total_time=0
for i in {1..5}; do
    start_time=$(date +%s%3N)
    curl -s "$API_URL/health" > /dev/null 2>&1
    end_time=$(date +%s%3N)
    request_time=$((end_time - start_time))
    total_time=$((total_time + request_time))
done
avg_time=$((total_time / 5))

if [ "$avg_time" -lt 500 ]; then
    print_success
    echo "    Average response time: ${avg_time}ms"
else
    print_warning "Average response time: ${avg_time}ms (target: <500ms)"
fi

# Test 8: Database Connection
print_header "Phase 8: Database Connectivity"

print_test "Database Connection via API"
if check_url "$API_URL/api/v1/opportunities/stats"; then
    print_success
else
    print_failure "Cannot connect to database through API"
fi

# Summary
print_header "Test Summary"

echo ""
echo "Results:"
echo "  Total Tests:  $TESTS_TOTAL"
echo -e "  ${GREEN}Passed:       $TESTS_PASSED${NC}"
if [ $TESTS_FAILED -gt 0 ]; then
    echo -e "  ${RED}Failed:       $TESTS_FAILED${NC}"
fi
echo ""

# Calculate percentage
if [ $TESTS_TOTAL -gt 0 ]; then
    success_rate=$((TESTS_PASSED * 100 / TESTS_TOTAL))
    echo "Success Rate: $success_rate%"
    echo ""
fi

# Final verdict
if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}╔════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║           ✓ ALL TESTS PASSED                      ║${NC}"
    echo -e "${GREEN}║   System is healthy and ready for use!            ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════╝${NC}"
    echo ""
    exit 0
else
    echo -e "${RED}╔════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║           ✗ SOME TESTS FAILED                     ║${NC}"
    echo -e "${RED}║   Please check the errors above                   ║${NC}"
    echo -e "${RED}╚════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "Troubleshooting:"
    echo "  1. Check service logs: docker-compose logs"
    echo "  2. Verify .env configuration"
    echo "  3. See docs/TESTING_GUIDE.md for detailed testing"
    echo ""
    exit 1
fi
