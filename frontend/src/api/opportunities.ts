import { apiClient } from "./client"
import type {
  Opportunity,
  OpportunityListResponse,
  OpportunityStats,
  OpportunityFilters,
  CreateOpportunityRequest,
  UpdateOpportunityRequest,
} from "@/types"

export async function getOpportunities(
  skip: number = 0,
  limit: number = 10,
  filters?: OpportunityFilters
): Promise<OpportunityListResponse> {
  const params = new URLSearchParams({
    skip: skip.toString(),
    limit: limit.toString(),
  })

  if (filters?.tier) params.set("tier", filters.tier)
  if (filters?.status) params.set("status", filters.status)
  if (filters?.min_score) params.set("min_score", filters.min_score.toString())
  if (filters?.company) params.set("company", filters.company)
  if (filters?.sort_by) params.set("sort_by", filters.sort_by)
  if (filters?.sort_order) params.set("sort_order", filters.sort_order)

  const response = await apiClient.get<OpportunityListResponse>(`/opportunities?${params}`)
  return response.data
}

export async function getOpportunity(id: number): Promise<Opportunity> {
  const response = await apiClient.get<Opportunity>(`/opportunities/${id}`)
  return response.data
}

export async function getOpportunityStats(): Promise<OpportunityStats> {
  const response = await apiClient.get<OpportunityStats>("/opportunities/stats")
  return response.data
}

export async function createOpportunity(data: CreateOpportunityRequest): Promise<Opportunity> {
  const response = await apiClient.post<Opportunity>("/opportunities", data)
  return response.data
}

export async function updateOpportunity(id: number, data: UpdateOpportunityRequest): Promise<Opportunity> {
  const response = await apiClient.patch<Opportunity>(`/opportunities/${id}`, data)
  return response.data
}

export async function deleteOpportunity(id: number): Promise<void> {
  await apiClient.delete(`/opportunities/${id}`)
}

export async function getManualReviewQueue(
  skip: number = 0,
  limit: number = 10
): Promise<OpportunityListResponse> {
  const params = new URLSearchParams({
    skip: skip.toString(),
    limit: limit.toString(),
  })

  const response = await apiClient.get<OpportunityListResponse>(
    `/opportunities/manual-review?${params}`
  )
  return response.data
}
