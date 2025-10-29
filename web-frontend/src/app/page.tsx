// AICODE-NOTE: Main page for article generation with SSE streaming (T033-T040)
// Integrates InputForm and ExecutionView components
// Uses EventSource API for real-time progress updates from backend
'use client'

import { useState, useRef, useEffect } from 'react'
import { InputForm } from '@/components/input-form'
import { ExecutionView } from '@/components/execution-view'
import { ThemeToggle } from '@/components/theme-toggle'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { AlertCircle } from 'lucide-react'

export default function Home() {
  // AICODE-NOTE: T033 - State management for article generation
  const [isLoading, setIsLoading] = useState(false)
  const [logLines, setLogLines] = useState<string[]>([])
  const [finalArticle, setFinalArticle] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  // AICODE-TODO: T111 - Add profile state management
  // For now, set to null to allow component to compile
  // Will be integrated with StyleProfileSection in future task
  const [currentProfile] = useState(null)

  // AICODE-NOTE: Ref to store EventSource instance for cleanup
  const eventSourceRef = useRef<EventSource | null>(null)

  // AICODE-NOTE: Cleanup EventSource on component unmount
  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close()
      }
    }
  }, [])

  // AICODE-NOTE: T034 - handleSubmit creates EventSource with query parameters
  // AICODE-TODO: T108 - Will be updated to use POST /api/generate with profile_id
  const handleSubmit = (data: { title: string; keyPoints?: string; enableResearch: boolean }) => {
    // AICODE-NOTE: T052 - Reset all state including error when starting new generation
    setIsLoading(true)
    setLogLines([])
    setFinalArticle(null)
    setError(null)

    // Close existing connection if any
    if (eventSourceRef.current) {
      eventSourceRef.current.close()
    }

    // AICODE-NOTE: Temporary compatibility layer - maps new interface to old API
    // TODO: T108 - Replace with POST request using profile_id
    const params = new URLSearchParams({
      topic: data.title, // Map title -> topic for old API
      source_urls: '', // Placeholder - will use profile_id in T108
      research: data.enableResearch.toString(),
    })

    const url = `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/generate?${params}`

    // AICODE-NOTE: T034 - Create EventSource for SSE connection
    const eventSource = new EventSource(url)
    eventSourceRef.current = eventSource

    // AICODE-NOTE: T035 - Message handler appends log lines to array
    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)

        if (data.type === 'log') {
          // Append log message to logLines array
          setLogLines((prev) => [...prev, data.message])
        } else if (data.type === 'result') {
          // AICODE-NOTE: T036 - Result handler sets finalArticle and isLoading=false
          setFinalArticle(data.article)
          setIsLoading(false)

          // AICODE-NOTE: T037 - Close EventSource connection after receiving result
          eventSource.close()
          eventSourceRef.current = null
        } else if (data.type === 'error') {
          // AICODE-NOTE: T051 - Handle backend error events (custom 'error' event type)
          // Display error message in Alert component with destructive variant
          setError(data.message || 'An error occurred')
          setIsLoading(false)
          eventSource.close()
          eventSourceRef.current = null
        }
      } catch (err) {
        console.error('Failed to parse SSE message:', err)
      }
    }

    // AICODE-NOTE: T050 - EventSource.onerror handler for connection failures
    // Triggers on network errors, server disconnections, or invalid SSE format
    eventSource.onerror = (err) => {
      console.error('EventSource error:', err)
      setError('Connection error. Please try again.')
      setIsLoading(false)
      eventSource.close()
      eventSourceRef.current = null
    }
  }

  return (
    // AICODE-NOTE: T040 - Layout: single-column max-w-3xl container with dark zinc theme
    // Using min-h-screen for full viewport height and centered content
    <div className="min-h-screen bg-background">
      <main className="container mx-auto px-4 py-8 max-w-3xl">
        {/* Header with Theme Toggle */}
        {/* AICODE-NOTE: T055 - Added ThemeToggle component to header for theme switching */}
        <div className="mb-8">
          <div className="flex justify-between items-center mb-6">
            <div className="flex-1" />
            <ThemeToggle />
          </div>
          <div className="text-center">
            <h1 className="text-4xl font-bold tracking-tight mb-2">
              TextScript
            </h1>
            <p className="text-muted-foreground">
              AI-powered article generation with real-time progress tracking
            </p>
          </div>
        </div>

        {/* AICODE-NOTE: T040 - Vertical spacing with space-y-8 for consistent gaps */}
        <div className="space-y-8">
          {/* Input Form */}
          <InputForm onSubmit={handleSubmit} isLoading={isLoading} currentProfile={currentProfile} />

          {/* AICODE-NOTE: T051 - Error Display using shadcn/ui Alert with destructive variant */}
          {/* Shows above ExecutionView to ensure visibility */}
          {error && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {/* Execution View */}
          <ExecutionView logLines={logLines} finalArticle={finalArticle} />
        </div>
      </main>
    </div>
  )
}
