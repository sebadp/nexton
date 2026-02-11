---
name: Scraping Best Practices
description: Best practices for implementing web scrapers, specifically focused on handling infinite scroll and configuration.
---

# Scraping Best Practices

This skill documents best practices for web scraping, particularly for single-page applications (SPAs) like LinkedIn.

## 1. Infinite Scroll Handling

When scraping lists that use infinite scrolling, simple `scrollTop = scrollHeight` assignments are often insufficient because they don't trigger the checks (like `IntersectionObserver`) that the site uses to load more content.

### Bad Approach
```python
# abrupt jump, often ignored by SPAs
await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
```

### Recommended Approach
Scroll the **last element** into view. This mimics user behavior and ensures the specific element monitoring for visibility is triggered.

```python
# Get the updated list of items
items = await page.query_selector_all("li.item")
if items:
    last_item = items[-1]
    # Scroll the specific element into view
    await last_item.scroll_into_view_if_needed()

    # Optional: Small "shimmy" or mouse wheel action to ensure event trigger
    await page.mouse.wheel(0, 100)

    # CRITICAL: Wait for network request and DOM update
    await asyncio.sleep(2)
```

## 2. Configuration & Limits

Frontend triggers for scraping jobs should always respect the backend's configuration defaults unless explicitly overridden by the user.

-   **Frontend**: Do NOT hardcode limits (e.g., `limit=20`) in API calls. Pass `undefined` or `null` to let the backend use its default.
-   **Backend**: Use Pydantic defaults or settings classes to define the "source of truth" for limits.

### Frontend Example (React)

```typescript
// Good: Passes undefined if no specific limit is requested
const startScraping = (limit?: number) => {
    const params = new URLSearchParams();
    if (limit) params.append("limit", limit.toString());

    // URL becomes /api/scrape or /api/scrape?limit=50
    const eventSource = new EventSource(\`/api/scrape?\${params.toString()}\`);
}
```

### Backend Example (FastAPI)

```python
@router.get("/scrape")
async def scrape(limit: int | None = None):
    # Fallback to settings if limit is not provided
    final_limit = limit or settings.DEFAULT_SCRAPE_LIMIT
    await scraper.run(limit=final_limit)
```

## 3. Robust Selectors

SPAs often change class names (e.g., `msg-conversation-card__content--active`).

-   Use **partial matches** where possible: `[class*="message-list"]`.
-   Try **multiple known selectors** in a loop until one works.
-   Log which selector succeeded to help with maintenance.
