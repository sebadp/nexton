# Plan de Mejora de UI Web - LinkedIn Agent

## Resumen Ejecutivo

La UI web actual no refleja la riqueza del sistema de clasificación del pipeline DSPy. Este plan detalla las mejoras necesarias para exponer todas las categorías y estados de mensajes.

---

## 1. Análisis de Brechas

### Estados del Backend vs Frontend Actual

| Backend (Pipeline) | Frontend Actual | Gap |
|-------------------|-----------------|-----|
| `processed` | `processed` | OK |
| `ignored` (COURTESY_CLOSE) | No existe | **FALTA** |
| `declined` (Hard filters failed) | No existe | **FALTA** |
| `manual_review` (FOLLOW_UP) | No existe | **FALTA** |
| `auto_responded` (FOLLOW_UP) | No existe | **FALTA** |

### Conversation States del Backend vs Frontend

| Backend | Frontend | Gap |
|---------|----------|-----|
| `NEW_OPPORTUNITY` | No existe | **FALTA** |
| `FOLLOW_UP` | No existe | **FALTA** |
| `COURTESY_CLOSE` | No existe | **FALTA** |

### Información adicional no mostrada

- **Hard Filters Results**: work_week, salary, tech_match, remote_policy, rejection_criteria
- **Follow-up Analysis**: question_type, can_auto_respond, requires_context
- **Manual Review Reason**: Por qué requiere revisión humana
- **Scoring Breakdown**: Desglose de scores por categoría

---

## 2. Cambios en el Backend

### 2.1 Actualizar Modelo de Opportunity (Base de Datos)

```python
# app/database/models.py - Nuevos campos
class Opportunity(Base):
    # ... campos existentes ...

    # Nuevos campos para clasificación
    conversation_state: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    # Valores: NEW_OPPORTUNITY, FOLLOW_UP, COURTESY_CLOSE

    processing_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    # Valores: processed, ignored, declined, manual_review, auto_responded

    requires_manual_review: Mapped[bool] = mapped_column(Boolean, default=False)
    manual_review_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Hard filter results (JSON)
    hard_filter_results: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Follow-up analysis (JSON)
    follow_up_analysis: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
```

### 2.2 Actualizar API Schema

```python
# app/api/v1/schemas.py
class OpportunityResponse(BaseModel):
    # ... campos existentes ...

    # Nuevos campos
    conversation_state: Optional[str] = None  # NEW_OPPORTUNITY, FOLLOW_UP, COURTESY_CLOSE
    processing_status: Optional[str] = None   # processed, ignored, declined, manual_review, auto_responded
    requires_manual_review: bool = False
    manual_review_reason: Optional[str] = None
    hard_filter_results: Optional[dict] = None
    follow_up_analysis: Optional[dict] = None
```

### 2.3 Actualizar Stats API

```python
# app/api/v1/opportunities.py - Nuevas estadísticas
class OpportunityStats(BaseModel):
    total_count: int
    by_tier: dict
    by_status: dict
    by_conversation_state: dict  # NUEVO
    by_processing_status: dict   # NUEVO
    pending_manual_review: int   # NUEVO
    average_score: Optional[float]
    highest_score: Optional[int]
    lowest_score: Optional[int]
```

### 2.4 Nuevo Endpoint: Manual Review Queue

```python
# app/api/v1/opportunities.py
@router.get("/manual-review", response_model=OpportunityListResponse)
async def get_manual_review_queue(
    skip: int = 0,
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
):
    """Get opportunities that require manual review."""
    repo = OpportunityRepository(db)
    opportunities = await repo.get_manual_review_queue(skip, limit)
    total = await repo.count_manual_review()
    return OpportunityListResponse(items=opportunities, total=total, skip=skip, limit=limit)
```

---

## 3. Cambios en el Frontend

### 3.1 Actualizar Types

```typescript
// frontend/src/types/opportunity.ts

export type ConversationState = "NEW_OPPORTUNITY" | "FOLLOW_UP" | "COURTESY_CLOSE"

export type ProcessingStatus =
  | "processed"
  | "ignored"
  | "declined"
  | "manual_review"
  | "auto_responded"

export type QuestionType =
  | "SALARY"
  | "AVAILABILITY"
  | "EXPERIENCE"
  | "INTEREST"
  | "SCHEDULING"
  | "NONE"
  | "OTHER"

export interface HardFilterResults {
  work_week: {
    status: "CONFIRMED" | "NOT_MENTIONED" | "FIVE_DAY" | "UNKNOWN"
    passed: boolean
    reason?: string
  }
  salary: {
    passed: boolean
    offered_min?: number
    offered_max?: number
    required_min: number
  }
  tech_match: {
    passed: boolean
    match_percentage: number
    matched_skills: string[]
    missing_skills: string[]
  }
  remote_policy: {
    passed: boolean
    offered: string
    required: string
  }
  rejection_criteria: {
    passed: boolean
    matched_criteria?: string
  }
  overall_passed: boolean
  should_decline: boolean
}

export interface FollowUpAnalysis {
  question_type: QuestionType
  can_auto_respond: boolean
  requires_context: boolean
  reasoning: string
  suggested_response?: string
}

export interface Opportunity {
  // ... campos existentes ...

  // Nuevos campos
  conversation_state: ConversationState | null
  processing_status: ProcessingStatus | null
  requires_manual_review: boolean
  manual_review_reason: string | null
  hard_filter_results: HardFilterResults | null
  follow_up_analysis: FollowUpAnalysis | null
}

export interface OpportunityStats {
  // ... campos existentes ...
  by_conversation_state: Record<ConversationState, number>
  by_processing_status: Record<ProcessingStatus, number>
  pending_manual_review: number
}
```

### 3.2 Nuevos Componentes

#### 3.2.1 ConversationStateBadge

```tsx
// frontend/src/components/opportunities/ConversationStateBadge.tsx
import { Badge } from "@/components/ui/badge"
import { MessageSquare, MessageCircle, CheckCheck } from "lucide-react"
import type { ConversationState } from "@/types"

const stateConfig: Record<ConversationState, { label: string; variant: string; icon: any }> = {
  NEW_OPPORTUNITY: { label: "New Opportunity", variant: "default", icon: MessageSquare },
  FOLLOW_UP: { label: "Follow-up", variant: "secondary", icon: MessageCircle },
  COURTESY_CLOSE: { label: "Courtesy", variant: "outline", icon: CheckCheck },
}

export function ConversationStateBadge({ state }: { state: ConversationState | null }) {
  if (!state) return null
  const config = stateConfig[state]
  const Icon = config.icon

  return (
    <Badge variant={config.variant as any} className="gap-1">
      <Icon className="h-3 w-3" />
      {config.label}
    </Badge>
  )
}
```

#### 3.2.2 ProcessingStatusBadge

```tsx
// frontend/src/components/opportunities/ProcessingStatusBadge.tsx
import { Badge } from "@/components/ui/badge"
import { Check, X, AlertTriangle, RotateCcw, Minus } from "lucide-react"
import type { ProcessingStatus } from "@/types"

const statusConfig: Record<ProcessingStatus, { label: string; color: string; icon: any }> = {
  processed: { label: "Processed", color: "bg-green-500", icon: Check },
  declined: { label: "Declined", color: "bg-red-500", icon: X },
  manual_review: { label: "Manual Review", color: "bg-amber-500", icon: AlertTriangle },
  auto_responded: { label: "Auto-responded", color: "bg-blue-500", icon: RotateCcw },
  ignored: { label: "Ignored", color: "bg-gray-400", icon: Minus },
}

export function ProcessingStatusBadge({ status }: { status: ProcessingStatus | null }) {
  if (!status) return null
  const config = statusConfig[status]
  const Icon = config.icon

  return (
    <Badge className={`${config.color} text-white gap-1`}>
      <Icon className="h-3 w-3" />
      {config.label}
    </Badge>
  )
}
```

#### 3.2.3 HardFiltersCard

```tsx
// frontend/src/components/opportunities/HardFiltersCard.tsx
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Check, X, AlertCircle } from "lucide-react"
import type { HardFilterResults } from "@/types"

export function HardFiltersCard({ results }: { results: HardFilterResults | null }) {
  if (!results) return null

  const filters = [
    { name: "Work Week", passed: results.work_week.passed, detail: results.work_week.status },
    { name: "Salary", passed: results.salary.passed, detail: results.salary.offered_min ? `$${results.salary.offered_min}k+` : "Not mentioned" },
    { name: "Tech Match", passed: results.tech_match.passed, detail: `${results.tech_match.match_percentage}%` },
    { name: "Remote Policy", passed: results.remote_policy.passed, detail: results.remote_policy.offered },
    { name: "Rejection Criteria", passed: results.rejection_criteria.passed, detail: results.rejection_criteria.matched_criteria || "None" },
  ]

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          {results.overall_passed ? (
            <Check className="h-5 w-5 text-green-500" />
          ) : (
            <X className="h-5 w-5 text-red-500" />
          )}
          Hard Filters
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {filters.map((filter) => (
            <div key={filter.name} className="flex items-center justify-between text-sm">
              <span className="flex items-center gap-2">
                {filter.passed ? (
                  <Check className="h-4 w-4 text-green-500" />
                ) : (
                  <X className="h-4 w-4 text-red-500" />
                )}
                {filter.name}
              </span>
              <span className="text-muted-foreground">{filter.detail}</span>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
```

#### 3.2.4 FollowUpAnalysisCard

```tsx
// frontend/src/components/opportunities/FollowUpAnalysisCard.tsx
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { MessageCircle, Bot, User } from "lucide-react"
import type { FollowUpAnalysis } from "@/types"

const questionTypeLabels: Record<string, string> = {
  SALARY: "Salary Question",
  AVAILABILITY: "Availability Question",
  EXPERIENCE: "Experience Question",
  INTEREST: "Interest Question",
  SCHEDULING: "Scheduling Request",
  NONE: "No Question",
  OTHER: "Other",
}

export function FollowUpAnalysisCard({ analysis }: { analysis: FollowUpAnalysis | null }) {
  if (!analysis) return null

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <MessageCircle className="h-5 w-5" />
          Follow-up Analysis
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium">Question Type</span>
          <Badge>{questionTypeLabels[analysis.question_type]}</Badge>
        </div>

        <div className="flex items-center justify-between">
          <span className="text-sm font-medium">Response Mode</span>
          {analysis.can_auto_respond ? (
            <Badge className="bg-blue-500 text-white gap-1">
              <Bot className="h-3 w-3" />
              Auto-respond
            </Badge>
          ) : (
            <Badge className="bg-amber-500 text-white gap-1">
              <User className="h-3 w-3" />
              Manual Review
            </Badge>
          )}
        </div>

        <div className="text-sm">
          <span className="font-medium">Reasoning:</span>
          <p className="text-muted-foreground mt-1">{analysis.reasoning}</p>
        </div>

        {analysis.suggested_response && (
          <div className="text-sm">
            <span className="font-medium">Suggested Response:</span>
            <p className="text-muted-foreground mt-1 p-2 bg-muted rounded">
              {analysis.suggested_response}
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
```

#### 3.2.5 ManualReviewAlert

```tsx
// frontend/src/components/opportunities/ManualReviewAlert.tsx
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { AlertTriangle } from "lucide-react"

export function ManualReviewAlert({ reason }: { reason: string | null }) {
  if (!reason) return null

  return (
    <Alert variant="warning" className="border-amber-500 bg-amber-50">
      <AlertTriangle className="h-4 w-4 text-amber-500" />
      <AlertTitle>Manual Review Required</AlertTitle>
      <AlertDescription>{reason}</AlertDescription>
    </Alert>
  )
}
```

### 3.3 Actualizar Dashboard

#### 3.3.1 Nuevas Stats Cards

```tsx
// frontend/src/components/dashboard/StatsCards.tsx - Actualizado
const cards = [
  { title: "Total Opportunities", value: stats?.total_count ?? 0, icon: Briefcase },
  { title: "High Priority", value: stats?.by_tier?.HIGH_PRIORITY ?? 0, icon: Star, className: "text-green-500" },
  { title: "Manual Review", value: stats?.pending_manual_review ?? 0, icon: AlertTriangle, className: "text-amber-500" },
  { title: "Declined", value: stats?.by_processing_status?.declined ?? 0, icon: X, className: "text-red-500" },
  { title: "Auto-responded", value: stats?.by_processing_status?.auto_responded ?? 0, icon: Bot, className: "text-blue-500" },
  { title: "Average Score", value: stats?.average_score ? Math.round(stats.average_score) : "-", icon: TrendingUp },
]
```

#### 3.3.2 Nuevo Chart: Processing Status Distribution

```tsx
// frontend/src/components/dashboard/ProcessingStatusChart.tsx
// Pie chart showing distribution of processing statuses
```

#### 3.3.3 Nuevo Chart: Conversation State Distribution

```tsx
// frontend/src/components/dashboard/ConversationStateChart.tsx
// Pie chart showing NEW_OPPORTUNITY vs FOLLOW_UP vs COURTESY_CLOSE
```

### 3.4 Nueva Página: Manual Review Queue

```tsx
// frontend/src/pages/ManualReview.tsx
import { useManualReviewQueue } from "@/hooks"
import { ManualReviewCard } from "@/components/manual-review"

export default function ManualReview() {
  const { data, isLoading } = useManualReviewQueue()

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Manual Review Queue</h1>
        <p className="text-muted-foreground">
          Messages that require your attention
        </p>
      </div>

      <div className="space-y-4">
        {data?.items.map((opportunity) => (
          <ManualReviewCard key={opportunity.id} opportunity={opportunity} />
        ))}
      </div>
    </div>
  )
}
```

### 3.5 Actualizar Filtros de Opportunities

```tsx
// frontend/src/components/opportunities/OpportunityFilters.tsx
// Agregar filtros para:
// - Conversation State (NEW_OPPORTUNITY, FOLLOW_UP, COURTESY_CLOSE)
// - Processing Status (processed, declined, manual_review, auto_responded, ignored)
// - Requires Manual Review (checkbox)
```

### 3.6 Actualizar OpportunityDetail

```tsx
// frontend/src/pages/OpportunityDetail.tsx
// Agregar secciones:
// - ConversationStateBadge y ProcessingStatusBadge en el header
// - ManualReviewAlert si requires_manual_review
// - HardFiltersCard si hay resultados
// - FollowUpAnalysisCard si conversation_state === "FOLLOW_UP"
```

---

## 4. Navegación Actualizada

```tsx
// frontend/src/components/layout/Sidebar.tsx
const navigation = [
  { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { name: "Opportunities", href: "/opportunities", icon: Briefcase },
  { name: "Manual Review", href: "/manual-review", icon: AlertTriangle, badge: pendingCount },
  { name: "Responses", href: "/responses", icon: MessageSquare },
  { name: "Profile", href: "/profile", icon: User },
  { name: "Settings", href: "/settings", icon: Settings },
]
```

---

## 5. Priorización de Implementación

### Fase 1: Backend (Crítico)
1. [ ] Actualizar modelo Opportunity con nuevos campos
2. [ ] Crear migración de base de datos
3. [ ] Actualizar processing_tasks.py para guardar nuevos campos
4. [ ] Actualizar OpportunityResponse schema
5. [ ] Actualizar OpportunityStats con nuevas métricas
6. [ ] Crear endpoint manual-review queue

### Fase 2: Frontend - Types y API (Crítico)
1. [ ] Actualizar types/opportunity.ts
2. [ ] Actualizar API client
3. [ ] Actualizar hooks

### Fase 3: Frontend - Componentes Base (Alto)
1. [ ] ConversationStateBadge
2. [ ] ProcessingStatusBadge
3. [ ] ManualReviewAlert
4. [ ] HardFiltersCard
5. [ ] FollowUpAnalysisCard

### Fase 4: Frontend - Integración (Alto)
1. [ ] Actualizar OpportunityCard
2. [ ] Actualizar OpportunityDetail
3. [ ] Actualizar StatsCards
4. [ ] Actualizar filtros

### Fase 5: Frontend - Nuevas Páginas (Medio)
1. [ ] Crear página ManualReview
2. [ ] Agregar ProcessingStatusChart al dashboard
3. [ ] Agregar ConversationStateChart al dashboard
4. [ ] Actualizar navegación con badge de pending review

### Fase 6: Polish (Bajo)
1. [ ] Animaciones y transiciones
2. [ ] Empty states personalizados por categoría
3. [ ] Tooltips explicativos
4. [ ] Acciones rápidas en ManualReview

---

## 6. Wireframes

### Dashboard Actualizado

```
+--------------------------------------------------+
|  Dashboard                                        |
+--------------------------------------------------+
| +----------+ +----------+ +----------+ +--------+ |
| | Total    | | High     | | Manual   | | Auto   | |
| | 156      | | Priority | | Review   | | Resp.  | |
| |          | | 23       | | 12 (!)   | | 45     | |
| +----------+ +----------+ +----------+ +--------+ |
|                                                   |
| +------------------------+ +--------------------+ |
| |   Tier Distribution    | | Processing Status  | |
| |   [Pie Chart]          | | [Pie Chart]        | |
| +------------------------+ +--------------------+ |
|                                                   |
| Recent Opportunities                              |
| +-----------------------------------------------+ |
| | Company A - NEW_OPPORTUNITY - Processed       | |
| | Company B - FOLLOW_UP - Manual Review (!)     | |
| | Recruiter C - COURTESY_CLOSE - Ignored        | |
| +-----------------------------------------------+ |
+--------------------------------------------------+
```

### Manual Review Page

```
+--------------------------------------------------+
|  Manual Review Queue                    12 items  |
+--------------------------------------------------+
| +-----------------------------------------------+ |
| | [!] Follow-up from John Doe                   | |
| | Question: "What's your availability?"         | |
| | Type: SCHEDULING | Requires: Human judgment   | |
| | [View] [Respond] [Dismiss]                    | |
| +-----------------------------------------------+ |
| | [!] Follow-up from Jane Smith                 | |
| | Question: "Are you interested?"               | |
| | Type: INTEREST | Requires: Context needed     | |
| | [View] [Respond] [Dismiss]                    | |
| +-----------------------------------------------+ |
+--------------------------------------------------+
```

### Opportunity Detail Actualizado

```
+--------------------------------------------------+
|  < Back                                           |
+--------------------------------------------------+
| Company Name                                      |
| Recruiter: John Doe                              |
| [NEW_OPPORTUNITY] [Processed] [HIGH_PRIORITY]    |
|                                                   |
| +-----------------------------------------------+ |
| | (!) MANUAL REVIEW REQUIRED                    | |
| | Reason: Question requires conversation context | |
| +-----------------------------------------------+ |
|                                                   |
| Hard Filters                     Match Score: 85  |
| +------------------------+  +------------------+  |
| | [✓] Work Week: 4-day  |  | Tech: 35/40      |  |
| | [✓] Salary: $120k     |  | Salary: 25/25    |  |
| | [✓] Tech Match: 85%   |  | Seniority: 18/20 |  |
| | [✓] Remote: Yes       |  | Company: 7/15    |  |
| | [✓] No rejection      |  |                  |  |
| +------------------------+  +------------------+  |
|                                                   |
| Original Message                                  |
| +-----------------------------------------------+ |
| | "Hi Sebastian, we have a Senior Python..."    | |
| +-----------------------------------------------+ |
|                                                   |
| AI Response                                       |
| +-----------------------------------------------+ |
| | "Hola John, gracias por contactarme..."       | |
| | [Edit] [Approve] [Decline]                    | |
| +-----------------------------------------------+ |
+--------------------------------------------------+
```

---

## 7. Estimación de Esfuerzo

| Fase | Archivos | Complejidad | Estimación |
|------|----------|-------------|------------|
| 1. Backend | 5 | Media | 4-6 horas |
| 2. Frontend Types | 3 | Baja | 1-2 horas |
| 3. Componentes Base | 5 | Media | 3-4 horas |
| 4. Integración | 4 | Media | 3-4 horas |
| 5. Nuevas Páginas | 4 | Media | 4-5 horas |
| 6. Polish | - | Baja | 2-3 horas |

**Total estimado: 17-24 horas de desarrollo**

---

## 8. Testing Requerido

1. **Unit Tests**: Nuevos componentes de badge
2. **Integration Tests**: Flujo de manual review
3. **E2E Tests**:
   - Dashboard muestra stats correctas
   - Filtros funcionan con nuevas categorías
   - Manual review queue funciona
4. **Visual Tests**: Screenshots de nuevos estados
