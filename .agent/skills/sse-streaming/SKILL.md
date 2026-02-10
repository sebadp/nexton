---
name: Advanced SSE Streaming Patterns
description: Best practices for implementing Server-Sent Events (SSE) in FastAPI, specifically handling blocking synchronous code and granular progress updates.
---

# Advanced SSE Streaming Patterns

This skill covers how to implement robust Server-Sent Events (SSE) streaming in FastAPI, particularly when dealing with blocking synchronous operations (like LLM calls or heavy computation) that need to report granular progress.

## The Problem: Blocking the Event Loop

Standard `async` endpoints in FastAPI run on the main event loop. If you call a synchronous blocking function (e.g., `dspy.backward` or a CPU-intensive task) directly, you freeze the loop. No SSE events can be sent until the blocking function returns.

## The Solution: Threadpool + Queue Bridge

To stream progress from a blocking function:
1.  **Run in Threadpool**: Execute the blocking function in a separate thread using `starlette.concurrency.run_in_threadpool`.
2.  **Callback Interface**: The blocking function should accept an `on_progress` callback.
3.  **Thread-Safe Queue**: create an `asyncio.Queue` in the async handler.
4.  **Bridge Callback**: The callback puts items into the queue using `loop.call_soon_threadsafe`.
5.  **Consumer Loop**: The async handler consumes the queue while waiting for the threadpool task.

## Implementation Pattern

### 1. Blocking Service Method
Update your synchronous (or effectively blocking) code to accept a callback.

```python
from typing import Callable

class AnalysisPipeline:
    def execute(self, data: str, on_progress: Callable[[str, dict], None] | None = None):
        # ... logic ...
        if on_progress:
            on_progress("step_name", {"details": "..."})
        # ... more logic ...
```

### 2. Async Orchestrator
Bridge the gap in your service layer.

```python
import asyncio
from starlette.concurrency import run_in_threadpool

async def execute_with_streaming(self, data: str):
    queue = asyncio.Queue()
    loop = asyncio.get_running_loop()

    def on_progress(step: str, details: dict):
        # Thread-safe put
        loop.call_soon_threadsafe(queue.put_nowait, (step, details))

    # Start blocking task in thread
    task = asyncio.create_task(run_in_threadpool(
        self.pipeline.execute,
        data=data,
        on_progress=on_progress
    ))

    # Consume queue while task runs
    while not task.done() or not queue.empty():
        try:
             # Wait for event with short timeout to check task status frequently
            step, details = await asyncio.wait_for(queue.get(), timeout=0.1)
            yield {"event": "progress", "step": step, "details": details}
        except asyncio.TimeoutError:
            if task.done(): break
            continue

    # Get final result (re-raises exceptions from thread)
    result = await task
    yield {"event": "completed", "result": result}
```

## Frontend Handling (Nginx)
Ensure Nginx proxy buffering is **OFF** for SSE endpoints, otherwise events will be batched and arrive all at once.

```nginx
location /api/v1/stream {
    proxy_pass http://backend;
    proxy_buffering off;
    proxy_cache off;
    proxy_set_header Connection '';
    proxy_http_version 1.1;
    chunked_transfer_encoding off;
}
```

## Robust Data Serialization

When streaming data (especially complex objects from databases or third-party APIs), standard `json.dumps` often fails.

### Handling Non-Serializable Types
FastAPI's automatic serialization doesn't apply when you manually yield JSON strings. You must handle types like `datetime` yourself.

**Bad:**
```python
yield f"data: {json.dumps(event)}\n\n" # Fails with TypeError: Object of type datetime is not JSON serializable
```

**Good:**
```python
import json

# Use default=str to automatically convert datetime, UUIDs, etc. to strings
yield f"data: {json.dumps(event, default=str)}\n\n"
```

### Handling Non-ASCII Characters
By default, `json.dumps` escapes non-ASCII characters (e.g., "café" becomes "caf\u00e9"). This can break downstream parsers (like Docker logs or Go-based listeners) that expect raw UTF-8.

**Good:**
```python
# ensure_ascii=False outputs raw UTF-8 characters
yield f"data: {json.dumps(event, ensure_ascii=False, default=str)}\n\n"
```

## Text Sanitization

Systems with strict character set requirements (like some Docker log drivers or older terminals) may crash on obscure Unicode characters.

**Best Practice:**
Normalize text before streaming if you suspect incompatible characters using `unidecode`.

```python
# poetry add unidecode
from unidecode import unidecode

def sanitize_event(event: dict) -> dict:
    # Recursively clean strings in the event dict
    clean_event = {}
    for k, v in event.items():
        if isinstance(v, str):
            clean_event[k] = unidecode(v)
        else:
            clean_event[k] = v
    return clean_event
```

## Common Pitfalls
1.  **Queue Draining**: Always check `queue.empty()` after `task.done()` to capture final events emitted just before completion.
2.  **Exception Handling**: `await task` will re-raise exceptions from the thread. Wrap it in `try/except` to yield an error event to the client.
3.  **Typing**: Use `Callable[[str, dict], None]` for clear callback contracts.
4.  **JSON Encoding Errors**: Default `json.dumps` fails on `datetime` and other complex types. Use `default=str`.
5.  **Strict Character Sets**: Docker/Go logs may crash on extended Unicode. Use `ensure_ascii=False` or `unidecode` if necessary.
