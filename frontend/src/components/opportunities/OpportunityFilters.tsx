import { Search, X } from "lucide-react"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { useAppStore } from "@/store"
import type { OpportunityTier, OpportunityStatus } from "@/types"

const tiers: { value: OpportunityTier; label: string }[] = [
  { value: "HIGH_PRIORITY", label: "High Priority" },
  { value: "INTERESANTE", label: "Interesting" },
  { value: "POCO_INTERESANTE", label: "Low Interest" },
  { value: "NO_INTERESA", label: "Not Interested" },
]

const statuses: { value: OpportunityStatus; label: string }[] = [
  { value: "new", label: "New" },
  { value: "processing", label: "Processing" },
  { value: "processed", label: "Processed" },
  { value: "error", label: "Error" },
  { value: "archived", label: "Archived" },
]

export function OpportunityFilters() {
  const filters = useAppStore((state) => state.opportunityFilters)
  const setFilters = useAppStore((state) => state.setOpportunityFilters)
  const resetFilters = useAppStore((state) => state.resetOpportunityFilters)
  const setCurrentPage = useAppStore((state) => state.setCurrentPage)

  const handleFilterChange = (key: string, value: string | undefined) => {
    setFilters({ [key]: value })
    setCurrentPage(1)
  }

  const hasActiveFilters =
    filters.tier || filters.status || filters.company || filters.min_score

  return (
    <div className="flex flex-wrap items-center gap-4">
      <div className="relative flex-1 min-w-[200px] max-w-sm">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          placeholder="Search by company..."
          value={filters.company || ""}
          onChange={(e) => handleFilterChange("company", e.target.value || undefined)}
          className="pl-9"
        />
      </div>

      <Select
        value={filters.tier || "all"}
        onValueChange={(value) =>
          handleFilterChange("tier", value === "all" ? undefined : value)
        }
      >
        <SelectTrigger className="w-[160px]">
          <SelectValue placeholder="All Tiers" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">All Tiers</SelectItem>
          {tiers.map((tier) => (
            <SelectItem key={tier.value} value={tier.value}>
              {tier.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      <Select
        value={filters.status || "all"}
        onValueChange={(value) =>
          handleFilterChange("status", value === "all" ? undefined : value)
        }
      >
        <SelectTrigger className="w-[160px]">
          <SelectValue placeholder="All Statuses" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">All Statuses</SelectItem>
          {statuses.map((status) => (
            <SelectItem key={status.value} value={status.value}>
              {status.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      <Select
        value={filters.min_score?.toString() || "all"}
        onValueChange={(value) =>
          handleFilterChange(
            "min_score",
            value === "all" ? undefined : value
          )
        }
      >
        <SelectTrigger className="w-[160px]">
          <SelectValue placeholder="Min Score" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">Any Score</SelectItem>
          <SelectItem value="80">80% or higher</SelectItem>
          <SelectItem value="60">60% or higher</SelectItem>
          <SelectItem value="40">40% or higher</SelectItem>
        </SelectContent>
      </Select>

      {hasActiveFilters && (
        <Button
          variant="ghost"
          size="sm"
          onClick={() => {
            resetFilters()
            setCurrentPage(1)
          }}
        >
          <X className="mr-2 h-4 w-4" />
          Clear filters
        </Button>
      )}
    </div>
  )
}
