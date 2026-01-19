#!/bin/bash
# Script to help capture screenshots for documentation

set -e

echo "📸 LinkedIn AI Agent - Screenshot Helper"
echo "========================================"
echo ""

# Check if system is running
echo "🔍 Checking if system is running..."
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "❌ System is not running!"
    echo ""
    echo "Start the system first:"
    echo "  ./scripts/start.sh"
    echo ""
    exit 1
fi

echo "✅ System is running!"
echo ""

# Create images directory if it doesn't exist
mkdir -p docs/images

echo "📋 Screenshot Checklist:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Required Screenshots (5):"
echo "  [ ] api-docs.png         - http://localhost:8000/docs"
echo "  [ ] grafana-dashboard.png - http://localhost:3000 (admin/admin)"
echo "  [ ] jaeger-traces.png    - http://localhost:16686"
echo "  [ ] flower-tasks.png     - http://localhost:5555 (admin/admin)"
echo "  [ ] prometheus-metrics.png - http://localhost:9090"
echo ""
echo "Optional Screenshots (3):"
echo "  [ ] email-notification.png"
echo "  [ ] scraper-working.png"
echo "  [ ] database-records.png"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Ask if user wants to open URLs
read -p "📱 Open all URLs in browser? (y/n): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🌐 Opening URLs..."
    echo ""

    # Detect OS and use appropriate command
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        OPEN_CMD="open"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        OPEN_CMD="xdg-open"
    else
        # Windows or other
        OPEN_CMD="start"
    fi

    echo "1️⃣  Opening API Docs..."
    $OPEN_CMD "http://localhost:8000/docs" 2>/dev/null
    sleep 2

    echo "2️⃣  Opening Grafana..."
    $OPEN_CMD "http://localhost:3000" 2>/dev/null
    sleep 2

    echo "3️⃣  Opening Prometheus..."
    $OPEN_CMD "http://localhost:9090" 2>/dev/null
    sleep 2

    echo "4️⃣  Opening Jaeger..."
    $OPEN_CMD "http://localhost:16686" 2>/dev/null
    sleep 2

    echo "5️⃣  Opening Flower..."
    $OPEN_CMD "http://localhost:5555" 2>/dev/null

    echo ""
    echo "✅ All URLs opened in browser!"
fi

echo ""
echo "📸 Screenshot Instructions:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "macOS:"
    echo "  Cmd + Shift + 4  → Select area to capture"
    echo "  Cmd + Shift + 5  → Screenshot toolbar with options"
    echo ""
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "Linux:"
    echo "  Shift + Print    → Select area to capture"
    echo "  Or use: gnome-screenshot -a"
    echo ""
else
    echo "Windows:"
    echo "  Win + Shift + S  → Snipping tool"
    echo "  Or use: Snipping Tool app"
    echo ""
fi

echo "Save screenshots to: docs/images/"
echo ""
echo "Guidelines:"
echo "  ✓ Resolution: 1920x1080 or higher"
echo "  ✓ Format: PNG"
echo "  ✓ Size: < 500KB (optimize if needed)"
echo "  ✓ No sensitive data visible"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Offer to show detailed guide
read -p "📖 View detailed screenshot guide? (y/n): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    if command -v bat &> /dev/null; then
        bat docs/SCREENSHOTS_GUIDE.md
    elif command -v less &> /dev/null; then
        less docs/SCREENSHOTS_GUIDE.md
    else
        cat docs/SCREENSHOTS_GUIDE.md
    fi
fi

echo ""
echo "✨ Happy screenshotting!"
echo ""
echo "See full guide: docs/SCREENSHOTS_GUIDE.md"
