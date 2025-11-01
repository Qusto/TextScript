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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
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

  // AICODE-NOTE: Phase 11 - Profile selection state
  const [allProfiles, setAllProfiles] = useState<StyleProfile[]>([])
  const [selectedProfileId, setSelectedProfileId] = useState<number | null>(null)

  /**
   * Load current profile status and all profiles on mount.
   *
   * AICODE-NOTE: T097 - GET /api/profiles/current on component mount
   * Phase 11 - Also load all profiles for selection dropdown
   */
  useEffect(() => {
    loadProfileStatus()
    loadAllProfiles()
  }, [])

  const loadProfileStatus = async () => {
    try {
      setIsLoading(true)
      setError(null)

      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      const response = await fetch(`${apiUrl}/api/profiles/current`)

      // AICODE-NOTE: Sprint 3.1 - Distinguish between API errors and missing profile
      // Only show red error for actual failures (network, 500s)
      // Missing profile (null response) is normal state, not an error
      if (!response.ok) {
        // 4xx/5xx errors are real errors
        throw new Error(`API error: ${response.status}`)
      }

      const data = await response.json()
      setProfile(data) // null if no profile exists

      // AICODE-NOTE: Show create form automatically if no profile (not an error state)
      if (!data) {
        setIsCreating(true)
      }
    } catch (err) {
      console.error('Failed to load profile status:', err)
      // AICODE-NOTE: Only set error for actual API failures (network, 500s)
      setError('Ошибка загрузки профиля')
    } finally {
      setIsLoading(false)
    }
  }

  /**
   * Load all available profiles for selection dropdown.
   *
   * AICODE-NOTE: Phase 11 - GET /api/profiles for profile list
   * Populates dropdown with all saved style profiles
   */
  const loadAllProfiles = async () => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      const response = await fetch(`${apiUrl}/api/profiles`)

      if (!response.ok) {
        console.error('Failed to load profiles list')
        return
      }

      const data = await response.json()
      setAllProfiles(data)

      // Set current profile as selected if it exists
      if (profile && data.length > 0) {
        setSelectedProfileId(profile.id)
      }
    } catch (err) {
      console.error('Failed to load profiles list:', err)
    }
  }

  /**
   * Handle profile selection from dropdown.
   *
   * AICODE-NOTE: Phase 11 - Load selected profile and notify parent
   */
  const handleProfileSelect = async (profileId: number) => {
    try {
      setSelectedProfileId(profileId)
      setError(null)

      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      const response = await fetch(`${apiUrl}/api/profiles/${profileId}`)

      if (!response.ok) {
        throw new Error(`API error: ${response.status}`)
      }

      const selectedProfile = await response.json()
      setProfile(selectedProfile)
      setIsCreating(false)

      // Notify parent component about profile selection
      onProfileUpdate(selectedProfile)
    } catch (err) {
      console.error('Failed to load selected profile:', err)
      setError('Ошибка загрузки выбранного профиля')
    }
  }

  /**
   * Delete selected profile from database.
   *
   * AICODE-NOTE: Phase 11 - DELETE /api/profiles/{id} from dropdown
   * Removes profile and refreshes list
   */
  const handleDeleteProfile = async (profileId: number | null) => {
    if (!profileId) return

    try {
      setIsSubmitting(true)
      setError(null)

      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      const response = await fetch(`${apiUrl}/api/profiles/${profileId}`, {
        method: 'DELETE',
      })

      if (!response.ok) {
        throw new Error(`API error: ${response.status}`)
      }

      // Reload profiles list and current profile
      await loadAllProfiles()
      await loadProfileStatus()

      // Notify parent component about profile deletion
      onProfileUpdate(null)
    } catch (err) {
      console.error('Failed to delete profile:', err)
      setError('Ошибка удаления профиля')
    } finally {
      setIsSubmitting(false)
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

      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      const response = await fetch(`${apiUrl}/api/profiles`, {
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

      // AICODE-NOTE: Phase 11 - Reload profiles list after creation
      await loadAllProfiles()

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

      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      const response = await fetch(`${apiUrl}/api/profiles/${profile.id}`, {
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
      <div className="space-y-2">
        <h3 className="text-sm font-semibold">Профиль стиля</h3>
        <p className="text-sm text-muted-foreground">Загрузка...</p>
      </div>
    )
  }

  return (
    <div className="space-y-3">
      {/* AICODE-NOTE: T097 - Profile status display (removed Card wrapper for consistency) */}
      {/* AICODE-NOTE: Sprint 4 - Matches AccordionContent styling (no white card) */}
      <div className="space-y-2">
        <h3 className="text-sm font-semibold">Профиль стиля</h3>
        <p className="text-sm">
          {profile ? (
            <>
              {/* AICODE-NOTE: T126 - Display profile.name instead of generic text */}
              <span className="text-green-600 dark:text-green-400">✓ {profile.name}</span>
              <span className="text-muted-foreground ml-2">
                ({profile.source_urls.length} URL{profile.source_urls.length > 1 ? 'ов' : ''})
              </span>
            </>
          ) : (
            // AICODE-NOTE: T130 - Changed from "для начала работы" to "(опционально)"
            <span className="text-blue-600 dark:text-blue-400">→ Профиль стиля (опционально)</span>
          )}
        </p>
      </div>

      <div className="space-y-3">
          {/* AICODE-NOTE: Error display */}
          {error && (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {/* AICODE-NOTE: Phase 11 - Profile selection dropdown (when multiple profiles exist) */}
          {allProfiles.length > 1 && (
            <div className="space-y-2">
              <label htmlFor="profile-select" className="text-sm font-medium">
                Выбор профиля стиля
              </label>
              <div className="flex gap-2">
                <Select
                  value={selectedProfileId?.toString() || ''}
                  onValueChange={(value) => handleProfileSelect(Number(value))}
                >
                  <SelectTrigger id="profile-select" className="flex-1">
                    <SelectValue placeholder="Выберите профиль" />
                  </SelectTrigger>
                  <SelectContent>
                    {allProfiles.map((p) => (
                      <SelectItem key={p.id} value={p.id.toString()}>
                        {p.name} ({p.source_urls.length} URL{p.source_urls.length > 1 ? 'ов' : ''})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Button
                  variant="outline"
                  size="icon"
                  onClick={() => handleDeleteProfile(selectedProfileId)}
                  disabled={!selectedProfileId || isSubmitting}
                  title="Удалить профиль"
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    width="16"
                    height="16"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <path d="M3 6h18" />
                    <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6" />
                    <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2" />
                  </svg>
                </Button>
              </div>
            </div>
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
            <div className="bg-muted/50 rounded-md p-4">
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
            </div>
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
      </div>
    </div>
  )
}
