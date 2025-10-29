/**
 * InputForm component for article generation (Phase 10 - Updated).
 *
 * AICODE-NOTE: T100-T103 - Reorganized form with accordion and new fields
 * Changes from Phase 1-9:
 * - T100: "Topic" renamed to "Название статьи" (title)
 * - T101: Added "Ключевые тезисы" field (keyPoints, optional)
 * - T102: Updated interface to match ArticleRequest
 * - T103: Three accordion sections:
 *   1. Контент (title, keyPoints)
 *   2. Стиль (StyleProfileSection)
 *   3. Настройки (research checkbox)
 * - T110: Disabled when no profile loaded
 */
'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Checkbox } from '@/components/ui/checkbox'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion'
import { StyleProfile } from '@/types/profile'
import StyleProfileSection from './style-profile-section'
import { ru } from '@/lib/i18n'

// AICODE-NOTE: T102 - Updated props interface for Phase 10
interface InputFormProps {
  onSubmit: (data: { title: string; keyPoints?: string; enableResearch: boolean }) => void
  isLoading: boolean
  currentProfile: StyleProfile | null
}

export function InputForm({ onSubmit, isLoading, currentProfile }: InputFormProps) {
  // AICODE-NOTE: T100 - State renamed from "topic" to "title"
  const [title, setTitle] = useState('')

  // AICODE-NOTE: T101 - New state for optional key points field
  const [keyPoints, setKeyPoints] = useState('')

  const [enableResearch, setEnableResearch] = useState(false)

  // AICODE-NOTE: Sprint 3.1 - Track current accordion section for progress stepper
  const [currentSection, setCurrentSection] = useState<string>('content')

  // AICODE-NOTE: T110 - Form valid only when profile exists AND title is not empty
  // This ensures user cannot generate article without creating style profile first
  const isFormValid = currentProfile !== null && title.trim() !== ''

  // AICODE-NOTE: T102 - Updated onSubmit handler with new data structure
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    if (!isFormValid || isLoading) {
      return
    }

    onSubmit({
      title: title.trim(),
      // AICODE-NOTE: T101 - keyPoints is optional: undefined if empty, otherwise trimmed value
      keyPoints: keyPoints.trim() || undefined,
      enableResearch,
    })
  }

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle>{ru.inputForm.formTitle}</CardTitle>
        <CardDescription>
          Укажите детали для генерации статьи в вашем стиле
        </CardDescription>
      </CardHeader>
      <CardContent className="p-4">
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* AICODE-NOTE: Sprint 3.1 - Progress stepper shows workflow: Content → Style → Settings
              Helps users understand the 3-step process and current position */}
          <div className="flex items-center justify-center gap-2 mb-4 text-sm">
            <span className={`font-medium transition-colors ${currentSection === 'content' ? 'text-blue-600 dark:text-blue-400' : 'text-muted-foreground'}`}>
              Шаг 1: Контент
            </span>
            <span className="text-muted-foreground">→</span>
            <span className={`font-medium transition-colors ${currentSection === 'style' ? 'text-green-600 dark:text-green-400' : 'text-muted-foreground'}`}>
              Шаг 2: Стиль
            </span>
            <span className="text-muted-foreground">→</span>
            <span className={`font-medium transition-colors ${currentSection === 'settings' ? 'text-purple-600 dark:text-purple-400' : 'text-muted-foreground'}`}>
              Шаг 3: Настройки
            </span>
          </div>

          {/* AICODE-NOTE: Sprint 3.1 - Changed to type="single" to prevent cognitive overload
              Progressive disclosure pattern: user focuses on one section at a time
              Only "Контент" section open by default to start workflow */}
          <Accordion
            type="single"
            defaultValue="content"
            collapsible
            className="w-full"
            onValueChange={(value) => setCurrentSection(value || 'content')}
          >

            {/* AICODE-NOTE: T103 - Section 1: Контент (Content) */}
            <AccordionItem value="content">
              {/* AICODE-NOTE: Sprint 3.1 - Blue accent for Content section */}
              <AccordionTrigger className="text-base font-semibold text-blue-600 dark:text-blue-400">
                {ru.inputForm.sections.content}
              </AccordionTrigger>
              <AccordionContent className="space-y-2 pt-3">

                {/* AICODE-NOTE: T100 - "Название статьи" field (replaces old "Тема") */}
                <div className="space-y-1.5">
                  <Label htmlFor="title">
                    {ru.inputForm.title.label}
                    {/* AICODE-NOTE: T085 - Required field indicator (asterisk) */}
                    <span className="text-destructive ml-1">*</span>
                  </Label>
                  <Input
                    id="title"
                    type="text"
                    placeholder={ru.inputForm.title.placeholder}
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    disabled={isLoading}
                    className="min-h-[44px]"
                    required
                  />
                </div>

                {/* AICODE-NOTE: T101 - "Ключевые тезисы" field (optional, multiline) */}
                <div className="space-y-1.5">
                  <Label htmlFor="keyPoints">
                    {ru.inputForm.keyPoints.label}
                    {/* AICODE-NOTE: No asterisk - this field is optional */}
                  </Label>
                  <Textarea
                    id="keyPoints"
                    placeholder={ru.inputForm.keyPoints.placeholder}
                    value={keyPoints}
                    onChange={(e) => setKeyPoints(e.target.value)}
                    disabled={isLoading}
                    rows={6}
                    className="resize-none"
                  />
                  <p className="text-xs text-muted-foreground">
                    Опционально: введите основные тезисы статьи по одному на строку
                  </p>
                </div>

              </AccordionContent>
            </AccordionItem>

            {/* AICODE-NOTE: T103 - Section 2: Стиль (Style Profile) */}
            <AccordionItem value="style">
              {/* AICODE-NOTE: Sprint 3.1 - Green accent for Style section */}
              <AccordionTrigger className="text-base font-semibold text-green-600 dark:text-green-400">
                {ru.inputForm.sections.style}
              </AccordionTrigger>
              <AccordionContent className="pt-3">
                {/* AICODE-NOTE: T103 - StyleProfileSection manages profile state internally
                    It doesn't receive currentProfile as prop - it loads from /api/profiles/current
                    The onProfileUpdate callback is currently not used but kept for future integration */}
                <StyleProfileSection onProfileUpdate={(profile) => {
                  // AICODE-TODO: T111 - Integrate profile updates with parent component
                  // Currently InputForm receives currentProfile as prop from parent (page.tsx)
                  // Future: Make InputForm manage profile state internally
                  console.log('Profile updated:', profile)
                }} />
              </AccordionContent>
            </AccordionItem>

            {/* AICODE-NOTE: T103 - Section 3: Настройки (Settings) */}
            <AccordionItem value="settings">
              {/* AICODE-NOTE: Sprint 3.1 - Purple accent for Settings section */}
              <AccordionTrigger className="text-base font-semibold text-purple-600 dark:text-purple-400">
                {ru.inputForm.sections.settings}
              </AccordionTrigger>
              <AccordionContent className="pt-3">

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
                    {ru.inputForm.research.label}
                  </Label>
                </div>

              </AccordionContent>
            </AccordionItem>

          </Accordion>

          {/* AICODE-NOTE: T110 - Warning when no profile loaded
              Shows alert to guide user to create profile in "Стиль" section */}
          {!currentProfile && (
            <Alert className="border-yellow-500 bg-yellow-50 dark:bg-yellow-950/20">
              <AlertDescription className="text-yellow-800 dark:text-yellow-200">
                {ru.inputForm.warnings.noProfile}
              </AlertDescription>
            </Alert>
          )}

          {/* Submit Button */}
          {/* AICODE-NOTE: T110 - Button disabled when:
              1. No profile loaded (currentProfile === null)
              2. Title is empty (title.trim() === '')
              3. Generation in progress (isLoading === true) */}
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
