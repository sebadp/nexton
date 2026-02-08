export type OpportunityTier = "HIGH_PRIORITY" | "INTERESANTE" | "POCO_INTERESANTE" | "NO_INTERESA"

export type OpportunityStatus = "new" | "processing" | "processed" | "error" | "archived"

// New classification types
export type ConversationState = "NEW_OPPORTUNITY" | "FOLLOW_UP" | "COURTESY_CLOSE"

export type ProcessingStatus =
  | "processed"
  | "ignored"
  | "declined"
  | "manual_review"
  | "auto_responded"

export type QuestionType =
  | "SALARY"
  | "AVAILABILITY"
  | "EXPERIENCE"
  | "INTEREST"
  | "SCHEDULING"
  | "TECH_STACK"
  | "NONE"
  | "OTHER"

export interface HardFilterResults {
  passed: boolean
  failed_filters: string[]
  score_penalty: number
  should_decline: boolean
  work_week_status: "CONFIRMED" | "NOT_MENTIONED" | "FIVE_DAY" | "UNKNOWN" | "SKIPPED"
}

export interface FollowUpAnalysis {
  can_auto_respond: boolean
  question_type: QuestionType | null
  detected_question: string | null
  suggested_response: string | null
  reasoning: string
  requires_context: boolean
}

export interface Opportunity {
  id: number
  recruiter_name: string
  raw_message: string | null
  company: string | null
  role: string | null
  seniority: string | null
  tech_stack: string[]
  salary_min: number | null
  salary_max: number | null
  currency: string | null
  remote_policy: string | null
  location: string | null
  tech_stack_score: number | null
  salary_score: number | null
  seniority_score: number | null
  company_score: number | null
  total_score: number | null
  tier: OpportunityTier | null
  ai_response: string | null
  status: OpportunityStatus
  processing_time_ms: number | null
  created_at: string
  updated_at: string
  message_timestamp: string | null

  // New classification fields
  conversation_state: ConversationState | null
  processing_status: ProcessingStatus | null
  requires_manual_review: boolean
  manual_review_reason: string | null
  hard_filter_results: HardFilterResults | null
  follow_up_analysis: FollowUpAnalysis | null
}

export interface OpportunityListResponse {
  items: Opportunity[]
  total: number
  skip: number
  limit: number
  has_more: boolean
}

export interface OpportunityStats {
  total_count: number
  by_tier: Record<OpportunityTier, number>
  by_status: Record<OpportunityStatus, number>
  // New classification stats
  by_conversation_state: Record<ConversationState, number> | null
  by_processing_status: Record<ProcessingStatus, number> | null
  pending_manual_review: number
  // Score metrics
  average_score: number | null
  highest_score: number | null
  lowest_score: number | null
}

export interface OpportunityFilters {
  tier?: OpportunityTier
  status?: OpportunityStatus
  conversation_state?: ConversationState
  processing_status?: ProcessingStatus
  requires_manual_review?: boolean
  min_score?: number
  company?: string
  sort_by?: string
  sort_order?: "asc" | "desc"
}

export interface CreateOpportunityRequest {
  recruiter_name: string
  raw_message: string
}

export interface UpdateOpportunityRequest {
  status?: OpportunityStatus
  notes?: string
}
