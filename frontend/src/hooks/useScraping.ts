import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { triggerScraping, getScrapingStatus, cancelScraping } from "@/api"
import type { ScrapingTriggerRequest } from "@/api/scraping"

export function useScrapingStatus() {
  return useQuery({
    queryKey: ["scrapingStatus"],
    queryFn: getScrapingStatus,
    refetchInterval: (query) => {
      // Poll every 2 seconds while scraping is running
      return query.state.data?.is_running ? 2000 : false
    },
  })
}

export function useTriggerScraping() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (request?: ScrapingTriggerRequest) => triggerScraping(request),
    onSuccess: () => {
      // Start polling for status
      queryClient.invalidateQueries({ queryKey: ["scrapingStatus"] })
    },
    onSettled: () => {
      // Refresh opportunities after scraping completes
      queryClient.invalidateQueries({ queryKey: ["opportunities"] })
      queryClient.invalidateQueries({ queryKey: ["opportunityStats"] })
    },
  })
}

export function useCancelScraping() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: cancelScraping,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["scrapingStatus"] })
    },
  })
}
