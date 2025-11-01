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
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion'
import { StyleProfile } from '@/types/profile'
import StyleProfileSection from './style-profile-section'
import { ru } from '@/lib/i18n'
import { FileText, Palette, Settings } from 'lucide-react'

// AICODE-NOTE: T102 - Updated props interface for Phase 10
// AICODE-NOTE: T131 - currentProfile no longer used for validation (profile is optional)
// AICODE-NOTE: Phase 11.2 - Added wordCount parameter for article length control
interface InputFormProps {
  onSubmit: (data: { title: string; keyPoints?: string; enableResearch: boolean; wordCount: number }) => void
  isLoading: boolean
  currentProfile: StyleProfile | null
  onProfileUpdate?: (profile: StyleProfile | null) => void
}

export function InputForm({ onSubmit, isLoading, onProfileUpdate }: InputFormProps) {
  // AICODE-NOTE: T100 - State renamed from "topic" to "title"
  const [title, setTitle] = useState('')

  // AICODE-NOTE: T101 - New state for optional key points field
  const [keyPoints, setKeyPoints] = useState('')

  const [enableResearch, setEnableResearch] = useState(false)

  // AICODE-NOTE: Phase 11.2 - Word count control for article length (default: 500 words)
  const [wordCount, setWordCount] = useState(500)

  // AICODE-NOTE: Sprint 3.1 - Track current accordion section for progress stepper
  const [currentSection, setCurrentSection] = useState<string>('content')

  // AICODE-NOTE: T110 - Form valid only when profile exists AND title is not empty
  // AICODE-NOTE: T131 - Removed profile dependency, now only checks title
  const isFormValid = title.trim() !== ''

  // AICODE-NOTE: T102 - Updated onSubmit handler with new data structure
  // AICODE-NOTE: Phase 11.2 - Added wordCount to submission data
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
      wordCount,  // Phase 11.2 - Article length in words
    })
  }

  return (
    // AICODE-NOTE: T188 - Increased border-radius for modern look: rounded-lg → rounded-xl
    // AICODE-NOTE: T189 - Added shadow for depth: shadow-sm → shadow-lg
    <Card className="w-full rounded-xl shadow-lg">
      <CardHeader>
        <CardTitle>{ru.inputForm.formTitle}</CardTitle>
        <CardDescription>
          Укажите детали для генерации статьи в вашем стиле
        </CardDescription>
      </CardHeader>
      <CardContent className="p-3">
        <form onSubmit={handleSubmit} className="space-y-3">
          {/* AICODE-NOTE: Sprint 3.1 - Progress stepper shows workflow: Content → Style → Settings
              Helps users understand the 3-step process and current position */}
          {/* AICODE-NOTE: T168 - Compact stepper: text-sm → text-xs, mb-4 → mb-2, gap-2 → gap-1 (saves ~15px) */}
          {/* AICODE-NOTE: T179 - Strengthened active step with font-semibold for better contrast */}
          <div className="flex items-center justify-center gap-1 mb-2 text-xs">
            <span className={`transition-colors ${currentSection === 'content' ? 'font-semibold text-blue-600 dark:text-blue-400' : 'font-medium text-muted-foreground'}`}>
              Шаг 1: Контент
            </span>
            <span className="text-muted-foreground">→</span>
            <span className={`transition-colors ${currentSection === 'style' ? 'font-semibold text-green-600 dark:text-green-400' : 'font-medium text-muted-foreground'}`}>
              Шаг 2: Стиль
            </span>
            <span className="text-muted-foreground">→</span>
            <span className={`transition-colors ${currentSection === 'settings' ? 'font-semibold text-purple-600 dark:text-purple-400' : 'font-medium text-muted-foreground'}`}>
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
            {/* AICODE-NOTE: T173 - Added left border accent for visual hierarchy */}
            {/* AICODE-NOTE: T182 - Added bottom border divider between sections */}
            <AccordionItem value="content" className="border-l-4 border-blue-500 pl-3 pr-1 border-b border-border mb-2">
              {/* AICODE-NOTE: Sprint 3.1 - Blue accent for Content section */}
              {/* AICODE-NOTE: T186 - Added FileText icon for better visual identification */}
              <AccordionTrigger className="text-base font-semibold text-blue-600 dark:text-blue-400">
                <div className="flex items-center gap-2">
                  <FileText className="h-4 w-4" />
                  <span>{ru.inputForm.sections.content}</span>
                </div>
              </AccordionTrigger>
              {/* AICODE-NOTE: T169 - Reduced padding: pt-3 → pt-2, space-y-2 → space-y-1.5 */}
              {/* AICODE-NOTE: T174 - Added subtle background for visual distinction */}
              <AccordionContent className="space-y-1.5 pt-2 bg-blue-50 dark:bg-blue-950/20 rounded-md p-2">

                {/* AICODE-NOTE: T100 - "Название статьи" field (replaces old "Тема") */}
                <div className="space-y-1.5">
                  <Label htmlFor="title">
                    {ru.inputForm.title.label}
                    {/* AICODE-NOTE: T085 - Required field indicator (asterisk) */}
                    <span className="text-destructive ml-1">*</span>
                  </Label>
                  {/* AICODE-NOTE: T170 - Optimized height: min-h-[44px] → h-10 (saves ~4px) */}
                  <Input
                    id="title"
                    type="text"
                    placeholder={ru.inputForm.title.placeholder}
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    disabled={isLoading}
                    className="h-10"
                    required
                  />
                </div>

                {/* AICODE-NOTE: T101 - "Ключевые тезисы" field (optional, multiline) */}
                <div className="space-y-1.5">
                  <Label htmlFor="keyPoints">
                    {ru.inputForm.keyPoints.label}
                    {/* AICODE-NOTE: No asterisk - this field is optional */}
                  </Label>
                  {/* AICODE-NOTE: T171 - Reduced rows: 6 → 4 (saves ~40px) */}
                  <Textarea
                    id="keyPoints"
                    placeholder={ru.inputForm.keyPoints.placeholder}
                    value={keyPoints}
                    onChange={(e) => setKeyPoints(e.target.value)}
                    disabled={isLoading}
                    rows={4}
                    className="resize-none"
                  />
                  <p className="text-xs text-muted-foreground">
                    Опционально: введите основные тезисы статьи по одному на строку
                  </p>
                </div>

              </AccordionContent>
            </AccordionItem>

            {/* AICODE-NOTE: T103 - Section 2: Стиль (Style Profile) */}
            {/* AICODE-NOTE: T175 - Added left border accent for visual hierarchy */}
            {/* AICODE-NOTE: T182 - Added bottom border divider between sections */}
            <AccordionItem value="style" className="border-l-4 border-green-500 pl-3 pr-1 border-b border-border mb-2">
              {/* AICODE-NOTE: Sprint 3.1 - Green accent for Style section */}
              {/* AICODE-NOTE: T186 - Added Palette icon for better visual identification */}
              <AccordionTrigger className="text-base font-semibold text-green-600 dark:text-green-400">
                <div className="flex items-center gap-2">
                  <Palette className="h-4 w-4" />
                  <span>{ru.inputForm.sections.style}</span>
                </div>
              </AccordionTrigger>
              {/* AICODE-NOTE: T169 - Reduced padding: pt-3 → pt-2 */}
              {/* AICODE-NOTE: T176 - Added subtle background for visual distinction */}
              <AccordionContent className="pt-2 bg-green-50 dark:bg-green-950/20 rounded-md p-2">
                {/* AICODE-NOTE: T110 - StyleProfileSection notifies parent of profile changes
                    Parent (page.tsx) uses this to enable/disable generation button */}
                <StyleProfileSection onProfileUpdate={(profile) => {
                  if (onProfileUpdate) {
                    onProfileUpdate(profile)
                  }
                }} />
              </AccordionContent>
            </AccordionItem>

            {/* AICODE-NOTE: T103 - Section 3: Настройки (Settings) */}
            {/* AICODE-NOTE: T177 - Added left border accent for visual hierarchy */}
            {/* AICODE-NOTE: T182 - Added bottom border divider (last section, no bottom border needed but keeping for consistency) */}
            <AccordionItem value="settings" className="border-l-4 border-purple-500 pl-3 pr-1 mb-2">
              {/* AICODE-NOTE: Sprint 3.1 - Purple accent for Settings section */}
              {/* AICODE-NOTE: T186 - Added Settings icon for better visual identification */}
              <AccordionTrigger className="text-base font-semibold text-purple-600 dark:text-purple-400">
                <div className="flex items-center gap-2">
                  <Settings className="h-4 w-4" />
                  <span>{ru.inputForm.sections.settings}</span>
                </div>
              </AccordionTrigger>
              {/* AICODE-NOTE: T169 - Reduced padding: pt-3 → pt-2, space-y-4 → space-y-3 */}
              {/* AICODE-NOTE: T178 - Added subtle background for visual distinction */}
              <AccordionContent className="pt-2 space-y-3 bg-purple-50 dark:bg-purple-950/20 rounded-md p-2">

                {/* AICODE-NOTE: Phase 11.2 - Word count input for article length control */}
                <div className="space-y-1.5">
                  <Label htmlFor="wordCount">
                    Размер статьи (слов) <span className="text-destructive">*</span>
                  </Label>
                  <Input
                    id="wordCount"
                    type="number"
                    placeholder="500"
                    value={wordCount}
                    onChange={(e) => setWordCount(Math.max(100, Math.min(5000, Number(e.target.value) || 500)))}
                    disabled={isLoading}
                    min={100}
                    max={5000}
                    step={100}
                  />
                  <p className="text-xs text-muted-foreground">
                    Укажите желаемый размер статьи от 100 до 5000 слов (±10-20% точность)
                  </p>
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
                    {ru.inputForm.research.label}
                  </Label>
                </div>

              </AccordionContent>
            </AccordionItem>

          </Accordion>

          {/* AICODE-NOTE: T131 - Removed profile dependency warning
              Profile is now optional, so no warning needed */}

          {/* Submit Button */}
          {/* AICODE-NOTE: T131 - Button disabled when:
              1. Title is empty (title.trim() === '')
              2. Generation in progress (isLoading === true)
              Profile is now optional, so no longer checked */}
          {/* AICODE-NOTE: T172 - Reduced button height: min-h-[44px] → h-10 (saves ~4px) */}
          {/* AICODE-NOTE: T180 - Added gradient for high visual impact and better contrast */}
          <Button
            type="submit"
            disabled={!isFormValid || isLoading}
            className="w-full h-10 font-semibold bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700"
          >
            {isLoading ? ru.inputForm.button.submitting : ru.inputForm.button.submit}
          </Button>
        </form>
      </CardContent>
    </Card>
  )
}
