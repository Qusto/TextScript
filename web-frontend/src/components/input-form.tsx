// AICODE-NOTE: InputForm component for article generation input (T021-T025)
// Uses shadcn/ui components (Card, Input, Textarea, Checkbox, Button)
// Manages local state for topic, sourceUrls, and enableResearch
// Implements validation: button disabled when topic OR sourceUrls is empty
// AICODE-NOTE: T082 - Russian localization applied (FR-026)
'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Checkbox } from '@/components/ui/checkbox'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { ru } from '@/lib/i18n'

interface InputFormProps {
  onSubmit: (data: { topic: string; sourceUrls: string; enableResearch: boolean }) => void
  isLoading: boolean
}

export function InputForm({ onSubmit, isLoading }: InputFormProps) {
  // AICODE-NOTE: T022 - State management for form inputs
  const [topic, setTopic] = useState('')
  const [sourceUrls, setSourceUrls] = useState('')
  const [enableResearch, setEnableResearch] = useState(false)

  // AICODE-NOTE: T023 - Button disabled when topic OR sourceUrls is empty
  // This enforces validation before allowing form submission
  const isFormValid = topic.trim() !== '' && sourceUrls.trim() !== ''

  // AICODE-NOTE: T024 - onSubmit handler that passes data to parent callback
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    if (!isFormValid || isLoading) {
      return
    }

    onSubmit({
      topic: topic.trim(),
      sourceUrls: sourceUrls.trim(),
      enableResearch,
    })
  }

  return (
    <Card className="w-full">
      <CardHeader>
        {/* AICODE-NOTE: T082 - Russian translation applied */}
        <CardTitle>{ru.inputForm.title}</CardTitle>
        <CardDescription>
          {ru.inputForm.description}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Topic Input */}
          <div className="space-y-2">
            {/* AICODE-NOTE: T082 - Russian label */}
            {/* AICODE-NOTE: T085 - Required field indicator (asterisk) */}
            <Label htmlFor="topic">
              {ru.inputForm.topic.label}
              <span className="text-destructive ml-1">*</span>
            </Label>
            <Input
              id="topic"
              type="text"
              placeholder={ru.inputForm.topic.placeholder}
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              disabled={isLoading}
              className="min-h-[44px]"
              required
            />
          </div>

          {/* Source URLs Textarea */}
          <div className="space-y-2">
            {/* AICODE-NOTE: T082 - Russian label */}
            {/* AICODE-NOTE: T085 - Required field indicator (asterisk) */}
            <Label htmlFor="sourceUrls">
              {ru.inputForm.sourceUrls.label}
              <span className="text-destructive ml-1">*</span>
            </Label>
            <Textarea
              id="sourceUrls"
              placeholder={ru.inputForm.sourceUrls.placeholder}
              value={sourceUrls}
              onChange={(e) => setSourceUrls(e.target.value)}
              disabled={isLoading}
              rows={6}
              className="resize-none font-mono text-sm"
              required
            />
          </div>

          {/* Research Checkbox */}
          <div className="flex items-center space-x-2">
            <Checkbox
              id="enableResearch"
              checked={enableResearch}
              onCheckedChange={(checked) => setEnableResearch(checked === true)}
              disabled={isLoading}
            />
            <Label
              htmlFor="enableResearch"
              className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
            >
              {/* AICODE-NOTE: T082 - Russian label */}
              {ru.inputForm.research.label}
            </Label>
          </div>

          {/* Submit Button */}
          {/* AICODE-NOTE: T023 - Button disabled when form is invalid OR isLoading */}
          {/* AICODE-NOTE: T025 - Button shows "Generating..." text when isLoading=true */}
          {/* AICODE-NOTE: T082 - Russian button text */}
          <Button
            type="submit"
            disabled={!isFormValid || isLoading}
            className="w-full min-h-[44px]"
          >
            {isLoading ? ru.inputForm.button.submitting : ru.inputForm.button.submit}
          </Button>
        </form>
      </CardContent>
    </Card>
  )
}
