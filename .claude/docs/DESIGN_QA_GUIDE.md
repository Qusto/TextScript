# Design QA Automation - Полное руководство

## 📖 Содержание

1. [Что это такое](#что-это-такое)
2. [Установка и настройка](#установка-и-настройка)
3. [Архитектура системы](#архитектура-системы)
4. [Использование](#использование)
5. [Что проверяется](#что-проверяется)
6. [Интерпретация отчетов](#интерпретация-отчетов)
7. [Best Practices](#best-practices)
8. [Troubleshooting](#troubleshooting)

---

## Что это такое

**Design QA Automation** - это интеллектуальная система автоматизированной проверки качества фронтенда через Chrome DevTools MCP (Model Context Protocol).

### Ключевые возможности

✅ **Responsive Design Testing**
- Автоматическое тестирование на 7 viewports (375px → 3840px)
- Детекция horizontal scroll issues
- Проверка touch target sizes на mobile (≥44x44px)
- Screenshots для visual regression

✅ **Performance Analysis**
- Core Web Vitals (LCP, FID, CLS)
- Bundle size analysis
- Network timing под разными условиями (3G, 4G, WiFi)
- Performance traces для bottle necks

✅ **Accessibility (WCAG 2.1 AA)**
- Color contrast ratio (4.5:1 для text, 3:1 для large text)
- Semantic HTML validation
- ARIA labels и alt text
- Keyboard navigation testing
- Screen reader compatibility

✅ **Visual Consistency**
- Font family usage analysis
- Color palette consistency
- Spacing system validation (4px/8px grid)

✅ **Error Monitoring**
- JavaScript console errors
- Console warnings
- Network failed requests
- CORS issues detection

### Почему это важно

| Проблема | Как решается |
|----------|--------------|
| "Работает на моей машине, но не на iPhone" | Автоматическое тестирование на 7+ devices |
| "Слишком медленно загружается" | Performance metrics с конкретными рекомендациями |
| "Пользователи жалуются на доступность" | WCAG AA compliance из коробки |
| "Дизайн ломается на планшете" | Screenshots всех breakpoints |
| "Ошибки в production, которых не было локально" | Console monitoring + network analysis |

---

## Установка и настройка

### Шаг 1: Установка Chrome DevTools MCP

```bash
# Установить через Claude CLI
claude mcp add chrome-devtools npx chrome-devtools-mcp@latest
```

**Что происходит:**
- Добавляется конфигурация в `~/.claude.json`
- MCP server настраивается для работы с Chrome DevTools Protocol

**Проверка установки:**
```bash
cat ~/.claude.json | grep chrome-devtools
```

Должно показать:
```json
{
  "mcpServers": {
    "chrome-devtools": {
      "command": "npx",
      "args": ["-y", "chrome-devtools-mcp@latest"]
    }
  }
}
```

### Шаг 2: Перезапуск Claude Code

**ВАЖНО:** MCP серверы загружаются при старте Claude Code.

```bash
# 1. Выйти из текущей сессии Claude Code
exit

# 2. Запустить заново
claude
```

### Шаг 3: Проверка доступности MCP tools

После перезапуска, MCP Chrome DevTools tools должны стать доступны:

```typescript
// Доступные tools (пример):
mcp__chrome-devtools__navigate_to
mcp__chrome-devtools__take_screenshot
mcp__chrome-devtools__performance_start_trace
mcp__chrome-devtools__get_console_messages
// ... и другие
```

**Тестовая команда:**
```bash
# Попросить Claude использовать MCP tool
"Can you take a screenshot of https://example.com using Chrome DevTools MCP?"
```

Если работает - установка успешна ✅

### Шаг 4: Создание директории для отчетов

```bash
mkdir -p .claude/reports/design-qa
```

---

## Архитектура системы

### Компоненты

```
┌─────────────────────────────────────────────────┐
│                  Claude Code                    │
│  (AI Assistant with Tool Calling Capability)    │
└────────────┬────────────────────────────────────┘
             │
             │ Invokes
             ▼
┌─────────────────────────────────────────────────┐
│        design-qa-automation Agent               │
│   (.claude/agents/design-qa-automation.md)      │
│                                                 │
│  - Orchestrates testing workflow                │
│  - Calls MCP Chrome DevTools tools              │
│  - Analyzes results                             │
│  - Generates reports                            │
└────────────┬────────────────────────────────────┘
             │
             │ Uses MCP Protocol
             ▼
┌─────────────────────────────────────────────────┐
│       Chrome DevTools MCP Server                │
│      (chrome-devtools-mcp@latest)               │
│                                                 │
│  - Starts Chrome browser instance               │
│  - Exposes DevTools Protocol via MCP            │
│  - Provides tools: navigate, screenshot, etc.   │
└────────────┬────────────────────────────────────┘
             │
             │ Chrome DevTools Protocol (CDP)
             ▼
┌─────────────────────────────────────────────────┐
│             Chrome Browser                      │
│                                                 │
│  - Renders web application                      │
│  - Executes JavaScript                          │
│  - Provides performance metrics                 │
│  - Captures screenshots                         │
└─────────────────────────────────────────────────┘
```

### Workflow

```
User Request: "/design-qa http://localhost:3000"
      │
      ▼
[1] Agent: Pre-Check Setup
    - Verify dev server running
    - Create report directory
    - Connect to MCP server
      │
      ▼
[2] Agent: Responsive Testing Loop
    FOR EACH viewport in [375px, 768px, 1440px, ...]
      - MCP: resize_page(width, height)
      - MCP: take_screenshot()
      - MCP: evaluate_javascript(check_touch_targets)
      - Collect issues
      │
      ▼
[3] Agent: Performance Analysis
    - MCP: performance_start_trace()
    - MCP: navigate_to(url)
    - MCP: performance_stop_trace()
    - Analyze Core Web Vitals
    - Check bundle sizes
      │
      ▼
[4] Agent: Accessibility Testing
    - MCP: evaluate_javascript(contrast_checker)
    - MCP: evaluate_javascript(semantic_html_checker)
    - MCP: evaluate_javascript(keyboard_nav_checker)
    - WCAG AA compliance validation
      │
      ▼
[5] Agent: Console & Network Monitoring
    - MCP: enable_console_monitoring()
    - MCP: get_console_messages()
    - MCP: enable_network_monitoring()
    - MCP: get_network_requests()
    - Check for errors, CORS issues
      │
      ▼
[6] Agent: Report Generation
    - Sort issues by severity
    - Generate markdown report
    - Save screenshots
    - Write to .claude/reports/design-qa/
      │
      ▼
User receives:
  - Executive summary
  - Detailed issues list
  - Screenshots
  - Actionable recommendations
```

---

## Использование

### Basic Usage

```bash
# Полный аудит текущей страницы (auto-detect dev server)
/design-qa

# Полный аудит конкретного URL
/design-qa http://localhost:3000

# Полный аудит конкретной страницы
/design-qa http://localhost:3000/dashboard
```

### Advanced Usage

**Performance-only check:**
```bash
/design-qa perf
/design-qa performance http://localhost:3000
```

**Accessibility-only check:**
```bash
/design-qa a11y
/design-qa accessibility
```

**Responsive design only:**
```bash
/design-qa rwd
/design-qa responsive
```

**Multiple pages:**
```bash
/design-qa --urls "http://localhost:3000,http://localhost:3000/dashboard,http://localhost:3000/profile"
```

**Custom viewports:**
```bash
/design-qa --viewports "375x667,768x1024,1920x1080"
```

### Workflow Integration

**Scenario 1: Pre-PR Checklist**

```bash
# 1. Запустить dev server
cd web-frontend && npm run dev

# 2. Полная проверка всех critical pages
/design-qa http://localhost:3000           # Homepage
/design-qa http://localhost:3000/dashboard # Dashboard
/design-qa http://localhost:3000/profile   # Profile

# 3. Изучить отчеты
cat .claude/reports/design-qa/design-qa-2025-11-02.md

# 4. Если CRITICAL issues > 0 - исправить
/design-qa fix

# 5. Повторная проверка
/design-qa verify

# 6. PR только когда 0 CRITICAL issues
```

**Scenario 2: Performance Optimization**

```bash
# Baseline
/design-qa perf
# Output: LCP 3200ms, CLS 0.15

# Apply optimizations...
# - Add Next.js <Image> component
# - Enable gzip compression
# - Lazy load components

# Re-check
/design-qa perf
# Output: LCP 1800ms ✅, CLS 0.08 ✅

# Compare improvement
# LCP: 3200ms → 1800ms (43% faster)
# CLS: 0.15 → 0.08 (46% better)
```

**Scenario 3: Accessibility Compliance**

```bash
# Initial check
/design-qa a11y

# Report shows:
# - CRITICAL: 4 text elements contrast < 4.5:1
# - CRITICAL: 2 buttons < 44px on mobile
# - MAJOR: 3 images missing alt text

# Auto-fix what's possible
/design-qa fix

# Manual fixes via frontend-developer
claude task frontend-developer "Fix remaining a11y issues from report"

# Final verification
/design-qa a11y
# ✅ WCAG 2.1 AA Compliant
```

---

## Что проверяется

### 1. Responsive Design

**Viewports Matrix:**

| Viewport | Width | Height | Device Example |
|----------|-------|--------|----------------|
| Mobile Portrait | 375px | 667px | iPhone SE |
| Mobile Landscape | 667px | 375px | iPhone SE rotated |
| Tablet Portrait | 768px | 1024px | iPad |
| Tablet Landscape | 1024px | 768px | iPad rotated |
| Desktop Standard | 1440px | 900px | MacBook Pro |
| Desktop Large | 1920px | 1080px | Full HD |
| Desktop 4K | 3840px | 2160px | 4K Monitor |

**Checks:**

✅ Horizontal scroll detection
```javascript
// CRITICAL if true
document.documentElement.scrollWidth > document.documentElement.clientWidth
```

✅ Touch target sizes (mobile only)
```javascript
// CRITICAL if < 44x44px on mobile viewports
button.width >= 44 && button.height >= 44
```

✅ Layout breakpoints
- Verify responsive classes (`sm:`, `md:`, `lg:`) work correctly
- Check content doesn't overflow containers
- Verify images don't distort

✅ Screenshots for visual regression
- Full-page screenshots at each viewport
- Saved to `.claude/reports/design-qa/screenshots/`

### 2. Performance (Core Web Vitals)

**Metrics:**

| Metric | Good | Needs Improvement | Poor |
|--------|------|-------------------|------|
| **LCP** (Largest Contentful Paint) | ≤ 2.5s | 2.5s - 4.0s | > 4.0s |
| **FID** (First Input Delay) | ≤ 100ms | 100ms - 300ms | > 300ms |
| **CLS** (Cumulative Layout Shift) | ≤ 0.1 | 0.1 - 0.25 | > 0.25 |

**Additional checks:**

✅ **Bundle size**
- Total JS size threshold: 500KB
- Individual chunk size: 200KB
- Recommendation: Code splitting, lazy loading

✅ **Network timing**
- Time to First Byte (TTFB)
- Resource load timing
- Slow 3G simulation (2s latency)

✅ **Image optimization**
- Unoptimized images detection
- Missing width/height attributes
- WebP/AVIF format recommendations

### 3. Accessibility (WCAG 2.1 AA)

**Color Contrast:**

```javascript
// Normal text (< 18px or < 14px bold)
contrast_ratio >= 4.5:1  // WCAG AA

// Large text (≥ 18px or ≥ 14px bold)
contrast_ratio >= 3:1    // WCAG AA
```

**Touch Targets:**
```javascript
// iOS Human Interface Guidelines
min_width >= 44px && min_height >= 44px
```

**Semantic HTML:**
- Proper heading hierarchy (h1 → h2 → h3, no skips)
- No `div`/`span` with `onclick` (use `<button>`)
- Forms have `<label>` elements
- Lists use `<ul>`/`<ol>` + `<li>`

**ARIA & Alt Text:**
- All `<img>` have `alt` attribute
- Interactive elements have accessible names
- Form inputs have associated labels
- Dynamic content has ARIA live regions

**Keyboard Navigation:**
- All interactive elements focusable
- Tab order is logical
- Focus indicators visible
- No `tabindex` > 0

### 4. Visual Consistency

**Font Analysis:**
```javascript
// Collect all unique font families
const fonts = Array.from(
  new Set(
    Array.from(document.querySelectorAll('*'))
      .map(el => getComputedStyle(el).fontFamily)
  )
);

// MINOR issue if > 5 unique fonts
// Recommendation: Stick to 2-3 fonts max
```

**Color Palette:**
```javascript
// Collect all unique colors (text, background, border)
const colors = collectUniqueColors();

// MINOR issue if > 20 unique colors
// Recommendation: Use design tokens
```

**Spacing System:**
```javascript
// Verify 4px/8px grid adherence
// Check padding, margin, gap values
// Recommendation: Use Tailwind spacing scale
```

### 5. Console & Network

**Console Errors:**
```javascript
// CRITICAL if any errors found
const errors = console.filter(msg => msg.level === 'error');

// MINOR if warnings found
const warnings = console.filter(msg => msg.level === 'warning');
```

**Network Issues:**
```javascript
// CRITICAL: Failed requests (4xx, 5xx)
const failedRequests = requests.filter(r => r.status >= 400);

// MAJOR: CORS issues
const corsIssues = requests.filter(r =>
  !r.responseHeaders['access-control-allow-origin']
);

// MINOR: Uncompressed resources
const uncompressed = requests.filter(r =>
  !r.responseHeaders['content-encoding']
);
```

---

## Интерпретация отчетов

### Report Structure

```markdown
# Design QA Automation Report

**Generated:** 2025-11-02T10:30:00Z
**Agent:** design-qa-automation
**URLs Tested:** 3
**Total Issues:** 11

## Executive Summary

| Severity | Count |
|----------|-------|
| 🔴 CRITICAL | 3 |
| 🟡 MAJOR    | 5 |
| 🔵 MINOR    | 2 |

## Test Coverage
- ✅ Responsive Design (7 viewports)
- ✅ Performance (Core Web Vitals)
- ✅ Accessibility (WCAG 2.1 AA)
- ✅ Console Monitoring
- ✅ Network Analysis
- ✅ Visual Consistency

## Issues Found

### CRITICAL-001: Accessibility - Touch Targets
**Issue:** Found 3 touch targets smaller than 44x44px on mobile viewport
**Details:**
- Button "Submit" - 32x32px
- Link "Read More" - 40x28px
- Icon button "Menu" - 36x36px

**Recommendation:** Increase to minimum 44x44px using `min-h-[44px] min-w-[44px]`

**WCAG Reference:** WCAG 2.1 AA - 2.5.5 Target Size

**File(s):**
- app/(auth)/login/page.tsx:67
- components/features/articles/ArticleCard.tsx:45

---

### CRITICAL-002: Accessibility - Color Contrast
**Issue:** Found 5 text elements with contrast ratio below WCAG AA threshold

**Details:**
| Element | Text | Contrast | Required | Font Size |
|---------|------|----------|----------|-----------|
| p | "Lorem ipsum..." | 3.2:1 | 4.5:1 | 16px |
| span | "Secondary text" | 2.8:1 | 4.5:1 | 14px |

**Recommendation:** Use darker colors
- `text-gray-400` → `text-gray-700` (or darker)
- Check with contrast checker: https://webaim.org/resources/contrastchecker/

**WCAG Reference:** WCAG 2.1 AA - 1.4.3 Contrast (Minimum)

**File(s):**
- components/ui/text.tsx:12

---

### MAJOR-001: Performance - Layout Shift
**Issue:** CLS is 0.15 (threshold: 0.1)

**Recommendation:**
- Set explicit width/height on all images
- Reserve space for dynamic content (ads, embeds)
- Use Next.js <Image> component with dimensions

**File(s):**
- app/blog/page.tsx (missing image dimensions)

---

### MINOR-001: Design - Font Consistency
**Issue:** Too many font families used (7)

**Details:**
- "Inter", sans-serif
- "Roboto", sans-serif
- "Arial", sans-serif
- ... (4 more)

**Recommendation:** Stick to 2-3 font families max
- Primary: "Inter" for UI
- Secondary: "Roboto Mono" for code

---

## Screenshots

### Mobile Portrait (375x667)
![Mobile Portrait](./screenshots/homepage-mobile-portrait.png)

### Desktop Standard (1440x900)
![Desktop](./screenshots/homepage-desktop-standard.png)

## Performance Metrics

| Metric | Value | Threshold | Status |
|--------|-------|-----------|--------|
| LCP    | 1823ms | 2500ms | ✅ Good |
| FID    | 45ms   | 100ms  | ✅ Good |
| CLS    | 0.15   | 0.1    | ⚠️ Needs Improvement |
| Bundle | 385KB  | 500KB  | ✅ Good |

## Next Steps

1. **Fix CRITICAL issues first** (3 issues)
   - Touch target sizes
   - Color contrast

2. **Address MAJOR issues** (5 issues)
   - Layout shift (CLS)
   - Console errors

3. **Polish MINOR issues** (2 issues)
   - Font consistency
   - Color palette

## Automated Fix

```bash
claude task frontend-developer "Apply fixes from .claude/reports/design-qa/design-qa-2025-11-02.md"
```
```

### Severity Levels

**🔴 CRITICAL** - Must fix before deployment
- Accessibility blockers (WCAG AA violations)
- Console errors affecting functionality
- Failed network requests
- Touch targets < 44px on mobile
- Contrast ratio < 4.5:1 for normal text

**🟡 MAJOR** - Should fix soon
- Performance issues (LCP > 2.5s, CLS > 0.1)
- Semantic HTML issues
- Missing ARIA labels
- CORS warnings
- Slow load on 3G

**🔵 MINOR** - Nice to have
- Visual consistency (fonts, colors)
- Console warnings (non-critical)
- Uncompressed resources
- Code quality suggestions

### How to prioritize

```
Priority = (Severity Weight) × (User Impact)

Severity Weights:
- CRITICAL: 10
- MAJOR: 5
- MINOR: 1

User Impact (estimate % affected users):
- Accessibility: 15-20% (users with disabilities)
- Mobile touch targets: 60% (mobile users)
- Performance: 100% (all users)
- Visual consistency: 30% (design-conscious users)

Example:
CRITICAL Touch Target Issue:
  Priority = 10 × 0.6 = 6.0 (HIGH)

MINOR Font Consistency:
  Priority = 1 × 0.3 = 0.3 (LOW)
```

---

## Best Practices

### 1. Run Before Every PR

```bash
# Git hook (.git/hooks/pre-push)
#!/bin/bash

echo "Running Design QA checks..."

# Start dev server in background
npm run dev &
DEV_PID=$!

# Wait for server to be ready
sleep 5

# Run design QA
claude task design-qa-automation "Audit http://localhost:3000"

# Check for CRITICAL issues
CRITICAL_COUNT=$(grep -c "CRITICAL" .claude/reports/design-qa/design-qa-*.md)

# Kill dev server
kill $DEV_PID

if [ $CRITICAL_COUNT -gt 0 ]; then
  echo "❌ Found $CRITICAL_COUNT CRITICAL issues. Fix before pushing."
  exit 1
else
  echo "✅ Design QA passed!"
  exit 0
fi
```

### 2. Create Baselines for Visual Regression

```bash
# First run - create baseline
/design-qa --baseline

# Subsequent runs - compare against baseline
/design-qa --compare

# If differences found, review screenshots
diff -r .claude/reports/design-qa/baseline/ \
        .claude/reports/design-qa/current/

# Update baseline if changes are intentional
/design-qa --update-baseline
```

### 3. Test Critical User Journeys

```bash
# Homepage → Login → Dashboard → Profile
/design-qa --journey "home,login,dashboard,profile"

# Simulates user flow and checks each step
# Reports issues specific to each page
```

### 4. Performance Budgets

```yaml
# .claude/config/performance-budget.yml
budgets:
  lcp: 2000ms      # Stricter than default 2500ms
  fid: 50ms        # Stricter than default 100ms
  cls: 0.05        # Stricter than default 0.1
  bundle_js: 400kb # Stricter than default 500kb
```

```bash
/design-qa perf --budget .claude/config/performance-budget.yml
```

### 5. Accessibility First

```bash
# Run a11y check on EVERY component creation
/design-qa a11y http://localhost:3000/new-feature

# Block PR if WCAG AA violations exist
# Treat accessibility as non-negotiable
```

### 6. Document Exceptions

```yaml
# .claude/config/design-qa-exceptions.yml
exceptions:
  - rule: "touch-target-size"
    reason: "Icon buttons in compact toolbar - acceptable UX tradeoff"
    approved_by: "Lead Designer"
    expires: "2025-12-31"

  - rule: "color-contrast"
    element: ".branding-logo-text"
    reason: "Brand colors mandated by marketing - cannot change"
    approved_by: "CMO"
    waiver: "permanent"
```

---

## Troubleshooting

### Issue: "MCP server chrome-devtools not found"

**Причина:** MCP server не установлен или не загружен

**Решение:**

```bash
# 1. Проверить установлен ли MCP server
cat ~/.claude.json | grep chrome-devtools

# 2. Если нет - установить
claude mcp add chrome-devtools npx chrome-devtools-mcp@latest

# 3. Перезапустить Claude Code
exit
claude

# 4. Проверить доступность tools
# Попросить Claude показать доступные MCP tools
"Show me available MCP Chrome DevTools tools"
```

### Issue: "Connection refused on localhost:3000"

**Причина:** Dev server не запущен

**Решение:**

```bash
# 1. Проверить запущен ли server
lsof -i :3000

# 2. Если нет - запустить
cd web-frontend
npm run dev

# 3. Дождаться "Ready on http://localhost:3000"

# 4. Повторить design-qa команду
```

### Issue: "Cannot take screenshot - Chrome not found"

**Причина:** Chrome browser не установлен или недоступен

**Решение:**

```bash
# 1. Проверить Chrome установлен
which google-chrome || which chromium

# 2. Если нет - установить Chrome
# macOS:
brew install --cask google-chrome

# Linux:
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo apt install ./google-chrome-stable_current_amd64.deb

# 3. Проверить MCP server может запустить Chrome
npx chrome-devtools-mcp@latest --test
```

### Issue: "Performance metrics show 0ms for everything"

**Причина:** Page не загрузилась полностью

**Решение:**

```bash
# 1. Увеличить wait time в агенте
# Editing .claude/agents/design-qa-automation.md
# Find: await wait(5000)
# Change to: await wait(10000)

# 2. Проверить нет ли console errors блокирующих load event

# 3. Добавить explicit wait for specific element
await wait_for_selector('.page-loaded-indicator')
```

### Issue: "Too many issues reported (100+)"

**Причина:** Страница имеет серьезные проблемы ИЛИ ложные срабатывания

**Решение:**

```bash
# 1. Фильтровать только CRITICAL
/design-qa --severity critical

# 2. Проверить один category за раз
/design-qa a11y      # Only accessibility
/design-qa perf      # Only performance

# 3. Exclude known false positives
# .claude/config/design-qa-ignore.yml
ignore:
  - selector: ".third-party-widget"
    rules: ["color-contrast", "touch-target"]
    reason: "External widget - cannot modify"
```

### Issue: "Report generated but screenshots are broken"

**Причина:** Screenshot paths неправильные или файлы не сохранились

**Решение:**

```bash
# 1. Проверить директория существует
ls -la .claude/reports/design-qa/screenshots/

# 2. Проверить права на запись
chmod 755 .claude/reports/design-qa/screenshots/

# 3. Проверить disk space
df -h

# 4. Debug screenshot saving
# В агенте добавить logging:
console.log('Saving screenshot to:', screenshotPath);
```

### Issue: "WCAG contrast checker reports incorrect values"

**Причина:** Background color неправильно определен (transparent, gradient)

**Решение:**

```javascript
// Улучшить contrast checker
function getEffectiveBackground(element) {
  let el = element;
  let bgColor = null;

  // Traverse up until we find non-transparent background
  while (el && !bgColor) {
    const style = getComputedStyle(el);
    const bg = style.backgroundColor;

    if (bg && bg !== 'transparent' && bg !== 'rgba(0, 0, 0, 0)') {
      bgColor = bg;
      break;
    }

    el = el.parentElement;
  }

  return bgColor || 'rgb(255, 255, 255)'; // Default white
}
```

---

## Advanced Topics

### Custom Test Scenarios

```yaml
# .claude/scenarios/user-registration.yml
name: "User Registration Flow"
steps:
  - url: "http://localhost:3000/register"
    checks:
      - accessibility
      - responsive
    screenshots: true

  - action: "fill_form"
    fields:
      email: "test@example.com"
      password: "Test123!"
    submit: true

  - url: "http://localhost:3000/verify-email"
    checks:
      - accessibility
      - console_errors

  - action: "click"
    selector: ".verify-button"

  - url: "http://localhost:3000/dashboard"
    checks:
      - performance
      - accessibility
```

```bash
# Run custom scenario
/design-qa --scenario .claude/scenarios/user-registration.yml
```

### CI/CD Integration

```yaml
# .github/workflows/design-qa.yml
name: Design QA

on: [pull_request]

jobs:
  design-qa:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Install dependencies
        run: |
          cd web-frontend
          npm install

      - name: Start dev server
        run: |
          cd web-frontend
          npm run dev &
          npx wait-on http://localhost:3000

      - name: Install Claude Code
        run: |
          curl -fsSL https://claude.ai/install.sh | sh
          claude mcp add chrome-devtools npx chrome-devtools-mcp@latest

      - name: Run Design QA
        run: |
          claude task design-qa-automation "Full audit http://localhost:3000"

      - name: Check for CRITICAL issues
        run: |
          CRITICAL=$(grep -c "CRITICAL" .claude/reports/design-qa/*.md || echo 0)
          if [ $CRITICAL -gt 0 ]; then
            echo "❌ Found $CRITICAL CRITICAL issues"
            cat .claude/reports/design-qa/*.md
            exit 1
          fi

      - name: Upload report
        uses: actions/upload-artifact@v3
        with:
          name: design-qa-report
          path: .claude/reports/design-qa/
```

### Performance Monitoring Over Time

```bash
# Track performance metrics over time
# .claude/scripts/track-performance.sh

#!/bin/bash

DATE=$(date +%Y-%m-%d)
REPORT_DIR=".claude/reports/design-qa"
METRICS_FILE=".claude/metrics/performance-history.csv"

# Run performance check
claude task design-qa-automation "Performance check http://localhost:3000"

# Extract metrics from latest report
LATEST_REPORT=$(ls -t $REPORT_DIR/design-qa-*.md | head -1)
LCP=$(grep "LCP" $LATEST_REPORT | awk '{print $3}')
FID=$(grep "FID" $LATEST_REPORT | awk '{print $3}')
CLS=$(grep "CLS" $LATEST_REPORT | awk '{print $3}')

# Append to CSV
echo "$DATE,$LCP,$FID,$CLS" >> $METRICS_FILE

# Generate trend chart
python .claude/scripts/generate-performance-chart.py $METRICS_FILE
```

---

## Summary

**Design QA Automation** с Chrome DevTools MCP предоставляет:

✅ Полную автоматизацию проверки качества фронтенда
✅ WCAG 2.1 AA compliance из коробки
✅ Core Web Vitals мониторинг
✅ Responsive design validation на 7+ devices
✅ Детальные отчеты с actionable recommendations
✅ Интеграция с frontend-developer агентом для автофиксов
✅ CI/CD готовность

**Ключевые преимущества:**

- Экономия времени QA (автоматизация 80% рутинных проверок)
- Раннее обнаружение accessibility issues
- Предотвращение performance regression
- Consistency в дизайне
- Compliance с web standards (WCAG, Core Web Vitals)

**Когда использовать:**

- ✅ Перед каждым PR
- ✅ После UI изменений
- ✅ Во время performance оптимизации
- ✅ При добавлении новых страниц/компонентов
- ✅ В CI/CD pipeline

---

**Version:** 1.0.0
**Last Updated:** 2025-11-02
**Author:** design-qa-automation agent
**License:** MIT
