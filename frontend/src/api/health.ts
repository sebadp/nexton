import { apiClient } from "./client"
import type { HealthStatus } from "@/types"

export async function getHealthStatus(): Promise<HealthStatus> {
  const response = await apiClient.get<HealthStatus>("/health/ready")
  return response.data
}

export async function getBasicHealth(): Promise<{ status: string }> {
  const response = await apiClient.get<{ status: string }>("/health")
  return response.data
}
