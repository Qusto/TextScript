/**
 * Style Profile Management Section Component (Phase 10 Sprint 3).
 *
 * AICODE-NOTE: T096-T099 - Profile management UI for Sprint 3
 * Features:
 * - T097: Profile status display (loaded/not loaded)
 * - T098: Profile viewer dialog (shows profile_text)
 * - T099: Profile update form (create/delete profile)
 *
 * Component shows:
 * - Status indicator (profile loaded/not loaded)
 * - "View Profile" button (if profile exists)
 * - "Update Profile" button (if profile exists) - deletes current, shows create form
 * - Collapsible URL input (visible when no profile exists)
 * - "Create Profile" button (when creating new profile)
 */

'use client'

import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { StyleProfile } from '@/types/profile'

interface StyleProfileSectionProps {
  /** Callback when profile is created or deleted */
  onProfileUpdate: (profile: StyleProfile | null) => void
}

/**
 * StyleProfileSection component.
 *
 * AICODE-NOTE: T096 - Main profile management component
 * Handles profile status check, viewing, creation, and deletion.
 */
export default function StyleProfileSection({ onProfileUpdate }: StyleProfileSectionProps) {
  // AICODE-NOTE: T097 - Profile state management
  const [profile, setProfile] = useState<StyleProfile | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // AICODE-NOTE: T098 - Profile viewer dialog state
  const [isViewerOpen, setIsViewerOpen] = useState(false)

  // AICODE-NOTE: T099 - Profile creation form state
  const [isCreating, setIsCreating] = useState(false)
  const [sourceUrls, setSourceUrls] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  /**
   * Load current profile status on mount.
   *
   * AICODE-NOTE: T097 - GET /api/profiles/current on component mount
   * Returns StyleProfile if exists, null otherwise
   */
  useEffect(() => {
    loadProfileStatus()
  }, [])

  const loadProfileStatus = async () => {
    try {
      setIsLoading(true)
      setError(null)

      const response = await fetch('/api/profiles/current')

      if (!response.ok) {
        throw new Error(`API error: ${response.status}`)
      }

      const data = await response.json()
      setProfile(data) // null if no profile exists

      // AICODE-NOTE: Show create form automatically if no profile
      if (!data) {
        setIsCreating(true)
      }
    } catch (err) {
      console.error('Failed to load profile status:', err)
      setError('Ошибка загрузки профиля')
    } finally {
      setIsLoading(false)
    }
  }

  /**
   * Create new style profile from URLs.
   *
   * AICODE-NOTE: T099 - POST /api/profiles with source_urls array
   * Calls backend style extraction (src/ugly_script.py) and saves to DB
   */
  const handleCreateProfile = async () => {
    // AICODE-NOTE: Parse URLs from textarea (one per line)
    const urls = sourceUrls
      .split('\n')
      .map(url => url.trim())
      .filter(url => url.length > 0)

    if (urls.length === 0) {
      setError('Введите хотя бы один URL')
      return
    }

    try {
      setIsSubmitting(true)
      setError(null)

      const response = await fetch('/api/profiles', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          source_urls: urls,
        }),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || `API error: ${response.status}`)
      }

      const newProfile = await response.json()
      setProfile(newProfile)
      setIsCreating(false)
      setSourceUrls('')

      // AICODE-NOTE: Notify parent component about profile creation
      onProfileUpdate(newProfile)
    } catch (err) {
      console.error('Failed to create profile:', err)
      setError(err instanceof Error ? err.message : 'Ошибка создания профиля')
    } finally {
      setIsSubmitting(false)
    }
  }

  /**
   * Delete current profile and show create form.
   *
   * AICODE-NOTE: T099 - DELETE /api/profiles/{id}
   * Allows user to create new profile with different URLs
   */
  const handleUpdateProfile = async () => {
    if (!profile) return

    try {
      setIsSubmitting(true)
      setError(null)

      const response = await fetch(`/api/profiles/${profile.id}`, {
        method: 'DELETE',
      })

      if (!response.ok) {
        throw new Error(`API error: ${response.status}`)
      }

      // AICODE-NOTE: Clear profile and show create form
      setProfile(null)
      setIsCreating(true)

      // AICODE-NOTE: Notify parent component about profile deletion
      onProfileUpdate(null)
    } catch (err) {
      console.error('Failed to delete profile:', err)
      setError('Ошибка удаления профиля')
    } finally {
      setIsSubmitting(false)
    }
  }

  // AICODE-NOTE: Loading state
  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Профиль стиля</CardTitle>
          <CardDescription>Загрузка...</CardDescription>
        </CardHeader>
      </Card>
    )
  }

  return (
    <div className="space-y-4">
      {/* AICODE-NOTE: T097 - Profile status display */}
      <Card>
        <CardHeader>
          <CardTitle>Профиль стиля</CardTitle>
          <CardDescription>
            {profile ? (
              <>
                <span className="text-green-600 dark:text-green-400">✓ Профиль загружен</span>
                <span className="text-muted-foreground ml-2">
                  ({profile.source_urls.length} URL{profile.source_urls.length > 1 ? 'ов' : ''})
                </span>
              </>
            ) : (
              <span className="text-yellow-600 dark:text-yellow-400">⚠ Профиль не загружен</span>
            )}
          </CardDescription>
        </CardHeader>

        <CardContent className="space-y-3">
          {/* AICODE-NOTE: Error display */}
          {error && (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {/* AICODE-NOTE: T098 - View Profile button (only when profile exists) */}
          {profile && (
            <div className="flex gap-2">
              <Button
                variant="outline"
                onClick={() => setIsViewerOpen(!isViewerOpen)}
                className="flex-1"
              >
                {isViewerOpen ? 'Скрыть профиль' : 'Посмотреть профиль'}
              </Button>

              {/* AICODE-NOTE: T099 - Update Profile button */}
              <Button
                variant="outline"
                onClick={handleUpdateProfile}
                disabled={isSubmitting}
                className="flex-1"
              >
                Обновить профиль
              </Button>
            </div>
          )}

          {/* AICODE-NOTE: T098 - Profile viewer (shows profile_text) */}
          {profile && isViewerOpen && (
            <Card className="bg-muted/50">
              <CardContent className="pt-4">
                <pre className="text-sm whitespace-pre-wrap font-mono">
                  {profile.profile_text}
                </pre>
                <div className="mt-4 text-xs text-muted-foreground">
                  <p>Источники:</p>
                  <ul className="list-disc list-inside mt-1">
                    {profile.source_urls.map((url, index) => (
                      <li key={index} className="truncate">
                        {url}
                      </li>
                    ))}
                  </ul>
                </div>
              </CardContent>
            </Card>
          )}

          {/* AICODE-NOTE: T099 - Profile creation form (visible when no profile or updating) */}
          {isCreating && (
            <div className="space-y-3">
              <div>
                <label htmlFor="source-urls" className="text-sm font-medium mb-1 block">
                  URL источников (по одному на строку)
                </label>
                <Textarea
                  id="source-urls"
                  placeholder="https://example.com/article1&#10;https://example.com/article2"
                  value={sourceUrls}
                  onChange={(e) => setSourceUrls(e.target.value)}
                  rows={4}
                  disabled={isSubmitting}
                />
                <p className="text-xs text-muted-foreground mt-1">
                  Введите 1-10 URL статей для анализа стиля
                </p>
              </div>

              <Button
                onClick={handleCreateProfile}
                disabled={isSubmitting || sourceUrls.trim().length === 0}
                className="w-full"
              >
                {isSubmitting ? 'Создание профиля...' : 'Создать профиль'}
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
