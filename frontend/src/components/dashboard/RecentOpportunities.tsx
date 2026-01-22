import { Link } from "react-router-dom"
import { ArrowRight } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { getTierLabel } from "@/lib/utils"
import type { Opportunity } from "@/types"

interface RecentOpportunitiesProps {
  opportunities?: Opportunity[]
  isLoading: boolean
}

function getTierVariant(tier: string | null) {
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

export function RecentOpportunities({
  opportunities,
  isLoading,
}: RecentOpportunitiesProps) {
  if (isLoading) {
    return (
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Recent Opportunities</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="flex items-center justify-between">
                <div className="space-y-1">
                  <Skeleton className="h-4 w-32" />
                  <Skeleton className="h-3 w-24" />
                </div>
                <Skeleton className="h-5 w-16" />
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>Recent Opportunities</CardTitle>
        <Button variant="ghost" size="sm" asChild>
          <Link to="/opportunities">
            View all
            <ArrowRight className="ml-2 h-4 w-4" />
          </Link>
        </Button>
      </CardHeader>
      <CardContent>
        {!opportunities || opportunities.length === 0 ? (
          <p className="text-center text-muted-foreground">
            No opportunities yet
          </p>
        ) : (
          <div className="space-y-4">
            {opportunities.slice(0, 5).map((opportunity) => (
              <Link
                key={opportunity.id}
                to={`/opportunities/${opportunity.id}`}
                className="flex items-center justify-between rounded-lg p-2 transition-colors hover:bg-accent"
              >
                <div className="space-y-1">
                  <p className="text-sm font-medium leading-none">
                    {opportunity.company || opportunity.recruiter_name}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {opportunity.role || "Role not specified"}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  {opportunity.total_score !== null && (
                    <span className="text-sm font-medium">
                      {opportunity.total_score}%
                    </span>
                  )}
                  {opportunity.tier && (
                    <Badge variant={getTierVariant(opportunity.tier)}>
                      {getTierLabel(opportunity.tier)}
                    </Badge>
                  )}
                </div>
              </Link>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
