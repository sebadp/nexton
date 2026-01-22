import { useState } from "react"
import { Link } from "react-router-dom"
import { Check, X, Edit2, ExternalLink } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Textarea } from "@/components/ui/textarea"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { useApproveResponse, useDeclineResponse } from "@/hooks"
import { formatDateTime } from "@/lib/utils"
import type { PendingResponse } from "@/types"

interface ResponseCardProps {
  response: PendingResponse
  opportunityInfo?: {
    company?: string
    role?: string
    recruiter_name?: string
  }
}

export function ResponseCard({ response, opportunityInfo }: ResponseCardProps) {
  const [editDialogOpen, setEditDialogOpen] = useState(false)
  const [editedText, setEditedText] = useState(
    response.edited_response || response.original_response
  )

  const approveMutation = useApproveResponse()
  const declineMutation = useDeclineResponse()

  const handleApprove = async () => {
    await approveMutation.mutateAsync({
      opportunityId: response.opportunity_id,
    })
  }

  const handleApproveWithEdit = async () => {
    await approveMutation.mutateAsync({
      opportunityId: response.opportunity_id,
      editedResponse: editedText,
    })
    setEditDialogOpen(false)
  }

  const handleDecline = async () => {
    await declineMutation.mutateAsync(response.opportunity_id)
  }

  const isPending = response.status === "pending"

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between">
          <div>
            <CardTitle className="text-lg">
              {opportunityInfo?.company || `Opportunity #${response.opportunity_id}`}
            </CardTitle>
            {opportunityInfo?.role && (
              <p className="text-sm text-muted-foreground">
                {opportunityInfo.role}
              </p>
            )}
          </div>
          <div className="flex items-center gap-2">
            <Badge
              variant={
                response.status === "approved"
                  ? "success"
                  : response.status === "declined"
                    ? "destructive"
                    : response.status === "sent"
                      ? "default"
                      : "secondary"
              }
            >
              {response.status}
            </Badge>
            <Button variant="ghost" size="icon" asChild>
              <Link to={`/opportunities/${response.opportunity_id}`}>
                <ExternalLink className="h-4 w-4" />
              </Link>
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="rounded-lg bg-muted p-4">
          <p className="whitespace-pre-wrap text-sm">
            {response.edited_response || response.original_response}
          </p>
        </div>

        <div className="flex items-center justify-between text-xs text-muted-foreground">
          <span>Created: {formatDateTime(response.created_at)}</span>
          {response.send_attempts > 0 && (
            <span>Send attempts: {response.send_attempts}</span>
          )}
        </div>

        {response.error_message && (
          <div className="rounded-lg border border-destructive bg-destructive/10 p-3">
            <p className="text-sm text-destructive">{response.error_message}</p>
          </div>
        )}

        {isPending && (
          <div className="flex gap-2">
            <Button
              onClick={handleApprove}
              disabled={approveMutation.isPending || declineMutation.isPending}
              className="flex-1"
            >
              <Check className="mr-2 h-4 w-4" />
              {approveMutation.isPending ? "Approving..." : "Approve"}
            </Button>

            <Dialog open={editDialogOpen} onOpenChange={setEditDialogOpen}>
              <Button
                variant="outline"
                onClick={() => setEditDialogOpen(true)}
                disabled={approveMutation.isPending || declineMutation.isPending}
              >
                <Edit2 className="mr-2 h-4 w-4" />
                Edit
              </Button>
              <DialogContent className="max-w-2xl">
                <DialogHeader>
                  <DialogTitle>Edit Response</DialogTitle>
                  <DialogDescription>
                    Make changes to the AI-generated response before approving.
                  </DialogDescription>
                </DialogHeader>
                <Textarea
                  value={editedText}
                  onChange={(e) => setEditedText(e.target.value)}
                  rows={12}
                  className="font-mono text-sm"
                />
                <DialogFooter>
                  <Button
                    variant="outline"
                    onClick={() => setEditDialogOpen(false)}
                  >
                    Cancel
                  </Button>
                  <Button
                    onClick={handleApproveWithEdit}
                    disabled={approveMutation.isPending}
                  >
                    {approveMutation.isPending
                      ? "Saving..."
                      : "Save & Approve"}
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>

            <Button
              variant="destructive"
              onClick={handleDecline}
              disabled={approveMutation.isPending || declineMutation.isPending}
            >
              <X className="mr-2 h-4 w-4" />
              {declineMutation.isPending ? "..." : "Decline"}
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
