import { Menu, Activity, CheckCircle, XCircle } from "lucide-react"
import { Button } from "@/components/ui/button"
import { useAppStore } from "@/store"
import { useHealthStatus } from "@/hooks"
import { cn } from "@/lib/utils"
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip"

export function Header() {
  const toggleSidebar = useAppStore((state) => state.toggleSidebar)
  const sidebarOpen = useAppStore((state) => state.sidebarOpen)
  const { data: health, isLoading } = useHealthStatus()

  const isHealthy = health?.status === "healthy"

  return (
    <header
      className={cn(
        "fixed top-0 z-30 flex h-16 items-center border-b bg-background transition-all duration-300",
        sidebarOpen ? "left-64" : "left-16",
        "right-0"
      )}
    >
      <div className="flex w-full items-center justify-between px-4">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={toggleSidebar}>
            <Menu className="h-5 w-5" />
          </Button>
        </div>

        <div className="flex items-center gap-4">
          <Tooltip>
            <TooltipTrigger asChild>
              <div className="flex items-center gap-2">
                {isLoading ? (
                  <Activity className="h-4 w-4 animate-pulse text-muted-foreground" />
                ) : isHealthy ? (
                  <CheckCircle className="h-4 w-4 text-green-500" />
                ) : (
                  <XCircle className="h-4 w-4 text-red-500" />
                )}
                <span
                  className={cn(
                    "text-sm font-medium",
                    isHealthy ? "text-green-500" : "text-red-500"
                  )}
                >
                  {isLoading ? "Checking..." : isHealthy ? "Healthy" : "Unhealthy"}
                </span>
              </div>
            </TooltipTrigger>
            <TooltipContent>
              {health ? (
                <div className="space-y-1 text-xs">
                  <div className="flex items-center gap-2">
                    <span>Database:</span>
                    {health.database ? (
                      <CheckCircle className="h-3 w-3 text-green-500" />
                    ) : (
                      <XCircle className="h-3 w-3 text-red-500" />
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    <span>Redis:</span>
                    {health.redis ? (
                      <CheckCircle className="h-3 w-3 text-green-500" />
                    ) : (
                      <XCircle className="h-3 w-3 text-red-500" />
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    <span>Ollama:</span>
                    {health.ollama ? (
                      <CheckCircle className="h-3 w-3 text-green-500" />
                    ) : (
                      <XCircle className="h-3 w-3 text-red-500" />
                    )}
                  </div>
                </div>
              ) : (
                <span>Unable to fetch health status</span>
              )}
            </TooltipContent>
          </Tooltip>
        </div>
      </div>
    </header>
  )
}
