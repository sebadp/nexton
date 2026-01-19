# Email Notifications & Automated Responses

**Feature**: Sprint 3 - Phase 1 & 2
**Version**: 1.3.0
**Last Updated**: January 18, 2026

---

## Overview

Sistema completo de notificaciones por email y respuestas automáticas para oportunidades de LinkedIn:

- **Email Notifications** - Notificaciones HTML por email cuando llegan oportunidades relevantes
- **AI Response Suggestions** - Respuestas generadas automáticamente por IA incluidas en el email
- **User Approval Workflow** - Revisar, editar o rechazar respuestas antes de enviar
- **Automated LinkedIn Sending** - Envío automático de respuestas aprobadas a LinkedIn

---

## Features

### ✅ Implementado

#### 1. Email Notifications
- ✅ Cliente SMTP con soporte para múltiples proveedores
- ✅ Templates HTML hermosos y responsive
- ✅ Reglas de notificación configurables (tier, score)
- ✅ Integración automática al crear oportunidades
- ✅ Información completa de la oportunidad en el email

#### 2. Automated Responses
- ✅ Generación automática de respuestas con DSPy
- ✅ Modelo de base de datos para pending responses
- ✅ API REST para approve/edit/decline
- ✅ Workflow completo de aprobación
- ✅ Envío automático a LinkedIn con Celery tasks
- ✅ Retry logic y error handling

---

## Architecture

```
┌─────────────────────┐
│  LinkedIn Message   │
│    (New Inquiry)    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   DSPy Pipeline     │
│  - Extract info     │
│  - Score opportunity│
│  - Generate response│
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Create Opportunity │
│  + PendingResponse  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Send Email Notif   │
│  with AI response   │
│  + Action buttons   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   User Reviews      │
│  (Email buttons)    │
└─┬─────────┬─────┬───┘
  │         │     │
  │Approve  │Edit │Decline
  │         │     │
  ▼         ▼     ▼
┌─────────────────────┐
│   API Endpoint      │
│  Update status      │
└──────────┬──────────┘
           │
           ▼ (if approved)
┌─────────────────────┐
│   Celery Task       │
│  Queue message send │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  LinkedIn Messenger │
│  Send via Playwright│
└─────────────────────┘
```

---

## Quick Start

### 1. Configure Email Settings

Edit `.env`:

```bash
# SMTP Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USE_TLS=true
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
SMTP_FROM_EMAIL=noreply@yourcompany.com

# Notification Settings
NOTIFICATION_EMAIL=you@example.com
NOTIFICATION_ENABLED=true
NOTIFICATION_TIER_THRESHOLD=["A", "B"]
NOTIFICATION_SCORE_THRESHOLD=60
NOTIFICATION_INCLUDE_RESPONSE=true
```

### 2. Start Services

```bash
# Start all services (API, Worker, Redis, etc.)
docker-compose up -d

# Or start individually
docker-compose up -d redis postgres
python -m uvicorn app.main:app --reload
celery -A app.tasks.celery_app worker --loglevel=info
```

### 3. Test Notification System

```bash
# Create a test opportunity (will trigger notification)
curl -X POST http://localhost:8000/api/v1/opportunities \
  -H "Content-Type: application/json" \
  -d '{
    "recruiter_name": "Jane Smith",
    "raw_message": "Hi! We have a Senior Python position at TechCorp..."
  }'

# Check your email for the notification
```

---

## Email Configuration

### Development Setup (Mailpit)

For development, use Mailpit - captures emails without sending them:

```bash
# Start Mailpit
docker run -d -p 1025:1025 -p 8025:8025 axllent/mailpit

# Configure .env
SMTP_HOST=localhost
SMTP_PORT=1025
SMTP_USE_TLS=false

# View emails at http://localhost:8025
```

### Production Setup (Gmail)

```bash
# 1. Enable 2FA on your Google account
# 2. Generate an App Password
# 3. Configure .env

SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USE_TLS=true
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_16_char_app_password
```

### Production Setup (SendGrid)

```bash
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USE_TLS=true
SMTP_USERNAME=apikey
SMTP_PASSWORD=your_sendgrid_api_key
```

---

## Notification Rules

Configure which opportunities trigger notifications:

### Tier Threshold

```python
# Only notify for A and B tier opportunities
NOTIFICATION_TIER_THRESHOLD=["A", "B"]

# Notify for all tiers
NOTIFICATION_TIER_THRESHOLD=["A", "B", "C", "D"]

# Only top tier
NOTIFICATION_TIER_THRESHOLD=["A"]
```

### Score Threshold

```python
# Only notify if score >= 70
NOTIFICATION_SCORE_THRESHOLD=70

# Notify for all scores
NOTIFICATION_SCORE_THRESHOLD=0
```

### Combined Rules

Opportunities must meet BOTH conditions to trigger notification:

```python
# Example: Only A/B tier with score >= 60
NOTIFICATION_TIER_THRESHOLD=["A", "B"]
NOTIFICATION_SCORE_THRESHOLD=60
```

---

## Email Template

The notification email includes:

### Header
- 🎯 "New LinkedIn Opportunity" title
- Gradient background

### Opportunity Details
- **Tier Badge** - Color-coded (A=Green, B=Blue, C=Orange, D=Red)
- **Score Badge** - Color-coded by value
- Recruiter name
- Company
- Position
- Salary range
- Tech stack (as pills/badges)

### AI-Generated Response
- Suggested response text
- Formatted in blue box with chat icon

### Action Buttons
- ✓ **Approve & Send** (Green) - Send as-is to LinkedIn
- ✏️ **Edit Response** (Blue) - Modify before sending
- ✗ **Decline** (Gray) - Don't send any response

### Footer
- Opportunity ID for reference

---

## API Endpoints

### Response Management

#### Get Pending Response

```bash
GET /api/v1/responses/{opportunity_id}
```

Response:
```json
{
  "id": 1,
  "opportunity_id": 123,
  "original_response": "Thank you for reaching out...",
  "edited_response": null,
  "final_response": null,
  "status": "pending",
  "created_at": "2026-01-18T10:00:00Z"
}
```

#### Approve Response

```bash
POST /api/v1/responses/{opportunity_id}/approve
Content-Type: application/json

{
  "edited_response": null  # Optional - edit before approving
}
```

Response:
```json
{
  "id": 1,
  "status": "approved",
  "approved_at": "2026-01-18T10:05:00Z",
  "final_response": "Thank you for reaching out..."
}
```

#### Edit & Approve Response

```bash
POST /api/v1/responses/{opportunity_id}/edit
Content-Type: application/json

{
  "edited_response": "Thank you for your message. I'm very interested..."
}
```

#### Decline Response

```bash
POST /api/v1/responses/{opportunity_id}/decline
```

Response:
```json
{
  "id": 1,
  "status": "declined",
  "declined_at": "2026-01-18T10:05:00Z"
}
```

#### List Pending Responses

```bash
GET /api/v1/responses?skip=0&limit=10
```

---

## Workflow Examples

### Scenario 1: Approve Without Changes

1. **Opportunity arrives** → Email sent with AI response
2. **User clicks "Approve & Send"** → POST `/api/v1/responses/123/approve`
3. **API updates status** to `approved`
4. **Celery task queued** to send to LinkedIn
5. **LinkedIn Messenger sends** message via Playwright
6. **Status updated** to `sent`

### Scenario 2: Edit Before Sending

1. **Opportunity arrives** → Email sent with AI response
2. **User clicks "Edit Response"** → Opens web form
3. **User modifies text** → POST `/api/v1/responses/123/edit` with `edited_response`
4. **API updates** with edited version
5. **Celery task queued** with edited response
6. **Message sent** to LinkedIn

### Scenario 3: Decline

1. **Opportunity arrives** → Email sent
2. **User clicks "Decline"** → POST `/api/v1/responses/123/decline`
3. **Status updated** to `declined`
4. **No message sent** to LinkedIn

---

## Database Schema

### PendingResponse Model

```python
class PendingResponse:
    id: int                              # Primary key
    opportunity_id: int                  # FK to Opportunity
    original_response: str               # AI-generated response
    edited_response: Optional[str]       # User-edited version
    final_response: Optional[str]        # What will be sent
    status: str                          # pending, approved, declined, sent, failed

    # Timestamps
    approved_at: Optional[datetime]
    declined_at: Optional[datetime]
    sent_at: Optional[datetime]

    # Error tracking
    error_message: Optional[str]
    send_attempts: int

    created_at: datetime
    updated_at: datetime
```

### Status Flow

```
pending → approved → sent
         ↓
         declined
         ↓
         failed (with retries)
```

---

## LinkedIn Message Sending

### How It Works

1. **Celery Task Triggered** when response approved
2. **LinkedInMessenger initialized** with Playwright
3. **Browser launched** (headless)
4. **Login to LinkedIn** with credentials
5. **Navigate to conversation**
6. **Fill message box** with response text
7. **Click send button**
8. **Status updated** to `sent` or `failed`

### Configuration

```bash
# LinkedIn credentials (required)
LINKEDIN_EMAIL=your_linkedin_email@example.com
LINKEDIN_PASSWORD=your_linkedin_password

# Scraper settings
SCRAPER_HEADLESS=true
SCRAPER_TIMEOUT=30000
```

### Retry Logic

- **Max retries**: 3
- **Retry delay**: 5 minutes (300 seconds)
- **Exponential backoff**: Yes
- **Error tracking**: Stored in `error_message` field

---

## Testing

### Manual Testing

1. **Test Email Sending**:
```bash
# Use Mailpit to capture emails
docker run -d -p 1025:1025 -p 8025:8025 axllent/mailpit

# Create opportunity
curl -X POST http://localhost:8000/api/v1/opportunities \
  -H "Content-Type: application/json" \
  -d @tests/fixtures/sample_message.json

# Check http://localhost:8025 for email
```

2. **Test Response Approval**:
```bash
# Get opportunity ID from previous step
OPPORTUNITY_ID=1

# Approve response
curl -X POST http://localhost:8000/api/v1/responses/$OPPORTUNITY_ID/approve

# Check Celery logs
celery -A app.tasks.celery_app worker --loglevel=info
```

3. **Test LinkedIn Sending**:
```bash
# Make sure LinkedIn credentials are configured
# Approve a response and watch Celery logs
# Message should be sent to LinkedIn
```

### Unit Tests

```bash
# Run notification tests
pytest tests/unit/test_notifications.py -v

# Run response tests
pytest tests/unit/test_responses.py -v

# Run integration tests
pytest tests/integration/test_notification_workflow.py -v
```

---

## Monitoring

### Logs

```bash
# API logs (notifications sent)
docker-compose logs -f api | grep notification

# Celery logs (messages sent)
docker-compose logs -f worker | grep linkedin_response

# Email logs
docker-compose logs -f api | grep email
```

### Metrics

Available Prometheus metrics:

```promql
# Notifications sent
notification_emails_sent_total{tier, status}

# Responses approved
pending_responses_approved_total

# Messages sent to LinkedIn
linkedin_messages_sent_total{status}

# Failed sends
linkedin_message_failures_total{error_type}
```

### Database Queries

```sql
-- Pending responses waiting for approval
SELECT * FROM pending_responses WHERE status = 'pending';

-- Approved but not sent
SELECT * FROM pending_responses WHERE status = 'approved';

-- Failed sends
SELECT * FROM pending_responses WHERE status = 'failed';

-- Success rate
SELECT
    status,
    COUNT(*) as count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage
FROM pending_responses
GROUP BY status;
```

---

## Troubleshooting

### Email Not Sending

**Issue**: Notification emails not received

**Solutions**:
1. Check SMTP configuration:
```bash
# Test SMTP connection
python -c "
import smtplib
smtp = smtplib.SMTP('$SMTP_HOST', $SMTP_PORT)
smtp.starttls()
smtp.login('$SMTP_USERNAME', '$SMTP_PASSWORD')
print('SMTP connection successful')
"
```

2. Check if notifications are enabled:
```bash
grep NOTIFICATION_ENABLED .env
```

3. Check opportunity meets criteria:
```bash
# Opportunity must match tier_threshold AND score_threshold
```

4. Check logs:
```bash
docker-compose logs api | grep notification_failed
```

### LinkedIn Sending Fails

**Issue**: Messages not sending to LinkedIn

**Solutions**:
1. Check LinkedIn credentials:
```bash
# Make sure credentials are correct
grep LINKEDIN .env
```

2. Check if LinkedIn requires verification:
```bash
# LinkedIn may require manual verification
# Check Celery logs for "checkpoint" or "challenge"
```

3. Check Playwright installation:
```bash
playwright install chromium
```

4. Run in non-headless mode for debugging:
```bash
SCRAPER_HEADLESS=false celery -A app.tasks.celery_app worker
```

### Response Not Creating

**Issue**: PendingResponse not created for opportunity

**Solutions**:
1. Check if AI response was generated:
```sql
SELECT id, ai_response FROM opportunities WHERE id = ?;
```

2. Check logs:
```bash
docker-compose logs api | grep pending_response_creation_failed
```

---

## Best Practices

### 1. Email Frequency

```python
# Don't spam - use tier/score thresholds
NOTIFICATION_TIER_THRESHOLD=["A", "B"]  # Only top opportunities
NOTIFICATION_SCORE_THRESHOLD=70         # High-quality only
```

### 2. Response Quality

```python
# Always review AI responses before sending
# Use LLM_MODEL with high quality for response generation
RESPONSE_LLM_PROVIDER=openai
RESPONSE_LLM_MODEL=gpt-4
```

### 3. LinkedIn Rate Limiting

```python
# Don't send too many messages too quickly
# Celery will handle rate limiting automatically
# Max ~10-20 messages per hour to avoid LinkedIn limits
```

### 4. Error Handling

```python
# Monitor failed sends
# Review error messages
# Retry manually if needed
```

---

## Future Enhancements

Potential improvements for future sprints:

- [ ] Web UI for response management (replace email buttons)
- [ ] Bulk approve/decline multiple responses
- [ ] Response templates and customization
- [ ] A/B testing for response effectiveness
- [ ] Track LinkedIn message read status
- [ ] Response analytics and success metrics
- [ ] Slack notifications as alternative to email
- [ ] Mobile app for approval workflow

---

## Support

- **Documentation**: `docs/`
- **API Docs**: http://localhost:8000/docs
- **Configuration**: `.env.example`
- **Issues**: GitHub Issues

---

*Last Updated: January 18, 2026*
*Feature: Sprint 3 - Email Notifications & Automated Responses*
*Version: 1.3.0*
