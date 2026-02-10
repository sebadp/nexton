import { useState } from "react"
import { Linkedin, Loader2, Square, CheckCircle2, XCircle, Clock } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { useScrapingStatus, useScrapingStream, toast } from "@/hooks"
import { formatDateTime } from "@/lib/utils"
import { ScrapingProgress } from "./ScrapingProgress"

export function ScrapeButton() {
  const [dialogOpen, setDialogOpen] = useState(false)
  const { data: status, isLoading: statusLoading, refetch } = useScrapingStatus()
  const { events, isStreaming, startStream, reset } = useScrapingStream()

  const isRunning = (status?.is_running ?? false) || isStreaming

  const handleScrape = () => {
    reset()
    startStream(20, true)
  }

  const handleDialogChange = (open: boolean) => {
    if (!open && !isStreaming) {
      // Dialog closing and not streaming - reset and close
      reset()
      setDialogOpen(false)
      refetch() // Refresh status after closing
    } else if (!open && isStreaming) {
      // Don't close while streaming
      return
    } else {
      setDialogOpen(open)
    }
  }

  // When streaming completes, show toast
  const lastEvent = events[events.length - 1]
  if (lastEvent?.event === "completed" || (lastEvent?.event === "error" && lastEvent?.status)) {
    if (lastEvent.event === "completed" && lastEvent.status === "success") {
      // Small delay to let user see the final state
      setTimeout(() => {
        toast({
          variant: "success",
          title: "Scraping exitoso",
          description: lastEvent.message,
        })
      }, 500)
    } else if (lastEvent.event === "completed" && lastEvent.status === "no_messages") {
      setTimeout(() => {
        toast({
          title: "Scraping completado",
          description: lastEvent.message,
        })
      }, 500)
    } else if (lastEvent.event === "error") {
      setTimeout(() => {
        toast({
          variant: "destructive",
          title: "Error",
          description: lastEvent.message,
        })
      }, 500)
    }
  }

  return (
    <Card>
      <CardContent className="pt-6">
        <div className="flex items-center justify-between">
          <div className="space-y-1">
            <h3 className="font-semibold">LinkedIn Scanner</h3>
            {status?.last_run ? (
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                {status.last_run_status === "success" ? (
                  <CheckCircle2 className="h-4 w-4 text-green-500" />
                ) : status.last_run_status === "failed" ? (
                  <XCircle className="h-4 w-4 text-red-500" />
                ) : (
                  <Clock className="h-4 w-4" />
                )}
                <span>
                  Last run: {formatDateTime(status.last_run)}
                  {status.last_run_count !== null && ` (${status.last_run_count} messages)`}
                </span>
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">No previous scans</p>
            )}
          </div>

          <div className="flex items-center gap-2">
            {isRunning && !isStreaming ? (
              <>
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span>Scanning...</span>
                </div>
                <Button variant="outline" size="sm" disabled>
                  <Square className="mr-2 h-4 w-4" />
                  Stop
                </Button>
              </>
            ) : (
              <Dialog open={dialogOpen} onOpenChange={handleDialogChange}>
                <DialogTrigger asChild>
                  <Button disabled={statusLoading || isStreaming}>
                    <Linkedin className="mr-2 h-4 w-4" />
                    Scan LinkedIn
                  </Button>
                </DialogTrigger>
                <DialogContent className="max-w-lg">
                  <DialogHeader>
                    <DialogTitle>Scan LinkedIn Messages</DialogTitle>
                    <DialogDescription>
                      {isStreaming
                        ? "Scanning in progress. Please wait..."
                        : "This will connect to your LinkedIn account and scan for new recruiter messages."}
                    </DialogDescription>
                  </DialogHeader>

                  {isStreaming || events.length > 0 ? (
                    <div className="py-2 max-h-80 overflow-y-auto">
                      <ScrapingProgress events={events} isStreaming={isStreaming} />
                    </div>
                  ) : (
                    <div className="py-4">
                      <p className="text-sm text-muted-foreground">The scan will:</p>
                      <ul className="mt-2 list-inside list-disc text-sm text-muted-foreground">
                        <li>Fetch up to 20 unread messages</li>
                        <li>Extract company, role, salary, and tech stack</li>
                        <li>Calculate match scores based on your profile</li>
                        <li>Generate AI responses for each opportunity</li>
                      </ul>
                    </div>
                  )}

                  <DialogFooter>
                    {!isStreaming && events.length === 0 && (
                      <>
                        <Button variant="outline" onClick={() => setDialogOpen(false)}>
                          Cancel
                        </Button>
                        <Button onClick={handleScrape}>
                          <Linkedin className="mr-2 h-4 w-4" />
                          Start Scan
                        </Button>
                      </>
                    )}
                    {!isStreaming && events.length > 0 && (
                      <Button onClick={() => handleDialogChange(false)}>
                        Close
                      </Button>
                    )}
                    {isStreaming && (
                      <Button disabled>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Scanning...
                      </Button>
                    )}
                  </DialogFooter>
                </DialogContent>
              </Dialog>
            )}
          </div>
        </div>

        {isRunning && !isStreaming && status?.task_status && (
          <div className="mt-4 rounded-lg bg-muted p-3">
            <p className="text-sm">
              <span className="font-medium">Status:</span> {status.task_status}
            </p>
            {status.task_progress && (
              <p className="text-sm text-muted-foreground">
                {JSON.stringify(status.task_progress)}
              </p>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
