---
description: Toast notification system for user feedback in the frontend
---

# Toast Notifications Skill

System for showing user-friendly toast notifications for async operations like scraping.

## Components

### Backend (`app/services/scraping_service.py`)

Returns structured result with `status` and `message`:

```python
results = {
    "status": "success" | "no_messages" | "error",
    "message": "User-friendly message in Spanish",
    ...
}
```

**Message patterns:**
- Success: `"✅ Scraping completado. Se crearon N nuevas oportunidades."`
- No messages: `"No hay mensajes nuevos sin leer en LinkedIn."`
- Login error: `"❌ Error de autenticación: No se pudo iniciar sesión..."`
- Timeout: `"❌ LinkedIn no respondió a tiempo..."`
- Session expired: `"❌ La sesión de LinkedIn expiró..."`

### Frontend Hook (`src/hooks/useToast.ts`)

Standard shadcn/ui toast implementation:

```typescript
import { toast } from "@/hooks"

// Success (green)
toast({ variant: "success", title: "Éxito", description: "Mensaje" })

// Error (red)
toast({ variant: "destructive", title: "Error", description: "Mensaje" })

// Default (neutral)
toast({ title: "Info", description: "Mensaje" })
```

### Toaster Component (`src/components/ui/toaster.tsx`)

Add to root layout:

```tsx
import { Toaster } from "@/components/ui/toaster"

function App() {
  return (
    <>
      <YourRoutes />
      <Toaster />
    </>
  )
}
```

## Usage Pattern

```typescript
const handleAction = async () => {
  try {
    const result = await mutation.mutateAsync(params)

    if (result.status === "failed") {
      toast({ variant: "destructive", title: "Error", description: result.message })
    } else {
      toast({ variant: "success", title: "Éxito", description: result.message })
    }
  } catch (error) {
    toast({ variant: "destructive", title: "Error", description: error.message })
  }
}
```

## Files

- `frontend/src/hooks/useToast.ts` - Toast state management hook
- `frontend/src/components/ui/toast.tsx` - Toast UI components
- `frontend/src/components/ui/toaster.tsx` - Toast container
- `app/services/scraping_service.py` - Backend message generation
