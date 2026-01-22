import { apiClient } from "./client"

export interface ScrapingTriggerRequest {
  limit?: number
  unread_only?: boolean
  send_email?: boolean
}

export interface ScrapingTriggerResponse {
  task_id: string
  status: string
  message: string
}

export interface ScrapingStatus {
  is_running: boolean
  last_run: string | null
  last_run_status: string | null
  last_run_count: number | null
  task_id: string | null
  task_status: string | null
  task_progress: Record<string, unknown> | null
}

export async function triggerScraping(
  request: ScrapingTriggerRequest = {}
): Promise<ScrapingTriggerResponse> {
  const response = await apiClient.post<ScrapingTriggerResponse>("/scraping/trigger", request)
  return response.data
}

export async function getScrapingStatus(): Promise<ScrapingStatus> {
  const response = await apiClient.get<ScrapingStatus>("/scraping/status")
  return response.data
}

export async function cancelScraping(): Promise<{ status: string; message: string }> {
  const response = await apiClient.post<{ status: string; message: string }>("/scraping/cancel")
  return response.data
}
