import { useEffect, useRef } from "react"
import { CheckCircle2, Loader2, AlertCircle, Linkedin, Package, Circle } from "lucide-react"
import type { ScrapingEvent } from "@/hooks/useScrapingStream"
import { cn } from "@/lib/utils"

interface ScrapingProgressProps {
    events: ScrapingEvent[]
    isStreaming: boolean
    className?: string
}

function getEventIcon(event: ScrapingEvent, isLast: boolean, isStreaming: boolean) {
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
        return event.status === "done" ? (
            <CheckCircle2 className="h-4 w-4 text-green-500" />
        ) : (
            <Linkedin className="h-4 w-4 text-blue-600" />
        )
    }

    if (event.status === "done") {
        return <CheckCircle2 className="h-4 w-4 text-green-500" />
    }

    // Only show spinner for the active (last) event while streaming
    if (isLast && isStreaming) {
        return <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
    }

    // Past progress events show a static circle
    return <Circle className="h-2 w-2 text-muted-foreground/40 fill-current" />
}

export function ScrapingProgress({ events, isStreaming, className }: ScrapingProgressProps) {
    const scrollRef = useRef<HTMLDivElement>(null)

    // Auto-scroll to bottom when events update
    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight
        }
    }, [events])

    return (
        <div
            ref={scrollRef}
            className={cn("space-y-2 text-sm max-h-[300px] overflow-y-auto pr-2 custom-scrollbar", className)}
        >
            {events.map((event, index) => {
                const isLast = index === events.length - 1
                return (
                    <div
                        key={index}
                        className={cn(
                            "flex items-start gap-2 rounded-md px-2 py-1.5 transition-colors",
                            event.event === "completed" && "bg-green-500/10",
                            event.event === "error" && event.status && "bg-red-500/10",
                            event.event === "opportunity_created" && "bg-blue-500/10",
                        )}
                    >
                        <span className="mt-0.5 flex-shrink-0 flex items-center justify-center w-4 h-4">
                            {getEventIcon(event, isLast, isStreaming)}
                        </span>
                        <div className="flex-1 min-w-0">
                            <p className="text-foreground leading-tight">{event.message}</p>
                            {event.event === "opportunity_created" && event.company && (
                                <p className="text-xs text-muted-foreground mt-0.5">
                                    {event.role} @ {event.company} • {event.tier} tier • {event.score} pts
                                </p>
                            )}
                        </div>
                    </div>
                )
            })}

            {isStreaming && events.length === 0 && (
                <div className="flex items-center gap-2 text-muted-foreground px-2">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    <span>Conectando...</span>
                </div>
            )}
        </div>
    )
}
