import { Briefcase, Star, AlertTriangle, TrendingUp, X, RotateCcw } from "lucide-react"
import { Link } from "react-router-dom"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import type { OpportunityStats } from "@/types"

interface StatsCardsProps {
  stats?: OpportunityStats
  isLoading: boolean
}

export function StatsCards({ stats, isLoading }: StatsCardsProps) {
  const cards = [
    {
      title: "Total Opportunities",
      value: stats?.total_count ?? 0,
      icon: Briefcase,
      description: "All time",
    },
    {
      title: "High Priority",
      value: stats?.by_tier?.HIGH_PRIORITY ?? 0,
      icon: Star,
      description: "Top opportunities",
      className: "text-green-500",
    },
    {
      title: "Manual Review",
      value: stats?.pending_manual_review ?? 0,
      icon: AlertTriangle,
      description: "Needs attention",
      className: "text-amber-500",
      href: "/manual-review",
    },
    {
      title: "Declined",
      value: stats?.by_processing_status?.declined ?? 0,
      icon: X,
      description: "Auto-declined",
      className: "text-red-500",
    },
    {
      title: "Auto-responded",
      value: stats?.by_processing_status?.auto_responded ?? 0,
      icon: RotateCcw,
      description: "Follow-up answered",
      className: "text-blue-500",
    },
    {
      title: "Average Score",
      value: stats?.average_score ? Math.round(stats.average_score) : "-",
      icon: TrendingUp,
      description: "Overall match",
    },
  ]

  if (isLoading) {
    return (
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
        {Array.from({ length: 6 }).map((_, i) => (
          <Card key={i}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <Skeleton className="h-4 w-24" />
              <Skeleton className="h-4 w-4" />
            </CardHeader>
            <CardContent>
              <Skeleton className="h-8 w-16" />
              <Skeleton className="mt-1 h-3 w-20" />
            </CardContent>
          </Card>
        ))}
      </div>
    )
  }

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
      {cards.map((card) => {
        const content = (
          <Card className={card.href ? "cursor-pointer hover:bg-accent/50 transition-colors" : ""}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">{card.title}</CardTitle>
              <card.icon className={`h-4 w-4 text-muted-foreground ${card.className ?? ""}`} />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{card.value}</div>
              <p className="text-xs text-muted-foreground">{card.description}</p>
            </CardContent>
          </Card>
        )

        if (card.href) {
          return (
            <Link key={card.title} to={card.href}>
              {content}
            </Link>
          )
        }

        return <div key={card.title}>{content}</div>
      })}
    </div>
  )
}
