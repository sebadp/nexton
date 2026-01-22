import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { MessageCircle, Bot, User } from "lucide-react"
import type { FollowUpAnalysis, QuestionType } from "@/types"

interface FollowUpAnalysisCardProps {
  analysis: FollowUpAnalysis | null
}

const questionTypeLabels: Record<QuestionType, string> = {
  SALARY: "Salary Question",
  AVAILABILITY: "Availability",
  EXPERIENCE: "Experience",
  INTEREST: "Interest",
  SCHEDULING: "Scheduling",
  TECH_STACK: "Tech Stack",
  NONE: "No Question",
  OTHER: "Other",
}

export function FollowUpAnalysisCard({ analysis }: FollowUpAnalysisCardProps) {
  if (!analysis) return null

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-base">
          <MessageCircle className="h-5 w-5" />
          Follow-up Analysis
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium">Question Type</span>
          <Badge variant="secondary">
            {analysis.question_type
              ? questionTypeLabels[analysis.question_type]
              : "Unknown"}
          </Badge>
        </div>

        <div className="flex items-center justify-between">
          <span className="text-sm font-medium">Response Mode</span>
          {analysis.can_auto_respond ? (
            <Badge variant="blue" className="gap-1">
              <Bot className="h-3 w-3" />
              Auto-respond
            </Badge>
          ) : (
            <Badge variant="amber" className="gap-1">
              <User className="h-3 w-3" />
              Manual Review
            </Badge>
          )}
        </div>

        {analysis.requires_context && (
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium">Requires Context</span>
            <Badge variant="orange">Yes</Badge>
          </div>
        )}

        {analysis.detected_question && (
          <div className="text-sm">
            <span className="font-medium">Detected Question:</span>
            <p className="text-muted-foreground mt-1 italic">
              "{analysis.detected_question}"
            </p>
          </div>
        )}

        <div className="text-sm">
          <span className="font-medium">Reasoning:</span>
          <p className="text-muted-foreground mt-1">{analysis.reasoning}</p>
        </div>

        {analysis.suggested_response && (
          <div className="text-sm">
            <span className="font-medium">Suggested Response:</span>
            <div className="mt-1 p-3 bg-muted rounded-md text-muted-foreground">
              {analysis.suggested_response}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
