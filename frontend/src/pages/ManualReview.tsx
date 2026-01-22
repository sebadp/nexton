import { useState } from "react"
import { Link } from "react-router-dom"
import { useManualReviewQueue } from "@/hooks"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import {
  ConversationStateBadge,
  ProcessingStatusBadge,
  FollowUpAnalysisCard,
} from "@/components/opportunities"
import { AlertTriangle, Eye, MessageSquare, ChevronLeft, ChevronRight } from "lucide-react"
import type { Opportunity } from "@/types"

function ManualReviewCard({ opportunity }: { opportunity: Opportunity }) {
  return (
    <Card className="border-l-4 border-l-amber-500">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="space-y-1">
            <CardTitle className="flex items-center gap-2 text-lg">
              <AlertTriangle className="h-5 w-5 text-amber-500" />
              {opportunity.recruiter_name}
            </CardTitle>
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <span>{opportunity.company || "Unknown Company"}</span>
              {opportunity.role && (
                <>
                  <span>-</span>
                  <span>{opportunity.role}</span>
                </>
              )}
            </div>
          </div>
          <div className="flex items-center gap-2">
            <ConversationStateBadge state={opportunity.conversation_state} />
            <ProcessingStatusBadge status={opportunity.processing_status} />
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {opportunity.manual_review_reason && (
          <div className="text-sm">
            <span className="font-medium text-amber-700 dark:text-amber-300">
              Reason for Review:
            </span>
            <p className="text-muted-foreground mt-1">
              {opportunity.manual_review_reason}
            </p>
          </div>
        )}

        {opportunity.raw_message && (
          <div className="text-sm">
            <span className="font-medium">Original Message:</span>
            <div className="mt-1 p-3 bg-muted rounded-md text-muted-foreground max-h-32 overflow-y-auto">
              {opportunity.raw_message.slice(0, 300)}
              {opportunity.raw_message.length > 300 && "..."}
            </div>
          </div>
        )}

        {opportunity.follow_up_analysis && (
          <div className="pt-2">
            <FollowUpAnalysisCard analysis={opportunity.follow_up_analysis} />
          </div>
        )}

        <div className="flex items-center justify-end gap-2 pt-2">
          <Link to={`/opportunities/${opportunity.id}`}>
            <Button variant="outline" size="sm" className="gap-1">
              <Eye className="h-4 w-4" />
              View Details
            </Button>
          </Link>
          <Button size="sm" className="gap-1">
            <MessageSquare className="h-4 w-4" />
            Respond
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}

function ManualReviewSkeleton() {
  return (
    <Card>
      <CardHeader>
        <Skeleton className="h-6 w-48" />
        <Skeleton className="h-4 w-32" />
      </CardHeader>
      <CardContent className="space-y-4">
        <Skeleton className="h-20 w-full" />
        <div className="flex justify-end gap-2">
          <Skeleton className="h-9 w-24" />
          <Skeleton className="h-9 w-24" />
        </div>
      </CardContent>
    </Card>
  )
}

export default function ManualReview() {
  const [page, setPage] = useState(1)
  const pageSize = 10
  const skip = (page - 1) * pageSize

  const { data, isLoading } = useManualReviewQueue(skip, pageSize)

  const totalPages = data ? Math.ceil(data.total / pageSize) : 0

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
            <AlertTriangle className="h-8 w-8 text-amber-500" />
            Manual Review Queue
          </h1>
          <p className="text-muted-foreground">
            Messages that require your attention and manual response
          </p>
        </div>
        {data && (
          <Badge variant="amber" className="text-lg px-4 py-2">
            {data.total} pending
          </Badge>
        )}
      </div>

      {isLoading ? (
        <div className="space-y-4">
          <ManualReviewSkeleton />
          <ManualReviewSkeleton />
          <ManualReviewSkeleton />
        </div>
      ) : data?.items.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <div className="rounded-full bg-green-100 p-4 mb-4">
              <AlertTriangle className="h-8 w-8 text-green-600" />
            </div>
            <h3 className="text-lg font-semibold">All Caught Up!</h3>
            <p className="text-muted-foreground text-center mt-2">
              There are no messages requiring manual review at this time.
            </p>
          </CardContent>
        </Card>
      ) : (
        <>
          <div className="space-y-4">
            {data?.items.map((opportunity) => (
              <ManualReviewCard key={opportunity.id} opportunity={opportunity} />
            ))}
          </div>

          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-4">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
              >
                <ChevronLeft className="h-4 w-4" />
                Previous
              </Button>
              <span className="text-sm text-muted-foreground">
                Page {page} of {totalPages}
              </span>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
              >
                Next
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          )}
        </>
      )}
    </div>
  )
}
