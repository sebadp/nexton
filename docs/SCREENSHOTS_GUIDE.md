# Screenshots Guide for Documentation

Quick guide to capture professional screenshots for the project documentation.

## Prerequisites

1. **System running**:
   ```bash
   ./scripts/start.sh
   # Wait for all services to be healthy
   ```

2. **Generate test data**:
   ```bash
   # Run test script to create sample opportunities
   python test_message_generation.py
   ```

3. **Screenshot tool ready**:
   - macOS: Built-in (Cmd+Shift+4)
   - Windows: Snipping Tool
   - Linux: gnome-screenshot

## Screenshots Checklist

### 1. API Documentation (Swagger UI)
- **URL**: http://localhost:8000/docs
- **File**: `docs/images/api-docs.png`
- **What to capture**:
  - Full page showing all endpoints
  - Expand one endpoint (e.g., POST /opportunities) to show details
  - Make sure to show request/response schemas
- **Resolution**: 1920x1080+
- **Tips**:
  - Zoom browser to 90% for better overview
  - Use light theme for better visibility

### 2. Grafana Dashboard
- **URL**: http://localhost:3000
- **Login**: admin/admin
- **File**: `docs/images/grafana-dashboard.png`
- **What to capture**:
  - Main "LinkedIn Agent Overview" dashboard
  - Show panels with actual data:
    - Opportunities by Tier (pie chart)
    - Pipeline Execution Time (graph)
    - Cache Hit Rate (gauge)
    - Total Opportunities (stat)
- **Tips**:
  - Run system for 10-15 minutes to get interesting data
  - Set time range to "Last 1 hour"
  - Dark theme looks more professional

### 3. Jaeger Tracing
- **URL**: http://localhost:16686
- **File**: `docs/images/jaeger-traces.png`
- **What to capture**:
  - Search results showing multiple traces
  - Click on one trace to show detailed view
  - Show span timeline with multiple services
- **Steps**:
  1. Select "linkedin-ai-agent" service
  2. Click "Find Traces"
  3. Click on a trace with multiple spans
  4. Capture the timeline view

### 4. Flower (Celery Monitor)
- **URL**: http://localhost:5555
- **Login**: admin/admin
- **File**: `docs/images/flower-tasks.png`
- **What to capture**:
  - Tasks page showing active/successful tasks
  - At least 3-4 completed tasks visible
  - Show task details (name, args, runtime)
- **Tips**:
  - Trigger some tasks first: `python -c "from app.tasks.scraping_tasks import scrape_linkedin_messages; scrape_linkedin_messages.delay()"`

### 5. Prometheus Metrics
- **URL**: http://localhost:9090
- **File**: `docs/images/prometheus-metrics.png`
- **What to capture**:
  - Graph view with a custom query
  - Example query: `rate(opportunities_created_total[5m])`
  - Show legend with different series (by tier)
- **Tips**:
  - Use "Graph" tab (not "Table")
  - Set time range to 1 hour
  - Enable "Stacked" view for better visualization

### 6. Email Notification (HTML)
- **File**: `docs/images/email-notification.png`
- **What to capture**:
  - Full email view in email client or Mailpit
  - Show subject, sender, recipient
  - Show formatted HTML content with:
    - Opportunity details
    - Tier badge
    - AI-generated response
    - Action buttons (Approve/Edit/Decline)
- **How to get**:
  1. Use Mailpit if configured (http://localhost:8025)
  2. Or check your actual email inbox
  3. Or use browser dev tools to render HTML from email template

### 7. LinkedIn Scraper in Action (Optional)
- **File**: `docs/images/scraper-working.png`
- **What to capture**:
  - Browser window with LinkedIn open (if SCRAPER_HEADLESS=false)
  - Terminal showing scraper logs
  - Shows authentication and message extraction
- **Tips**:
  - Run: `SCRAPER_HEADLESS=false python scripts/scrape_linkedin.py`
  - Capture during message extraction phase

### 8. Database Content (Optional)
- **File**: `docs/images/database-records.png`
- **What to capture**:
  - PGAdmin or psql showing opportunities table
  - At least 5-10 records with different tiers
  - Show relevant columns: company, role, tier, score
- **Command**:
  ```bash
  docker-compose exec postgres psql -U user -d linkedin_agent -c "SELECT id, company_name, role_title, tier, total_score FROM opportunities LIMIT 10;"
  ```

## Screenshot Workflow

### Step-by-step Process

1. **Start system and let it run**:
   ```bash
   ./scripts/start.sh
   # Wait 2-3 minutes for all services
   ```

2. **Generate test data**:
   ```bash
   # Create 5-10 test opportunities
   python test_message_generation.py
   ```

3. **Open all URLs in separate tabs**:
   - http://localhost:8000/docs
   - http://localhost:3000 (Grafana)
   - http://localhost:9090 (Prometheus)
   - http://localhost:16686 (Jaeger)
   - http://localhost:5555 (Flower)

4. **Take screenshots systematically**:
   - One service at a time
   - Save with descriptive names
   - Check image quality before moving on

5. **Optimize images**:
   ```bash
   # macOS
   brew install imagemagick
   cd docs/images/
   for img in *.png; do
     convert "$img" -quality 85 -resize 1920x "optimized-$img"
   done
   ```

6. **Verify all screenshots**:
   - Check resolution (at least 1920px wide)
   - Verify no sensitive data visible
   - Ensure text is readable
   - Confirm file sizes are reasonable (< 500KB)

## Post-Processing

### Adding Annotations (Optional)

Use tools like:
- **Skitch** (macOS)
- **Greenshot** (Windows)
- **Flameshot** (Linux)

Add:
- Arrows pointing to key features
- Text boxes explaining important elements
- Highlights/boxes around important areas

### Example Annotations

For API docs screenshot:
- Arrow → "30+ REST endpoints"
- Box around → "Interactive testing"
- Highlight → "OpenAPI specification"

For Grafana:
- Arrow → "Real-time metrics"
- Box around → "60% cache hit rate"
- Highlight → "Business KPIs"

## Quick Screenshot Script

```bash
#!/bin/bash
# scripts/take_screenshots.sh

echo "📸 Starting screenshot capture process..."

echo "1. Make sure system is running..."
curl -s http://localhost:8000/health > /dev/null
if [ $? -ne 0 ]; then
    echo "❌ System not running. Start with: ./scripts/start.sh"
    exit 1
fi

echo "2. Opening URLs in browser..."
open http://localhost:8000/docs
sleep 2
open http://localhost:3000
sleep 2
open http://localhost:9090
sleep 2
open http://localhost:16686
sleep 2
open http://localhost:5555

echo "✅ All URLs opened!"
echo ""
echo "📸 Now capture screenshots:"
echo "   1. API Docs (http://localhost:8000/docs)"
echo "   2. Grafana (http://localhost:3000)"
echo "   3. Prometheus (http://localhost:9090)"
echo "   4. Jaeger (http://localhost:16686)"
echo "   5. Flower (http://localhost:5555)"
echo ""
echo "Save to: docs/images/"
echo ""
echo "Press Cmd+Shift+4 (macOS) to take screenshots"
```

## Verification Checklist

Before considering screenshots complete:

- [ ] All screenshots are at least 1920px wide
- [ ] No sensitive data (passwords, tokens, emails) visible
- [ ] Text is readable at 100% zoom
- [ ] File sizes are < 500KB each
- [ ] Files follow naming convention: `service-description.png`
- [ ] All required screenshots captured (minimum 5):
  - [ ] api-docs.png
  - [ ] grafana-dashboard.png
  - [ ] jaeger-traces.png
  - [ ] flower-tasks.png
  - [ ] prometheus-metrics.png
- [ ] Optional screenshots:
  - [ ] email-notification.png
  - [ ] scraper-working.png
  - [ ] database-records.png

## Alternative: Use Existing Screenshots

If you can't run the system right now, you can:

1. **Use demo screenshots from similar projects**:
   - Grafana: https://grafana.com/grafana/dashboards/
   - Jaeger: https://www.jaegertracing.io/docs/getting-started/
   - Prometheus: https://prometheus.io/docs/introduction/overview/

2. **Create mockups** using:
   - Figma: https://figma.com
   - Excalidraw: https://excalidraw.com

3. **Use placeholders temporarily**:
   - Add "Coming soon" images
   - Use badges and shields.io
   - Focus on code examples and architecture

## Adding Screenshots to README

Once you have screenshots:

```markdown
## 🎨 Live Dashboard

![Grafana Dashboard](docs/images/grafana-dashboard.png)
*Real-time monitoring with Grafana - Track opportunities, pipeline performance, and system health*

## 🔍 Distributed Tracing

![Jaeger Traces](docs/images/jaeger-traces.png)
*End-to-end request tracing with Jaeger - Visualize the complete pipeline flow*

## 📊 API Documentation

![API Docs](docs/images/api-docs.png)
*Interactive API documentation with Swagger UI - Test endpoints directly from the browser*
```

---

**Ready to capture?** Run `./scripts/start.sh` and follow this guide!
