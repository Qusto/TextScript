---
name: design-check
type: command
description: Design & UX audit with actionable tasks (Notion/Strava/Canva standards)
version: 4.0.0
mcp_required: chrome-devtools-mcp@latest
language: russian
output: task-oriented (JIRA-ready)
---

# /design-check Command

Проверка дизайна и UX по стандартам лучших SaaS (Notion, Strava, Canva, Headspace).
**Результат:** Список конкретных задач для frontend агента.

## Использование

```bash
/design-check [URL] [OPTIONS]
```

**Аргументы:**
- `URL` - URL для проверки (default: `http://localhost:3000`)

**Опции:**
- `--mode <type>` - Режим:
  - `full` - Полный анализ (default)
  - `quick` - Только критичные проблемы
  - `accessibility` - WCAG AAA compliance
  - `ux` - UX фрикшн-поинты
  - `performance` - Core Web Vitals

- `--benchmark <product>` - Сравнить с эталоном:
  - `notion` - Функциональность и гибкость
  - `strava` - Динамика и мотивация
  - `canva` - Креативность и простота
  - `headspace` - Спокойствие и mindfulness

- `--fix` - Применить автоматические исправления
- `--tasks-only` - Только список задач (без отчета)

## Примеры

```bash
# Полная проверка с эталоном Notion
/design-check --benchmark notion

# Быстрая проверка критичных проблем
/design-check --mode quick

# Только accessibility tasks
/design-check --mode accessibility --tasks-only
```

## Что проверяется

### 1. Accessibility (WCAG AAA)
- Контраст текста (7:1 для <18px, 4.5:1 для ≥18px)
- Keyboard navigation (skip links, tab order)
- Screen reader support (ARIA, landmarks, alt texts)
- Color blind friendly (не только цвет для важной информации)

### 2. UX Excellence
- Когнитивная нагрузка (≤7 действий на экране)
- Loading states для async операций
- Inline validation для форм
- Toast notifications / Feedback механизмы
- Empty states с guidance

### 3. Mobile Experience
- Touch targets ≥44x44px (Apple HIG)
- Text size ≥14px (16px recommended)
- Горизонтальный scroll (должен отсутствовать)
- Gesture support (swipe, pull-to-refresh)

### 4. Performance
- LCP <2.5s (≤1.5s отлично)
- CLS <0.1
- FCP <1.8s

### 5. Design System
- Цвета: ≤12 уникальных
- Шрифты: ≤3 семейства
- Spacing: 8px grid compliance
- Консистентность border-radius, shadows

### 6. Component Patterns
- Button hierarchy (Primary/Secondary/Tertiary)
- Form best practices (float labels, smart defaults)
- Navigation (sticky header, breadcrumbs)
- Feedback systems (toasts, skeletons, empty states)

## Формат вывода

### Краткий (в терминале)

```
🎨 Design Excellence Check
━━━━━━━━━━━━━━━━━━━━━━━━

📊 Общий балл: 72/100

✅ Сильные стороны:
  • Performance: 9/10 (LCP 779ms - быстрее Notion!)
  • Touch targets: все ≥44px

⚠️ Проблемы:
  • Accessibility: 6/10 (7 контрастов < 7:1)
  • UX: 6/10 (нет loading states, toast notifications)

📝 Сгенерировано:
  🔴 4 критичных задачи (исправить сегодня)
  🟡 5 важных задач (этот спринт)
  🟢 3 улучшения (следующий квартал)

📄 Отчет: .claude/reports/design-check/tasks-2025-11-02.md
```

### Детальный (в файле .md)

```markdown
# Design Check Tasks

## 🔴 Critical Tasks (Fix Today)

### Task #1: WCAG AAA Contrast

**User Story:**
As a visually impaired user
I want proper text contrast (7:1)
So that I can read content easily

**Acceptance Criteria:**
- [ ] Update --muted-foreground color
- [ ] All 7 elements pass axe-core contrast check
- [ ] Verify in Chrome DevTools Lighthouse

**Implementation:**
```css
/* web-frontend/src/app/globals.css:54 */
--muted-foreground: hsl(0 0% 25%); /* was: hsl(0 0% 63.9%) */
```

**Impact:** Critical (ADA compliance, legal risk)
**Effort:** 5 minutes
**Files:** `web-frontend/src/app/globals.css:54`
**Benchmark:** Notion uses rgb(55, 53, 47)

---

### Task #2: Loading State for Generate Button

**User Story:**
As a user generating an article
I want to see loading indicator
So that I know the system is working

**Acceptance Criteria:**
- [ ] Add Loader2 spinner from lucide-react
- [ ] Change button text to "Генерация..." during loading
- [ ] Disable button during loading state

**Implementation:**
```tsx
// web-frontend/src/components/input-form.tsx:278
import { Loader2 } from "lucide-react"

<Button disabled={isLoading || !canGenerate}>
  {isLoading ? (
    <>
      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
      Генерация...
    </>
  ) : (
    'Сгенерировать'
  )}
</Button>
```

**Impact:** Major (UX clarity, reduce user confusion)
**Effort:** 10 minutes
**Files:** `web-frontend/src/components/input-form.tsx:278-285`
**Benchmark:** Vercel deploy button, Linear task creation

---

## 🟡 Important Tasks (This Sprint)

[Similar format for 5 important tasks]

---

## 🟢 Nice-to-Have (Next Quarter)

[Similar format for 3 enhancement tasks]

---

## 📊 Metrics Improvement

After implementing critical + important tasks:

| Metric | Current | After | Improvement |
|--------|---------|-------|-------------|
| Accessibility Score | 6/10 | 9/10 | +50% |
| UX Excellence | 6/10 | 8/10 | +33% |
| Overall Score | 72/100 | 85/100 | +18% |

---

## 🚀 Ready for Frontend Agent

Copy critical tasks and paste:

```
Implement these 4 critical tasks from design-check:
1. Fix WCAG contrast (5 min)
2. Add loading state (10 min)
3. Increase text size (5 min)
4. Add skip link (5 min)

Total effort: ~25 minutes
```
```

## Процесс выполнения (внутренний)

Агент выполняет:

1. **Подключение** (5s)
   - Проверка доступности сервера
   - Подключение Chrome DevTools MCP
   - Создание папок для отчетов

2. **Сбор данных** (10s)
   - Snapshot текущей страницы
   - Screenshots: desktop + mobile
   - Evaluate: accessibility, UX, performance scripts

3. **Анализ** (15s)
   - WCAG AAA проверки (контраст, keyboard, ARIA)
   - UX friction points (cognitive load, forms, feedback)
   - Mobile excellence (touch targets, text size, gestures)
   - Performance (LCP, CLS, FCP)
   - Design system (colors, spacing, typography)
   - Component patterns (buttons, forms, navigation)

4. **Генерация задач** (5s)
   - Приоритизация: Critical > Important > Nice-to-have
   - Форматирование: JIRA-ready User Stories
   - Добавление: acceptance criteria, code, effort, benchmarks

5. **Сохранение** (2s)
   - Markdown отчет с задачами
   - Screenshots для reference
   - Краткий summary в терминал

**Total time:** ~40 seconds

## Автоисправления (--fix)

При флаге `--fix` агент:

1. Показывает предлагаемые изменения:
```
🔧 Автоисправления готовы (4 изменения)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Контраст текста
   Файл: web-frontend/src/app/globals.css:54
   Было: hsl(0 0% 63.9%)
   Станет: hsl(0 0% 25%)
   Влияние: ADA compliance

2. Loading state
   [...]

Применить? (y/n/selective):
```

2. Применяет изменения через Edit tool

3. Создает commit:
```
feat(accessibility): fix 4 critical design issues

- WCAG AAA contrast (7.5:1)
- Loading states for async actions
- Text size increased to 14px
- Skip link for keyboard navigation

Inspired by: Notion, Vercel
```

## Интеграция

После design-check можно:

```bash
# Применить исправления
/design-check --fix

# Проверить только критичные
/design-check --mode quick

# Сгенерировать только tasks для frontend агента
/design-check --tasks-only

# Сравнить с конкретным продуктом
/design-check --benchmark strava
```

## Best Practices

1. **Запускай после major UI changes**
2. **Используй --benchmark** для целевого сравнения
3. **Применяй critical tasks сразу** (legal/accessibility риски)
4. **Отдавай tasks frontend агенту** без дополнительного анализа
5. **Измеряй улучшения** после применения

---

**Агент:** design-excellence-checker
**Вдохновение:** Notion, Strava, Canva, Headspace, Vercel, Linear
**Output:** Task-oriented (JIRA-ready format)
