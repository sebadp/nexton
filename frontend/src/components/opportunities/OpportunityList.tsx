import { ChevronLeft, ChevronRight } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { OpportunityCard } from "./OpportunityCard"
import { useAppStore } from "@/store"
import type { OpportunityListResponse } from "@/types"

interface OpportunityListProps {
  data?: OpportunityListResponse
  isLoading: boolean
}

export function OpportunityList({ data, isLoading }: OpportunityListProps) {
  const currentPage = useAppStore((state) => state.currentPage)
  const pageSize = useAppStore((state) => state.pageSize)
  const setCurrentPage = useAppStore((state) => state.setCurrentPage)

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="rounded-lg border p-4">
              <div className="space-y-3">
                <div className="flex items-start justify-between">
                  <div className="space-y-1">
                    <Skeleton className="h-5 w-32" />
                    <Skeleton className="h-4 w-24" />
                  </div>
                  <Skeleton className="h-5 w-20" />
                </div>
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-3/4" />
                <div className="flex gap-1">
                  <Skeleton className="h-5 w-16" />
                  <Skeleton className="h-5 w-16" />
                  <Skeleton className="h-5 w-16" />
                </div>
                <Skeleton className="h-2 w-full" />
              </div>
            </div>
          ))}
        </div>
      </div>
    )
  }

  if (!data || data.items.length === 0) {
    return (
      <div className="flex h-64 items-center justify-center rounded-lg border">
        <p className="text-muted-foreground">No opportunities found</p>
      </div>
    )
  }

  const totalPages = Math.ceil(data.total / pageSize)

  return (
    <div className="space-y-4">
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {data.items.map((opportunity) => (
          <OpportunityCard key={opportunity.id} opportunity={opportunity} />
        ))}
      </div>

      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-muted-foreground">
            Showing {(currentPage - 1) * pageSize + 1} to{" "}
            {Math.min(currentPage * pageSize, data.total)} of {data.total}{" "}
            opportunities
          </p>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setCurrentPage(currentPage - 1)}
              disabled={currentPage === 1}
            >
              <ChevronLeft className="h-4 w-4" />
              Previous
            </Button>
            <span className="text-sm">
              Page {currentPage} of {totalPages}
            </span>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setCurrentPage(currentPage + 1)}
              disabled={!data.has_more}
            >
              Next
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}
