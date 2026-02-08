import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import {
  getOpportunities,
  getOpportunity,
  getOpportunityStats,
  getManualReviewQueue,
  createOpportunity,
  updateOpportunity,
  deleteOpportunity,
} from "@/api"
import type { OpportunityFilters, CreateOpportunityRequest, UpdateOpportunityRequest } from "@/types"

export function useOpportunities(skip: number = 0, limit: number = 10, filters?: OpportunityFilters) {
  return useQuery({
    queryKey: ["opportunities", skip, limit, filters],
    queryFn: () => getOpportunities(skip, limit, filters),
  })
}

export function useOpportunity(id: number) {
  return useQuery({
    queryKey: ["opportunity", id],
    queryFn: () => getOpportunity(id),
    enabled: !!id,
  })
}

export function useOpportunityStats() {
  return useQuery({
    queryKey: ["opportunityStats"],
    queryFn: getOpportunityStats,
  })
}

export function useCreateOpportunity() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: CreateOpportunityRequest) => createOpportunity(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["opportunities"] })
      queryClient.invalidateQueries({ queryKey: ["opportunityStats"] })
    },
  })
}

export function useUpdateOpportunity() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: UpdateOpportunityRequest }) =>
      updateOpportunity(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: ["opportunities"] })
      queryClient.invalidateQueries({ queryKey: ["opportunity", id] })
      queryClient.invalidateQueries({ queryKey: ["opportunityStats"] })
    },
  })
}

export function useDeleteOpportunity() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => deleteOpportunity(id),
    onSuccess: (_data, deletedId) => {
      queryClient.invalidateQueries({ queryKey: ["opportunities"] })
      queryClient.invalidateQueries({ queryKey: ["opportunityStats"] })
      // Remove the response query for the deleted opportunity
      queryClient.removeQueries({ queryKey: ["response", deletedId] })
    },
  })
}

export function useManualReviewQueue(skip: number = 0, limit: number = 10) {
  return useQuery({
    queryKey: ["manualReviewQueue", skip, limit],
    queryFn: () => getManualReviewQueue(skip, limit),
  })
}
