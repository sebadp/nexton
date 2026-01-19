# LinkedIn Scraper Documentation

Complete guide for the LinkedIn message scraper using Playwright.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)
- [Rate Limiting](#rate-limiting)
- [Session Management](#session-management)
- [Error Handling](#error-handling)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

---

## Overview

The LinkedIn scraper is a robust, production-ready tool for extracting messages from LinkedIn using Playwright browser automation. It includes intelligent rate limiting, session management, and retry logic to avoid detection and account suspension.

**Key Components:**
- `LinkedInScraper`: Main scraper class
- `SessionManager`: Browser session and cookie management
- `RateLimiter` / `AdaptiveRateLimiter`: Request rate control
- `ScraperConfig`: Configuration management

---

## Features

- **Browser Automation**: Uses Playwright for reliable scraping
- **Session Management**: Persistent cookies for faster subsequent runs
- **Rate Limiting**: Token bucket algorithm with adaptive adjustment
- **Retry Logic**: Exponential backoff for failed requests
- **Anti-Detection**: Realistic browser fingerprint, randomized delays
- **Context Manager**: Automatic cleanup with async context managers
- **Structured Logging**: Detailed logs for monitoring and debugging
- **Error Handling**: Comprehensive exception handling with custom errors

---

## Architecture

```
LinkedInScraper
├── SessionManager
│   ├── Playwright Browser
│   ├── Browser Context
│   └── Cookie Storage
├── AdaptiveRateLimiter
│   ├── Token Bucket
│   └── Error Tracking
└── Configuration
    ├── Credentials
    ├── Rate Limits
    └── Retry Policy
```

### Component Responsibilities

**LinkedInScraper** (`linkedin_scraper.py`):
- Orchestrates scraping workflow
- Message extraction and parsing
- Navigation with retry logic
- Unread message detection

**SessionManager** (`session_manager.py`):
- Browser lifecycle management
- Cookie persistence (save/load)
- Authentication (login)
- Session validation

**RateLimiter** (`rate_limiter.py`):
- Request throttling
- Time window management
- Adaptive rate adjustment
- Error reporting

---

## Installation

### 1. Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install Playwright browsers
python -m playwright install chromium
```

### 2. Verify Installation

```bash
# Check Playwright installation
python -m playwright --version

# Test browser
python -m playwright open https://www.linkedin.com
```

---

## Usage

### Basic Usage

```python
import asyncio
from app.scraper import LinkedInScraper, ScraperConfig

async def main():
    # Create configuration
    config = ScraperConfig(
        email="your@email.com",
        password="your-password",
        headless=True,
    )

    # Use context manager for automatic cleanup
    async with LinkedInScraper(config) as scraper:
        # Get unread count
        count = await scraper.get_unread_count()
        print(f"Unread messages: {count}")

        # Scrape messages
        messages = await scraper.scrape_messages(limit=10, unread_only=True)

        for msg in messages:
            print(f"From: {msg.sender_name}")
            print(f"Message: {msg.message_text}")
            print(f"URL: {msg.conversation_url}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Using the Example Script

```bash
# Set credentials
export LINKEDIN_EMAIL="your@email.com"
export LINKEDIN_PASSWORD="your-password"

# Run scraper
python scripts/scrape_linkedin.py
```

### Advanced Usage

```python
from app.scraper import LinkedInScraper, ScraperConfig, RateLimitConfig
from app.scraper.rate_limiter import AdaptiveRateLimiter

# Custom configuration
config = ScraperConfig(
    email="your@email.com",
    password="your-password",
    headless=True,
    max_requests_per_minute=15,  # More aggressive
    min_delay_seconds=2.0,       # Faster
    max_retries=5,               # More retries
    exponential_backoff=True,
)

scraper = LinkedInScraper(config)

try:
    await scraper.initialize()

    # Scrape with custom limits
    messages = await scraper.scrape_messages(
        limit=50,           # Get up to 50 messages
        unread_only=False   # Include read messages
    )

    # Process messages
    for msg in messages:
        # Your processing logic here
        pass

finally:
    await scraper.cleanup()
```

---

## Configuration

### ScraperConfig Options

```python
@dataclass
class ScraperConfig:
    # Credentials (required)
    email: str
    password: str

    # Rate limiting
    max_requests_per_minute: int = 10
    min_delay_seconds: float = 3.0

    # Retry configuration
    max_retries: int = 3
    retry_delay: float = 5.0
    exponential_backoff: bool = True

    # Timeouts (seconds)
    page_timeout: int = 30
    navigation_timeout: int = 60

    # Scraping options
    headless: bool = True
    save_cookies: bool = True
```

### Environment Variables

```bash
# LinkedIn credentials
LINKEDIN_EMAIL="your@email.com"
LINKEDIN_PASSWORD="your-password"

# Optional: Cookie storage path
COOKIES_PATH="data/cookies.json"

# Optional: Headless mode
SCRAPER_HEADLESS="true"
```

---

## Rate Limiting

### How It Works

The scraper uses a **token bucket algorithm** for rate limiting:

1. **Token Bucket**: Maintains a fixed number of tokens (requests)
2. **Time Window**: Tokens replenish over a time window (default: 60s)
3. **Min Delay**: Enforces minimum delay between consecutive requests
4. **Adaptive**: Automatically reduces rate on errors

### Configuration

```python
from app.scraper.rate_limiter import RateLimitConfig, AdaptiveRateLimiter

# Create custom rate limit config
config = RateLimitConfig(
    max_requests=10,      # Max 10 requests
    time_window=60,       # Per 60 seconds
    min_delay=3.0,        # Minimum 3s between requests
    max_delay=6.0,        # Maximum delay for jitter
)

# Create rate limiter
limiter = AdaptiveRateLimiter(config)

# Before each request
limiter.wait_if_needed()

# Report success/failure
limiter.report_success()
limiter.report_rate_limit_error()
```

### Adaptive Rate Limiting

The `AdaptiveRateLimiter` automatically adjusts rates based on errors:

- **On Error**: Reduces rate by 25% (e.g., 10 req/min → 7.5 → 5.6 → ...)
- **On Success**: Gradually recovers to original rate after 5 minutes
- **Minimum**: Never goes below 1 request per window

### Rate Limit Warnings

LinkedIn may show warnings if you scrape too aggressively:

- **429 Too Many Requests**: Hit rate limit, wait longer
- **Account Warning**: Reduce rate immediately
- **Temporary Ban**: Wait 24 hours, use more conservative settings

**Recommended Settings:**
```python
# Conservative (safe)
max_requests_per_minute=5
min_delay_seconds=5.0

# Moderate (default)
max_requests_per_minute=10
min_delay_seconds=3.0

# Aggressive (risky)
max_requests_per_minute=15
min_delay_seconds=2.0
```

---

## Session Management

### Cookie Persistence

Cookies are saved to disk to avoid logging in on every run:

```python
# Cookies saved automatically on cleanup
async with LinkedInScraper(config) as scraper:
    # Your scraping logic
    pass
# Cookies saved here

# Next run will load cookies and skip login
```

**Cookie Storage:**
- **Path**: `data/cookies.json` (configurable)
- **Format**: JSON with cookies + timestamp
- **Expiry**: 30 days (configurable)

### Manual Session Management

```python
from app.scraper import SessionManager

# Create session manager
session_mgr = SessionManager(
    cookies_path=Path("data/cookies.json"),
    headless=True,
)

await session_mgr.start()

# Check login status
if not await session_mgr.is_logged_in():
    # Login manually
    await session_mgr.login(email="...", password="...")

# Save cookies
await session_mgr.save_cookies()

# Get page for custom scraping
page = await session_mgr.get_page()

await session_mgr.close()
```

---

## Error Handling

### Exception Hierarchy

```
LinkedInAgentException
└── ScraperError
    ├── LinkedInAuthError (authentication failed)
    └── RateLimitError (rate limit exceeded)
```

### Handling Errors

```python
from app.core.exceptions import ScraperError, LinkedInAuthError, RateLimitError

try:
    async with LinkedInScraper(config) as scraper:
        messages = await scraper.scrape_messages()

except LinkedInAuthError as e:
    print(f"Authentication failed: {e.message}")
    print(f"Details: {e.details}")
    # Handle: Check credentials, solve captcha

except RateLimitError as e:
    print(f"Rate limit exceeded: {e.message}")
    # Handle: Wait longer, reduce rate

except ScraperError as e:
    print(f"Scraping failed: {e.message}")
    # Handle: Retry with backoff

except Exception as e:
    print(f"Unexpected error: {e}")
    # Handle: Log and alert
```

### Retry Logic

The scraper includes automatic retry with exponential backoff:

```python
# Configured in ScraperConfig
config = ScraperConfig(
    max_retries=3,              # Try up to 3 times
    retry_delay=5.0,            # Initial delay: 5s
    exponential_backoff=True,   # 5s → 10s → 20s
)

# Retries are automatic for:
# - Network errors
# - Timeouts
# - Rate limit errors (with adaptive rate reduction)
```

---

## Best Practices

### 1. Use Conservative Rate Limits

Start with conservative settings and increase gradually:

```python
# Start here
config = ScraperConfig(
    max_requests_per_minute=5,
    min_delay_seconds=5.0,
)

# Monitor for 24 hours
# If no issues, gradually increase
```

### 2. Enable Cookie Persistence

Always save cookies to avoid frequent logins:

```python
config = ScraperConfig(
    save_cookies=True,  # Enable (default)
)
```

### 3. Use Headless Mode in Production

```python
config = ScraperConfig(
    headless=True,  # Faster, uses less resources
)

# Use headless=False only for debugging
```

### 4. Monitor Logs

Enable structured logging to track scraping:

```python
from app.core.logging import get_logger

logger = get_logger(__name__)

# Logs include:
# - rate_limit_check_passed
# - cookies_loaded
# - login_successful
# - message_extracted
# - rate_limit_hit (warning)
```

### 5. Handle Graceful Shutdown

```python
import signal

scraper = None

async def cleanup(sig):
    if scraper:
        await scraper.cleanup()

# Register signal handlers
loop = asyncio.get_event_loop()
for sig in (signal.SIGTERM, signal.SIGINT):
    loop.add_signal_handler(sig, lambda: asyncio.create_task(cleanup(sig)))
```

### 6. Limit Scraping Window

Don't scrape 24/7 - use realistic patterns:

```python
import datetime

# Only scrape during business hours
now = datetime.datetime.now()
if 9 <= now.hour <= 18:  # 9 AM - 6 PM
    messages = await scraper.scrape_messages()
else:
    print("Outside business hours, skipping")
```

---

## Troubleshooting

### Issue: Login Fails

**Symptoms:**
- `LinkedInAuthError` raised
- "login_failed" in logs

**Solutions:**
1. Verify credentials are correct
2. Check for LinkedIn captcha (use `headless=False` to see)
3. Try logging in manually first
4. LinkedIn may require 2FA - not supported yet

---

### Issue: No Messages Found

**Symptoms:**
- `unread_count = 0`
- Empty messages list

**Solutions:**
1. Verify you have unread messages
2. Try `unread_only=False` to scrape all messages
3. Check LinkedIn UI selectors haven't changed (update code)
4. Enable `headless=False` to see what's happening

---

### Issue: Rate Limit Errors

**Symptoms:**
- "rate_limit_hit" warnings
- `RateLimitError` raised
- LinkedIn shows "Too many requests"

**Solutions:**
1. Reduce `max_requests_per_minute` to 5 or lower
2. Increase `min_delay_seconds` to 10 or higher
3. Wait 24 hours before retrying
4. Use `AdaptiveRateLimiter` (default) to auto-adjust

---

### Issue: Stale Cookies

**Symptoms:**
- Redirected to login despite saved cookies
- "cookies_expired" warning

**Solutions:**
1. Delete `data/cookies.json`
2. Login again with fresh credentials
3. Cookies expire after 30 days by default

---

### Issue: Browser Crashes

**Symptoms:**
- Browser process dies unexpectedly
- "browser_closed" errors

**Solutions:**
1. Increase system resources (RAM)
2. Reduce concurrent operations
3. Update Playwright: `pip install --upgrade playwright`
4. Reinstall browsers: `python -m playwright install chromium --force`

---

## Security Considerations

### Credential Storage

**Never hardcode credentials:**

```python
# ❌ BAD
config = ScraperConfig(
    email="myemail@example.com",
    password="mypassword123",
)

# ✅ GOOD
import os
config = ScraperConfig(
    email=os.getenv("LINKEDIN_EMAIL"),
    password=os.getenv("LINKEDIN_PASSWORD"),
)
```

### Cookie Security

Cookies can be used to access your account:

1. **Store securely**: Encrypt `data/cookies.json` at rest
2. **Limit access**: Set file permissions to 600 (owner-only)
3. **Rotate regularly**: Delete cookies every 7-14 days
4. **Never commit**: Add to `.gitignore`

```bash
# Secure cookie file
chmod 600 data/cookies.json

# Add to .gitignore
echo "data/cookies.json" >> .gitignore
```

---

## Performance Tips

### 1. Reduce Page Waits

```python
# Instead of waiting for networkidle
await page.goto(url, wait_until="networkidle")  # Slow

# Use domcontentloaded (faster)
await page.goto(url, wait_until="domcontentloaded")
```

### 2. Reuse Browser Context

```python
# Don't create new browser for each scrape
# Use single SessionManager for multiple scrapes
session_mgr = SessionManager()
await session_mgr.start()

for i in range(10):
    page = await session_mgr.get_page()
    # Scrape using same browser

await session_mgr.close()
```

### 3. Parallel Scraping

```python
# Scrape multiple accounts in parallel
async def scrape_account(config):
    async with LinkedInScraper(config) as scraper:
        return await scraper.scrape_messages()

# Run in parallel
results = await asyncio.gather(
    scrape_account(config1),
    scrape_account(config2),
    scrape_account(config3),
)
```

---

## API Reference

See inline documentation in:
- `app/scraper/linkedin_scraper.py`
- `app/scraper/session_manager.py`
- `app/scraper/rate_limiter.py`

---

## Support

- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions
- **Documentation**: This file + inline docs
