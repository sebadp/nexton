import { useEffect, useRef, useState } from "react"
import {
    CheckCircle2,
    Loader2,
    AlertCircle,
    Linkedin,
    Package,
    Circle,
    ChevronDown,
    ChevronRight,
    Brain,
    ThumbsUp,
    ThumbsDown
} from "lucide-react"
import type { ScrapingEvent } from "@/hooks/useScrapingStream"
import { cn } from "@/lib/utils"
import { Badge } from "@/components/ui/badge"

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

    if (event.status === "done" || event.status === "completed" || event.status === "success") {
        return <CheckCircle2 className="h-4 w-4 text-green-500" />
    }

    // Only show spinner for the active (last) event while streaming
    if (isLast && isStreaming) {
        return <Loader2 className="h-4 w-4 animate-spin text-blue-500" />
    }

    // Past progress events show a static circle
    return <Circle className="h-2 w-2 text-muted-foreground/40 fill-current" />
}

export function ScrapingProgress({ events, isStreaming, className }: ScrapingProgressProps) {
    const scrollRef = useRef<HTMLDivElement>(null)
    // Track expanded state for reasoning items. Key: index
    const [expandedItems, setExpandedItems] = useState<Record<number, boolean>>({})

    // Auto-scroll to bottom when events update
    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight
        }
    }, [events])

    const toggleExpand = (index: number) => {
        setExpandedItems(prev => ({
            ...prev,
            [index]: !prev[index]
        }))
    }

    // Identify if an event has rich details to show
    const hasDetails = (event: ScrapingEvent) => {
        if (!event.detail) return false

        // Has reasoning?
        if (event.detail.reasoning) return true
        if (event.detail.tech_stack_reasoning) return true

        // Has extraction data?
        if (event.step === "extracted" && (event.detail.company || event.detail.role)) return true

        // Has scoring data?
        if (event.step === "scored" && event.detail.total_score !== undefined) return true

        // Has filter data?
        if (event.step === "filtered" && event.detail.failed_filters) return true

        return false
    }

    return (
        <div
            ref={scrollRef}
            className={cn("space-y-2 text-sm max-h-[400px] overflow-y-auto pr-2 custom-scrollbar", className)}
        >
            {events.map((event, index) => {
                const isLast = index === events.length - 1
                const showDetails = hasDetails(event)
                const isExpanded = expandedItems[index]

                // Determine if this is a "thinking" step
                const isThinking = isLast && isStreaming && event.status !== "done" && event.status !== "completed"

                return (
                    <div
                        key={index}
                        className={cn(
                            "flex flex-col gap-1 rounded-md px-2 py-1.5 transition-colors border border-transparent",
                            event.event === "completed" && "bg-green-500/5 border-green-500/20",
                            event.event === "error" && "bg-red-500/5 border-red-500/20",
                            event.event === "opportunity_created" && "bg-blue-500/5 border-blue-500/20",
                            isThinking && "bg-muted/30"
                        )}
                    >
                        <div className="flex items-start gap-2">
                            <span className="mt-0.5 flex-shrink-0 flex items-center justify-center w-4 h-4">
                                {getEventIcon(event, isLast, isStreaming)}
                            </span>

                            <div className="flex-1 min-w-0">
                                <div className="flex items-center justify-between">
                                    <p className={cn(
                                        "leading-tight transition-colors",
                                        isThinking ? "text-blue-500 font-medium animate-pulse" : "text-foreground"
                                    )}>
                                        {event.message}
                                    </p>

                                    {showDetails && !isThinking && (
                                        <button
                                            onClick={() => toggleExpand(index)}
                                            className="text-xs text-muted-foreground hover:text-foreground flex items-center gap-1 transition-colors"
                                        >
                                            {isExpanded ? "Hide" : "Details"}
                                            {isExpanded ? <ChevronDown className="h-3 w-3" /> : <ChevronRight className="h-3 w-3" />}
                                        </button>
                                    )}
                                </div>

                                {/* Opportunity Created Summary */}
                                {event.event === "opportunity_created" && event.company && (
                                    <div className="mt-1 flex flex-wrap gap-2">
                                        <Badge variant="outline" className="text-xs font-normal bg-background/50">
                                            {event.role} @ {event.company}
                                        </Badge>
                                        <Badge variant="secondary" className="text-xs font-normal">
                                            {event.tier} tier
                                        </Badge>
                                        <Badge variant="outline" className={cn(
                                            "text-xs font-normal",
                                            (event.score || 0) >= 80 ? "text-green-500 border-green-200" :
                                                (event.score || 0) >= 50 ? "text-yellow-500 border-yellow-200" : "text-gray-500"
                                        )}>
                                            {event.score} pts
                                        </Badge>
                                    </div>
                                )}
                            </div>
                        </div>

                        {/* Collapsible Details */}
                        {showDetails && (isExpanded || isThinking) && (
                            <div className="ml-6 space-y-2 pt-1 pb-1 animate-in fade-in slide-in-from-top-1 duration-200">
                                {/* Reasoning Block */}
                                {event.detail?.reasoning && (
                                    <div className="text-xs bg-muted/40 p-2 rounded border border-border/50">
                                        <div className="flex items-center gap-1.5 text-muted-foreground mb-1">
                                            <Brain className="h-3 w-3" />
                                            <span className="font-medium">Reasoning</span>
                                        </div>
                                        <p className="text-muted-foreground/90 pl-4.5 border-l-2 border-muted pl-2">
                                            {event.detail.reasoning}
                                        </p>
                                    </div>
                                )}

                                {/* Extraction Data */}
                                {event.step === "extracted" && event.detail && (
                                    <div className="flex flex-wrap gap-2 text-xs">
                                        <div className="bg-muted/30 px-2 py-1 rounded flex items-center gap-1">
                                            <span className="text-muted-foreground">Company:</span>
                                            <span className="font-medium">{event.detail.company || "Unknown"}</span>
                                        </div>
                                        <div className="bg-muted/30 px-2 py-1 rounded flex items-center gap-1">
                                            <span className="text-muted-foreground">Role:</span>
                                            <span className="font-medium">{event.detail.role || "Unknown"}</span>
                                        </div>
                                        <div className="bg-muted/30 px-2 py-1 rounded flex items-center gap-1">
                                            <span className="text-muted-foreground">Tech:</span>
                                            <span className="font-medium">{(event.detail.tech_stack || []).join(", ") || "None"}</span>
                                        </div>
                                    </div>
                                )}

                                {/* Scoring Breakdown */}
                                {event.step === "scored" && event.detail && (
                                    <div className="grid gap-2 text-xs bg-muted/30 p-2 rounded">
                                        <div className="grid grid-cols-[1fr_auto] gap-2 items-start">
                                            <span className="text-muted-foreground">Stack Match:</span>
                                            <div className="text-right">
                                                <span className="font-mono font-medium">{event.detail.tech_stack_score}/30</span>
                                                {event.detail.tech_stack_reasoning && (
                                                    <p className="text-[10px] text-muted-foreground text-left mt-0.5">{event.detail.tech_stack_reasoning}</p>
                                                )}
                                            </div>
                                        </div>
                                        <div className="grid grid-cols-[1fr_auto] gap-2 items-start border-t border-border/40 pt-1">
                                            <span className="text-muted-foreground">Salary:</span>
                                            <div className="text-right">
                                                <span className="font-mono font-medium">{event.detail.salary_score}/20</span>
                                                {event.detail.salary_reasoning && (
                                                    <p className="text-[10px] text-muted-foreground text-left mt-0.5">{event.detail.salary_reasoning}</p>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                )}

                                {/* Filter Results */}
                                {event.step === "filtered" && event.detail && (
                                    <div className="text-xs">
                                        {event.detail.passed ? (
                                            <div className="flex items-center gap-1.5 text-green-600 dark:text-green-400">
                                                <ThumbsUp className="h-3 w-3" />
                                                <span>Passed all hard filters</span>
                                            </div>
                                        ) : (
                                            <div className="space-y-1">
                                                <div className="flex items-center gap-1.5 text-red-600 dark:text-red-400 font-medium">
                                                    <ThumbsDown className="h-3 w-3" />
                                                    <span>Failed filters:</span>
                                                </div>
                                                <ul className="list-disc pl-5 space-y-0.5 text-muted-foreground">
                                                    {(event.detail.failed_filters || []).map((filter: string, i: number) => (
                                                        <li key={i}>{filter}</li>
                                                    ))}
                                                </ul>
                                            </div>
                                        )}
                                    </div>
                                )}
                            </div>
                        )}
                    </div>
                )
            })}

            {isStreaming && events.length === 0 && (
                <div className="flex items-center gap-2 text-muted-foreground px-2 py-4 justify-center">
                    <Loader2 className="h-5 w-5 animate-spin text-blue-500" />
                    <span className="animate-pulse">Connecting to LinkedIn...</span>
                </div>
            )}
        </div>
    )
}
