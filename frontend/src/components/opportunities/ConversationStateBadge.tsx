import { Badge } from "@/components/ui/badge"
import { MessageSquare, MessageCircle, CheckCheck } from "lucide-react"
import type { ConversationState } from "@/types"

interface ConversationStateBadgeProps {
  state: ConversationState | null
}

const stateConfig: Record<
  ConversationState,
  { label: string; variant: "default" | "secondary" | "outline"; icon: typeof MessageSquare }
> = {
  NEW_OPPORTUNITY: { label: "New", variant: "default", icon: MessageSquare },
  FOLLOW_UP: { label: "Follow-up", variant: "secondary", icon: MessageCircle },
  COURTESY_CLOSE: { label: "Courtesy", variant: "outline", icon: CheckCheck },
}

export function ConversationStateBadge({ state }: ConversationStateBadgeProps) {
  if (!state) return null

  const config = stateConfig[state]
  const Icon = config.icon

  return (
    <Badge variant={config.variant} className="gap-1">
      <Icon className="h-3 w-3" />
      {config.label}
    </Badge>
  )
}
