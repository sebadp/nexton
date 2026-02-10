import { useEffect } from "react"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { Save, Loader2, Eye, EyeOff } from "lucide-react"
import { useState } from "react"
import { useSettings, useUpdateSettings } from "@/hooks"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"

const settingsSchema = z.object({
  llm_provider: z.string(),
  llm_model: z.string(),
  llm_temperature: z.number().min(0).max(2),
  llm_temperature_generation: z.number().min(0).max(2),
  linkedin_email: z.string().email().or(z.literal("")),
  linkedin_password: z.string().optional(),
  smtp_host: z.string(),
  smtp_port: z.number().min(1).max(65535),
  notification_enabled: z.boolean(),
  notification_email: z.string().email().or(z.literal("")),
})

type SettingsFormData = z.infer<typeof settingsSchema>

export default function Settings() {
  const { data: settings, isLoading } = useSettings()
  const updateMutation = useUpdateSettings()
  const [showPassword, setShowPassword] = useState(false)

  const form = useForm<SettingsFormData>({
    resolver: zodResolver(settingsSchema),
    defaultValues: {
      llm_provider: "ollama",
      llm_model: "llama2",
      llm_temperature: 0.0,
      llm_temperature_generation: 0.7,
      linkedin_email: "",
      linkedin_password: "",
      smtp_host: "localhost",
      smtp_port: 1025,
      notification_enabled: false,
      notification_email: "",
    },
  })

  useEffect(() => {
    if (settings) {
      form.reset({
        llm_provider: settings.llm_provider,
        llm_model: settings.llm_model,
        llm_temperature: settings.llm_temperature,
        llm_temperature_generation: settings.llm_temperature_generation,
        linkedin_email: settings.linkedin_email,
        linkedin_password: "",
        smtp_host: settings.smtp_host,
        smtp_port: settings.smtp_port,
        notification_enabled: settings.notification_enabled,
        notification_email: settings.notification_email,
      })
    }
  }, [settings, form])

  const onSubmit = async (data: SettingsFormData) => {
    const updateData: Record<string, unknown> = {}

    if (data.llm_provider !== settings?.llm_provider) {
      updateData.llm_provider = data.llm_provider
    }
    if (data.llm_model !== settings?.llm_model) {
      updateData.llm_model = data.llm_model
    }
    if (data.llm_temperature !== settings?.llm_temperature) {
      updateData.llm_temperature = data.llm_temperature
    }
    if (data.llm_temperature_generation !== settings?.llm_temperature_generation) {
      updateData.llm_temperature_generation = data.llm_temperature_generation
    }
    if (data.linkedin_email !== settings?.linkedin_email) {
      updateData.linkedin_email = data.linkedin_email
    }
    if (data.linkedin_password) {
      updateData.linkedin_password = data.linkedin_password
    }
    if (data.smtp_host !== settings?.smtp_host) {
      updateData.smtp_host = data.smtp_host
    }
    if (data.smtp_port !== settings?.smtp_port) {
      updateData.smtp_port = data.smtp_port
    }
    if (data.notification_enabled !== settings?.notification_enabled) {
      updateData.notification_enabled = data.notification_enabled
    }
    if (data.notification_email !== settings?.notification_email) {
      updateData.notification_email = data.notification_email
    }

    if (Object.keys(updateData).length > 0) {
      await updateMutation.mutateAsync(updateData)
    }
  }

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div>
          <Skeleton className="h-8 w-32" />
          <Skeleton className="mt-2 h-4 w-64" />
        </div>
        <div className="grid gap-6 lg:grid-cols-2">
          <Skeleton className="h-64" />
          <Skeleton className="h-64" />
        </div>
      </div>
    )
  }

  return (
    <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Settings</h1>
          <p className="text-muted-foreground">
            Configure application settings and credentials
          </p>
        </div>
        <Button type="submit" disabled={updateMutation.isPending}>
          {updateMutation.isPending ? (
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          ) : (
            <Save className="mr-2 h-4 w-4" />
          )}
          Save Changes
        </Button>
      </div>

      <div className="flex gap-2">
        <Badge variant="outline">{settings?.app_name}</Badge>
        <Badge variant="outline">v{settings?.app_version}</Badge>
        <Badge variant={settings?.env === "production" ? "destructive" : "secondary"}>
          {settings?.env}
        </Badge>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>LLM Configuration</CardTitle>
            <CardDescription>Configure the AI model settings</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="llm_provider">Provider</Label>
              <Select
                value={form.watch("llm_provider")}
                onValueChange={(value) => form.setValue("llm_provider", value)}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="ollama">Ollama (Local)</SelectItem>
                  <SelectItem value="openai">OpenAI</SelectItem>
                  <SelectItem value="anthropic">Anthropic</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="llm_model">Model</Label>
              <Input
                id="llm_model"
                {...form.register("llm_model")}
                placeholder="llama2, gpt-4, claude-3..."
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="llm_temperature">
                Analysis Temperature (Strict) - {form.watch("llm_temperature")}
              </Label>
              <Input
                id="llm_temperature"
                type="range"
                min="0"
                max="2"
                step="0.1"
                {...form.register("llm_temperature", { valueAsNumber: true })}
              />
              <p className="text-xs text-muted-foreground">
                Controls data extraction and scoring. Keep low (0.0 - 0.2) for accuracy.
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="llm_temperature_generation">
                Generation Temperature (Creative) - {form.watch("llm_temperature_generation")}
              </Label>
              <Input
                id="llm_temperature_generation"
                type="range"
                min="0"
                max="2"
                step="0.1"
                {...form.register("llm_temperature_generation", { valueAsNumber: true })}
              />
              <p className="text-xs text-muted-foreground">
                Controls response drafting. Increase (0.7 - 1.0) for more natural, less robotic replies.
              </p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>LinkedIn Credentials</CardTitle>
            <CardDescription>
              Credentials for scraping LinkedIn messages
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="linkedin_email">Email</Label>
              <Input
                id="linkedin_email"
                type="email"
                {...form.register("linkedin_email")}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="linkedin_password">
                Password{" "}
                {settings?.linkedin_password_set && (
                  <span className="text-xs text-muted-foreground">
                    (currently set)
                  </span>
                )}
              </Label>
              <div className="relative">
                <Input
                  id="linkedin_password"
                  type={showPassword ? "text" : "password"}
                  {...form.register("linkedin_password")}
                  placeholder={
                    settings?.linkedin_password_set
                      ? "Leave blank to keep current"
                      : "Enter password"
                  }
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                >
                  {showPassword ? (
                    <EyeOff className="h-4 w-4" />
                  ) : (
                    <Eye className="h-4 w-4" />
                  )}
                </button>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Email Settings</CardTitle>
            <CardDescription>SMTP configuration for notifications</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="smtp_host">SMTP Host</Label>
              <Input id="smtp_host" {...form.register("smtp_host")} />
            </div>

            <div className="space-y-2">
              <Label htmlFor="smtp_port">SMTP Port</Label>
              <Input
                id="smtp_port"
                type="number"
                {...form.register("smtp_port", { valueAsNumber: true })}
              />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Notifications</CardTitle>
            <CardDescription>Configure email notifications</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <Label htmlFor="notification_enabled">Enable Notifications</Label>
              <Switch
                id="notification_enabled"
                checked={form.watch("notification_enabled")}
                onCheckedChange={(checked) =>
                  form.setValue("notification_enabled", checked)
                }
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="notification_email">Notification Email</Label>
              <Input
                id="notification_email"
                type="email"
                {...form.register("notification_email")}
                disabled={!form.watch("notification_enabled")}
              />
            </div>
          </CardContent>
        </Card>
      </div>
    </form>
  )
}
