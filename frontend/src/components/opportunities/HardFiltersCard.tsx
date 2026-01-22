import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Check, X } from "lucide-react"
import type { HardFilterResults } from "@/types"

interface HardFiltersCardProps {
  results: HardFilterResults | null
}

const workWeekLabels: Record<string, string> = {
  CONFIRMED: "4-day confirmed",
  NOT_MENTIONED: "Not mentioned",
  FIVE_DAY: "5-day week",
  UNKNOWN: "Unknown",
  SKIPPED: "Skipped",
}

export function HardFiltersCard({ results }: HardFiltersCardProps) {
  if (!results) return null

  const filters = [
    {
      name: "Work Week",
      passed: results.work_week_status === "CONFIRMED" || results.work_week_status === "NOT_MENTIONED",
      detail: workWeekLabels[results.work_week_status] || results.work_week_status,
    },
    {
      name: "Overall",
      passed: results.passed,
      detail: results.passed ? "All filters passed" : `${results.failed_filters.length} filter(s) failed`,
    },
  ]

  // Add failed filters as individual items if any
  if (results.failed_filters.length > 0) {
    results.failed_filters.forEach((filter) => {
      filters.push({
        name: filter.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase()),
        passed: false,
        detail: "Failed",
      })
    })
  }

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-base">
          {results.passed ? (
            <Check className="h-5 w-5 text-green-500" />
          ) : (
            <X className="h-5 w-5 text-red-500" />
          )}
          Hard Filters
          {results.should_decline && (
            <span className="text-xs font-normal text-red-500 ml-2">
              (Will decline)
            </span>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {filters.map((filter, index) => (
            <div
              key={index}
              className="flex items-center justify-between text-sm"
            >
              <span className="flex items-center gap-2">
                {filter.passed ? (
                  <Check className="h-4 w-4 text-green-500" />
                ) : (
                  <X className="h-4 w-4 text-red-500" />
                )}
                {filter.name}
              </span>
              <span className="text-muted-foreground text-xs">{filter.detail}</span>
            </div>
          ))}
        </div>
        {results.score_penalty > 0 && (
          <p className="mt-3 text-xs text-muted-foreground">
            Score penalty: -{results.score_penalty} points
          </p>
        )}
      </CardContent>
    </Card>
  )
}
