---
description: Best practices for implementing observability and tracing in the Nexton application
---

# Observability Best Practices

This guide outlines the standards for implementing observability, tracing, and metrics in the Nexton application.

## 1. Tracing Decorator

**ALWAYS** import the `observe` decorator from `app.observability`.

**❌ INCORRECT:**
```python
# Do NOT import directly from langfuse.decorators
from langfuse.decorators import observe

# Do NOT define fallback decorators locally
try:
    from langfuse.decorators import observe
except ImportError:
    def observe(*args, **kwargs): ...
```

**✅ CORRECT:**
```python
from app.observability import observe

@observe(name="module.function_name")
def my_function():
    ...
```

### Why?
The `app.observability` module handles:
- **Centralized Configuration**: Ensures tracing is enabled/disabled based on environment variables.
- **Unified Backend**: Routes traces to the correct backend (Langfuse, Jaeger, etc.) without changing application code.
- **Fallback Logic**: Provides a safe no-op implementation if tracing dependencies are missing, preventing runtime errors.

## 1.1 Deprecated Components

**❌ DO NOT USE:** `CallbackHandler` from `langfuse.callback` is deprecated/removed in newer SDK versions.
Instead, rely on the `@observe` decorator, which automatically handles context and hierarchy.

## 2. Span Naming Convention

Use dot-notation for span names to create a clear hierarchy.

Format: `{module_type}.{module_name}.{method}`

Examples:
- `api.scraping.trigger` (API Level)
- `db.opportunity.create` (Database Level)
- `dspy.pipeline.forward` (DSPy Module Level)
- `dspy.scorer.score` (Specific Step)

## 3. Granular Instrumentation

Instrument at the appropriate level of granularity.

### High-Level (Must Have)
- API Endpoints
- Public Service Methods
- Background Tasks

### thorough-Level (Recommended for Core Logic)
- **DSPy Modules**: Instrument `forward` methods of all DSPy modules (`dspy_modules/*.py`).
- **Complex Logic**: Instrument key decision-making functions (e.g., `apply_hard_filters`).
- **External Calls**: Instrument calls to 3rd party APIs if not auto-instrumented.

### Attributes
Add meaningful attributes to spans to aid debugging.

```python
from app.observability import add_span_attributes

@observe(name="my.function")
def my_function(user_id: str):
    add_span_attributes(user_id=user_id)
    ...
```

## 4. Metrics

Use the `app.observability.metrics` module for counters, gauges, and histograms.

**✅ CORRECT:**
```python
from app.observability.metrics import track_opportunity_created

track_opportunity_created(source="linkedin", status="new")
```

## 5. Context Propagation with Async/Threadpool

When using `run_in_threadpool` (or executing synchronous code on a background thread) within an async function, the OpenTelemetry/Langfuse trace context is **NOT** automatically propagated. This leads to broken traces (orphaned root spans).

**❌ INCORRECT (Broken Trace Hierarchy):**

```python
from starlette.concurrency import run_in_threadpool

# Trace context is LOST here; my_blocking_function starts a NEW trace.
result = await run_in_threadpool(my_blocking_function, arg1, arg2)
```

**✅ CORRECT (Preserved Trace Hierarchy):**

```python
from contextvars import copy_context
from starlette.concurrency import run_in_threadpool

# Capture the current context (snapshot of trace ID, baggage, etc.)
ctx = copy_context()

# Run the function within the captured context on the thread
result = await run_in_threadpool(ctx.run, my_blocking_function, arg1, arg2)
```

### Explanation
- `copy_context()` creates a snapshot of the current `ContextVar` state.
- `ctx.run(func, *args)` executes the function *using* that context.
- Passing `ctx.run` to the threadpool ensures the blocking function inherits the parent trace.
