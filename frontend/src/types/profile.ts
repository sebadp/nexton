export interface JobSearchStatus {
  currently_employed: boolean
  actively_looking: boolean
  urgency: "urgent" | "moderate" | "selective" | "not_looking"
  situation: string
  must_have: string[]
  nice_to_have: string[]
  reject_if: string[]
}

export interface Profile {
  name: string
  preferred_technologies: string[]
  years_of_experience: number
  current_seniority: "Junior" | "Mid" | "Senior" | "Staff" | "Principal"
  minimum_salary_usd: number
  ideal_salary_usd: number
  preferred_remote_policy: "Remote" | "Hybrid" | "Flexible" | "On-site"
  preferred_work_week: "4-days" | "5-days" | "flexible"
  preferred_locations: string[]
  preferred_company_size: "Startup" | "Mid-size" | "Enterprise"
  industry_preferences: string[]
  open_to_relocation: boolean
  looking_for_change: boolean
  job_search_status: JobSearchStatus
}
