// AICODE-NOTE: Jest setup file to import testing-library matchers
// This makes expect() assertions like toBeInTheDocument() available
import '@testing-library/jest-dom'

// AICODE-NOTE: ResizeObserver polyfill for Radix UI components (used by shadcn/ui)
// Required because jsdom doesn't provide ResizeObserver
global.ResizeObserver = jest.fn().mockImplementation(() => ({
  observe: jest.fn(),
  unobserve: jest.fn(),
  disconnect: jest.fn(),
}))

// AICODE-NOTE: Design Excellence Check - Mock fetch for SSE streaming tests
// page.tsx now uses fetch instead of EventSource for POST /api/generate
global.fetch = jest.fn()
