// AICODE-NOTE: ExecutionView component for displaying generation logs and results (T026-T029, T038-T039)
// Uses shadcn/ui Tabs component for log/result views
// Implements auto-scroll for log display and copy/download functionality
// AICODE-NOTE: T083 - Russian localization applied (FR-026)
'use client'

import { useEffect, useRef, useState } from 'react'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Copy, Download, Check } from 'lucide-react'
import { ru } from '@/lib/i18n'

interface ExecutionViewProps {
  logLines: string[]
  finalArticle: string | null
}

// AICODE-NOTE: Parse log line into structured format for colorized display
interface ParsedLogLine {
  timestamp: string
  level: 'INFO' | 'SUCCESS' | 'WARNING' | 'ERROR' | 'DEBUG' | null
  message: string
  raw: string
}

function parseLogLine(line: string): ParsedLogLine {
  // Format: "HH:MM:SS | LEVEL     | message"
  const match = line.match(/^(\d{2}:\d{2}:\d{2})\s*\|\s*(\w+)\s*\|\s*(.+)$/)

  if (match) {
    const [, timestamp, level, message] = match
    return {
      timestamp,
      level: level as ParsedLogLine['level'],
      message: message.trim(),
      raw: line
    }
  }

  // Fallback for lines that don't match format
  return {
    timestamp: '',
    level: null,
    message: line,
    raw: line
  }
}

// AICODE-NOTE: Get color classes for log level
function getLevelColor(level: ParsedLogLine['level']): string {
  switch (level) {
    case 'SUCCESS':
      return 'text-green-600 dark:text-green-400'
    case 'ERROR':
      return 'text-red-600 dark:text-red-400'
    case 'WARNING':
      return 'text-yellow-600 dark:text-yellow-400'
    case 'INFO':
      return 'text-blue-600 dark:text-blue-400'
    case 'DEBUG':
      return 'text-gray-500 dark:text-gray-400'
    default:
      return 'text-foreground'
  }
}

export function ExecutionView({ logLines, finalArticle }: ExecutionViewProps) {
  // AICODE-NOTE: T027 - Auto-scroll to bottom when new log lines are added
  const logEndRef = useRef<HTMLDivElement>(null)

  // AICODE-NOTE: T038 - Copy feedback state
  const [copied, setCopied] = useState(false)

  // AICODE-NOTE: T027 - Scroll to bottom whenever logLines change
  useEffect(() => {
    if (logEndRef.current) {
      logEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [logLines])

  // AICODE-NOTE: T038 - Copy article to clipboard using navigator.clipboard API
  const handleCopy = async () => {
    if (!finalArticle) return

    try {
      await navigator.clipboard.writeText(finalArticle)
      setCopied(true)
      // Reset copied state after 2 seconds
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      console.error('Failed to copy:', err)
    }
  }

  // AICODE-NOTE: T039 - Download article as .md file using Blob API
  const handleDownload = () => {
    if (!finalArticle) return

    // Create Blob with markdown content
    const blob = new Blob([finalArticle], { type: 'text/markdown' })
    const url = URL.createObjectURL(blob)

    // Create temporary link and trigger download
    const link = document.createElement('a')
    link.href = url
    link.download = `article-${Date.now()}.md`
    document.body.appendChild(link)
    link.click()

    // Cleanup
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  }

  return (
    <Card className="w-full">
      <CardHeader>
        {/* AICODE-NOTE: T083 - Russian translation applied */}
        <CardTitle>{ru.executionView.title}</CardTitle>
        <CardDescription>
          {ru.executionView.description}
        </CardDescription>
      </CardHeader>
      <CardContent>
        {/* AICODE-NOTE: T026 - Tabs component with Log and Result tabs */}
        <Tabs defaultValue="log" className="w-full">
          <TabsList className="grid w-full grid-cols-2">
            {/* AICODE-NOTE: T083 - Russian tab labels */}
            {/* AICODE-NOTE: WCAG 2.5.5 AA - Minimum touch target 44x44px height (h-11) */}
            <TabsTrigger value="log" className="h-11">{ru.executionView.tabs.log}</TabsTrigger>
            {/* AICODE-NOTE: T028 - Result tab disabled until finalArticle is set */}
            {/* AICODE-NOTE: WCAG 2.5.5 AA - Minimum touch target 44x44px height (h-11) */}
            <TabsTrigger value="result" disabled={!finalArticle} className="h-11">
              {ru.executionView.tabs.result}
            </TabsTrigger>
          </TabsList>

          {/* AICODE-NOTE: T027 - Log tab content with pre-formatted scrollable block */}
          <TabsContent value="log" className="mt-4">
            <div className="rounded-lg border bg-muted/50 p-4 overflow-auto max-h-[500px]">
              {logLines.length === 0 ? (
                <p className="text-sm text-muted-foreground">
                  {/* AICODE-NOTE: T083 - Russian waiting message */}
                  {ru.executionView.log.waiting}
                </p>
              ) : (
                <pre className="text-xs font-mono whitespace-pre-wrap break-words">
                  {logLines.map((line, index) => {
                    const parsed = parseLogLine(line)

                    return (
                      <div key={index} className="py-0.5 flex gap-2">
                        {/* Timestamp - muted gray */}
                        {parsed.timestamp && (
                          <span className="text-muted-foreground shrink-0">
                            {parsed.timestamp}
                          </span>
                        )}

                        {/* Level - colorized */}
                        {parsed.level && (
                          <>
                            <span className="text-muted-foreground">|</span>
                            <span className={`${getLevelColor(parsed.level)} font-semibold shrink-0 min-w-[60px]`}>
                              {parsed.level}
                            </span>
                            <span className="text-muted-foreground">|</span>
                          </>
                        )}

                        {/* Message - default color, supports emojis */}
                        <span className="flex-1">{parsed.message}</span>
                      </div>
                    )
                  })}
                  {/* AICODE-NOTE: Invisible div used for auto-scroll target */}
                  <div ref={logEndRef} />
                </pre>
              )}
            </div>
          </TabsContent>

          {/* AICODE-NOTE: T028 - Result tab content (only enabled when finalArticle exists) */}
          <TabsContent value="result" className="mt-4">
            <div className="space-y-4">
              {/* AICODE-NOTE: T029 - Copy and Download buttons */}
              {/* AICODE-NOTE: T083 - Russian button labels */}
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleCopy}
                  className="gap-2"
                >
                  {copied ? (
                    <>
                      <Check className="h-4 w-4" />
                      {ru.executionView.result.buttons.copied}
                    </>
                  ) : (
                    <>
                      <Copy className="h-4 w-4" />
                      {ru.executionView.result.buttons.copy}
                    </>
                  )}
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleDownload}
                  className="gap-2"
                >
                  <Download className="h-4 w-4" />
                  {ru.executionView.result.buttons.download}
                </Button>
              </div>

              {/* Article content display */}
              <div className="rounded-lg border bg-muted/50 p-4 overflow-auto max-h-[500px]">
                {finalArticle ? (
                  <pre className="text-sm font-mono whitespace-pre-wrap break-words">
                    {finalArticle}
                  </pre>
                ) : (
                  <p className="text-sm text-muted-foreground">
                    {/* AICODE-NOTE: T083 - Russian empty state message */}
                    {ru.executionView.result.empty}
                  </p>
                )}
              </div>
            </div>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  )
}
