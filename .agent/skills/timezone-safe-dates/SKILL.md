---
description: Best practices for handling timezone issues when parsing and storing dates
---

# Timezone-Safe Date Handling

When parsing and storing dates that will be displayed across different timezones, follow these practices to avoid off-by-one day errors.

## The Problem

Dates parsed without time components default to **midnight (00:00:00)**. When stored in UTC and displayed in a different timezone (e.g., UTC-3), the date can shift to the previous day.

**Example:**
- Parsed: `"6 feb"` → `2026-02-06T00:00:00` (UTC)
- Displayed in UTC-3: `2026-02-05T21:00:00` → Shows as **Feb 5** ❌

## The Solution: Normalize to Noon

Always set the time to **12:00:00 (noon)** for date-only values. This provides a ±12 hour buffer for any timezone.

```python
from datetime import datetime

def parse_date_safely(date_string: str) -> datetime:
    """Parse a date and normalize to noon to avoid timezone day shifts."""
    parsed = your_parser.parse(date_string)

    if parsed:
        # Normalize to noon to avoid timezone-related day shifts
        parsed = parsed.replace(hour=12, minute=0, second=0, microsecond=0)

    return parsed
```

## When to Apply This

Apply noon normalization when:
- Parsing relative dates (e.g., "yesterday", "5 days ago", "viernes")
- Parsing date strings without time (e.g., "6 feb", "Jan 29", "2026-02-06")
- The exact time is not important, only the day matters

Do NOT apply when:
- The exact timestamp is important (e.g., message sent at 3:45 PM)
- You're parsing full datetime strings with time components

## Implementation in This Project

See `app/scraper/linkedin_scraper.py`:
- `parse_relative_timestamp()` - Normalizes all parsed dates to noon
- `_parse_linkedin_custom()` - Custom LinkedIn parsing also normalized

## Verification

When debugging date issues:
1. Check the parsed timestamp in logs (should show `T12:00:00`)
2. Verify the stored value in database
3. Check how frontend displays the date (should match expected day regardless of timezone)
