import { apiClient } from "./client"
import type { Settings, UpdateSettingsRequest } from "@/types"

export async function getSettings(): Promise<Settings> {
  const response = await apiClient.get<Settings>("/settings")
  return response.data
}

export async function updateSettings(data: UpdateSettingsRequest): Promise<Settings> {
  const response = await apiClient.patch<Settings>("/settings", data)
  return response.data
}
