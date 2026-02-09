import { CheckCircle2, Loader2, AlertCircle, Linkedin, Package } from "lucide-react"
import type { ScrapingEvent } from "@/hooks/useScrapingStream"
import { cn } from "@/lib/utils"

interface ScrapingProgressProps {
    events: ScrapingEvent[]
    isStreaming: boolean
    className?: string
}

function getEventIcon(event: ScrapingEvent) {
    if (event.event === "completed") {
        return <CheckCircle2 className="h-4 w-4 text-green-500" />
    }
    if (event.event === "error" && event.status) {
        return <AlertCircle className="h-4 w-4 text-red-500" />
    }
    if (event.event === "opportunity_created") {
        return <Package className="h-4 w-4 text-blue-500" />
    }
    if (event.step === "login") {
        return <Linkedin className="h-4 w-4 text-blue-600" />
    }
    return <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
}

export function ScrapingProgress({ events, isStreaming, className }: ScrapingProgressProps) {
    // Show only the latest events to avoid overwhelming the UI
    const displayEvents = events.slice(-8)

    return (
        <div className={cn("space-y-2 text-sm", className)}>
            {displayEvents.map((event, index) => (
                <div
                    key={index}
                    className={cn(
                        "flex items-start gap-2 rounded-md px-2 py-1.5 transition-colors",
                        event.event === "completed" && "bg-green-500/10",
                        event.event === "error" && event.status && "bg-red-500/10",
                        event.event === "opportunity_created" && "bg-blue-500/10",
                    )}
                >
                    <span className="mt-0.5 flex-shrink-0">{getEventIcon(event)}</span>
                    <div className="flex-1 min-w-0">
                        <p className="text-foreground">{event.message}</p>
                        {event.event === "opportunity_created" && event.company && (
                            <p className="text-xs text-muted-foreground">
                                {event.role} @ {event.company} • {event.tier} tier • {event.score} pts
                            </p>
                        )}
                    </div>
                </div>
            ))}

            {isStreaming && events.length === 0 && (
                <div className="flex items-center gap-2 text-muted-foreground">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    <span>Conectando...</span>
                </div>
            )}
        </div>
    )
}
