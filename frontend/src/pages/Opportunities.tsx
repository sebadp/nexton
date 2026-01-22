import { useOpportunities } from "@/hooks"
import { useAppStore } from "@/store"
import { OpportunityFilters, OpportunityList } from "@/components/opportunities"

export default function Opportunities() {
  const currentPage = useAppStore((state) => state.currentPage)
  const pageSize = useAppStore((state) => state.pageSize)
  const filters = useAppStore((state) => state.opportunityFilters)

  const skip = (currentPage - 1) * pageSize

  const { data, isLoading } = useOpportunities(skip, pageSize, filters)

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Opportunities</h1>
        <p className="text-muted-foreground">
          Browse and filter your LinkedIn opportunities
        </p>
      </div>

      <OpportunityFilters />
      <OpportunityList data={data} isLoading={isLoading} />
    </div>
  )
}
