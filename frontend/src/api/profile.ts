import { apiClient } from "./client"
import type { Profile } from "@/types"

export async function getProfile(): Promise<Profile> {
  const response = await apiClient.get<Profile>("/profile")
  return response.data
}

export async function updateProfile(data: Record<string, unknown>): Promise<Profile> {
  const response = await apiClient.put<Profile>("/profile", data)
  return response.data
}
