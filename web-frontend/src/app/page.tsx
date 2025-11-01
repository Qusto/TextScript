// AICODE-NOTE: Main page for article generation with SSE streaming (T033-T040)
// Integrates InputForm and ExecutionView components
// Uses EventSource API for real-time progress updates from backend
'use client'

import { useState } from 'react'
import { InputForm } from '@/components/input-form'
import { ExecutionView } from '@/components/execution-view'
import { ThemeToggle } from '@/components/theme-toggle'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { AlertCircle } from 'lucide-react'
import { StyleProfile } from '@/types/profile'

export default function Home() {
  // AICODE-NOTE: T033 - State management for article generation
  const [isLoading, setIsLoading] = useState(false)
  const [logLines, setLogLines] = useState<string[]>([])
  const [finalArticle, setFinalArticle] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  // AICODE-NOTE: T110 - Profile state management
  // Passed to StyleProfileSection which updates when profile is created/deleted
  const [currentProfile, setCurrentProfile] = useState<StyleProfile | null>(null)

  // AICODE-NOTE: T110 - Callback from StyleProfileSection when profile changes
  const handleProfileUpdate = (profile: StyleProfile | null) => {
    setCurrentProfile(profile)
  }

  // AICODE-NOTE: T108 - Updated handleSubmit to use POST /api/generate
  // AICODE-NOTE: Phase 11.2 - Added wordCount parameter
  // Uses fetch with ReadableStream for SSE since EventSource doesn't support POST
  const handleSubmit = async (data: { title: string; keyPoints?: string; enableResearch: boolean; wordCount: number }) => {
    // AICODE-NOTE: T052 - Reset all state including error when starting new generation
    setIsLoading(true)
    setLogLines([])
    setFinalArticle(null)
    setError(null)

    // AICODE-NOTE: T127 - Removed mandatory profile check, now optional
    // profileId will be null if no profile is loaded

    try {
      const url = `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/generate`

      // AICODE-NOTE: T108 - Send POST request with JSON body
      // AICODE-NOTE: T127 - profileId is now optional (null if no profile)
      // AICODE-NOTE: Phase 11.2 - Include wordCount in request
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          title: data.title,
          keyPoints: data.keyPoints || undefined,
          profileId: currentProfile?.id || null,
          enableResearch: data.enableResearch,
          wordCount: data.wordCount,  // Phase 11.2: Target article length
        }),
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      // AICODE-NOTE: T109 - Read SSE stream from fetch response body
      const reader = response.body?.getReader()
      const decoder = new TextDecoder()

      if (!reader) {
        throw new Error('Response body is not readable')
      }

      // AICODE-NOTE: Process SSE stream
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()

        if (done) {
          break
        }

        // Decode chunk and add to buffer
        buffer += decoder.decode(value, { stream: true })

        // AICODE-NOTE: Process complete SSE messages (split by double newline)
        const lines = buffer.split('\n\n')
        buffer = lines.pop() || '' // Keep incomplete message in buffer

        for (const line of lines) {
          if (!line.trim() || !line.startsWith('data: ')) {
            continue
          }

          try {
            // AICODE-NOTE: Parse SSE data field
            const jsonStr = line.substring(6) // Remove "data: " prefix
            const eventData = JSON.parse(jsonStr)

            if (eventData.type === 'log') {
              // AICODE-NOTE: T035 - Append log message to logLines array
              setLogLines((prev) => [...prev, eventData.message])
            } else if (eventData.type === 'result') {
              // AICODE-NOTE: T036 - Result handler sets finalArticle and isLoading=false
              setFinalArticle(eventData.message)
              setIsLoading(false)
            } else if (eventData.type === 'error') {
              // AICODE-NOTE: T051 - Handle backend error events
              setError(eventData.message || 'Произошла ошибка')
              setIsLoading(false)
            } else if (eventData.type === 'close') {
              // AICODE-NOTE: T037 - Close event indicates stream end
              break
            }
          } catch (err) {
            console.error('Failed to parse SSE message:', err, line)
          }
        }
      }

      // AICODE-NOTE: Ensure loading state is cleared
      setIsLoading(false)
    } catch (err) {
      console.error('Fetch error:', err)
      setError('Ошибка подключения. Попробуйте снова.')
      setIsLoading(false)
    }
  }

  return (
    // AICODE-NOTE: T040 - Layout: single-column max-w-3xl container with dark zinc theme
    // Using min-h-screen for full viewport height and centered content
    <div className="min-h-screen bg-background">
      <main className="container mx-auto px-4 py-2 max-w-3xl">
        {/* Header with Theme Toggle */}
        {/* AICODE-NOTE: T055 - Added ThemeToggle component to header for theme switching */}
        {/* AICODE-NOTE: T165 - Optimized header: removed subtitle, moved title to header row (saves ~40px) */}
        <div className="mb-3">
          <div className="flex justify-between items-center mb-3">
            <h1 className="text-3xl font-bold tracking-tight">
              TextScript
            </h1>
            <ThemeToggle />
          </div>
        </div>

        {/* AICODE-NOTE: T040 - Vertical spacing with space-y-8 for consistent gaps */}
        <div className="space-y-8">
          {/* Input Form */}
          <InputForm
            onSubmit={handleSubmit}
            isLoading={isLoading}
            currentProfile={currentProfile}
            onProfileUpdate={handleProfileUpdate}
          />

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
