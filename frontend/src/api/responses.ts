import { apiClient } from "./client"
import type { PendingResponse, ApproveResponseRequest } from "@/types"

export async function getPendingResponses(
  skip: number = 0,
  limit: number = 10
): Promise<{ items: PendingResponse[]; total: number }> {
  const response = await apiClient.get<{ items: PendingResponse[]; total: number }>(
    `/responses/?skip=${skip}&limit=${limit}`
  )
  return response.data
}

export async function getResponse(opportunityId: number): Promise<PendingResponse | null> {
  const response = await apiClient.get<PendingResponse>(`/responses/${opportunityId}`)
  // Backend returns 204 No Content if no pending response
  if (response.status === 204) {
    return null
  }
  return response.data
}

export async function approveResponse(
  opportunityId: number,
  data?: ApproveResponseRequest
): Promise<PendingResponse> {
  const response = await apiClient.post<PendingResponse>(
    `/responses/${opportunityId}/approve`,
    data || {}
  )
  return response.data
}

export async function editResponse(
  opportunityId: number,
  editedResponse: string
): Promise<PendingResponse> {
  const response = await apiClient.post<PendingResponse>(
    `/responses/${opportunityId}/edit`,
    { edited_response: editedResponse }
  )
  return response.data
}

export async function declineResponse(opportunityId: number): Promise<PendingResponse> {
  const response = await apiClient.post<PendingResponse>(
    `/responses/${opportunityId}/decline`,
    {}
  )
  return response.data
}

export async function updateResponseFeedback(
  responseId: number,
  feedback: { feedback_score: number; feedback_notes?: string }
): Promise<PendingResponse> {
  const response = await apiClient.patch<PendingResponse>(
    `/responses/${responseId}/feedback`,
    feedback
  )
  return response.data
}
