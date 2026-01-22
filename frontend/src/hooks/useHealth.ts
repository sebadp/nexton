import { useQuery } from "@tanstack/react-query"
import { getHealthStatus, getBasicHealth } from "@/api"

export function useHealthStatus() {
  return useQuery({
    queryKey: ["health"],
    queryFn: getHealthStatus,
    refetchInterval: 30000, // Refetch every 30 seconds
  })
}

export function useBasicHealth() {
  return useQuery({
    queryKey: ["basicHealth"],
    queryFn: getBasicHealth,
    refetchInterval: 30000,
  })
}
