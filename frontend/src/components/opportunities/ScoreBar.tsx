import { cn } from "@/lib/utils"

interface ScoreBarProps {
  score: number | null
  label?: string
  showValue?: boolean
}

function getScoreColor(score: number) {
  if (score >= 80) return "bg-green-500"
  if (score >= 60) return "bg-yellow-500"
  if (score >= 40) return "bg-orange-500"
  return "bg-red-500"
}

export function ScoreBar({ score, label, showValue = true }: ScoreBarProps) {
  if (score === null) {
    return (
      <div className="space-y-1">
        {label && <p className="text-xs text-muted-foreground">{label}</p>}
        <div className="h-2 w-full rounded-full bg-muted">
          <div className="h-full w-0 rounded-full bg-muted-foreground" />
        </div>
        {showValue && <p className="text-xs text-muted-foreground">N/A</p>}
      </div>
    )
  }

  return (
    <div className="space-y-1">
      {label && (
        <div className="flex items-center justify-between">
          <p className="text-xs text-muted-foreground">{label}</p>
          {showValue && <p className="text-xs font-medium">{score}%</p>}
        </div>
      )}
      <div className="h-2 w-full rounded-full bg-muted">
        <div
          className={cn("h-full rounded-full transition-all", getScoreColor(score))}
          style={{ width: `${Math.min(100, Math.max(0, score))}%` }}
        />
      </div>
    </div>
  )
}
