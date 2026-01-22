import { Badge } from "@/components/ui/badge"
import { Check, X, AlertTriangle, RotateCcw, Minus } from "lucide-react"
import type { ProcessingStatus } from "@/types"

interface ProcessingStatusBadgeProps {
  status: ProcessingStatus | null
}

const statusConfig: Record<
  ProcessingStatus,
  { label: string; variant: "success" | "destructive" | "amber" | "blue" | "gray"; icon: typeof Check }
> = {
  processed: { label: "Processed", variant: "success", icon: Check },
  declined: { label: "Declined", variant: "destructive", icon: X },
  manual_review: { label: "Manual Review", variant: "amber", icon: AlertTriangle },
  auto_responded: { label: "Auto-responded", variant: "blue", icon: RotateCcw },
  ignored: { label: "Ignored", variant: "gray", icon: Minus },
}

export function ProcessingStatusBadge({ status }: ProcessingStatusBadgeProps) {
  if (!status) return null

  const config = statusConfig[status]
  const Icon = config.icon

  return (
    <Badge variant={config.variant} className="gap-1">
      <Icon className="h-3 w-3" />
      {config.label}
    </Badge>
  )
}
