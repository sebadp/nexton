import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import {
  getPendingResponses,
  getResponse,
  approveResponse,
  editResponse,
  declineResponse,
  updateResponseFeedback,
} from "@/api"

export function usePendingResponses(skip: number = 0, limit: number = 10) {
  return useQuery({
    queryKey: ["pendingResponses", skip, limit],
    queryFn: () => getPendingResponses(skip, limit),
  })
}

export function useResponse(opportunityId: number) {
  return useQuery({
    queryKey: ["response", opportunityId],
    queryFn: () => getResponse(opportunityId),
    enabled: !!opportunityId,
    retry: false, // Don't retry on 404
    staleTime: 30000, // Cache for 30 seconds
  })
}

export function useApproveResponse() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ opportunityId, editedResponse }: { opportunityId: number; editedResponse?: string }) =>
      approveResponse(opportunityId, editedResponse ? { edited_response: editedResponse } : undefined),
    onSuccess: (_, { opportunityId }) => {
      queryClient.invalidateQueries({ queryKey: ["pendingResponses"] })
      queryClient.invalidateQueries({ queryKey: ["response", opportunityId] })
      queryClient.invalidateQueries({ queryKey: ["opportunity", opportunityId] })
    },
  })
}

export function useEditResponse() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ opportunityId, editedResponse }: { opportunityId: number; editedResponse: string }) =>
      editResponse(opportunityId, editedResponse),
    onSuccess: (_, { opportunityId }) => {
      queryClient.invalidateQueries({ queryKey: ["pendingResponses"] })
      queryClient.invalidateQueries({ queryKey: ["response", opportunityId] })
    },
  })
}

export function useDeclineResponse() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (opportunityId: number) => declineResponse(opportunityId),
    onSuccess: (_, opportunityId) => {
      queryClient.invalidateQueries({ queryKey: ["pendingResponses"] })
      queryClient.invalidateQueries({ queryKey: ["response", opportunityId] })
      queryClient.invalidateQueries({ queryKey: ["opportunity", opportunityId] })
    },
  })
}

export function useUpdateResponseFeedback() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      responseId,
      feedback,
    }: {
      responseId: number
      feedback: { feedback_score: number; feedback_notes?: string }
    }) => updateResponseFeedback(responseId, feedback),
    onSuccess: () => {
      // Invalidate queries to refresh data
      queryClient.invalidateQueries({ queryKey: ["response"] }) // Generic invalidation
      queryClient.invalidateQueries({ queryKey: ["pendingResponses"] })
    },
  })
}
