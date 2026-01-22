import { useEffect } from "react"
import { useForm, Controller } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { Save, Loader2 } from "lucide-react"
import { useProfile, useUpdateProfile } from "@/hooks"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Switch } from "@/components/ui/switch"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Separator } from "@/components/ui/separator"
import { Skeleton } from "@/components/ui/skeleton"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { TechStackEditor, ListEditor } from "@/components/profile"

const profileSchema = z.object({
  name: z.string().min(1, "Name is required"),
  preferred_technologies: z.array(z.string()),
  years_of_experience: z.number().min(0),
  current_seniority: z.string(),
  minimum_salary_usd: z.number().min(0),
  ideal_salary_usd: z.number().min(0),
  preferred_remote_policy: z.string(),
  preferred_work_week: z.string(),
  preferred_locations: z.array(z.string()),
  preferred_company_size: z.string(),
  industry_preferences: z.array(z.string()),
  open_to_relocation: z.boolean(),
  looking_for_change: z.boolean(),
  job_search_status: z.object({
    currently_employed: z.boolean(),
    actively_looking: z.boolean(),
    urgency: z.string(),
    situation: z.string(),
    must_have: z.array(z.string()),
    nice_to_have: z.array(z.string()),
    reject_if: z.array(z.string()),
  }),
})

type ProfileFormData = z.infer<typeof profileSchema>

export default function Profile() {
  const { data: profile, isLoading } = useProfile()
  const updateMutation = useUpdateProfile()

  const form = useForm<ProfileFormData>({
    resolver: zodResolver(profileSchema),
    defaultValues: {
      name: "",
      preferred_technologies: [],
      years_of_experience: 0,
      current_seniority: "Senior",
      minimum_salary_usd: 0,
      ideal_salary_usd: 0,
      preferred_remote_policy: "Remote",
      preferred_work_week: "5-days",
      preferred_locations: [],
      preferred_company_size: "Mid-size",
      industry_preferences: [],
      open_to_relocation: false,
      looking_for_change: true,
      job_search_status: {
        currently_employed: true,
        actively_looking: true,
        urgency: "selective",
        situation: "",
        must_have: [],
        nice_to_have: [],
        reject_if: [],
      },
    },
  })

  useEffect(() => {
    if (profile) {
      form.reset(profile as ProfileFormData)
    }
  }, [profile, form])

  const onSubmit = async (data: ProfileFormData) => {
    await updateMutation.mutateAsync(data as unknown as Record<string, unknown>)
  }

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div>
          <Skeleton className="h-8 w-32" />
          <Skeleton className="mt-2 h-4 w-64" />
        </div>
        <div className="grid gap-6 lg:grid-cols-2">
          <Skeleton className="h-96" />
          <Skeleton className="h-96" />
        </div>
      </div>
    )
  }

  return (
    <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Profile</h1>
          <p className="text-muted-foreground">
            Configure your preferences for opportunity matching
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

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Personal Information</CardTitle>
            <CardDescription>Basic information about you</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="name">Name</Label>
              <Input id="name" {...form.register("name")} />
            </div>

            <div className="space-y-2">
              <Label htmlFor="years_of_experience">Years of Experience</Label>
              <Input
                id="years_of_experience"
                type="number"
                {...form.register("years_of_experience", { valueAsNumber: true })}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="current_seniority">Current Seniority</Label>
              <Controller
                name="current_seniority"
                control={form.control}
                render={({ field }) => (
                  <Select value={field.value} onValueChange={field.onChange}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Junior">Junior</SelectItem>
                      <SelectItem value="Mid">Mid</SelectItem>
                      <SelectItem value="Senior">Senior</SelectItem>
                      <SelectItem value="Staff">Staff</SelectItem>
                      <SelectItem value="Principal">Principal</SelectItem>
                    </SelectContent>
                  </Select>
                )}
              />
            </div>

            <Separator />

            <div className="space-y-2">
              <Label>Tech Stack</Label>
              <Controller
                name="preferred_technologies"
                control={form.control}
                render={({ field }) => (
                  <TechStackEditor
                    technologies={field.value}
                    onChange={field.onChange}
                  />
                )}
              />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Compensation</CardTitle>
            <CardDescription>Salary expectations</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="minimum_salary_usd">Minimum Salary (USD)</Label>
              <Input
                id="minimum_salary_usd"
                type="number"
                {...form.register("minimum_salary_usd", { valueAsNumber: true })}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="ideal_salary_usd">Ideal Salary (USD)</Label>
              <Input
                id="ideal_salary_usd"
                type="number"
                {...form.register("ideal_salary_usd", { valueAsNumber: true })}
              />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Work Preferences</CardTitle>
            <CardDescription>How and where you want to work</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label>Remote Policy</Label>
              <Controller
                name="preferred_remote_policy"
                control={form.control}
                render={({ field }) => (
                  <Select value={field.value} onValueChange={field.onChange}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Remote">Remote</SelectItem>
                      <SelectItem value="Hybrid">Hybrid</SelectItem>
                      <SelectItem value="Flexible">Flexible</SelectItem>
                      <SelectItem value="On-site">On-site</SelectItem>
                    </SelectContent>
                  </Select>
                )}
              />
            </div>

            <div className="space-y-2">
              <Label>Work Week</Label>
              <Controller
                name="preferred_work_week"
                control={form.control}
                render={({ field }) => (
                  <Select value={field.value} onValueChange={field.onChange}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="4-days">4 Days</SelectItem>
                      <SelectItem value="5-days">5 Days</SelectItem>
                      <SelectItem value="flexible">Flexible</SelectItem>
                    </SelectContent>
                  </Select>
                )}
              />
            </div>

            <div className="space-y-2">
              <Label>Company Size</Label>
              <Controller
                name="preferred_company_size"
                control={form.control}
                render={({ field }) => (
                  <Select value={field.value} onValueChange={field.onChange}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Startup">Startup</SelectItem>
                      <SelectItem value="Mid-size">Mid-size</SelectItem>
                      <SelectItem value="Enterprise">Enterprise</SelectItem>
                    </SelectContent>
                  </Select>
                )}
              />
            </div>

            <div className="flex items-center justify-between">
              <Label htmlFor="open_to_relocation">Open to Relocation</Label>
              <Controller
                name="open_to_relocation"
                control={form.control}
                render={({ field }) => (
                  <Switch
                    id="open_to_relocation"
                    checked={field.value}
                    onCheckedChange={field.onChange}
                  />
                )}
              />
            </div>

            <div className="flex items-center justify-between">
              <Label htmlFor="looking_for_change">Looking for Change</Label>
              <Controller
                name="looking_for_change"
                control={form.control}
                render={({ field }) => (
                  <Switch
                    id="looking_for_change"
                    checked={field.value}
                    onCheckedChange={field.onChange}
                  />
                )}
              />
            </div>

            <Separator />

            <div className="space-y-2">
              <Label>Preferred Locations</Label>
              <Controller
                name="preferred_locations"
                control={form.control}
                render={({ field }) => (
                  <ListEditor
                    items={field.value}
                    onChange={field.onChange}
                    placeholder="Add location..."
                  />
                )}
              />
            </div>

            <div className="space-y-2">
              <Label>Industry Preferences</Label>
              <Controller
                name="industry_preferences"
                control={form.control}
                render={({ field }) => (
                  <ListEditor
                    items={field.value}
                    onChange={field.onChange}
                    placeholder="Add industry..."
                  />
                )}
              />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Job Search Status</CardTitle>
            <CardDescription>Current situation and requirements</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <Label htmlFor="currently_employed">Currently Employed</Label>
              <Controller
                name="job_search_status.currently_employed"
                control={form.control}
                render={({ field }) => (
                  <Switch
                    id="currently_employed"
                    checked={field.value}
                    onCheckedChange={field.onChange}
                  />
                )}
              />
            </div>

            <div className="flex items-center justify-between">
              <Label htmlFor="actively_looking">Actively Looking</Label>
              <Controller
                name="job_search_status.actively_looking"
                control={form.control}
                render={({ field }) => (
                  <Switch
                    id="actively_looking"
                    checked={field.value}
                    onCheckedChange={field.onChange}
                  />
                )}
              />
            </div>

            <div className="space-y-2">
              <Label>Urgency</Label>
              <Controller
                name="job_search_status.urgency"
                control={form.control}
                render={({ field }) => (
                  <Select value={field.value} onValueChange={field.onChange}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="urgent">Urgent</SelectItem>
                      <SelectItem value="moderate">Moderate</SelectItem>
                      <SelectItem value="selective">Selective</SelectItem>
                      <SelectItem value="not_looking">Not Looking</SelectItem>
                    </SelectContent>
                  </Select>
                )}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="situation">Situation Description</Label>
              <Textarea
                id="situation"
                {...form.register("job_search_status.situation")}
                rows={3}
              />
            </div>

            <Separator />

            <div className="space-y-2">
              <Label>Must Have</Label>
              <Controller
                name="job_search_status.must_have"
                control={form.control}
                render={({ field }) => (
                  <ListEditor
                    items={field.value}
                    onChange={field.onChange}
                    placeholder="Add requirement..."
                  />
                )}
              />
            </div>

            <div className="space-y-2">
              <Label>Nice to Have</Label>
              <Controller
                name="job_search_status.nice_to_have"
                control={form.control}
                render={({ field }) => (
                  <ListEditor
                    items={field.value}
                    onChange={field.onChange}
                    placeholder="Add preference..."
                  />
                )}
              />
            </div>

            <div className="space-y-2">
              <Label>Reject If</Label>
              <Controller
                name="job_search_status.reject_if"
                control={form.control}
                render={({ field }) => (
                  <ListEditor
                    items={field.value}
                    onChange={field.onChange}
                    placeholder="Add deal breaker..."
                  />
                )}
              />
            </div>
          </CardContent>
        </Card>
      </div>
    </form>
  )
}
