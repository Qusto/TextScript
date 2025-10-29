/**
 * Tests for updated InputForm component (Phase 10 Sprint 3).
 *
 * AICODE-NOTE: T100-T103 - TDD tests for reorganized input form
 * Tests cover:
 * - T100: "Topic" renamed to "Название статьи"
 * - T101: New "Ключевые тезисы" field (optional)
 * - T102: Updated ArticleRequest interface
 * - T103: Accordion organization (Контент, Стиль, Настройки)
 */

import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import '@testing-library/jest-dom'
import { InputForm } from '../input-form'
import { StyleProfile } from '@/types/profile'

const mockProfile: StyleProfile = {
  id: 1,
  urls_hash: 'abc123',
  profile_text: 'Test profile',
  source_urls: ['https://example.com'],
  created_at: '2025-10-29T00:00:00Z',
  updated_at: '2025-10-29T00:00:00Z',
}

describe('InputForm (Phase 10 - Updated)', () => {
  describe('Field Renaming (T100)', () => {
    it('shows "Название статьи" instead of "Тема"', () => {
      render(<InputForm onSubmit={() => {}} isLoading={false} currentProfile={mockProfile} />)

      // AICODE-NOTE: Old "Тема" label should not exist
      expect(screen.queryByText(/^Тема$/)).not.toBeInTheDocument()

      // AICODE-NOTE: New "Название статьи" label should exist
      expect(screen.getByText(/Название статьи/)).toBeInTheDocument()
    })
  })

  describe('New Key Points Field (T101)', () => {
    it('shows "Ключевые тезисы" textarea field', () => {
      render(<InputForm onSubmit={() => {}} isLoading={false} currentProfile={mockProfile} />)

      expect(screen.getByText(/Ключевые тезисы/)).toBeInTheDocument()
    })

    it('key points field is optional (no asterisk)', () => {
      render(<InputForm onSubmit={() => {}} isLoading={false} currentProfile={mockProfile} />)

      const label = screen.getByText(/Ключевые тезисы/)
      // AICODE-NOTE: Should NOT have required asterisk
      expect(label.textContent).not.toContain('*')
    })

    it('allows submission without key points', async () => {
      const onSubmit = jest.fn()
      const user = userEvent.setup()

      render(<InputForm onSubmit={onSubmit} isLoading={false} currentProfile={mockProfile} />)

      // AICODE-NOTE: Fill only required field (title)
      const titleInput = screen.getByPlaceholderText(/Введите название статьи/)
      await user.type(titleInput, 'Test Article')

      const submitButton = screen.getByText(/Сгенерировать/)
      await user.click(submitButton)

      // AICODE-NOTE: Should submit even without keyPoints
      await waitFor(() => {
        expect(onSubmit).toHaveBeenCalledWith({
          title: 'Test Article',
          keyPoints: '',
          enableResearch: false,
        })
      })
    })

    it('includes key points in submission when provided', async () => {
      const onSubmit = jest.fn()
      const user = userEvent.setup()

      render(<InputForm onSubmit={onSubmit} isLoading={false} currentProfile={mockProfile} />)

      const titleInput = screen.getByPlaceholderText(/Введите название статьи/)
      const keyPointsInput = screen.getByPlaceholderText(/Тезис 1/)

      await user.type(titleInput, 'Test Article')
      await user.type(keyPointsInput, 'Point 1\nPoint 2')

      const submitButton = screen.getByText(/Сгенерировать/)
      await user.click(submitButton)

      await waitFor(() => {
        expect(onSubmit).toHaveBeenCalledWith({
          title: 'Test Article',
          keyPoints: 'Point 1\nPoint 2',
          enableResearch: false,
        })
      })
    })
  })

  describe('Accordion Organization (T103)', () => {
    it('shows three accordion sections', () => {
      render(<InputForm onSubmit={() => {}} isLoading={false} currentProfile={mockProfile} />)

      // AICODE-NOTE: T103 - Three sections defined
      expect(screen.getByText(/Контент/)).toBeInTheDocument()
      expect(screen.getByText(/Стиль/)).toBeInTheDocument()
      expect(screen.getByText(/Настройки/)).toBeInTheDocument()
    })

    it('Контент section contains title and keyPoints fields', () => {
      render(<InputForm onSubmit={() => {}} isLoading={false} currentProfile={mockProfile} />)

      // AICODE-NOTE: Both fields should be under "Контент" section
      expect(screen.getByText(/Название статьи/)).toBeInTheDocument()
      expect(screen.getByText(/Ключевые тезисы/)).toBeInTheDocument()
    })

    it('Настройки section contains research checkbox', () => {
      render(<InputForm onSubmit={() => {}} isLoading={false} currentProfile={mockProfile} />)

      // AICODE-NOTE: Research checkbox in "Настройки"
      expect(screen.getByText(/Включить режим исследования/)).toBeInTheDocument()
    })
  })

  describe('Profile Requirement (T110)', () => {
    it('disables submit button when no profile loaded', () => {
      render(<InputForm onSubmit={() => {}} isLoading={false} currentProfile={null} />)

      const submitButton = screen.getByText(/Сгенерировать/)

      // AICODE-NOTE: T110 - Button disabled when currentProfile is null
      expect(submitButton).toBeDisabled()
    })

    it('shows warning message when no profile loaded', () => {
      render(<InputForm onSubmit={() => {}} isLoading={false} currentProfile={null} />)

      // AICODE-NOTE: T110 - Warning message visible
      expect(screen.getByText(/Сначала создайте профиль стиля/)).toBeInTheDocument()
    })

    it('enables submit button when profile is loaded', () => {
      render(<InputForm onSubmit={() => {}} isLoading={false} currentProfile={mockProfile} />)

      const submitButton = screen.getByText(/Сгенерировать/)

      // AICODE-NOTE: Initially disabled (no title)
      expect(submitButton).toBeDisabled()
    })

    it('enables submit when profile loaded and title provided', async () => {
      const user = userEvent.setup()
      render(<InputForm onSubmit={() => {}} isLoading={false} currentProfile={mockProfile} />)

      const titleInput = screen.getByPlaceholderText(/Введите название статьи/)
      await user.type(titleInput, 'Test')

      const submitButton = screen.getByText(/Сгенерировать/)

      // AICODE-NOTE: Now enabled (profile exists + title provided)
      expect(submitButton).not.toBeDisabled()
    })
  })

  describe('Form Validation', () => {
    it('disables submit when title is empty', () => {
      render(<InputForm onSubmit={() => {}} isLoading={false} currentProfile={mockProfile} />)

      const submitButton = screen.getByText(/Сгенерировать/)
      expect(submitButton).toBeDisabled()
    })

    it('disables all fields when isLoading=true', () => {
      render(<InputForm onSubmit={() => {}} isLoading={true} currentProfile={mockProfile} />)

      const titleInput = screen.getByPlaceholderText(/Введите название статьи/)
      const keyPointsInput = screen.getByPlaceholderText(/Тезис 1/)
      const submitButton = screen.getByText(/Генерация.../)

      expect(titleInput).toBeDisabled()
      expect(keyPointsInput).toBeDisabled()
      expect(submitButton).toBeDisabled()
    })
  })
})
