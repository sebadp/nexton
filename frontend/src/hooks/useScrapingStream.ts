import { useState, useCallback, useRef } from "react"

export interface ScrapingEvent {
    event: string
    message?: string
    step?: string
    status?: string
    current?: number
    total?: number
    count?: number
    sender?: string
    id?: number
    company?: string
    role?: string
    score?: number
    tier?: string
    opportunities_created?: number
    messages_found?: number
    duration_seconds?: number
    detail?: any
    reasoning?: string
    tech_stack_reasoning?: string
    salary_reasoning?: string
    seniority_reasoning?: string
    company_reasoning?: string
}

export interface UseScrapingStreamResult {
    events: ScrapingEvent[]
    isStreaming: boolean
    currentStep: string | null
    latestMessage: string | null
    progress: { current: number; total: number } | null
    startStream: (limit?: number, unreadOnly?: boolean) => void
    stopStream: () => void
    reset: () => void
}

export function useScrapingStream(): UseScrapingStreamResult {
    const [events, setEvents] = useState<ScrapingEvent[]>([])
    const [isStreaming, setIsStreaming] = useState(false)
    const [currentStep, setCurrentStep] = useState<string | null>(null)
    const [latestMessage, setLatestMessage] = useState<string | null>(null)
    const [progress, setProgress] = useState<{ current: number; total: number } | null>(null)

    const eventSourceRef = useRef<EventSource | null>(null)

    const stopStream = useCallback(() => {
        if (eventSourceRef.current) {
            eventSourceRef.current.close()
            eventSourceRef.current = null
        }
        setIsStreaming(false)
    }, [])

    const reset = useCallback(() => {
        stopStream()
        setEvents([])
        setCurrentStep(null)
        setLatestMessage(null)
        setProgress(null)
    }, [stopStream])

    const startStream = useCallback((limit = 20, unreadOnly = true) => {
        // Reset state
        setEvents([])
        setCurrentStep(null)
        setLatestMessage(null)
        setProgress(null)
        setIsStreaming(true)

        const url = `/api/v1/scraping/trigger/stream?limit=${limit}&unread_only=${unreadOnly}`
        const eventSource = new EventSource(url)
        eventSourceRef.current = eventSource

        const handleEvent = (e: MessageEvent) => {
            try {
                const data: ScrapingEvent = JSON.parse(e.data)

                setEvents((prev) => {
                    const lastEvent = prev[prev.length - 1]
                    // Deduplicate logic: if same step and message index, update in place
                    // This allows "Thinking..." to turn into "Done" without a new row
                    if (
                        lastEvent &&
                        lastEvent.event === "progress" &&
                        data.event === "progress" &&
                        lastEvent.step === data.step &&
                        lastEvent.current === data.current
                    ) {
                        return [...prev.slice(0, -1), data]
                    }
                    return [...prev, data]
                })

                // Update current step
                if (data.step) {
                    setCurrentStep(data.step)
                } else if (data.event) {
                    setCurrentStep(data.event)
                }

                // Update latest message
                if (data.message) {
                    setLatestMessage(data.message)
                }

                // Update progress
                if (data.current !== undefined && data.total !== undefined) {
                    setProgress({ current: data.current, total: data.total })
                }

                // Close on completion or error
                if (data.event === "completed" || (data.event === "error" && data.status)) {
                    eventSource.close()
                    setIsStreaming(false)
                }
            } catch (err) {
                console.error("Failed to parse SSE event:", err)
            }
        }

        // Listen for all event types
        eventSource.addEventListener("started", handleEvent)
        eventSource.addEventListener("progress", handleEvent)
        eventSource.addEventListener("opportunity_created", handleEvent)
        eventSource.addEventListener("completed", handleEvent)
        eventSource.addEventListener("error", (e) => {
            // Check if it's a MessageEvent with data (SSE error event)
            if (e instanceof MessageEvent && e.data) {
                handleEvent(e)
            } else {
                // Connection error
                console.error("SSE connection error")
                setIsStreaming(false)
                eventSource.close()
            }
        })

        return () => {
            eventSource.close()
        }
    }, [])

    return {
        events,
        isStreaming,
        currentStep,
        latestMessage,
        progress,
        startStream,
        stopStream,
        reset,
    }
}
