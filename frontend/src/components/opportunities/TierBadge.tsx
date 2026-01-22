import { Badge } from "@/components/ui/badge"
import { getTierLabel } from "@/lib/utils"
import type { OpportunityTier } from "@/types"

interface TierBadgeProps {
  tier: OpportunityTier | null
}

function getTierVariant(tier: OpportunityTier | null) {
  switch (tier) {
    case "HIGH_PRIORITY":
      return "success"
    case "INTERESANTE":
      return "warning"
    case "POCO_INTERESANTE":
      return "orange"
    case "NO_INTERESA":
      return "destructive"
    default:
      return "secondary"
  }
}

export function TierBadge({ tier }: TierBadgeProps) {
  if (!tier) return null

  return <Badge variant={getTierVariant(tier)}>{getTierLabel(tier)}</Badge>
}
