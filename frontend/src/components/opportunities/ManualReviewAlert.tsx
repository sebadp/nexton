import { AlertTriangle } from "lucide-react"

interface ManualReviewAlertProps {
  reason: string | null
}

export function ManualReviewAlert({ reason }: ManualReviewAlertProps) {
  if (!reason) return null

  return (
    <div className="rounded-lg border border-amber-500 bg-amber-50 p-4 dark:bg-amber-950/20">
      <div className="flex items-start gap-3">
        <AlertTriangle className="h-5 w-5 text-amber-500 flex-shrink-0 mt-0.5" />
        <div>
          <h4 className="font-medium text-amber-800 dark:text-amber-200">
            Manual Review Required
          </h4>
          <p className="mt-1 text-sm text-amber-700 dark:text-amber-300">
            {reason}
          </p>
        </div>
      </div>
    </div>
  )
}
