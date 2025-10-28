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
            <TabsTrigger value="log">{ru.executionView.tabs.log}</TabsTrigger>
            {/* AICODE-NOTE: T028 - Result tab disabled until finalArticle is set */}
            <TabsTrigger value="result" disabled={!finalArticle}>
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
                  {logLines.map((line, index) => (
                    <div key={index} className="py-0.5">
                      {line}
                    </div>
                  ))}
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
