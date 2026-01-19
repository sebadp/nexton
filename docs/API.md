# API Documentation - LinkedIn AI Agent

Complete REST API reference for the LinkedIn AI Agent platform.

## Base URL

```
http://localhost:8000
```

## Authentication

**Sprint 1**: No authentication required (development mode)
**Sprint 2+**: JWT-based authentication

## Response Format

All responses follow this structure:

```json
{
  "status": "success|error",
  "data": { ... },
  "message": "Optional message",
  "timestamp": "2024-01-16T10:00:00Z"
}
```

## Error Handling

### HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 204 | No Content |
| 400 | Bad Request |
| 404 | Not Found |
| 422 | Validation Error |
| 500 | Internal Server Error |
| 503 | Service Unavailable |

### Error Response

```json
{
  "error": "ValidationError",
  "message": "Request validation failed",
  "details": {
    "field": "recruiter_name",
    "error": "Field required"
  }
}
```

---

## Endpoints

### Health Checks

#### GET /health

Basic health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-16T10:00:00Z"
}
```

**Status Codes:**
- `200` - Service is healthy
- `503` - Service is unhealthy

---

#### GET /health/ready

Readiness check - verifies all dependencies.

**Response:**
```json
{
  "status": "ready",
  "timestamp": "2024-01-16T10:00:00Z",
  "checks": {
    "database": true,
    "redis": true,
    "ollama": true
  }
}
```

**Status Codes:**
- `200` - All dependencies ready
- `503` - One or more dependencies unavailable

---

#### GET /health/live

Liveness check for Kubernetes.

**Response:**
```json
{
  "status": "alive",
  "timestamp": "2024-01-16T10:00:00Z"
}
```

---

#### GET /health/startup

Startup check for Kubernetes.

**Response:**
```json
{
  "status": "started",
  "timestamp": "2024-01-16T10:00:00Z"
}
```

---

### Opportunities

#### POST /api/v1/opportunities

Create and process a new opportunity.

Runs the complete DSPy pipeline:
1. Extracts structured data from message
2. Scores the opportunity (0-100)
3. Generates personalized AI response
4. Stores in database

**Request Body:**
```json
{
  "recruiter_name": "María González",
  "raw_message": "Hola! Tenemos una posición de Senior Python Engineer en TechCorp. Remoto, 100-120K USD. Stack: Python, FastAPI, PostgreSQL, Docker. ¿Te interesa?"
}
```

**Response:** `201 Created`
```json
{
  "id": 1,
  "recruiter_name": "María González",
  "raw_message": "Hola! Tenemos una posición...",
  "company": "TechCorp",
  "role": "Senior Python Engineer",
  "seniority": "Senior",
  "tech_stack": ["Python", "FastAPI", "PostgreSQL", "Docker"],
  "salary_min": 100000,
  "salary_max": 120000,
  "currency": "USD",
  "remote_policy": "Remote",
  "tech_stack_score": 35,
  "salary_score": 25,
  "seniority_score": 18,
  "company_score": 8,
  "total_score": 86,
  "tier": "HIGH_PRIORITY",
  "ai_response": "Hola María, muchas gracias por contactarme...",
  "status": "processed",
  "processing_time_ms": 1500,
  "created_at": "2024-01-16T10:00:00Z",
  "updated_at": "2024-01-16T10:00:00Z"
}
```

**Validation Rules:**
- `recruiter_name`: Required, 1-255 characters
- `raw_message`: Required, minimum 10 characters

**Processing Time:** ~2-4 seconds (includes LLM calls)

---

#### GET /api/v1/opportunities

List opportunities with pagination and filtering.

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `skip` | integer | 0 | Number of items to skip (offset) |
| `limit` | integer | 10 | Number of items to return (max 100) |
| `tier` | string | - | Filter by tier (HIGH_PRIORITY, INTERESANTE, POCO_INTERESANTE, NO_INTERESA) |
| `status` | string | - | Filter by status (processed, processing, failed) |
| `min_score` | integer | - | Filter by minimum score (0-100) |
| `company` | string | - | Filter by company name (partial match) |
| `sort_by` | string | created_at | Sort field (created_at, total_score, company) |
| `sort_order` | string | desc | Sort order (asc, desc) |

**Example Request:**
```bash
GET /api/v1/opportunities?tier=HIGH_PRIORITY&limit=10&sort_by=total_score&sort_order=desc
```

**Response:** `200 OK`
```json
{
  "items": [
    {
      "id": 1,
      "recruiter_name": "María González",
      "company": "TechCorp",
      "role": "Senior Python Engineer",
      "total_score": 86,
      "tier": "HIGH_PRIORITY",
      "status": "processed",
      "created_at": "2024-01-16T10:00:00Z",
      "updated_at": "2024-01-16T10:00:00Z"
    }
  ],
  "total": 100,
  "skip": 0,
  "limit": 10,
  "has_more": true
}
```

---

#### GET /api/v1/opportunities/{id}

Get a single opportunity by ID.

**Path Parameters:**
- `id` (integer, required): Opportunity ID

**Response:** `200 OK`
```json
{
  "id": 1,
  "recruiter_name": "María González",
  "raw_message": "Hola! Tenemos...",
  "company": "TechCorp",
  "role": "Senior Python Engineer",
  "total_score": 86,
  "tier": "HIGH_PRIORITY",
  "ai_response": "Hola María...",
  "status": "processed",
  "created_at": "2024-01-16T10:00:00Z",
  "updated_at": "2024-01-16T10:00:00Z"
}
```

**Error Responses:**
- `404` - Opportunity not found

---

#### PATCH /api/v1/opportunities/{id}

Update opportunity metadata (status, notes).

**Path Parameters:**
- `id` (integer, required): Opportunity ID

**Request Body:**
```json
{
  "status": "contacted",
  "notes": "Scheduled interview for next Tuesday"
}
```

**Response:** `200 OK`
```json
{
  "id": 1,
  "status": "contacted",
  "notes": "Scheduled interview for next Tuesday",
  "updated_at": "2024-01-16T11:00:00Z"
}
```

**Note:** AI analysis results (scores, extracted data) are immutable.

---

#### DELETE /api/v1/opportunities/{id}

Delete an opportunity.

**Path Parameters:**
- `id` (integer, required): Opportunity ID

**Response:** `204 No Content`

**Error Responses:**
- `404` - Opportunity not found

---

#### GET /api/v1/opportunities/stats

Get opportunity statistics.

**Response:** `200 OK`
```json
{
  "total_count": 100,
  "by_tier": {
    "HIGH_PRIORITY": 15,
    "INTERESANTE": 35,
    "POCO_INTERESANTE": 30,
    "NO_INTERESA": 20
  },
  "by_status": {
    "processed": 95,
    "processing": 3,
    "failed": 2
  },
  "average_score": 52.5,
  "highest_score": 95,
  "lowest_score": 10
}
```

---

## Tier Classification

Opportunities are automatically classified into tiers based on total score:

| Tier | Score Range | Description |
|------|-------------|-------------|
| HIGH_PRIORITY | 75-100 | Excellent match - immediate action recommended |
| INTERESANTE | 50-74 | Good match - worth exploring |
| POCO_INTERESANTE | 30-49 | Moderate match - low priority |
| NO_INTERESA | 0-29 | Poor match - can be declined |

## Scoring Breakdown

Total score (0-100 points) is calculated from:

| Dimension | Max Points | Weight |
|-----------|------------|--------|
| Tech Stack Match | 40 | 40% |
| Salary Range | 30 | 30% |
| Seniority Level | 20 | 20% |
| Company Preference | 10 | 10% |

**Example:**
- Tech Stack: 35/40 (87.5% match)
- Salary: 25/30 (competitive)
- Seniority: 18/20 (good fit)
- Company: 8/10 (known company)
- **Total: 86/100** → HIGH_PRIORITY

---

## Rate Limiting

**Sprint 1**: No rate limiting
**Sprint 2**: 100 requests/minute per IP

---

## Pagination

All list endpoints support pagination:

```bash
# First page (10 items)
GET /api/v1/opportunities?skip=0&limit=10

# Second page
GET /api/v1/opportunities?skip=10&limit=10

# Large page (max 100)
GET /api/v1/opportunities?skip=0&limit=100
```

**Response includes:**
- `items`: Array of results
- `total`: Total count matching filters
- `skip`: Current offset
- `limit`: Page size
- `has_more`: Boolean indicating more results available

---

## Filtering Examples

### By Tier
```bash
GET /api/v1/opportunities?tier=HIGH_PRIORITY
```

### By Score Range
```bash
GET /api/v1/opportunities?min_score=80
```

### By Company
```bash
GET /api/v1/opportunities?company=TechCorp
```

### Combined Filters
```bash
GET /api/v1/opportunities?tier=HIGH_PRIORITY&min_score=80&company=Tech&limit=20
```

---

## Sorting Examples

### By Score (highest first)
```bash
GET /api/v1/opportunities?sort_by=total_score&sort_order=desc
```

### By Date (newest first)
```bash
GET /api/v1/opportunities?sort_by=created_at&sort_order=desc
```

### By Company (alphabetical)
```bash
GET /api/v1/opportunities?sort_by=company&sort_order=asc
```

---

## OpenAPI / Swagger

Interactive API documentation available at:

```
http://localhost:8000/docs
```

Features:
- Try out endpoints directly
- See request/response schemas
- View validation rules
- Export OpenAPI spec

Alternative (ReDoc):
```
http://localhost:8000/redoc
```

---

## Code Examples

### Python (httpx)

```python
import httpx

# Create opportunity
async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://localhost:8000/api/v1/opportunities",
        json={
            "recruiter_name": "María González",
            "raw_message": "Hola! Tenemos una posición..."
        }
    )
    opportunity = response.json()
    print(f"Created opportunity {opportunity['id']} with score {opportunity['total_score']}")
```

### cURL

```bash
# Create opportunity
curl -X POST http://localhost:8000/api/v1/opportunities \
  -H "Content-Type: application/json" \
  -d '{
    "recruiter_name": "María González",
    "raw_message": "Hola! Tenemos una posición..."
  }'

# List high priority opportunities
curl "http://localhost:8000/api/v1/opportunities?tier=HIGH_PRIORITY&limit=10"

# Get specific opportunity
curl http://localhost:8000/api/v1/opportunities/1

# Update opportunity
curl -X PATCH http://localhost:8000/api/v1/opportunities/1 \
  -H "Content-Type: application/json" \
  -d '{"status": "contacted"}'

# Delete opportunity
curl -X DELETE http://localhost:8000/api/v1/opportunities/1

# Get statistics
curl http://localhost:8000/api/v1/opportunities/stats
```

### JavaScript (fetch)

```javascript
// Create opportunity
const response = await fetch('http://localhost:8000/api/v1/opportunities', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    recruiter_name: 'María González',
    raw_message: 'Hola! Tenemos una posición...'
  })
});

const opportunity = await response.json();
console.log(`Score: ${opportunity.total_score}, Tier: ${opportunity.tier}`);
```

---

## Webhook Support (Sprint 2)

Future feature for real-time notifications:

```json
POST /api/v1/webhooks
{
  "url": "https://your-app.com/webhook",
  "events": ["opportunity.created", "opportunity.high_priority"]
}
```

---

## API Versioning

Current version: `v1`

Future versions will be available at:
- `/api/v2/...`

Old versions supported for 6 months after deprecation.

---

## Support

- **Issues**: Report bugs at GitHub Issues
- **Questions**: Use GitHub Discussions
- **Email**: support@example.com
