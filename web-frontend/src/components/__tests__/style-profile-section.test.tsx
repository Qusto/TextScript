/**
 * Tests for StyleProfileSection component (Phase 10 Sprint 3).
 *
 * AICODE-NOTE: T096-T099 - TDD tests for profile management UI
 * Tests cover:
 * - Profile status display (loaded/not loaded)
 * - Profile viewer dialog
 * - Profile update form
 * - API integration with GET /api/profiles/current and POST /api/profiles
 */

import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import '@testing-library/jest-dom'
import StyleProfileSection from '../style-profile-section'
import { StyleProfile } from '@/types/profile'

// AICODE-NOTE: Mock fetch API for testing profile endpoints
global.fetch = jest.fn()

const mockProfile: StyleProfile = {
  id: 1,
  urls_hash: 'abc123def456',
  profile_text:
    'Concise, data-driven writing with technical terminology. Uses bullet points.',
  source_urls: ['https://example.com/article1', 'https://example.com/article2'],
  created_at: '2025-10-29T00:00:00Z',
  updated_at: '2025-10-29T00:00:00Z',
  name: 'Example Profile', // AICODE-NOTE: T125 - Added name field for display
}

describe('StyleProfileSection', () => {
  beforeEach(() => {
    ;(fetch as jest.Mock).mockClear()
  })

  describe('Profile Status Display (T097)', () => {
    it('shows loading state initially', () => {
      ;(fetch as jest.Mock).mockImplementation(
        () => new Promise(() => {}) // Never resolves
      )

      render(<StyleProfileSection onProfileUpdate={() => {}} />)

      expect(screen.getByText(/загрузка/i)).toBeInTheDocument()
    })

    it('shows "not loaded" status when no profile exists', async () => {
      // AICODE-NOTE: GET /api/profiles/current returns null when no profile
      // Phase 13 - Also need to mock /api/profiles call
      ;(fetch as jest.Mock)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => null,
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => [],
        })

      render(<StyleProfileSection onProfileUpdate={() => {}} />)

      await waitFor(() => {
        expect(screen.getByText(/профиль стиля \(опционально\)/i)).toBeInTheDocument()
      })
    })

    it('shows "loaded" status when profile exists', async () => {
      // AICODE-NOTE: Phase 13 - Mock both /api/profiles/current and /api/profiles
      ;(fetch as jest.Mock)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockProfile,
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => [mockProfile],
        })

      render(<StyleProfileSection onProfileUpdate={() => {}} />)

      await waitFor(() => {
        expect(screen.getByText(/✓ Example Profile/i)).toBeInTheDocument()
      })
    })

    it('shows error state on API failure', async () => {
      // AICODE-NOTE: Phase 13 - Mock failed /api/profiles/current call
      ;(fetch as jest.Mock)
        .mockRejectedValueOnce(new Error('Network error'))
        .mockResolvedValueOnce({
          ok: true,
          json: async () => [],
        })

      render(<StyleProfileSection onProfileUpdate={() => {}} />)

      await waitFor(() => {
        expect(screen.getByText(/ошибка загрузки/i)).toBeInTheDocument()
      })
    })
  })

  describe('Profile Viewer Dialog (T098)', () => {
    it('shows "View Profile" button when profile loaded', async () => {
      // AICODE-NOTE: Phase 13 - Mock both API calls
      ;(fetch as jest.Mock)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockProfile,
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => [mockProfile],
        })

      render(<StyleProfileSection onProfileUpdate={() => {}} />)

      await waitFor(() => {
        expect(screen.getByText(/посмотреть профиль/i)).toBeInTheDocument()
      })
    })

    it('opens dialog and displays profile text when "View Profile" clicked', async () => {
      // AICODE-NOTE: Phase 13 - Mock both API calls
      ;(fetch as jest.Mock)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockProfile,
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => [mockProfile],
        })

      const user = userEvent.setup()
      render(<StyleProfileSection onProfileUpdate={() => {}} />)

      await waitFor(() => {
        expect(screen.getByText(/посмотреть профиль/i)).toBeInTheDocument()
      })

      const viewButton = screen.getByText(/посмотреть профиль/i)
      await user.click(viewButton)

      // AICODE-NOTE: Dialog should show profile_text content
      await waitFor(() => {
        expect(screen.getByText(mockProfile.profile_text)).toBeInTheDocument()
      })
    })

    it('hides "View Profile" button when no profile loaded', async () => {
      // AICODE-NOTE: Phase 13 - Mock both API calls
      ;(fetch as jest.Mock)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => null,
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => [],
        })

      render(<StyleProfileSection onProfileUpdate={() => {}} />)

      await waitFor(() => {
        expect(
          screen.queryByText(/посмотреть профиль/i)
        ).not.toBeInTheDocument()
      })
    })
  })

  describe('Profile Update Form (T099)', () => {
    it('shows URL input form when no profile exists', async () => {
      // AICODE-NOTE: Phase 13 - Mock both API calls
      ;(fetch as jest.Mock)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => null,
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => [],
        })

      render(<StyleProfileSection onProfileUpdate={() => {}} />)

      await waitFor(() => {
        // AICODE-NOTE: Phase 13 T201 - New placeholder supports URLs or text
        expect(
          screen.getByPlaceholderText(/https:\/\/example\.com\/article1/i)
        ).toBeInTheDocument()
      })
    })

    it('hides URL input when profile exists (collapsible)', async () => {
      // AICODE-NOTE: Phase 13 - Mock both API calls
      ;(fetch as jest.Mock)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockProfile,
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => [mockProfile],
        })

      render(<StyleProfileSection onProfileUpdate={() => {}} />)

      await waitFor(() => {
        // AICODE-NOTE: Phase 13 T201 - Check for new placeholder
        expect(
          screen.queryByPlaceholderText(/https:\/\/example\.com\/article1/i)
        ).not.toBeInTheDocument()
      })
    })

    it('creates new profile when form submitted', async () => {
      // AICODE-NOTE: Phase 13 - Mock: current profile, all profiles, POST response, reload profiles
      ;(fetch as jest.Mock)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => null, // GET /api/profiles/current
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => [], // GET /api/profiles
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockProfile, // POST /api/profiles
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => [mockProfile], // GET /api/profiles (reload after create)
        })

      const onProfileUpdate = jest.fn()
      const user = userEvent.setup()
      render(<StyleProfileSection onProfileUpdate={onProfileUpdate} />)

      await waitFor(() => {
        expect(
          screen.getByPlaceholderText(/https:\/\/example\.com\/article1/i)
        ).toBeInTheDocument()
      })

      const urlInput = screen.getByPlaceholderText(/https:\/\/example\.com\/article1/i)
      const submitButton = screen.getByText(/создать профиль/i)

      // AICODE-NOTE: Phase 13 T201 - Enter URLs (textarea now supports URLs or text)
      await user.type(
        urlInput,
        'https://example.com/article1{Enter}https://example.com/article2'
      )
      await user.click(submitButton)

      // AICODE-NOTE: Phase 13 T202 - Verify POST with source_content and profile_name
      await waitFor(() => {
        expect(fetch).toHaveBeenCalledWith('http://localhost:8000/api/profiles', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            source_content: [
              'https://example.com/article1',
              'https://example.com/article2',
            ],
            profile_name: null, // No custom name provided
          }),
        })
      })

      // AICODE-NOTE: Verify callback called with new profile
      await waitFor(() => {
        expect(onProfileUpdate).toHaveBeenCalledWith(mockProfile)
      })
    })

    it('validates URL input (requires at least 1 URL)', async () => {
      // AICODE-NOTE: Phase 13 - Mock both API calls
      ;(fetch as jest.Mock)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => null,
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => [],
        })

      render(<StyleProfileSection onProfileUpdate={() => {}} />)

      await waitFor(() => {
        expect(screen.getByText(/создать профиль/i)).toBeInTheDocument()
      })

      const submitButton = screen.getByText(/создать профиль/i)

      // AICODE-NOTE: Button should be disabled when no URLs entered
      expect(submitButton).toBeDisabled()
    })
  })

  describe('Profile Update Button (T099)', () => {
    it('shows "Update Profile" button when profile loaded', async () => {
      // AICODE-NOTE: Phase 13 - Mock both API calls
      ;(fetch as jest.Mock)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockProfile,
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => [mockProfile],
        })

      render(<StyleProfileSection onProfileUpdate={() => {}} />)

      await waitFor(() => {
        expect(screen.getByText(/обновить профиль/i)).toBeInTheDocument()
      })
    })

    it('deletes existing profile and shows create form when "Update" clicked', async () => {
      // AICODE-NOTE: Phase 13 - Mock: load current, load all, DELETE response
      ;(fetch as jest.Mock)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockProfile, // GET /api/profiles/current
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => [mockProfile], // GET /api/profiles
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ success: true }), // DELETE /api/profiles/1
        })

      const onProfileUpdate = jest.fn()
      const user = userEvent.setup()
      render(<StyleProfileSection onProfileUpdate={onProfileUpdate} />)

      await waitFor(() => {
        expect(screen.getByText(/обновить профиль/i)).toBeInTheDocument()
      })

      const updateButton = screen.getByText(/обновить профиль/i)
      await user.click(updateButton)

      // AICODE-NOTE: Phase 13 - Verify DELETE request with full URL
      await waitFor(() => {
        expect(fetch).toHaveBeenCalledWith('http://localhost:8000/api/profiles/1', {
          method: 'DELETE',
        })
      })

      // AICODE-NOTE: Verify callback called with null (profile deleted)
      await waitFor(() => {
        expect(onProfileUpdate).toHaveBeenCalledWith(null)
      })

      // AICODE-NOTE: Phase 13 T201 - Create form with new placeholder
      await waitFor(() => {
        expect(
          screen.getByPlaceholderText(/https:\/\/example\.com\/article1/i)
        ).toBeInTheDocument()
      })
    })
  })
})
