# Architecture Diagrams & Screenshots

This directory contains visual assets for documentation.

## Generating Architecture Diagrams

### Option 1: Mermaid CLI (Automated)

```bash
# Install mermaid-cli
npm install -g @mermaid-js/mermaid-cli

# Generate diagrams from markdown
cd docs/
mmdc -i ARCHITECTURE_DIAGRAM.md -o images/architecture-overview.png
mmdc -i ARCHITECTURE_DIAGRAM.md -o images/architecture-overview.svg
```

### Option 2: Mermaid Live Editor (Manual)

1. Go to https://mermaid.live/
2. Copy diagram code from `../ARCHITECTURE_DIAGRAM.md`
3. Click "Actions" → "Export PNG/SVG"
4. Save to this directory

### Option 3: draw.io (Custom Design)

1. Go to https://app.diagrams.net/
2. Create new diagram
3. Use architecture from `../ARCHITECTURE_DIAGRAM.md` as reference
4. Export as PNG (300 DPI recommended)
5. Save as `architecture-custom.png`

## Required Screenshots

For a complete showcase, capture these screenshots:

### 1. Grafana Dashboards
- **File**: `grafana-dashboard.png`
- **URL**: http://localhost:3000
- **What to show**: LinkedIn Agent Overview dashboard with metrics

### 2. Jaeger Tracing
- **File**: `jaeger-traces.png`
- **URL**: http://localhost:16686
- **What to show**: End-to-end trace of message processing

### 3. Flower Task Monitor
- **File**: `flower-tasks.png`
- **URL**: http://localhost:5555
- **What to show**: Active Celery workers and tasks

### 4. FastAPI Docs
- **File**: `api-docs.png`
- **URL**: http://localhost:8000/docs
- **What to show**: Interactive API documentation (Swagger UI)

### 5. Prometheus Metrics
- **File**: `prometheus-metrics.png`
- **URL**: http://localhost:9090
- **What to show**: Custom metrics query and graph

### 6. Email Notification
- **File**: `email-notification.png`
- **What to show**: HTML email with opportunity details

### 7. Response Workflow
- **File**: `response-workflow.png`
- **What to show**: Approve/Edit/Decline workflow

## Screenshot Guidelines

- **Resolution**: 1920x1080 or higher
- **Format**: PNG with transparency where possible
- **Size**: Optimize to < 500KB each
- **Annotations**: Add arrows/highlights if needed
- **Consistency**: Use same theme/colors across screenshots

## Tools for Screenshots

- **macOS**: Cmd+Shift+4 (select area)
- **Windows**: Snipping Tool or Win+Shift+S
- **Linux**: gnome-screenshot or scrot
- **Browser**: Full page screenshot extensions

## Optimization

Optimize images before committing:

```bash
# Install imagemagick
brew install imagemagick  # macOS
sudo apt install imagemagick  # Ubuntu

# Optimize PNG
convert input.png -quality 85 -resize 1920x output.png

# Or use online tools
# - TinyPNG: https://tinypng.com/
# - Squoosh: https://squoosh.app/
```

## Current Assets

- [ ] architecture-overview.png
- [ ] architecture-overview.svg
- [ ] grafana-dashboard.png
- [ ] jaeger-traces.png
- [ ] flower-tasks.png
- [ ] api-docs.png
- [ ] prometheus-metrics.png
- [ ] email-notification.png
- [ ] response-workflow.png

## Usage in Documentation

Reference images in markdown:

```markdown
![Architecture Overview](docs/images/architecture-overview.png)

![Grafana Dashboard](docs/images/grafana-dashboard.png)
```

Or with HTML for sizing:

```html
<img src="docs/images/architecture-overview.png" alt="Architecture" width="800">
```
