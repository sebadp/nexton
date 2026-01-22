import { Link } from "react-router-dom"
import { MapPin, Briefcase, Calendar } from "lucide-react"
import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { TierBadge } from "./TierBadge"
import { ScoreBar } from "./ScoreBar"
import { formatDate, formatCurrency } from "@/lib/utils"
import type { Opportunity } from "@/types"

interface OpportunityCardProps {
  opportunity: Opportunity
}

export function OpportunityCard({ opportunity }: OpportunityCardProps) {
  return (
    <Link to={`/opportunities/${opportunity.id}`}>
      <Card className="transition-shadow hover:shadow-md">
        <CardHeader className="pb-2">
          <div className="flex items-start justify-between">
            <div className="space-y-1">
              <h3 className="font-semibold leading-none">
                {opportunity.company || "Unknown Company"}
              </h3>
              <p className="text-sm text-muted-foreground">
                {opportunity.recruiter_name}
              </p>
            </div>
            <TierBadge tier={opportunity.tier} />
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-wrap gap-2 text-sm text-muted-foreground">
            {opportunity.role && (
              <div className="flex items-center gap-1">
                <Briefcase className="h-3 w-3" />
                <span>{opportunity.role}</span>
              </div>
            )}
            {opportunity.location && (
              <div className="flex items-center gap-1">
                <MapPin className="h-3 w-3" />
                <span>{opportunity.location}</span>
              </div>
            )}
            {opportunity.remote_policy && (
              <Badge variant="outline" className="text-xs">
                {opportunity.remote_policy}
              </Badge>
            )}
          </div>

          {(opportunity.salary_min || opportunity.salary_max) && (
            <p className="text-sm font-medium">
              {opportunity.salary_min && opportunity.salary_max
                ? `${formatCurrency(opportunity.salary_min, opportunity.currency || "USD")} - ${formatCurrency(opportunity.salary_max, opportunity.currency || "USD")}`
                : opportunity.salary_min
                  ? `From ${formatCurrency(opportunity.salary_min, opportunity.currency || "USD")}`
                  : `Up to ${formatCurrency(opportunity.salary_max!, opportunity.currency || "USD")}`}
            </p>
          )}

          {opportunity.tech_stack && opportunity.tech_stack.length > 0 && (
            <div className="flex flex-wrap gap-1">
              {opportunity.tech_stack.slice(0, 5).map((tech) => (
                <Badge key={tech} variant="secondary" className="text-xs">
                  {tech}
                </Badge>
              ))}
              {opportunity.tech_stack.length > 5 && (
                <Badge variant="secondary" className="text-xs">
                  +{opportunity.tech_stack.length - 5}
                </Badge>
              )}
            </div>
          )}

          <ScoreBar score={opportunity.total_score} label="Match Score" />

          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <div className="flex items-center gap-1">
              <Calendar className="h-3 w-3" />
              <span>{formatDate(opportunity.created_at)}</span>
            </div>
            <Badge
              variant={
                opportunity.status === "processed" ? "default" : "secondary"
              }
              className="text-xs"
            >
              {opportunity.status}
            </Badge>
          </div>
        </CardContent>
      </Card>
    </Link>
  )
}
