import { useOpportunityStats, useOpportunities } from "@/hooks"
import { StatsCards, TierChart, RecentOpportunities, ScrapeButton } from "@/components/dashboard"

export default function Dashboard() {
  const { data: stats, isLoading: statsLoading } = useOpportunityStats()
  const { data: opportunitiesData, isLoading: opportunitiesLoading } =
    useOpportunities(0, 5, { sort_by: "created_at", sort_order: "desc" })

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
          <p className="text-muted-foreground">
            Overview of your LinkedIn opportunities
          </p>
        </div>
      </div>

      <ScrapeButton />

      <StatsCards stats={stats} isLoading={statsLoading} />

      <div className="grid gap-6 md:grid-cols-2">
        <TierChart stats={stats} isLoading={statsLoading} />
        <RecentOpportunities
          opportunities={opportunitiesData?.items}
          isLoading={opportunitiesLoading}
        />
      </div>
    </div>
  )
}
