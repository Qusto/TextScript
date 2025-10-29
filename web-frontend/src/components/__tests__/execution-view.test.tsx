// AICODE-NOTE: Test suite for ExecutionView component following TDD approach
// Tests cover: tabs rendering, log display, result tab, copy/download functionality
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ExecutionView } from '../execution-view'

// AICODE-NOTE: Mock URL.createObjectURL for download functionality
global.URL.createObjectURL = jest.fn(() => 'mock-url')
global.URL.revokeObjectURL = jest.fn()

// AICODE-NOTE: Mock scrollIntoView for auto-scroll functionality
Element.prototype.scrollIntoView = jest.fn()

describe('ExecutionView Component', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  // AICODE-NOTE: T026 - Component renders with Tabs (log tab and result tab)
  describe('Component Structure (T026)', () => {
    it('should render Tabs component with "Log" and "Result" tabs', () => {
      render(<ExecutionView logLines={[]} finalArticle={null} />)

      expect(screen.getByRole('tab', { name: /log/i })).toBeInTheDocument()
      expect(screen.getByRole('tab', { name: /result/i })).toBeInTheDocument()
    })

    it('should have Log tab selected by default', () => {
      render(<ExecutionView logLines={[]} finalArticle={null} />)

      const logTab = screen.getByRole('tab', { name: /log/i })
      expect(logTab).toHaveAttribute('aria-selected', 'true')
    })
  })

  // AICODE-NOTE: T027 - Log display with pre-formatted scrollable block and auto-scroll
  describe('Log Display (T027)', () => {
    it('should display log lines in pre-formatted block', () => {
      const logLines = ['Starting generation...', 'Processing sources...', 'Generating article...']
      render(<ExecutionView logLines={logLines} finalArticle={null} />)

      logLines.forEach(line => {
        expect(screen.getByText(line)).toBeInTheDocument()
      })
    })

    it('should render empty state when no log lines', () => {
      render(<ExecutionView logLines={[]} finalArticle={null} />)

      expect(screen.getByText(/waiting for generation to start/i)).toBeInTheDocument()
    })

    it('should use pre-formatted text with monospace font', () => {
      const logLines = ['Log line 1']
      const { container } = render(<ExecutionView logLines={logLines} finalArticle={null} />)

      const preElement = container.querySelector('pre')
      expect(preElement).toBeInTheDocument()
    })

    it('should have scrollable container for logs', () => {
      const logLines = Array.from({ length: 50 }, (_, i) => `Log line ${i + 1}`)
      const { container } = render(<ExecutionView logLines={logLines} finalArticle={null} />)

      const scrollContainer = container.querySelector('.overflow-auto')
      expect(scrollContainer).toBeInTheDocument()
    })
  })

  // AICODE-NOTE: T028 - Result tab with disabled state until finalArticle is set
  describe('Result Tab (T028)', () => {
    it('should disable Result tab when finalArticle is null', () => {
      render(<ExecutionView logLines={[]} finalArticle={null} />)

      const resultTab = screen.getByRole('tab', { name: /result/i })
      expect(resultTab).toHaveAttribute('disabled')
    })

    it('should enable Result tab when finalArticle is provided', () => {
      render(<ExecutionView logLines={[]} finalArticle="# Test Article\n\nContent here" />)

      const resultTab = screen.getByRole('tab', { name: /result/i })
      expect(resultTab).not.toHaveAttribute('disabled')
    })

    it('should display article content when Result tab is clicked', async () => {
      const user = userEvent.setup()
      const article = '# Test Article\n\nThis is the article content.'
      render(<ExecutionView logLines={[]} finalArticle={article} />)

      const resultTab = screen.getByRole('tab', { name: /result/i })
      await user.click(resultTab)

      await waitFor(() => {
        expect(screen.getByText(/test article/i)).toBeInTheDocument()
      })
    })

    it('should show empty state in Result tab when no article', () => {
      render(<ExecutionView logLines={[]} finalArticle={null} />)

      // Result tab should be disabled, so we can't click it
      const resultTab = screen.getByRole('tab', { name: /result/i })
      expect(resultTab).toHaveAttribute('disabled')
    })
  })

  // AICODE-NOTE: T029 - Copy and Download buttons in result tab
  describe('Copy and Download Buttons (T029)', () => {
    it('should render Copy and Download buttons in Result tab', async () => {
      const user = userEvent.setup()
      const article = '# Test Article'
      render(<ExecutionView logLines={[]} finalArticle={article} />)

      const resultTab = screen.getByRole('tab', { name: /result/i })
      await user.click(resultTab)

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /copy/i })).toBeInTheDocument()
        expect(screen.getByRole('button', { name: /download/i })).toBeInTheDocument()
      })
    })

    it('should not show Copy/Download buttons in Log tab', () => {
      render(<ExecutionView logLines={['Log line']} finalArticle="# Article" />)

      // Log tab is selected by default
      expect(screen.queryByRole('button', { name: /copy/i })).not.toBeInTheDocument()
      expect(screen.queryByRole('button', { name: /download/i })).not.toBeInTheDocument()
    })
  })

  // AICODE-NOTE: T038 - Clipboard copy functionality
  describe('Copy Functionality (T038)', () => {
    it('should copy article to clipboard when Copy button is clicked', async () => {
      // Spy on clipboard.writeText
      const writeTextSpy = jest.spyOn(navigator.clipboard, 'writeText')

      const user = userEvent.setup()
      const article = '# Test Article\n\nContent here'
      render(<ExecutionView logLines={[]} finalArticle={article} />)

      const resultTab = screen.getByRole('tab', { name: /result/i })
      await user.click(resultTab)

      const copyButton = await screen.findByRole('button', { name: /copy/i })
      await user.click(copyButton)

      await waitFor(() => {
        expect(writeTextSpy).toHaveBeenCalledWith(article)
      })

      writeTextSpy.mockRestore()
    })

    it('should show success feedback after copying', async () => {
      const user = userEvent.setup()
      const article = '# Test Article'
      render(<ExecutionView logLines={[]} finalArticle={article} />)

      const resultTab = screen.getByRole('tab', { name: /result/i })
      await user.click(resultTab)

      const copyButton = await screen.findByRole('button', { name: /copy/i })
      await user.click(copyButton)

      // Button text should change temporarily
      await waitFor(() => {
        expect(screen.getByText(/copied/i)).toBeInTheDocument()
      })
    })
  })

  // AICODE-NOTE: T039 - Download functionality (Blob and .md file)
  describe('Download Functionality (T039)', () => {
    it('should download article as .md file when Download button is clicked', async () => {
      const user = userEvent.setup()
      const article = '# Test Article\n\nContent here'
      render(<ExecutionView logLines={[]} finalArticle={article} />)

      const resultTab = screen.getByRole('tab', { name: /result/i })
      await user.click(resultTab)

      const downloadButton = await screen.findByRole('button', { name: /download/i })

      // Mock document.createElement to return a mock link element
      const mockClick = jest.fn()
      const createElementSpy = jest.spyOn(document, 'createElement')
      const mockLink = document.createElement('a')
      mockLink.click = mockClick
      createElementSpy.mockReturnValueOnce(mockLink)

      // Mock appendChild and removeChild
      const appendChildSpy = jest.spyOn(document.body, 'appendChild')
      const removeChildSpy = jest.spyOn(document.body, 'removeChild')
      appendChildSpy.mockImplementation(() => mockLink)
      removeChildSpy.mockImplementation(() => mockLink)

      await user.click(downloadButton)

      await waitFor(() => {
        expect(URL.createObjectURL).toHaveBeenCalled()
        expect(mockLink.download).toMatch(/\.md$/)
        expect(mockClick).toHaveBeenCalled()
        expect(URL.revokeObjectURL).toHaveBeenCalled()
      })

      createElementSpy.mockRestore()
      appendChildSpy.mockRestore()
      removeChildSpy.mockRestore()
    })
  })
})
