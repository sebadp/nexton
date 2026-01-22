import { Loader2 } from "lucide-react"
import { cn } from "@/lib/utils"

interface LoadingSpinnerProps {
  className?: string
  size?: "sm" | "md" | "lg"
  label?: string
}

const sizes = {
  sm: "h-4 w-4",
  md: "h-8 w-8",
  lg: "h-12 w-12",
}

export function LoadingSpinner({
  className,
  size = "md",
  label = "Loading...",
}: LoadingSpinnerProps) {
  return (
    <div className={cn("flex flex-col items-center justify-center gap-2", className)}>
      <Loader2 className={cn("animate-spin text-primary", sizes[size])} />
      {label && <p className="text-sm text-muted-foreground">{label}</p>}
    </div>
  )
}

export function PageLoader() {
  return (
    <div className="flex h-[50vh] items-center justify-center">
      <LoadingSpinner size="lg" label="Loading page..." />
    </div>
  )
}
