# Design QA Automation - Quick Start

## 🚀 5-минутная установка

### 1. Установка MCP Chrome DevTools

```bash
claude mcp add chrome-devtools npx chrome-devtools-mcp@latest
```

### 2. Перезапуск Claude Code

```bash
exit
claude
```

### 3. Проверка работоспособности

```bash
# Запустить dev server
cd web-frontend && npm run dev

# В новом окне Claude Code
/design-qa http://localhost:3000
```

Готово! Через 1-2 минуты вы получите comprehensive отчет.

---

## 📊 Что вы получите

### Автоматические проверки:

✅ **Responsive Design**
- 7 viewports (mobile → 4K)
- Touch target sizes
- Layout stability
- Screenshots

✅ **Performance**
- Core Web Vitals (LCP, FID, CLS)
- Bundle size analysis
- Network timing
- Slow network simulation

✅ **Accessibility (WCAG 2.1 AA)**
- Color contrast (4.5:1)
- Touch targets (≥44px)
- Semantic HTML
- Keyboard navigation

✅ **Error Detection**
- Console errors
- Network failures
- CORS issues

### Пример отчета:

```
📊 Design QA Summary
━━━━━━━━━━━━━━━━━━━━━
Status: ⚠️ ISSUES FOUND
Total Issues: 11
- 🔴 CRITICAL: 3
- 🟡 MAJOR: 5
- 🔵 MINOR: 3

Report: .claude/reports/design-qa/design-qa-2025-11-02.md
```

---

## 🎯 Основные команды

```bash
# Полный аудит
/design-qa

# Только performance
/design-qa perf

# Только accessibility
/design-qa a11y

# Конкретный URL
/design-qa http://localhost:3000/dashboard

# Применить автофиксы
/design-qa fix
```

---

## 📖 Полная документация

Подробное руководство: `.claude/docs/DESIGN_QA_GUIDE.md`

---

## ⚡ Быстрые примеры

### Pre-PR checklist

```bash
# 1. Запустить проверку
/design-qa

# 2. Проверить CRITICAL issues
cat .claude/reports/design-qa/design-qa-*.md | grep CRITICAL

# 3. Исправить если нужно
/design-qa fix

# 4. Повторная проверка
/design-qa verify
```

### Performance optimization

```bash
# Baseline
/design-qa perf
# LCP: 3200ms ❌

# ... применить оптимизации ...

# Re-check
/design-qa perf
# LCP: 1800ms ✅
```

### Accessibility compliance

```bash
/design-qa a11y

# Автофиксы где возможно
/design-qa fix

# Проверка WCAG compliance
/design-qa a11y
# ✅ WCAG 2.1 AA Compliant
```

---

## 🔧 Troubleshooting

**MCP server not found**
```bash
claude mcp add chrome-devtools npx chrome-devtools-mcp@latest
exit
claude
```

**Connection refused**
```bash
cd web-frontend && npm run dev
```

**Chrome not found**
```bash
# macOS
brew install --cask google-chrome

# Linux
sudo apt install google-chrome-stable
```

---

## 💡 Pro Tips

1. **Запускайте перед каждым PR**
   - Ловит regression issues рано
   - Гарантирует quality standards

2. **Используйте быстрые режимы**
   - `/design-qa perf` - только performance
   - `/design-qa a11y` - только accessibility

3. **Приоритизируйте CRITICAL issues**
   - Accessibility blockers
   - Console errors
   - Failed requests

4. **Сохраняйте screenshots**
   - Visual regression baseline
   - Design review documentation

---

## 📚 Resources

- **Агент:** `.claude/agents/design-qa-automation.md`
- **Команда:** `.claude/commands/design-qa.md`
- **Полный гайд:** `.claude/docs/DESIGN_QA_GUIDE.md`

- **WCAG Guidelines:** https://www.w3.org/WAI/WCAG21/quickref/
- **Core Web Vitals:** https://web.dev/vitals/
- **Chrome DevTools MCP:** https://github.com/ChromeDevTools/chrome-devtools-mcp

---

**Готово!** Теперь у вас есть автоматизированная проверка качества фронтенда 🎉

Следующий шаг: `/design-qa http://localhost:3000`
