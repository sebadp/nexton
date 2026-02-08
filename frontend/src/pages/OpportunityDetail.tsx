import { useParams, useNavigate, Link } from "react-router-dom"
import {
  ArrowLeft,
  Building2,
  MapPin,
  Briefcase,
  Calendar,
  Clock,
  DollarSign,
  User,
  MessageSquare,
  Trash2,
} from "lucide-react"
import { useOpportunity, useDeleteOpportunity, useResponse } from "@/hooks"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { Skeleton } from "@/components/ui/skeleton"
import {
  TierBadge,
  ScoreBar,
  ConversationStateBadge,
  ProcessingStatusBadge,
  ManualReviewAlert,
  HardFiltersCard,
  FollowUpAnalysisCard,
} from "@/components/opportunities"
import { formatDate, formatDateTime, formatCurrency } from "@/lib/utils"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { useState } from "react"

export default function OpportunityDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)

  const { data: opportunity, isLoading } = useOpportunity(Number(id))
  const { data: response } = useResponse(Number(id))
  const deleteMutation = useDeleteOpportunity()

  const handleDelete = async () => {
    await deleteMutation.mutateAsync(Number(id))
    navigate("/opportunities")
  }

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Skeleton className="h-10 w-10" />
          <div className="space-y-2">
            <Skeleton className="h-8 w-64" />
            <Skeleton className="h-4 w-32" />
          </div>
        </div>
        <div className="grid gap-6 lg:grid-cols-3">
          <div className="lg:col-span-2 space-y-6">
            <Skeleton className="h-64" />
            <Skeleton className="h-48" />
          </div>
          <Skeleton className="h-96" />
        </div>
      </div>
    )
  }

  if (!opportunity) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <p className="text-lg text-muted-foreground">Opportunity not found</p>
        <Button asChild className="mt-4">
          <Link to="/opportunities">Back to Opportunities</Link>
        </Button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" asChild>
            <Link to="/opportunities">
              <ArrowLeft className="h-5 w-5" />
            </Link>
          </Button>
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <h1 className="text-3xl font-bold tracking-tight">
                {opportunity.company || "Unknown Company"}
              </h1>
              <TierBadge tier={opportunity.tier} />
              <ConversationStateBadge state={opportunity.conversation_state} />
              <ProcessingStatusBadge status={opportunity.processing_status} />
            </div>
            <p className="text-muted-foreground">{opportunity.role || "Role not specified"}</p>
          </div>
        </div>

        <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
          <DialogTrigger asChild>
            <Button variant="destructive" size="sm">
              <Trash2 className="mr-2 h-4 w-4" />
              Delete
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Delete Opportunity</DialogTitle>
              <DialogDescription asChild>
                <div className="space-y-3">
                  {response ? (
                    <>
                      <div className="p-3 bg-orange-50 dark:bg-orange-950 border border-orange-200 dark:border-orange-800 rounded-md">
                        <p className="font-semibold text-orange-700 dark:text-orange-300 flex items-center gap-2">
                          ⚠️ This opportunity has a {response.status} response:
                        </p>
                        <p className="mt-2 text-sm italic text-orange-600 dark:text-orange-400">
                          "{response.original_response?.slice(0, 150)}..."
                        </p>
                      </div>
                      <p>Deleting will also remove this response. This action cannot be undone.</p>
                    </>
                  ) : (
                    <p>Are you sure you want to delete this opportunity? This action cannot be undone.</p>
                  )}
                </div>
              </DialogDescription>
            </DialogHeader>
            <DialogFooter>
              <Button
                variant="outline"
                onClick={() => setDeleteDialogOpen(false)}
              >
                Cancel
              </Button>
              <Button
                variant="destructive"
                onClick={handleDelete}
                disabled={deleteMutation.isPending}
              >
                {deleteMutation.isPending
                  ? "Deleting..."
                  : response
                    ? "Delete Opportunity & Response"
                    : "Delete"}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {opportunity.requires_manual_review && (
        <ManualReviewAlert reason={opportunity.manual_review_reason} />
      )}

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2 space-y-6">
          {opportunity.hard_filter_results && (
            <HardFiltersCard results={opportunity.hard_filter_results} />
          )}

          {opportunity.follow_up_analysis && (
            <FollowUpAnalysisCard analysis={opportunity.follow_up_analysis} />
          )}

          <Card>
            <CardHeader>
              <CardTitle>Details</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="flex items-center gap-2">
                  <User className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm">
                    <span className="text-muted-foreground">Recruiter: </span>
                    {opportunity.recruiter_name}
                  </span>
                </div>
                {opportunity.location && (
                  <div className="flex items-center gap-2">
                    <MapPin className="h-4 w-4 text-muted-foreground" />
                    <span className="text-sm">{opportunity.location}</span>
                  </div>
                )}
                {opportunity.seniority && (
                  <div className="flex items-center gap-2">
                    <Briefcase className="h-4 w-4 text-muted-foreground" />
                    <span className="text-sm">{opportunity.seniority}</span>
                  </div>
                )}
                {opportunity.remote_policy && (
                  <div className="flex items-center gap-2">
                    <Building2 className="h-4 w-4 text-muted-foreground" />
                    <span className="text-sm">{opportunity.remote_policy}</span>
                  </div>
                )}
                {(opportunity.salary_min || opportunity.salary_max) && (
                  <div className="flex items-center gap-2">
                    <DollarSign className="h-4 w-4 text-muted-foreground" />
                    <span className="text-sm">
                      {opportunity.salary_min && opportunity.salary_max
                        ? `${formatCurrency(opportunity.salary_min, opportunity.currency || "USD")} - ${formatCurrency(opportunity.salary_max, opportunity.currency || "USD")}`
                        : opportunity.salary_min
                          ? `From ${formatCurrency(opportunity.salary_min, opportunity.currency || "USD")}`
                          : `Up to ${formatCurrency(opportunity.salary_max!, opportunity.currency || "USD")}`}
                    </span>
                  </div>
                )}
                <div className="flex items-center gap-2">
                  <Calendar className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm">
                    {formatDateTime(opportunity.created_at)}
                  </span>
                </div>
              </div>

              {opportunity.tech_stack && opportunity.tech_stack.length > 0 && (
                <>
                  <Separator />
                  <div>
                    <p className="text-sm font-medium mb-2">Tech Stack</p>
                    <div className="flex flex-wrap gap-2">
                      {opportunity.tech_stack.map((tech) => (
                        <Badge key={tech} variant="secondary">
                          {tech}
                        </Badge>
                      ))}
                    </div>
                  </div>
                </>
              )}

              <Separator />

              <div>
                <p className="text-sm font-medium mb-2">Original Message</p>
                <p className="text-sm text-muted-foreground whitespace-pre-wrap">
                  {opportunity.raw_message}
                </p>
              </div>
            </CardContent>
          </Card>

          {(opportunity.ai_response || response) && (
            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle className="flex items-center gap-2">
                  <MessageSquare className="h-5 w-5" />
                  AI Generated Response
                </CardTitle>
                {response && (
                  <Badge
                    variant={
                      response.status === "approved"
                        ? "success"
                        : response.status === "declined"
                          ? "destructive"
                          : "secondary"
                    }
                  >
                    {response.status}
                  </Badge>
                )}
              </CardHeader>
              <CardContent>
                <p className="whitespace-pre-wrap text-sm">
                  {response?.final_response ||
                    response?.edited_response ||
                    response?.original_response ||
                    opportunity.ai_response}
                </p>
                {response?.status === "pending" && (
                  <div className="mt-4">
                    <Button asChild>
                      <Link to="/responses">Review Response</Link>
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>
          )}
        </div>

        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Score Breakdown</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="text-center">
                <div className="text-4xl font-bold">
                  {opportunity.total_score ?? "-"}
                  {opportunity.total_score !== null && (
                    <span className="text-lg text-muted-foreground">%</span>
                  )}
                </div>
                <p className="text-sm text-muted-foreground">Overall Match</p>
              </div>
              <Separator />
              <div className="space-y-3">
                <ScoreBar
                  score={opportunity.tech_stack_score}
                  label="Tech Stack"
                />
                <ScoreBar score={opportunity.salary_score} label="Salary" />
                <ScoreBar
                  score={opportunity.seniority_score}
                  label="Seniority"
                />
                <ScoreBar score={opportunity.company_score} label="Company" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Status</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Status</span>
                <Badge>{opportunity.status}</Badge>
              </div>
              {opportunity.processing_time_ms && (
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">
                    Processing Time
                  </span>
                  <span className="text-sm flex items-center gap-1">
                    <Clock className="h-3 w-3" />
                    {(opportunity.processing_time_ms / 1000).toFixed(2)}s
                  </span>
                </div>
              )}
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Created</span>
                <span className="text-sm">
                  {formatDate(opportunity.created_at)}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Updated</span>
                <span className="text-sm">
                  {formatDate(opportunity.updated_at)}
                </span>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
