# 🔧 LinkedIn Scraper Selector Updates

## What Was Fixed

The LinkedIn scraper was failing with timeout errors because LinkedIn changed their HTML structure. I've updated the scraper to be much more robust.

### Changes Made

**File: `app/scraper/linkedin_scraper.py`**

#### 1. **Conversation Container Selectors** (Lines 184-207)
Added multiple fallback selectors for finding the conversation list:
- `ul[class*="msg-conversations-container"]` (original)
- `ul.msg-conversations-container__conversations-list`
- `div[role="navigation"] ul`
- `main ul[class*="list"]`

The scraper now tries each selector until one works.

#### 2. **Conversation Item Selectors** (Lines 209-223)
Added multiple fallback selectors for individual conversations:
- `li[class*="msg-conversation-listitem"]` (original)
- `li.msg-conversation-listitem__link`
- `ul li[data-test-id*="conversation"]`
- `main li[class*="conversation"]`

#### 3. **Debug Functionality** (Lines 225-254)
If no conversations are found, the scraper now:
- Saves a screenshot: `debug_linkedin_messaging.png`
- Saves the HTML: `debug_linkedin_messaging.html`
- Provides these files for manual inspection

This helps identify what LinkedIn's actual structure is if selectors fail.

#### 4. **Unread Indicator Selectors** (Lines 265-282, 520-534)
Added multiple fallback selectors for detecting unread messages:
- `[data-test-icon="unseen-icon"]` (original)
- `[class*="unseen"]`
- `[class*="unread"]`
- `div[class*="notification-badge"]`

#### 5. **Message Extraction Selectors** (Lines 321-398)
Updated message extraction with multiple fallback selectors for:

**Message list container:**
- `div[class*="msg-s-message-list"]`
- `div.msg-s-message-list-container`
- `main div[role="main"]`

**Sender name:**
- `h2[class*="msg-entity-lockup__entity-title"]`
- `h2.msg-entity-lockup__entity-title`
- `header h2`
- `div[class*="thread-details"] h2`

**Messages list:**
- `li[class*="msg-s-message-list__event"]`
- `ul.msg-s-message-list li`
- `div[class*="message-item"]`
- `div[class*="msg-s-event-listitem"]`

**Message text:**
- `p[class*="msg-s-event-listitem__body"]`
- `div[class*="msg-s-event-listitem__body"]`
- `div.msg-s-event-listitem__message-body`
- `p[dir="ltr"]`

If none work, it falls back to extracting all text from the message element.

---

## How to Test

### Option 1: Quick Test (Recommended)

```bash
python test_scraper_quick.py
```

This will:
- ✅ Use credentials from `.env`
- ✅ Show browser window (headless=False)
- ✅ Scrape up to 5 messages (all, not just unread)
- ✅ Display results in terminal

### Option 2: With Custom Parameters

```bash
python test_scraper.py scrape \
  --email your@email.com \
  --password 'your_password' \
  --headless false \
  --limit 10
```

---

## Expected Behavior

### Success Case

You should see logs like:
```
conversation_container_found selector=ul[class*="msg-conversations-container"]
conversations_found selector=li[class*="msg-conversation-listitem"] count=10
sender_found selector=h2[class*="msg-entity-lockup__entity-title"] name=John Doe
message_text_found selector=p[class*="msg-s-event-listitem__body"]
```

Then:
```
✨ Found 5 messages:

1. 📩 From: John Recruiter
   📅 2026-01-18 10:30:00
   💬 Hi! I came across your profile...
```

### Debug Case

If selectors still don't match, you'll see:
```
no_conversations_found_saving_debug_info
debug_screenshot_saved path=debug_linkedin_messaging.png
debug_html_saved path=debug_linkedin_messaging.html
```

Then you can:
1. Open `debug_linkedin_messaging.png` to see what the page looks like
2. Open `debug_linkedin_messaging.html` in a browser or text editor
3. Inspect the HTML to find the actual selectors LinkedIn is using
4. Update the selector lists in `linkedin_scraper.py` accordingly

---

## Why This Approach?

LinkedIn frequently changes their HTML class names to prevent scraping. Instead of relying on a single selector, we now:

1. **Try multiple selectors** - If one breaks, another might still work
2. **Use different selector strategies**:
   - Class-based: `[class*="msg-conversations"]`
   - Exact class: `ul.msg-conversations-container`
   - Role-based: `div[role="navigation"]`
   - Generic: `main ul[class*="list"]`

3. **Provide debugging info** - When all selectors fail, save screenshot + HTML so we can see what LinkedIn actually looks like

4. **Log everything** - Debug logs show which selector worked, making it easy to see patterns

---

## Troubleshooting

### If you still get "No conversations found"

1. Check the debug files:
   ```bash
   open debug_linkedin_messaging.png
   open debug_linkedin_messaging.html
   ```

2. Look for the conversation list in the HTML:
   ```bash
   grep -i "conversation" debug_linkedin_messaging.html | head -20
   ```

3. Find the actual class names being used

4. Add them to the selector lists in `linkedin_scraper.py`

### If messages are found but extraction fails

Check logs for which selectors are being tried:
```
sender_found selector=h2[class*="msg-entity-lockup__entity-title"]
messages_list_found selector=li[class*="msg-s-message-list__event"]
```

If you see warnings like:
```
no_messages_found_in_conversation
```

Then the conversation list works but message extraction needs updating.

---

## Next Steps

1. **Test the scraper** with the updated code
2. **Check if it works** - if yes, great! If no, check debug files
3. **Update selectors** if needed based on debug HTML
4. **Integrate with main app** once scraping works reliably

---

## Notes

- LinkedIn changes their HTML frequently (every few months)
- This multi-selector approach should be more resilient
- When LinkedIn updates, you may need to add new selectors
- The debug functionality makes this much easier to diagnose

---

**Last Updated:** 2026-01-18
