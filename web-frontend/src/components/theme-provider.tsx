"use client"

// AICODE-NOTE: ThemeProvider wrapper using next-themes for dark/light mode switching
// Default theme is set to "dark" to match Linear/Vercel design philosophy (zinc palette)
// Stores preference in localStorage for persistence across sessions

import * as React from "react"
import { ThemeProvider as NextThemesProvider } from "next-themes"

type ThemeProviderProps = Parameters<typeof NextThemesProvider>[0]

export function ThemeProvider({ children, ...props }: ThemeProviderProps) {
  return <NextThemesProvider {...props}>{children}</NextThemesProvider>
}
