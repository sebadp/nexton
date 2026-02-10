export interface Settings {
  app_name: string
  app_version: string
  env: "development" | "staging" | "production" | "test"
  log_level: string
  llm_provider: "ollama" | "openai" | "anthropic"
  llm_model: string
  llm_temperature: number
  llm_temperature_generation: number
  linkedin_email: string
  linkedin_password_set: boolean
  smtp_host: string
  smtp_port: number
  profile_path: string
  notification_enabled: boolean
  notification_email: string
}

export interface UpdateSettingsRequest {
  llm_provider?: string
  llm_model?: string
  llm_temperature?: number
  llm_temperature_generation?: number
  linkedin_email?: string
  linkedin_password?: string
  smtp_host?: string
  smtp_port?: number
}

export interface HealthStatus {
  status: "healthy" | "unhealthy"
  database: boolean
  redis: boolean
  ollama: boolean
}
