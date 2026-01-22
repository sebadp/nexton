import { Skeleton } from "@/components/ui/skeleton"
import { ResponseCard } from "./ResponseCard"
import type { PendingResponse } from "@/types"

interface ResponseListProps {
  responses?: PendingResponse[]
  isLoading: boolean
}

export function ResponseList({ responses, isLoading }: ResponseListProps) {
  if (isLoading) {
    return (
      <div className="space-y-4">
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="rounded-lg border p-4">
            <div className="space-y-3">
              <div className="flex items-start justify-between">
                <div className="space-y-1">
                  <Skeleton className="h-5 w-48" />
                  <Skeleton className="h-4 w-32" />
                </div>
                <Skeleton className="h-5 w-20" />
              </div>
              <Skeleton className="h-24 w-full" />
              <div className="flex gap-2">
                <Skeleton className="h-10 flex-1" />
                <Skeleton className="h-10 w-20" />
                <Skeleton className="h-10 w-20" />
              </div>
            </div>
          </div>
        ))}
      </div>
    )
  }

  if (!responses || responses.length === 0) {
    return (
      <div className="flex h-64 items-center justify-center rounded-lg border">
        <p className="text-muted-foreground">No pending responses</p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {responses.map((response) => (
        <ResponseCard key={response.id} response={response} />
      ))}
    </div>
  )
}
