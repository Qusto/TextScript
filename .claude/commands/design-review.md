---
name: design-review
description: Автоматическая проверка дизайна и верстки веб-страниц с Playwright MCP автоматизацией, AI-анализом в нескольких viewports, interactive testing, предложением фиксов и git commits
---

# Design Review Command

Команда для автоматической проверки качества дизайна и верстки веб-страниц через специализированного Design QA Agent с Playwright MCP интеграцией.

## 📋 Использование

```bash
/design-review <operation> [options]
```

**Доступные операции:**

### 1. `check` - Проверка дизайна страницы

Выполняет полный цикл проверки: скриншот → AI анализ → отчет → предложение фиксов.

```bash
# Проверить текущий localhost:5173
/design-review check

# Проверить конкретный URL
/design-review check http://localhost:5173/about

# Проверить с конкретным экраном
/design-review check --screen WelcomeScreen
```

**Что происходит (с Playwright MCP v2.0):**
1. 🎭 Автоматическая навигация через Playwright browser_navigate
2. 📸 Захват скриншотов в 3 viewports (mobile/tablet/desktop)
3. 🎯 Interactive testing - проверка touch targets, forms, buttons
4. ♿ Accessibility testing - проверка ARIA, labels, focus indicators
5. 🔍 AI анализ дизайна через vision-analyze (OpenRouter API)
6. 📝 Генерация детального отчета в `.claude/reports/`
7. 🔧 Предложение конкретных фиксов (Tailwind CSS)
8. ✅ Применение фиксов (с подтверждением)
9. 💾 Git commit с результатами
10. 🔄 Верификация через Playwright

**Категории проверки:**
- **Layout & Alignment** - Центрирование, выравнивание, иерархия
- **Typography** - Размеры, читаемость, контраст (WCAG AA)
- **Colors** - Контрастность, консистентность
- **Spacing** - Padding, margin, вертикальный ритм
- **Mobile Responsiveness** - Touch targets, breakpoints, overflow
- **Accessibility** (NEW) - ARIA, labels, focus indicators, keyboard navigation
- **Interactive Elements** (NEW) - Touch targets >= 44px, clickable, functional

**Severity Levels:**
- 🔴 **Critical** - Блокирует UX (маленькие touch targets, неконтрастный текст)
- 🟡 **Major** - Значительно ухудшает UX (неравномерные отступы, слабая иерархия)
- 🟢 **Minor** - Улучшения для polish (мелкие несоответствия)

---

### 2. `report` - Показать последний отчет

```bash
/design-review report

# Показать конкретный отчет
/design-review report 2025-10-07-143022
```

Отображает последний или конкретный Design QA отчет со всеми найденными проблемами.

---

### 3. `history` - История проверок

```bash
/design-review history

# Показать последние N проверок
/design-review history --limit 5
```

Показывает список всех проведенных Design QA проверок с summary.

---

### 4. `fix` - Применить конкретное исправление

```bash
# Применить фикс по ID из отчета
/design-review fix CRITICAL-001

# Применить все critical фиксы
/design-review fix --severity critical

# Применить все фиксы из последнего отчета
/design-review fix --all
```

Применяет конкретные исправления из сгенерированного отчета.

---

### 5. `verify` - Верификация после фиксов

```bash
/design-review verify

# Верифицировать конкретные issues
/design-review verify CRITICAL-001 MAJOR-002
```

Делает новый скриншот и проверяет что проблемы были исправлены. Создает BEFORE/AFTER сравнение.

---

## 🎯 Workflow Example

```bash
# 1. Запустить проверку
/design-review check

# Output:
# ✅ Starting Design QA check for http://localhost:5173
# 📸 Screenshot captured
# 🔍 Analyzing... Found 5 issues (1 critical, 2 major, 2 minor)
# 📝 Report saved: .claude/reports/design-qa-2025-10-07-143022.md
#
# Would you like to see the detailed report? (yes/no)

yes

# [Shows detailed report with issues]
#
# I can fix the critical and major issues. Apply fixes? (yes/no/selective)

yes

# 🔧 Applying fixes...
# ✅ Fixed CRITICAL-001: Button touch target (WelcomeScreen.tsx)
# ✅ Fixed MAJOR-001: Text contrast (ChatScreen.tsx)
# ✅ Fixed MAJOR-002: Inconsistent spacing (AmountScreen.tsx)
#
# 💾 Creating git commit...
# ✅ Commit created: fix(design): improve touch targets and contrast
#
# 🔄 Verifying fixes...

/design-review verify

# ✅ All fixes verified successfully!
# 📊 BEFORE vs AFTER screenshots saved
```

---

## 📊 Report Format

Отчеты сохраняются в `.claude/reports/design-qa-[timestamp].md` в следующем формате:

```markdown
# Design QA Report

**Date:** 2025-10-07 14:30:22
**URL:** http://localhost:5173
**Screen:** WelcomeScreen
**Screenshot:** .claude/reports/screenshots/2025-10-07-143022.png

## Executive Summary
The WelcomeScreen has good overall structure but requires attention to
mobile touch targets and text contrast for accessibility compliance.

## Issues Found: 5
- Critical: 1
- Major: 2
- Minor: 2

---

## Critical Issues

### [CRITICAL-001] Button touch target too small for mobile
- **Category:** Mobile
- **Location:** src/components/WelcomeScreen.tsx:45
- **Description:** Primary CTA button has insufficient touch target (32x32px)
- **Impact:** Difficult to tap on mobile devices, fails iOS HIG guidelines
- **Recommendation:** Increase to minimum 44x44px
- **Fix:**
  ```typescript
  // BEFORE
  <button className="px-4 py-2 text-sm">

  // AFTER
  <button className="px-6 py-3 text-base min-h-[44px] min-w-[44px]">
  ```
- **Status:** ⏳ Pending

[... остальные issues ...]
```

---

## 🔧 Configuration

Агент использует следующие настройки:

**Playwright MCP (NEW v2.0):**
- MCP Server: `@playwright/mcp@latest`
- Browser: Chromium (headed mode для MVP)
- Viewports:
  - Mobile: 375x667px
  - Tablet: 768x1024px
  - Desktop: 1920x1080px
- Timeout: 30s page load
- Tools: browser_navigate, browser_take_screenshot, browser_evaluate, browser_click, browser_accessibility
- Installation: `claude mcp add playwright npx '@playwright/mcp@latest'`

**Vision Analysis:**
- Tool: `vision-analyze` (OpenRouter API)
- Model: `google/gemini-2.5-flash-preview-09-2025`
- Screenshots: `.claude/reports/screenshots/`
- Requires: `OPENROUTER_API_KEY` environment variable

**Project Context:**
- Dev server: `http://localhost:5173`
- Tech stack: React 18 + Vite + Tailwind CSS + shadcn/ui
- Style system: Tailwind utility classes only (no inline styles)
- Theme: Custom coach-* colors

**Design Standards:**
- Touch targets: Minimum 44x44px (iOS HIG)
- Text contrast: WCAG AA (4.5:1 normal, 3:1 large)
- Spacing: 4px/8px grid system
- Typography: Minimum 16px for body text
- Line height: 1.5-1.75 for readability
- Accessibility: WCAG AA compliance

---

## 🚀 Best Practices

**Что проверяется:**
✅ Layout alignment и visual hierarchy
✅ Typography sizes и readability
✅ Color contrast (WCAG AA/AAA)
✅ Spacing consistency (Tailwind scale)
✅ Mobile touch targets (автоматически через Playwright)
✅ Responsive breakpoints (тестируется в 3 viewports)
✅ Component consistency (shadcn/ui patterns)
✅ Accessibility (ARIA, labels, focus - NEW)
✅ Interactive elements functionality (buttons, forms - NEW)

**Что НЕ изменяется:**
❌ Component logic (только styles)
❌ TypeScript types
❌ Event handlers
❌ State management
❌ Business logic

**Git Commits:**
- Format: `fix(design): [description]`
- Includes: Design QA report reference
- Co-authored: Claude Code

---

## 🔒 Safety Features

1. **Всегда показывает diff** перед применением изменений
2. **Запрашивает подтверждение** для Critical/Major fixes
3. **Создает git commits** для отслеживания изменений
4. **Сохраняет BEFORE/AFTER** скриншоты
5. **Не трогает логику** - только стили
6. **Использует только Tailwind** - no inline styles

---

## 📁 File Structure

```
.claude/
├── agents/
│   └── design-qa.md              # Субагент (это вы!)
├── commands/
│   └── design-review.md          # Документация команды
└── reports/
    ├── design-qa-[timestamp].md  # Отчеты проверок
    └── screenshots/
        ├── [timestamp].png       # BEFORE скриншоты
        └── [timestamp]-after.png # AFTER скриншоты
```

---

## 🆘 Troubleshooting

**Dev server не отвечает:**
```bash
npm run dev
# Подождать 3-5 секунд
```

**vision-analyze не работает:**
```bash
# Проверить environment variables
echo $OPENROUTER_API_KEY

# Установить если отсутствует
export OPENROUTER_API_KEY="sk-or-v1-..."
source ~/.zshrc
```

**Playwright MCP не подключен:**
```bash
# Установить Playwright MCP
claude mcp add playwright npx '@playwright/mcp@latest'

# Установить Chromium браузер
npx playwright install chromium

# Проверить установку
claude mcp list | grep playwright
```

**Не хватает Screen Recording permission (для screencapture fallback):**
```
System Settings > Privacy & Security > Screen Recording
→ Enable для Terminal/iTerm
```

**jq не установлен:**
```bash
brew install jq
```

---

## 📚 See Also

- `.claude/agents/design-qa.md` - Полная документация агента
- `CLAUDE.md` - Общая документация проекта
- [Tailwind CSS Docs](https://tailwindcss.com/docs)
- [shadcn/ui Components](https://ui.shadcn.com)
- [WCAG Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)

---

**Version:** 2.0.0 (с Playwright MCP)
**Created:** 2025-10-07
**Updated:** 2025-10-07 (Playwright MCP integration)
**Status:** MVP Ready

**Changelog:**
- ✅ 2.0.0: Playwright MCP integration
  - Автоматизация браузера
  - Multi-viewport testing
  - Interactive element testing
  - Accessibility testing
- 1.0.0: Initial MVP с screencapture

**Примеры:**

```bash
# Быстрая проверка
/design-review check

# Полная проверка с применением всех фиксов
/design-review check && /design-review fix --all && /design-review verify

# Просмотр истории
/design-review history

# Применить только critical фиксы
/design-review fix --severity critical
```
