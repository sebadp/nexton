# LinkedIn Scraper Testing Guide

**Quick guide for testing the LinkedIn scraper and messenger independently.**

---

## Overview

The LinkedIn scraper can be tested standalone without running the full application. This is useful for:

- ✅ Testing LinkedIn credentials
- ✅ Verifying scraper functionality
- ✅ Debugging message extraction
- ✅ Testing message sending
- ✅ Checking rate limiting

---

## Quick Start

### 1. Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

### 2. Test Message Scraping

```bash
# Basic scraping test (headless)
python test_scraper.py scrape \
  --email your_linkedin_email@example.com \
  --password your_password

# Scrape with visible browser (recommended for first test)
python test_scraper.py scrape \
  --email your_linkedin_email@example.com \
  --password your_password \
  --headless false

# Scrape more messages
python test_scraper.py scrape \
  --email your_linkedin_email@example.com \
  --password your_password \
  --limit 10
```

### 3. Test Message Sending

```bash
# Send a test message
python test_scraper.py send \
  --email your_linkedin_email@example.com \
  --password your_password \
  --url "https://www.linkedin.com/messaging/thread/2-ABC123..." \
  --message "This is a test message from the LinkedIn Agent"

# Send with visible browser
python test_scraper.py send \
  --email your_linkedin_email@example.com \
  --password your_password \
  --url "https://www.linkedin.com/messaging/thread/2-ABC123..." \
  --message "Test message" \
  --headless false
```

---

## Understanding the Output

### Successful Scrape

```
================================================================================
🚀 LinkedIn Scraper Test
================================================================================

📋 Configuration:
   Email: your@email.com
   Headless: True
   Limit: 5 messages

🔐 Initializing scraper (logging in)...
✅ Login successful!

📥 Scraping messages (limit: 5)...

✨ Successfully scraped 5 messages!
================================================================================

📩 1. Message from: John Recruiter
   Timestamp: 2026-01-18 10:30:00
   Preview: Hi! I came across your profile and I think you'd be a great fit for a Senior Python Developer...
   URL: https://www.linkedin.com/messaging/thread/2-ABC123...
--------------------------------------------------------------------------------

📩 2. Message from: Jane Tech
   Timestamp: 2026-01-18 09:15:00
   Preview: Hello! We're hiring for a Backend Engineer position at TechCorp...
   URL: https://www.linkedin.com/messaging/thread/2-DEF456...
--------------------------------------------------------------------------------

[... more messages ...]

================================================================================
📊 Summary:
   Total messages: 5
   Unread: 3
   Read: 2
   Unique senders: 4
   Senders: John Recruiter, Jane Tech, Bob Smith, Alice Johnson
================================================================================
✅ Test completed successfully!

🧹 Cleaning up...
✅ Cleanup complete!
```

### Successful Send

```
================================================================================
📤 LinkedIn Messenger Test
================================================================================

📋 Configuration:
   Email: your@email.com
   Headless: True
   Conversation: https://www.linkedin.com/messaging/thread/2-ABC123...
   Message: This is a test message from the LinkedIn...

🔐 Initializing messenger (logging in)...
✅ Login successful!

📤 Sending message...
✅ Message sent successfully!

🧹 Cleaning up...
✅ Cleanup complete!
```

---

## Common Issues

### Issue 1: Login Failed

**Error:**
```
❌ Error: Failed to login to LinkedIn
   Type: ScraperError
```

**Solutions:**

1. **Check credentials:**
```bash
# Verify email and password are correct
# Try logging in manually to LinkedIn first
```

2. **LinkedIn requires verification:**
```bash
# If you see "checkpoint" or "challenge" in logs:
# - Log in to LinkedIn manually in a browser
# - Complete any verification (phone, email, captcha)
# - Wait 10 minutes
# - Try script again
```

3. **Account locked:**
```bash
# LinkedIn may temporarily lock your account if:
# - Too many failed login attempts
# - Suspicious activity detected
# Solution: Wait 24 hours and try again
```

### Issue 2: No Messages Found

**Error:**
```
✨ Successfully scraped 0 messages!
```

**Possible causes:**

1. **No messages in inbox:**
   - Check LinkedIn manually - do you have messages?
   - The scraper only gets messages from the main inbox

2. **Selector changed:**
   - LinkedIn may have updated their HTML structure
   - Check `app/scraper/linkedin_scraper.py` selectors
   - May need to update selectors

3. **Rate limited:**
   - LinkedIn detected automated scraping
   - Wait 1 hour and try with `--headless false` to see what's happening

### Issue 3: Playwright Not Found

**Error:**
```
❌ Error: Playwright driver not found
```

**Solution:**
```bash
# Install Playwright browsers
playwright install chromium

# Or install all browsers
playwright install
```

### Issue 4: Message Sending Failed

**Error:**
```
❌ Failed to send message
```

**Solutions:**

1. **Invalid conversation URL:**
```bash
# URL must be exact LinkedIn messaging thread URL
# Format: https://www.linkedin.com/messaging/thread/2-ABC123...

# Get URL by:
# - Opening conversation in LinkedIn
# - Copying URL from browser address bar
```

2. **Message box not found:**
```bash
# LinkedIn may have changed their UI
# Run with --headless false to see what's happening
python test_scraper.py send --headless false ...
```

3. **Rate limiting:**
```bash
# LinkedIn may block if sending too many messages
# Wait 1 hour between tests
# Don't send more than 10-20 messages per day during testing
```

---

## Best Practices

### 1. Start with Visible Browser

For your first test, always use `--headless false`:

```bash
python test_scraper.py scrape \
  --email your@email.com \
  --password your_password \
  --headless false
```

This lets you:
- ✅ See what's happening
- ✅ Verify login works
- ✅ Check for LinkedIn verification prompts
- ✅ Debug selector issues

### 2. Test with Real Account

Use your real LinkedIn account for testing, but:

- ⚠️ **Don't spam** - Respect LinkedIn's terms of service
- ⚠️ **Test slowly** - Wait between operations
- ⚠️ **Limit tests** - Max 5-10 scrapes per day during development
- ⚠️ **Use production carefully** - Once working, limit to hourly scrapes

### 3. Handle Verification

LinkedIn may ask for verification:

1. **Email verification:**
   - Check your email
   - Click verification link
   - Try script again

2. **Phone verification:**
   - Complete verification manually
   - Wait 10 minutes
   - Try script again

3. **Captcha:**
   - Complete captcha manually (run with `--headless false`)
   - Script will continue after you solve it

### 4. Monitor for Rate Limits

Signs of rate limiting:
- Empty message list when you know there are messages
- Login succeeds but scraping fails
- Timeout errors

If rate limited:
- ⏰ Wait 1 hour
- 🐌 Reduce scraping frequency
- 📊 Check logs for patterns

---

## Advanced Usage

### Custom Configuration

You can modify the scraper config in the script:

```python
config = ScraperConfig(
    email=email,
    password=password,
    headless=headless,
    max_retries=3,              # Number of retries on failure
    max_requests_per_minute=10, # Rate limit
    page_timeout=30,            # Seconds to wait for page load
    navigation_timeout=60,      # Seconds to wait for navigation
)
```

### Scrape Unread Only

Modify `test_scraper.py`:

```python
# Change this line:
messages = await scraper.scrape_messages(limit=limit, unread_only=False)

# To:
messages = await scraper.scrape_messages(limit=limit, unread_only=True)
```

### Save Messages to File

Add after scraping:

```python
import json

# Save to JSON
with open('messages.json', 'w') as f:
    json.dump([
        {
            'sender': m.sender_name,
            'message': m.message_text,
            'timestamp': m.timestamp.isoformat(),
            'url': m.conversation_url,
        }
        for m in messages
    ], f, indent=2)

print("✅ Messages saved to messages.json")
```

### Test with Environment Variables

Create `.env.test`:

```bash
LINKEDIN_EMAIL=your@email.com
LINKEDIN_PASSWORD=yourpassword
```

Then modify script:

```python
from dotenv import load_dotenv
import os

load_dotenv('.env.test')

email = os.getenv('LINKEDIN_EMAIL')
password = os.getenv('LINKEDIN_PASSWORD')
```

---

## Integration with Main App

Once the scraper is working standalone, it integrates automatically:

### 1. Background Scraping

```python
# In app/tasks/scraping_tasks.py
from app.scraper.linkedin_scraper import LinkedInScraper, ScraperConfig

@celery_app.task
def scrape_linkedin_messages():
    config = ScraperConfig(
        email=settings.LINKEDIN_EMAIL,
        password=settings.LINKEDIN_PASSWORD,
        headless=True,
    )

    scraper = LinkedInScraper(config)
    messages = await scraper.scrape_messages(limit=50, unread_only=True)

    # Process messages...
```

### 2. Scheduled Scraping

```python
# Schedule to run every hour
celery_app.conf.beat_schedule = {
    'scrape-linkedin-hourly': {
        'task': 'scrape_linkedin_messages',
        'schedule': crontab(minute=0),  # Every hour
    },
}
```

### 3. Manual Trigger

```bash
# Trigger via API
curl -X POST http://localhost:8000/api/v1/scraper/run

# Or via Celery
celery -A app.tasks.celery_app call scrape_linkedin_messages
```

---

## Troubleshooting Checklist

Before asking for help, check:

- [ ] Playwright installed: `playwright install chromium`
- [ ] Credentials correct: Can you log in manually?
- [ ] LinkedIn account verified: No pending verifications?
- [ ] Not rate limited: Waited 1 hour since last test?
- [ ] Tried with `--headless false`: Can you see what's happening?
- [ ] Checked logs: Any specific error messages?
- [ ] LinkedIn UI changed: Selectors may need updating
- [ ] Network connection: Can you access linkedin.com?

---

## Security Notes

### Never Commit Credentials

```bash
# Add to .gitignore
.env
.env.test
.env.local
credentials.json

# Use environment variables
export LINKEDIN_EMAIL=your@email.com
export LINKEDIN_PASSWORD=yourpassword
```

### Use App Passwords

If LinkedIn supports it:
- Don't use your main password
- Create application-specific password
- Rotate credentials regularly

### Limit Access

```bash
# Only run scraper on trusted machines
# Don't expose scraper endpoint publicly
# Use authentication for API triggers
```

---

## Next Steps

Once scraper is working:

1. **Integrate with pipeline**: Process scraped messages through DSPy
2. **Setup scheduling**: Run hourly via Celery Beat
3. **Add monitoring**: Track scraping success rate
4. **Handle errors**: Implement retry logic and alerts
5. **Optimize**: Reduce scraping frequency as needed

---

## Support

- **Script**: `test_scraper.py`
- **Scraper code**: `app/scraper/linkedin_scraper.py`
- **Messenger code**: `app/services/linkedin_messenger.py`
- **Documentation**: `docs/`
- **Issues**: Check GitHub Issues for known problems

---

*Last Updated: January 18, 2026*
*Feature: LinkedIn Scraper Testing*
*Version: 1.3.0*
