// AICODE-NOTE: ThemeToggle component for dark/light theme switching (T053-T054)
// Uses next-themes library for theme management with localStorage persistence
// Displays sun/moon icons from lucide-react for visual feedback
'use client'

import { Moon, Sun } from 'lucide-react'
import { useTheme } from 'next-themes'
import { Button } from '@/components/ui/button'
import { useEffect, useState } from 'react'

export function ThemeToggle() {
  // AICODE-NOTE: T053 - useTheme hook provides theme state and setTheme function
  const { theme, setTheme } = useTheme()

  // AICODE-NOTE: Prevent hydration mismatch by only rendering after mount
  // next-themes uses localStorage which is not available during SSR
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  // AICODE-NOTE: Render placeholder during SSR to prevent layout shift
  // AICODE-NOTE: WCAG 2.5.5 AA - Minimum touch target 44x44px (h-11 w-11)
  if (!mounted) {
    return (
      <Button variant="ghost" size="icon" className="h-11 w-11" disabled>
        <span className="sr-only">Loading theme toggle</span>
      </Button>
    )
  }

  // AICODE-NOTE: Toggle between dark and light themes
  const toggleTheme = () => {
    setTheme(theme === 'dark' ? 'light' : 'dark')
  }

  // AICODE-NOTE: WCAG 2.5.5 AA - Minimum touch target 44x44px (h-11 w-11)
  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={toggleTheme}
      className="h-11 w-11"
      aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} theme`}
    >
      {/* AICODE-NOTE: T054 - Sun icon for light mode, Moon icon for dark mode */}
      {/* Show opposite icon to indicate what will happen on click */}
      {theme === 'dark' ? (
        <Sun className="h-4 w-4" />
      ) : (
        <Moon className="h-4 w-4" />
      )}
      <span className="sr-only">Toggle theme</span>
    </Button>
  )
}
