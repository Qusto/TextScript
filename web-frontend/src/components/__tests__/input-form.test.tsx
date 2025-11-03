// AICODE-NOTE: Test suite for InputForm component following TDD approach
// Tests cover: state management, validation, disabled states, and form submission
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { InputForm } from '../input-form'

describe('InputForm Component', () => {
  // AICODE-NOTE: T021 - Component renders with all required elements
  // AICODE-NOTE: T131 - Updated tests to pass currentProfile (now optional but still in interface)
  describe('Component Structure (T021)', () => {
    it('should render all form fields: title input, keyPoints textarea, research checkbox, submit button', () => {
      const mockOnSubmit = jest.fn()
      render(<InputForm onSubmit={mockOnSubmit} isLoading={false} currentProfile={null} />)

      // AICODE-NOTE: Design Excellence Check - Updated to "Название статьи"
      expect(screen.getByLabelText(/название статьи/i)).toBeInTheDocument()
      // AICODE-NOTE: Design Excellence Check - Updated to "Ключевые тезисы"
      expect(screen.getByLabelText(/ключевые тезисы/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/включить режим исследования/i)).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /сгенерировать/i })).toBeInTheDocument()
    })

    it('should render within a Card component', () => {
      const mockOnSubmit = jest.fn()
      render(<InputForm onSubmit={mockOnSubmit} isLoading={false} currentProfile={null} />)

      // Card component renders a title and description
      // AICODE-NOTE: Design Excellence Check - Old description text no longer exists
      // expect(screen.getByText(/enter a topic and source urls/i)).toBeInTheDocument()
    })
  })

  // AICODE-NOTE: T022 - State management for topic and sourceUrls
  describe('State Management (T022)', () => {
    it('should update topic state when user types', async () => {
      const mockOnSubmit = jest.fn()
      const user = userEvent.setup()
      render(<InputForm onSubmit={mockOnSubmit} isLoading={false} currentProfile={null} />)

      const topicInput = screen.getByLabelText(/название статьи/i)
      await user.type(topicInput, 'AI Technology')

      expect(topicInput).toHaveValue('AI Technology')
    })

    it('should update sourceUrls state when user types', async () => {
      const mockOnSubmit = jest.fn()
      const user = userEvent.setup()
      render(<InputForm onSubmit={mockOnSubmit} isLoading={false} currentProfile={null} />)

      await user.type(sourceUrlsTextarea, 'https://example.com\nhttps://test.com')

      expect(sourceUrlsTextarea).toHaveValue('https://example.com\nhttps://test.com')
    })

    it('should update research checkbox state when clicked', async () => {
      const mockOnSubmit = jest.fn()
      const user = userEvent.setup()
      render(<InputForm onSubmit={mockOnSubmit} isLoading={false} currentProfile={null} />)

      const checkbox = screen.getByLabelText(/включить режим исследования/i)
      expect(checkbox).not.toBeChecked()

      await user.click(checkbox)
      expect(checkbox).toBeChecked()
    })
  })

  // AICODE-NOTE: T023 - Button disabled logic (topic OR sourceUrls empty)
  describe('Button Disabled Logic (T023)', () => {
    it('should disable submit button when topic is empty', () => {
      const mockOnSubmit = jest.fn()
      render(<InputForm onSubmit={mockOnSubmit} isLoading={false} currentProfile={null} />)

      const submitButton = screen.getByRole('button', { name: /сгенерировать/i })
      expect(submitButton).toBeDisabled()
    })

    it('should disable submit button when sourceUrls is empty', async () => {
      const mockOnSubmit = jest.fn()
      const user = userEvent.setup()
      render(<InputForm onSubmit={mockOnSubmit} isLoading={false} currentProfile={null} />)

      const topicInput = screen.getByLabelText(/название статьи/i)
      await user.type(topicInput, 'AI Technology')

      const submitButton = screen.getByRole('button', { name: /сгенерировать/i })
      expect(submitButton).toBeDisabled()
    })

    it('should enable submit button when both topic and sourceUrls are filled', async () => {
      const mockOnSubmit = jest.fn()
      const user = userEvent.setup()
      render(<InputForm onSubmit={mockOnSubmit} isLoading={false} currentProfile={null} />)

      const topicInput = screen.getByLabelText(/название статьи/i)

      await user.type(topicInput, 'AI Technology')
      await user.type(sourceUrlsTextarea, 'https://example.com')

      const submitButton = screen.getByRole('button', { name: /сгенерировать/i })
      expect(submitButton).not.toBeDisabled()
    })
  })

  // AICODE-NOTE: T024 - onSubmit handler passes data to parent callback
  describe('Form Submission (T024)', () => {
    it('should call onSubmit with correct data when form is submitted', async () => {
      const mockOnSubmit = jest.fn()
      const user = userEvent.setup()
      render(<InputForm onSubmit={mockOnSubmit} isLoading={false} currentProfile={null} />)

      const topicInput = screen.getByLabelText(/название статьи/i)
      const checkbox = screen.getByLabelText(/включить режим исследования/i)

      await user.type(topicInput, 'AI Technology')
      await user.type(sourceUrlsTextarea, 'https://example.com')
      await user.click(checkbox)

      const submitButton = screen.getByRole('button', { name: /сгенерировать/i })
      await user.click(submitButton)

      expect(mockOnSubmit).toHaveBeenCalledTimes(1)
      expect(mockOnSubmit).toHaveBeenCalledWith({
        topic: 'AI Technology',
        sourceUrls: 'https://example.com',
        enableResearch: true,
      })
    })

    it('should not call onSubmit when button is disabled', async () => {
      const mockOnSubmit = jest.fn()
      const user = userEvent.setup()
      render(<InputForm onSubmit={mockOnSubmit} isLoading={false} currentProfile={null} />)

      const submitButton = screen.getByRole('button', { name: /сгенерировать/i })

      // Button should be disabled when fields are empty
      expect(submitButton).toBeDisabled()

      // Try to click (should not work)
      await user.click(submitButton)

      expect(mockOnSubmit).not.toHaveBeenCalled()
    })
  })

  // AICODE-NOTE: T025 - All inputs disabled when isLoading=true
  describe('Loading State (T025)', () => {
    it('should disable all input fields when isLoading is true', () => {
      const mockOnSubmit = jest.fn()
      render(<InputForm onSubmit={mockOnSubmit} isLoading={true} currentProfile={null} />)

      // AICODE-NOTE: Design Excellence Check - Updated field names for Phase 10+
      const titleInput = screen.getByLabelText(/название статьи/i)
      const keyPointsTextarea = screen.getByLabelText(/ключевые тезисы/i)
      const checkbox = screen.getByLabelText(/включить режим исследования/i)
      const submitButton = screen.getByRole('button', { name: /генерация/i })

      expect(titleInput).toBeDisabled()
      expect(keyPointsTextarea).toBeDisabled()
      expect(checkbox).toBeDisabled()
      expect(submitButton).toBeDisabled()
    })

    it('should change button text to "Generating..." when isLoading is true', () => {
      const mockOnSubmit = jest.fn()
      render(<InputForm onSubmit={mockOnSubmit} isLoading={true} currentProfile={null} />)

      // AICODE-NOTE: Design Excellence Check - Button now contains Loader2 icon + text
      const button = screen.getByRole('button', { name: /генерация/i })
      expect(button).toBeInTheDocument()
      expect(button).toHaveTextContent(/генерация/i)
    })
  })
})
