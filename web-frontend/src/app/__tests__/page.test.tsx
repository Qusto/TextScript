// AICODE-NOTE: Test suite for main page.tsx with SSE integration (T033-T040)
// Tests cover: state management, EventSource handling, SSE message parsing
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import Home from '../page'

// AICODE-NOTE: Mock EventSource for SSE testing
class MockEventSource {
  url: string
  onmessage: ((event: MessageEvent) => void) | null = null
  onerror: ((event: Event) => void) | null = null
  readyState: number = 0
  CONNECTING = 0
  OPEN = 1
  CLOSED = 2

  constructor(url: string) {
    this.url = url
    this.readyState = this.OPEN
  }

  close() {
    this.readyState = this.CLOSED
  }

  // Helper method for tests to simulate messages
  simulateMessage(data: string) {
    if (this.onmessage) {
      const event = new MessageEvent('message', { data })
      this.onmessage(event)
    }
  }

  addEventListener(event: string, handler: EventListener) {
    if (event === 'message') {
      this.onmessage = handler
    } else if (event === 'error') {
      this.onerror = handler
    }
  }

  removeEventListener() {}
}

global.EventSource = MockEventSource as unknown as typeof EventSource

// AICODE-NOTE: Mock scrollIntoView for ExecutionView auto-scroll
Element.prototype.scrollIntoView = jest.fn()

describe('Home Page (Main Integration)', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  // AICODE-NOTE: T033 - State management (isLoading, logLines, finalArticle, error)
  describe('State Management (T033)', () => {
    it('should render InputForm and ExecutionView components', () => {
      render(<Home />)

      // AICODE-NOTE: Design Excellence Check - Updated label from "topic" to "Название статьи"
      expect(screen.getByLabelText(/название статьи/i)).toBeInTheDocument()
      // AICODE-NOTE: Design Excellence Check - Tab names are in Russian ("Лог", not "log")
      expect(screen.getByRole('tab', { name: /лог/i })).toBeInTheDocument()
    })

    it('should initially have empty log lines and no final article', () => {
      render(<Home />)

      // AICODE-NOTE: Design Excellence Check - Russian translations applied
      expect(screen.getByText(/ожидание начала генерации/i)).toBeInTheDocument()
      expect(screen.getByRole('tab', { name: /результат/i })).toHaveAttribute('disabled')
    })

    it('should have isLoading=false initially', () => {
      render(<Home />)

      const submitButton = screen.getByRole('button', { name: /сгенерировать/i })
      // Button should be disabled because fields are empty, not because of loading
      expect(submitButton).toBeDisabled()
    })
  })

  // AICODE-NOTE: T034 - EventSource creation with query parameters
  describe('EventSource Creation (T034)', () => {
    it('should create EventSource with correct URL when form is submitted', async () => {
      const user = userEvent.setup()
      render(<Home />)

      const topicInput = screen.getByLabelText(/название статьи/i)
      // AICODE-NOTE: Design Excellence Check - sourceUrls field removed in Phase 10+
      const submitButton = screen.getByRole('button', { name: /сгенерировать/i })

      await user.type(topicInput, 'AI Technology')
      // AICODE-NOTE: Design Excellence Check - No longer typing into sourceUrls
      await user.click(submitButton)

      // Button text should change to "Генерация..."
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /генерация/i })).toBeInTheDocument()
      })
    })
  })

  // AICODE-NOTE: T035 - Message handler appends to logLines array
  describe('EventSource Message Handler (T035)', () => {
    it('should append log messages to logLines array', async () => {
      const user = userEvent.setup()
      let eventSource: MockEventSource | null = null

      // Capture EventSource instance
      const OriginalEventSource = global.EventSource as unknown as typeof EventSource
      global.EventSource = jest.fn().mockImplementation((url: string) => {
        eventSource = new MockEventSource(url)
        return eventSource
      }) as unknown as typeof EventSource

      render(<Home />)

      const topicInput = screen.getByLabelText(/название статьи/i)
      // AICODE-NOTE: Design Excellence Check - sourceUrls field removed in Phase 10+

      await user.type(topicInput, 'AI Technology')
      // AICODE-NOTE: Design Excellence Check - No longer typing into sourceUrls
      await user.click(screen.getByRole('button', { name: /сгенерировать/i }))

      await waitFor(() => {
        expect(eventSource).not.toBeNull()
      })

      // Simulate SSE messages
      eventSource!.simulateMessage(JSON.stringify({ type: 'log', message: 'Starting...' }))
      eventSource!.simulateMessage(JSON.stringify({ type: 'log', message: 'Processing...' }))

      await waitFor(() => {
        expect(screen.getByText('Starting...')).toBeInTheDocument()
        expect(screen.getByText('Processing...')).toBeInTheDocument()
      })

      global.EventSource = OriginalEventSource
    })
  })

  // AICODE-NOTE: T036 - Result handler sets finalArticle and isLoading=false
  describe('EventSource Result Handler (T036)', () => {
    it('should set finalArticle when result event is received', async () => {
      const user = userEvent.setup()
      let eventSource: MockEventSource | null = null

      const OriginalEventSource = global.EventSource as unknown as typeof EventSource
      global.EventSource = jest.fn().mockImplementation((url: string) => {
        eventSource = new MockEventSource(url)
        return eventSource
      }) as unknown as typeof EventSource

      render(<Home />)

      const topicInput = screen.getByLabelText(/название статьи/i)
      // AICODE-NOTE: Design Excellence Check - sourceUrls field removed in Phase 10+

      await user.type(topicInput, 'AI Technology')
      // AICODE-NOTE: Design Excellence Check - No longer typing into sourceUrls
      await user.click(screen.getByRole('button', { name: /сгенерировать/i }))

      await waitFor(() => {
        expect(eventSource).not.toBeNull()
      })

      // Simulate result message
      const article = '# Test Article\n\nGenerated content'
      eventSource!.simulateMessage(JSON.stringify({ type: 'result', article }))

      await waitFor(() => {
        const resultTab = screen.getByRole('tab', { name: /результат/i })
        expect(resultTab).not.toHaveAttribute('disabled')
      })

      // isLoading should be false (button should say "Generate Article" again)
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /сгенерировать/i })).toBeInTheDocument()
      })

      global.EventSource = OriginalEventSource
    })
  })

  // AICODE-NOTE: T037 - Close handler closes EventSource connection
  describe('EventSource Close Handler (T037)', () => {
    it('should close EventSource when result is received', async () => {
      const user = userEvent.setup()
      let eventSource: MockEventSource | null = null
      const closeSpy = jest.fn()

      const OriginalEventSource = global.EventSource as unknown as typeof EventSource
      global.EventSource = jest.fn().mockImplementation((url: string) => {
        eventSource = new MockEventSource(url)
        eventSource.close = closeSpy
        return eventSource
      }) as unknown as typeof EventSource

      render(<Home />)

      const topicInput = screen.getByLabelText(/название статьи/i)
      // AICODE-NOTE: Design Excellence Check - sourceUrls field removed in Phase 10+

      await user.type(topicInput, 'AI Technology')
      // AICODE-NOTE: Design Excellence Check - No longer typing into sourceUrls
      await user.click(screen.getByRole('button', { name: /сгенерировать/i }))

      await waitFor(() => {
        expect(eventSource).not.toBeNull()
      })

      // Simulate result message (should trigger close)
      eventSource!.simulateMessage(JSON.stringify({ type: 'result', article: '# Article' }))

      await waitFor(() => {
        expect(closeSpy).toHaveBeenCalled()
      })

      global.EventSource = OriginalEventSource
    })
  })

  // AICODE-NOTE: T040 - Layout and styling (single-column, max-w-3xl, dark zinc theme)
  describe('Layout and Styling (T040)', () => {
    it('should render with single-column layout', () => {
      const { container } = render(<Home />)

      // Should have a max-width container
      const mainContainer = container.querySelector('.max-w-3xl')
      expect(mainContainer).toBeInTheDocument()
    })

    it('should have proper spacing between components', () => {
      const { container } = render(<Home />)

      // Should have gap/space-y for vertical spacing
      const spacedContainer = container.querySelector('[class*="space-y"]')
      expect(spacedContainer).toBeInTheDocument()
    })
  })

  // AICODE-NOTE: T050 - EventSource.onerror handler (connection failures)
  describe('EventSource Error Handler (T050)', () => {
    it('should set error state when EventSource.onerror is triggered', async () => {
      const user = userEvent.setup()
      let eventSource: MockEventSource | null = null

      const OriginalEventSource = global.EventSource as unknown as typeof EventSource
      global.EventSource = jest.fn().mockImplementation((url: string) => {
        eventSource = new MockEventSource(url)
        return eventSource
      }) as unknown as typeof EventSource

      render(<Home />)

      const topicInput = screen.getByLabelText(/название статьи/i)
      // AICODE-NOTE: Design Excellence Check - sourceUrls field removed in Phase 10+

      await user.type(topicInput, 'AI Technology')
      // AICODE-NOTE: Design Excellence Check - No longer typing into sourceUrls
      await user.click(screen.getByRole('button', { name: /сгенерировать/i }))

      await waitFor(() => {
        expect(eventSource).not.toBeNull()
      })

      // Simulate connection error
      if (eventSource!.onerror) {
        eventSource!.onerror(new Event('error'))
      }

      // Should display error message
      await waitFor(() => {
        expect(screen.getByText(/connection error/i)).toBeInTheDocument()
      })

      // isLoading should be false
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /сгенерировать/i })).toBeInTheDocument()
      })

      global.EventSource = OriginalEventSource
    })
  })

  // AICODE-NOTE: T051 - Custom 'error' event handler (backend errors)
  describe('Custom Error Event Handler (T051)', () => {
    it('should display Alert when error event is received from backend', async () => {
      const user = userEvent.setup()
      let eventSource: MockEventSource | null = null

      const OriginalEventSource = global.EventSource as unknown as typeof EventSource
      global.EventSource = jest.fn().mockImplementation((url: string) => {
        eventSource = new MockEventSource(url)
        return eventSource
      }) as unknown as typeof EventSource

      render(<Home />)

      const topicInput = screen.getByLabelText(/название статьи/i)
      // AICODE-NOTE: Design Excellence Check - sourceUrls field removed in Phase 10+

      await user.type(topicInput, 'AI Technology')
      // AICODE-NOTE: Design Excellence Check - No longer typing into sourceUrls
      await user.click(screen.getByRole('button', { name: /сгенерировать/i }))

      await waitFor(() => {
        expect(eventSource).not.toBeNull()
      })

      // Simulate backend error message
      const errorMessage = 'Backend validation failed: Invalid topic'
      eventSource!.simulateMessage(JSON.stringify({ type: 'error', message: errorMessage }))

      // Should display error in Alert component with role="alert"
      await waitFor(() => {
        const alert = screen.getByRole('alert')
        expect(alert).toBeInTheDocument()
        expect(screen.getByText(errorMessage)).toBeInTheDocument()
      })

      // isLoading should be false
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /сгенерировать/i })).toBeInTheDocument()
      })

      global.EventSource = OriginalEventSource
    })

    it('should show Alert with destructive variant for errors', async () => {
      const user = userEvent.setup()
      let eventSource: MockEventSource | null = null

      const OriginalEventSource = global.EventSource as unknown as typeof EventSource
      global.EventSource = jest.fn().mockImplementation((url: string) => {
        eventSource = new MockEventSource(url)
        return eventSource
      }) as unknown as typeof EventSource

      render(<Home />)

      const topicInput = screen.getByLabelText(/название статьи/i)
      // AICODE-NOTE: Design Excellence Check - sourceUrls field removed in Phase 10+

      await user.type(topicInput, 'AI Technology')
      // AICODE-NOTE: Design Excellence Check - No longer typing into sourceUrls
      await user.click(screen.getByRole('button', { name: /сгенерировать/i }))

      await waitFor(() => {
        expect(eventSource).not.toBeNull()
      })

      // Simulate error
      eventSource!.simulateMessage(JSON.stringify({ type: 'error', message: 'Test error' }))

      // Alert should have destructive border class
      await waitFor(() => {
        const alert = screen.getByRole('alert')
        expect(alert).toHaveClass('border-destructive/50')
      })

      global.EventSource = OriginalEventSource
    })
  })

  // AICODE-NOTE: T052 - Clear error state when starting new generation
  describe('Error State Reset (T052)', () => {
    it('should clear previous error when starting new generation', async () => {
      const user = userEvent.setup()
      let eventSource: MockEventSource | null = null

      const OriginalEventSource = global.EventSource as unknown as typeof EventSource
      global.EventSource = jest.fn().mockImplementation((url: string) => {
        eventSource = new MockEventSource(url)
        return eventSource
      }) as unknown as typeof EventSource

      render(<Home />)

      const topicInput = screen.getByLabelText(/название статьи/i)
      // AICODE-NOTE: Design Excellence Check - sourceUrls field removed in Phase 10+
      const submitButton = screen.getByRole('button', { name: /сгенерировать/i })

      await user.type(topicInput, 'AI Technology')
      // AICODE-NOTE: Design Excellence Check - No longer typing into sourceUrls
      await user.click(submitButton)

      await waitFor(() => {
        expect(eventSource).not.toBeNull()
      })

      // Simulate error
      eventSource!.simulateMessage(JSON.stringify({ type: 'error', message: 'First error' }))

      await waitFor(() => {
        expect(screen.getByText('First error')).toBeInTheDocument()
      })

      // Start new generation
      await user.click(screen.getByRole('button', { name: /сгенерировать/i }))

      // Error should be cleared (not in document)
      await waitFor(() => {
        expect(screen.queryByText('First error')).not.toBeInTheDocument()
      })

      global.EventSource = OriginalEventSource
    })
  })
})
