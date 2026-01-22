import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Legend,
  Tooltip,
} from "recharts"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import type { OpportunityStats } from "@/types"

interface TierChartProps {
  stats?: OpportunityStats
  isLoading: boolean
}

const COLORS = {
  HIGH_PRIORITY: "#22c55e",
  INTERESANTE: "#eab308",
  POCO_INTERESANTE: "#f97316",
  NO_INTERESA: "#ef4444",
}

const LABELS = {
  HIGH_PRIORITY: "High Priority",
  INTERESANTE: "Interesting",
  POCO_INTERESANTE: "Low Interest",
  NO_INTERESA: "Not Interested",
}

export function TierChart({ stats, isLoading }: TierChartProps) {
  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Opportunities by Tier</CardTitle>
        </CardHeader>
        <CardContent>
          <Skeleton className="h-[300px] w-full" />
        </CardContent>
      </Card>
    )
  }

  const data = stats?.by_tier
    ? Object.entries(stats.by_tier)
        .filter(([, value]) => value > 0)
        .map(([key, value]) => ({
          name: LABELS[key as keyof typeof LABELS] || key,
          value,
          color: COLORS[key as keyof typeof COLORS] || "#gray",
        }))
    : []

  if (data.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Opportunities by Tier</CardTitle>
        </CardHeader>
        <CardContent className="flex h-[300px] items-center justify-center">
          <p className="text-muted-foreground">No data available</p>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Opportunities by Tier</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              labelLine={false}
              outerRadius={100}
              fill="#8884d8"
              dataKey="value"
              label={({ name, percent }) =>
                `${name} (${(percent * 100).toFixed(0)}%)`
              }
            >
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Pie>
            <Tooltip />
            <Legend />
          </PieChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  )
}
