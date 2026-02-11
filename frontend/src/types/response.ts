export type ResponseStatus = "pending" | "approved" | "declined" | "sent" | "failed"

export interface PendingResponse {
  id: number
  opportunity_id: number
  original_response: string
  edited_response: string | null
  final_response: string | null
  status: ResponseStatus
  approved_at: string | null
  declined_at: string | null
  sent_at: string | null
  error_message: string | null
  send_attempts: number
  created_at: string
  updated_at: string
  feedback_score: number | null
  feedback_notes: string | null
}

export interface ApproveResponseRequest {
  edited_response?: string
}

export interface UpdateResponseFeedbackRequest {
  feedback_score: number
  feedback_notes?: string
}

export interface PendingResponseWithOpportunity extends PendingResponse {
  opportunity?: {
    id: number
    recruiter_name: string
    company: string | null
    role: string | null
    tier: string | null
  }
}
