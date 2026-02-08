---
description: Best practices for implementing validations on both frontend and backend
---

# Dual-Side Validation Best Practices

## Core Principle

> **Never trust the client. Always validate on the server.**
>
> But also: **Provide great UX by validating early on the client.**

---

## Validation Layers

### 1. Frontend Validation (UX)
**Purpose:** Fast feedback, better user experience, prevent obvious mistakes

```typescript
// Example: Check before showing delete dialog
const { data: response } = useResponse(opportunityId)

const handleDelete = () => {
  if (response) {
    // Show enhanced warning dialog
    setWarningDialogOpen(true)
  } else {
    // Show simple confirmation
    setConfirmDialogOpen(true)
  }
}
```

**When to use:**
- Form validation (required fields, formats)
- Pre-flight checks before destructive actions
- Optimistic UI updates
- Showing contextual warnings

### 2. Backend Validation (Security)
**Purpose:** Data integrity, security, business rules enforcement

```python
@router.delete("/{id}")
async def delete_item(
    id: int,
    force: bool = Query(False),  # Explicit confirmation
    db: AsyncSession = Depends(get_db),
):
    # Always check dependencies
    has_children = await check_dependencies(db, id)

    if has_children and not force:
        raise HTTPException(
            status_code=409,  # Conflict
            detail={"message": "Item has dependencies", "count": has_children}
        )
```

**When to use:**
- ALL destructive operations (DELETE, significant UPDATE)
- Business rule enforcement
- Data integrity checks
- Permission/authorization checks

---

## HTTP Status Codes for Validation

| Code | Meaning | Use Case |
|------|---------|----------|
| 400 | Bad Request | Invalid input format |
| 403 | Forbidden | No permission |
| 404 | Not Found | Resource doesn't exist |
| 409 | Conflict | Would violate business rule |
| 422 | Unprocessable | Semantically invalid |

---

## Destructive Operation Pattern

### Backend

```python
@router.delete("/{id}")
async def delete(id: int, force: bool = False, confirm: str = None):
    item = await get_item(id)

    # 1. Check if deletion has consequences
    consequences = await get_deletion_consequences(id)

    # 2. Require explicit confirmation if consequences exist
    if consequences and not force:
        return JSONResponse(
            status_code=409,
            content={
                "action_required": "confirm",
                "consequences": consequences,
                "confirm_url": f"/items/{id}?force=true"
            }
        )

    # 3. Proceed with deletion
    await delete_with_cascade(id)
    return Response(status_code=204)
```

### Frontend

```typescript
async function deleteItem(id: number, force = false): Promise<void> {
  try {
    await api.delete(`/items/${id}`, { params: { force } })
  } catch (error) {
    if (error.response?.status === 409) {
      // Show consequences to user and ask for confirmation
      const confirmed = await showConfirmDialog(error.response.data.consequences)
      if (confirmed) {
        return deleteItem(id, true)  // Retry with force
      }
    }
    throw error
  }
}
```

---

## Pre-Delete Info Endpoint Pattern

For complex delete scenarios, create an info endpoint:

```python
@router.get("/{id}/delete-info")
async def get_delete_info(id: int):
    """Get information needed before deleting."""
    return {
        "can_delete": True,
        "has_dependencies": True,
        "dependencies": [
            {"type": "pending_response", "id": 1, "preview": "..."}
        ],
        "warnings": ["This will also delete 1 pending response"]
    }
```

Frontend calls this before showing the delete dialog to personalize the warning.

---

## Checklist for New Destructive Operations

- [ ] Frontend shows appropriate confirmation dialog
- [ ] Frontend shows warnings if related data will be affected
- [ ] Backend validates the operation can be performed
- [ ] Backend checks for dependencies/related data
- [ ] Backend returns 409 Conflict if confirmation needed
- [ ] Backend supports `force=true` to bypass soft checks
- [ ] Both sides handle errors gracefully
