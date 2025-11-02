## QA Automation Workflow

Автоматизированная система тестирования и исправления для TextScript.

## 🎯 Обзор

QA Automation система обеспечивает:
- **Spec-based testing** - тесты генерируются из спецификаций
- **Automated E2E testing** - реальное тестирование в Chrome
- **Auto-fixing** - автоматическое делегирование багов разработчикам
- **Continuous deployment** - деплой после исправлений
- **Iterative cycles** - повторение до успеха

## 🔄 Workflow Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    /qa-cycle command                          │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                  agent-organizer                             │
│           (Coordinates full QA cycle)                        │
└──┬───────────────┬──────────────┬──────────────┬───────────┘
   │               │              │              │
   ▼               ▼              ▼              ▼
┌──────┐    ┌────────────┐  ┌─────────┐  ┌──────────────┐
│ QA   │    │  Frontend  │  │ Backend │  │  Production  │
│ Auto │    │ Developer  │  │Developer│  │  Deployment  │
└──────┘    └────────────┘  └─────────┘  └──────────────┘
   │              │              │              │
   │              └──────┬───────┘              │
   │                     │                      │
   └─────────────────────┴──────────────────────┘
                         │
                         ▼
              ┌──────────────────┐
              │  test-reports/    │
              │  (Markdown files) │
              └──────────────────┘
```

## 📝 Components

### 1. qa-automation Agent

**Роль:** QA Automation Engineer
**Инструменты:** Chrome DevTools MCP, Read, Write, Grep, Glob
**Файл:** `.claude/agents/qa-automation.md`

**Обязанности:**
- Читать спецификации (spec.md)
- Генерировать тест-планы из user stories
- Выполнять E2E тесты через Chrome DevTools
- Создавать детальные багрепорты
- Категоризировать баги (frontend/backend/design)
- Генерировать Markdown отчеты

**Тестовое покрытие:**
- ✅ Happy path (основные сценарии)
- ✅ Edge cases (пустые поля, граничные значения)
- ✅ UI validation (элементы видны, доступны)
- ✅ API validation (запросы успешны)
- ✅ Console validation (нет JS ошибок)

### 2. agent-organizer (Enhanced)

**Роль:** Master Coordinator
**Файл:** `.claude/agents/agent-organizer.md`

**Новый workflow:** `qa_cycle_workflow`

**Алгоритм:**
```python
while iteration < max_iterations and not all_tests_passed:
    1. Run qa-automation → get test results
    2. If all passed → SUCCESS, exit
    3. Categorize bugs (frontend/backend/design)
    4. Delegate to specialist agents
    5. Ask deployment confirmation
    6. Deploy to production
    7. Wait for stabilization
    8. Loop (iteration++)
```

**Координирует:**
- qa-automation (testing)
- frontend-developer (UI fixes)
- python-backend-developer (API fixes)
- production-deployment (deployment)

### 3. /qa-cycle Command

**Файл:** `.claude/commands/qa-cycle.md`

**Параметры:**
- `url` - Application URL (default: auto-detect)
- `spec_path` - Spec file path (default: auto-detect)
- `max_iterations` - Maximum cycles (default: 3)

**Использование:**
```bash
# Basic (все по умолчанию)
/qa-cycle

# Custom URL
/qa-cycle url=http://localhost:3000

# Full customization
/qa-cycle url=http://192.168.0.24:3000 spec_path=specs/feature/spec.md max_iterations=5
```

## 🚀 Quick Start

### 1. Подготовка

Убедитесь что:
- ✅ Спецификация существует: `specs/*/spec.md`
- ✅ Приложение запущено: `http://192.168.0.24:3000`
- ✅ Chrome DevTools MCP доступен

### 2. Запуск QA Cycle

```bash
/qa-cycle
```

### 3. Мониторинг

Следите за:
- Прогрессом итераций (1/3, 2/3, ...)
- Результатами тестов (passed/failed counts)
- Категоризацией багов
- Запросами на deployment

### 4. Deployment Confirmation

При запросе деплоя выберите:
- **Yes, deploy now** - деплой и следующая итерация
- **Show changes first** - review git diff перед деплоем
- **No, stop cycle** - остановить цикл

### 5. Просмотр отчетов

```bash
ls -la test-reports/
cat test-reports/qa-report-iteration-1-*.md
```

## 📊 Test Report Format

Каждый отчет содержит:

```markdown
# QA Test Report - Iteration X

## Executive Summary
- Total: X tests
- Passed: Y
- Failed: Z
- Success Rate: X%

## Test Results by User Story
- US-001: Article Generation
  - TC-001: ✅ PASS
  - TC-002: ❌ FAIL

## Bug Reports
### BUG-001: Title
**Severity:** High
**Category:** frontend
**Description:** [детали]
**Steps to Reproduce:** [шаги]
**Screenshot:** [скриншот]
**Console Errors:** [ошибки]
**Recommendation:** [как исправить]

## Recommendations
[что нужно сделать]
```

## 🎯 Bug Categorization

### Frontend Issues
- UI elements не работают
- Валидация форм
- React/Next.js errors
- CSS/styling problems
- Accessibility issues

**Делегируется:** frontend-developer

### Backend Issues
- API errors (4xx, 5xx)
- CORS блокировки
- Медленные запросы
- Неправильный формат данных

**Делегируется:** python-backend-developer

### Design Issues
- WCAG violations
- Responsive problems
- UX inconsistencies
- Color contrast issues

**Делегируется:** frontend-developer

## 🔧 Advanced Usage

### Custom Test Scenarios

Если нужны специфичные тесты, обновите spec.md:

```markdown
## User Story: US-XXX
**As a** user
**I want to** perform action
**So that** I can achieve goal

### Acceptance Criteria
- [ ] AC-1: Criteria description
- [ ] AC-2: Edge case handling
- [ ] AC-3: Error scenarios

### Test Scenarios
**TC-XXX-01:** Happy path
- Step 1
- Step 2
- Expected: Result

**TC-XXX-02:** Edge case
- Step 1 with empty data
- Expected: Validation error
```

### Extending Test Coverage

В qa-automation агенте можно добавить:
- Performance testing (load times)
- Security testing (XSS, CSRF)
- Regression testing (previous bugs)
- Cross-browser testing

### Integration with CI/CD

Можно интегрировать в pipeline:

```yaml
# .github/workflows/qa-cycle.yml
name: QA Cycle
on: [push, pull_request]

jobs:
  qa:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run QA Cycle
        run: claude-code /qa-cycle
```

## 📈 Metrics & Monitoring

### Success Metrics
- **Success Rate:** (passed tests / total tests) × 100%
- **Iterations to Success:** Average number of cycles
- **Bug Fix Time:** Time from detection to fix
- **Deployment Frequency:** Number of deploys per cycle

### Quality Indicators
- **Zero Failed Tests:** All tests passing
- **No Console Errors:** Clean browser console
- **No Network Failures:** All API calls successful
- **WCAG AA Compliance:** Accessibility standards met

## 🐛 Troubleshooting

### Tests Always Failing

**Symptoms:**
- Same tests fail repeatedly
- Fixes don't resolve issues
- Reaching max_iterations

**Solutions:**
1. Check if bugs are too complex for auto-fix
2. Review test-reports for patterns
3. Manual intervention needed
4. Update spec.md if requirements changed

### Deployment Failures

**Symptoms:**
- Deploy step fails
- Services don't start
- Health checks failing

**Solutions:**
1. SSH to server: `ssh server24`
2. Check Docker: `docker-compose ps`
3. View logs: `docker-compose logs`
4. Manual rollback if needed

### Agent Communication Issues

**Symptoms:**
- Agents not receiving tasks
- No bug reports generated
- Workflow stuck

**Solutions:**
1. Check agent configurations
2. Verify Chrome DevTools MCP
3. Review agent-organizer logs
4. Restart QA cycle with `/qa-cycle`

### False Positives

**Symptoms:**
- Tests fail but app works fine
- Flaky tests (random failures)
- Timing issues

**Solutions:**
1. Add proper `wait_for` in tests
2. Increase timeouts
3. Update test assertions
4. Review test logic in qa-automation

## 💡 Best Practices

### 1. Specification First
- ✅ Always update spec.md before /qa-cycle
- ✅ Clear user stories and acceptance criteria
- ✅ Include edge cases in spec

### 2. Regular Testing
- ✅ Run /qa-cycle before major deployments
- ✅ After significant feature changes
- ✅ Weekly regression testing

### 3. Review Reports
- ✅ Check test-reports/ after each cycle
- ✅ Analyze patterns in failures
- ✅ Track bug resolution time

### 4. Deployment Hygiene
- ✅ Always review changes before deploy
- ✅ Monitor services after deployment
- ✅ Have rollback plan ready

### 5. Continuous Improvement
- ✅ Add new test cases as bugs found
- ✅ Update agents based on patterns
- ✅ Optimize test execution time

## 📚 Related Documentation

- **Agent Documentation:** `.claude/agents/`
  - `qa-automation.md` - QA agent details
  - `agent-organizer.md` - Coordinator logic
  - `frontend-developer.md` - Frontend fixes
  - `python-backend-developer.md` - Backend fixes
  - `production-deployment.md` - Deployment process

- **Command Documentation:** `.claude/commands/`
  - `qa-cycle.md` - Command usage

- **Project Documentation:**
  - `CLAUDE.md` - Project overview
  - `DEPLOYMENT.md` - Deployment guide
  - `specs/*/spec.md` - Feature specifications

## 🎓 Learning Resources

### Understanding E2E Testing
- Tests simulate real user interactions
- Validates entire user workflows
- Catches integration issues

### Chrome DevTools MCP
- Real browser automation
- Access to console, network, screenshots
- More reliable than headless testing

### Spec-Based Testing
- Tests derived from requirements
- Traceability (test → requirement)
- Ensures coverage of all features

---

## 🚀 Example Session

```bash
$ /qa-cycle

🚀 Starting QA Cycle
   URL: http://192.168.0.24:3000
   Spec: specs/002-web-frontend-docker/spec.md
   Max iterations: 3

============================================================
🔄 ITERATION 1/3
============================================================

📋 Running automated tests via qa-automation agent...

📊 Test Results:
  ✅ Passed: 8
  ❌ Failed: 2
  📝 Total: 10
  📄 Report: test-reports/qa-report-iteration-1-2025-11-02.md

🐛 Analyzing 2 bugs...
  Frontend issues: 1
  Backend issues: 1
  Design issues: 0

🔧 Delegating to frontend-developer...
🔧 Delegating to python-backend-developer...

✅ All fixes completed!

📦 Ready to deploy changes to production.
❓ Deploy fixes to production server24?
   → Yes, deploy now

🚀 Deploying to production server24...
✅ Deployment complete!
⏳ Waiting 10 seconds for services to stabilize...

✅ Iteration 1 completed.
   Next: Running tests again to verify fixes...

============================================================
🔄 ITERATION 2/3
============================================================

📋 Running automated tests via qa-automation agent...

📊 Test Results:
  ✅ Passed: 10
  ❌ Failed: 0
  📝 Total: 10

🎉 All tests passed! QA Cycle complete.

============================================================
📊 QA CYCLE SUMMARY
============================================================
Total iterations completed: 2
Final status: ✅ ALL TESTS PASSED

📄 Final test report: test-reports/qa-report-iteration-2-2025-11-02.md

Thank you for using QA Automation Cycle! 🎉
```

---

**Version:** 1.0.0
**Created:** 2025-11-02
**Status:** Production Ready
**Maintainer:** Claude Code Team
