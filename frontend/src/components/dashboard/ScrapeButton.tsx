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
import { useScrapingStatus, useTriggerScraping, useCancelScraping, toast } from "@/hooks"
import { formatDateTime } from "@/lib/utils"

export function ScrapeButton() {
  const [dialogOpen, setDialogOpen] = useState(false)
  const { data: status, isLoading: statusLoading } = useScrapingStatus()
  const triggerMutation = useTriggerScraping()
  const cancelMutation = useCancelScraping()

  const isRunning = status?.is_running ?? false

  const handleScrape = async () => {
    try {
      const result = await triggerMutation.mutateAsync({ limit: 20, unread_only: true })
      setDialogOpen(false)

      // Show toast with the result message
      if (result.status === "failed") {
        toast({
          variant: "destructive",
          title: "Error en el scraping",
          description: result.message,
        })
      } else if (result.message?.includes("No hay mensajes") || result.message?.includes("no se crearon")) {
        toast({
          title: "Scraping completado",
          description: result.message,
        })
      } else {
        toast({
          variant: "success",
          title: "Scraping exitoso",
          description: result.message,
        })
      }
    } catch (error) {
      setDialogOpen(false)
      toast({
        variant: "destructive",
        title: "Error",
        description: error instanceof Error ? error.message : "Error al ejecutar el scraping",
      })
    }
  }

  const handleCancel = async () => {
    await cancelMutation.mutateAsync()
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
            {isRunning ? (
              <>
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span>Scanning...</span>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleCancel}
                  disabled={cancelMutation.isPending}
                >
                  <Square className="mr-2 h-4 w-4" />
                  Stop
                </Button>
              </>
            ) : (
              <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
                <DialogTrigger asChild>
                  <Button disabled={statusLoading}>
                    <Linkedin className="mr-2 h-4 w-4" />
                    Scan LinkedIn
                  </Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>Scan LinkedIn Messages</DialogTitle>
                    <DialogDescription>
                      This will connect to your LinkedIn account and scan for new recruiter
                      messages. Each message will be analyzed and scored automatically.
                    </DialogDescription>
                  </DialogHeader>
                  <div className="py-4">
                    <p className="text-sm text-muted-foreground">
                      The scan will:
                    </p>
                    <ul className="mt-2 list-inside list-disc text-sm text-muted-foreground">
                      <li>Fetch up to 20 unread messages</li>
                      <li>Extract company, role, salary, and tech stack</li>
                      <li>Calculate match scores based on your profile</li>
                      <li>Generate AI responses for each opportunity</li>
                    </ul>
                  </div>
                  <DialogFooter>
                    <Button variant="outline" onClick={() => setDialogOpen(false)}>
                      Cancel
                    </Button>
                    <Button onClick={handleScrape} disabled={triggerMutation.isPending}>
                      {triggerMutation.isPending ? (
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      ) : (
                        <Linkedin className="mr-2 h-4 w-4" />
                      )}
                      Start Scan
                    </Button>
                  </DialogFooter>
                </DialogContent>
              </Dialog>
            )}
          </div>
        </div>

        {isRunning && status?.task_status && (
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
