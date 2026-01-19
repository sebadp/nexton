# 🧪 LinkedIn Scraper Testing

Quick guide to test the LinkedIn scraper independently.

---

## 🚀 Quick Test (Recommended for First Time)

### 1. Setup

```bash
# Install dependencies
pip install -r requirements.txt
playwright install chromium

# Configure credentials in .env
echo "LINKEDIN_EMAIL=your@email.com" >> .env
echo "LINKEDIN_PASSWORD=yourpassword" >> .env
```

### 2. Run Quick Test

```bash
# Simple test with browser visible (recommended)
python test_scraper_quick.py
```

This will:
- ✅ Log in to LinkedIn
- ✅ Scrape 5 recent messages
- ✅ Display results
- ✅ Show browser (so you can see what's happening)

**Output:**
```
🚀 Quick LinkedIn Scraper Test
============================================================
📧 Email: your@email.com
🔒 Password: **********
============================================================

🔐 Logging in to LinkedIn...
✅ Login successful!

📥 Scraping messages...

✨ Found 5 messages:

1. 📩 From: John Recruiter
   📅 2026-01-18 10:30:00
   💬 Hi! I came across your profile and I think you'd be a great fit...

2. 📩 From: Jane Tech Lead
   📅 2026-01-18 09:15:00
   💬 Hello! We're hiring for a Backend Engineer position...

[...]

============================================================
✅ Test completed successfully!
```

---

## 🎯 Advanced Testing

### Test with Different Options

```bash
# Scrape messages (headless)
python test_scraper.py scrape \
  --email your@email.com \
  --password yourpassword \
  --headless true \
  --limit 10

# Scrape with visible browser (debug)
python test_scraper.py scrape \
  --email your@email.com \
  --password yourpassword \
  --headless false

# Send a test message
python test_scraper.py send \
  --email your@email.com \
  --password yourpassword \
  --url "https://www.linkedin.com/messaging/thread/2-ABC123..." \
  --message "Test message from LinkedIn Agent"
```

---

## ⚠️ Common Issues

### 1. Login Failed

**Symptoms:** `❌ Error: Failed to login to LinkedIn`

**Solutions:**
- ✅ Verify credentials are correct
- ✅ Log in manually to LinkedIn first
- ✅ Complete any verification (email, phone, captcha)
- ✅ Wait 10 minutes and try again

### 2. No Messages Found

**Symptoms:** `✨ Found 0 messages`

**Solutions:**
- ✅ Check you have messages in LinkedIn manually
- ✅ Run with `--headless false` to see what's happening
- ✅ May be rate limited - wait 1 hour

### 3. Playwright Not Found

**Symptoms:** `Playwright driver not found`

**Solution:**
```bash
playwright install chromium
```

---

## 📚 Full Documentation

See [docs/SCRAPER_TESTING.md](docs/SCRAPER_TESTING.md) for:
- Detailed usage examples
- Troubleshooting guide
- Best practices
- Integration with main app
- Security notes

---

## ✅ What to Test

- [ ] Login works with your credentials
- [ ] Can scrape messages
- [ ] Messages contain correct data
- [ ] Can send messages (optional - be careful!)
- [ ] Rate limiting works
- [ ] Error handling works

---

## 🔒 Security

**Never commit your credentials!**

```bash
# .env is already in .gitignore
# Make sure your credentials are only in .env
grep -r "your_real_password" .  # Should return nothing!
```

---

## 🎓 Next Steps

Once scraper works:

1. ✅ Test message scraping
2. ✅ Test message sending
3. ✅ Integrate with main app
4. ✅ Setup Celery task for scheduled scraping
5. ✅ Monitor scraping success rate

---

**Need help?** See [docs/SCRAPER_TESTING.md](docs/SCRAPER_TESTING.md) for detailed troubleshooting.
