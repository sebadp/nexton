---
name: Database Imports
description: Correct database session and connection imports for the Nexton project
---

# Database Imports Guide

## Overview

This skill documents the correct way to import database components in the Nexton project to avoid `ModuleNotFoundError` issues.

## Database Module Structure

The database module is located at `app/database/` with the following key files:

| File | Purpose |
|------|---------|
| `base.py` | Engine, session factory, and base model |
| `models.py` | SQLAlchemy ORM models |
| `repositories.py` | Data access layer |
| `dependencies.py` | FastAPI dependency injection |

## Correct Import Patterns

### ✅ Session Factory (for async context managers)

```python
from app.database.base import AsyncSessionLocal

async with AsyncSessionLocal() as db:
    # Use db session here
    pass
```

### ✅ Dependency Injection (for FastAPI endpoints)

```python
from app.database.base import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

@router.get("/items")
async def get_items(db: AsyncSession = Depends(get_db)):
    # db is automatically managed
    pass
```

### ✅ Base Model (for creating new models)

```python
from app.database.base import Base
```

### ✅ Engine Access (rarely needed)

```python
from app.database.base import engine
```

## Common Mistakes to Avoid

### ❌ Wrong: Non-existent module

```python
# This file does NOT exist!
from app.database.session import async_session_factory  # ModuleNotFoundError
```

### ❌ Wrong: Incorrect variable name

```python
from app.database.base import async_session_factory  # Does not exist
```

### ✅ Correct

```python
from app.database.base import AsyncSessionLocal  # Correct name
```

## Quick Reference

| Need | Import |
|------|--------|
| Create session manually | `from app.database.base import AsyncSessionLocal` |
| FastAPI dependency | `from app.database.base import get_db` |
| Base model class | `from app.database.base import Base` |
| Database engine | `from app.database.base import engine` |
| ORM models | `from app.database.models import User, Opportunity, ...` |
| Repositories | `from app.database.repositories import UserRepository, ...` |
