/**
 * TypeScript type definitions for style profiles and article requests.
 *
 * AICODE-NOTE: T094 - Type definitions for Phase 10 features (FR-028, FR-035, FR-036, FR-041)
 * These types match the backend API contracts from profiles.py and generate.py
 */

/**
 * Style profile stored in database.
 *
 * AICODE-NOTE: T094 - Matches StyleProfileDB model from backend/src/db/models.py
 * Used for displaying profile information in UI (T097, T098)
 * AICODE-NOTE: T125 - Added name field for better profile display
 */
export interface StyleProfile {
  /** Database ID */
  id: number

  /** MD5 hash of sorted source URLs (unique identifier) */
  urls_hash: string

  /** LLM-generated style analysis (used as generation prompt) */
  profile_text: string

  /** Original URLs used for style extraction */
  source_urls: string[]

  /** ISO 8601 timestamp of creation */
  created_at: string

  /** ISO 8601 timestamp of last update */
  updated_at: string

  /** Short profile name for display (e.g., "Профиль Habr") */
  name: string
}

/**
 * Request body for creating new style profile.
 *
 * AICODE-NOTE: T094 - Matches ProfileCreateRequest from backend/src/api/profiles.py
 * Used in T099 when user creates/updates profile
 */
export interface ProfileCreateRequest {
  /** List of URLs to extract style from (1-10 URLs) */
  source_urls: string[]
}

/**
 * Article generation request (Phase 10 updated format).
 *
 * AICODE-NOTE: T094 - New API contract (FR-041)
 * Breaking change from Phase 1-9:
 * - OLD: GET /api/generate?topic=...&source_urls=...
 * - NEW: POST /api/generate with body containing title, keyPoints, profileId
 *
 * Used in T108 when switching from EventSource GET to POST
 */
export interface ArticleRequest {
  /** Article title (required) - replaces "topic" field */
  title: string

  /** Optional key points/theses to cover in article */
  key_points?: string

  /** Style profile ID to use for generation (required) */
  profile_id: number

  /** Enable research mode (two-stage generation) */
  enable_research: boolean
}

/**
 * Style profile status for UI display.
 *
 * AICODE-NOTE: T094 - UI state management for profile section (T096, T097)
 * Determines what to show: loading, error, profile loaded, or no profile
 */
export type ProfileStatus = 'loading' | 'loaded' | 'not_loaded' | 'error'

/**
 * Profile section state (for component props).
 *
 * AICODE-NOTE: T094 - State management for StyleProfileSection component (T096-T099)
 */
export interface ProfileSectionState {
  /** Current profile status */
  status: ProfileStatus

  /** Loaded profile data (if status === 'loaded') */
  profile: StyleProfile | null

  /** Error message (if status === 'error') */
  error: string | null

  /** Loading state for profile operations */
  is_loading: boolean
}

/**
 * Props for InputForm component (updated for Phase 10).
 *
 * AICODE-NOTE: T094 - Updated form props for T100-T103 (title, keyPoints fields)
 */
export interface InputFormProps {
  /** Callback when form is submitted */
  onSubmit: (data: ArticleFormData) => void

  /** Whether generation is in progress */
  isLoading: boolean

  /** Current profile (if loaded) - used to disable button when no profile */
  currentProfile: StyleProfile | null
}

/**
 * Form data from InputForm (Phase 10 format).
 *
 * AICODE-NOTE: T094 - New form data structure (FR-035, FR-036)
 * Replaces old { topic, sourceUrls, enableResearch } format
 */
export interface ArticleFormData {
  /** Article title (required) */
  title: string

  /** Optional key points/theses */
  keyPoints?: string

  /** Enable research mode */
  enableResearch: boolean
}
