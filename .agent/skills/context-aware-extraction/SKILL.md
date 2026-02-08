---
description: Best practices for extracting entities from conversation history and handling missing data
---

# Context-Aware Extraction & Robust Scraping

When extracting structured data (like company names, roles) from conversation threads, relying on a single message is often insufficient. Use the full conversation history to provide context to the LLM.

## The Problem

1.  **Missing Context:** A single "follow-up" message (e.g., "Are you interested?") contains no entity information.
2.  **"N/A" Fatigue:** Returning "N/A" or "None" for missing fields looks broken to users.
3.  **Fragile Scraping:** Scraping loops that crash on one malformed message can lose valid data.

## The Solution

### 1. Fetch Full Conversation History

Instead of scraping just the last message, fetch the last N messages to build a transcript.

```python
# Bad: Single message
text = await message_element.inner_text()

# Good: Conversation Transcript
transcript = []
for msg in last_20_messages:
    sender = determine_sender(msg)
    text = extract_text(msg)
    transcript.append(f"[{sender}]: {text}")
full_context = "\n\n".join(transcript)
```

### 2. Extract on Every Message Type

Do not skip extraction for "Follow-up" or "Courtesy" messages if you have the history. The entity (Company Name) might be in the first message, while the current message is just a bump.

**Pattern:**
- Always run the `MessageAnalyzer` logic.
- The LLM will find the entity in the history.
- Only skip if the *entire* conversation lacks the entity.

### 3. Graceful Fallbacks (UX)

Never display raw "N/A", "None", or "null" to the user.

**In LLM Prompts:**
Instruct the LLM to return a descriptive string if data is missing.

```python
company: str = dspy.OutputField(desc="Company name. If NOT mentioned, return 'Unknown Company'.")
```

**In Post-Processing:**
Normalize messy LLM outputs.

```python
def normalize_company(self, company: str) -> str:
    if not company or company.lower() in ["n/a", "none", "not mentioned"]:
        return "Unknown Company"
    return company
```

## Implementation in This Project

See `app/scraper/linkedin_scraper.py` and `app/dspy_modules/pipeline.py`:
- **Scraper:** Fetches last 20 messages to build `conversation_transcript`.
- **Pipeline:** Passes full transcript to `MessageAnalyzer` even for `FOLLOW_UP`.
- **Analyzer:** Normalizes "N/A" to "Unknown Company".
