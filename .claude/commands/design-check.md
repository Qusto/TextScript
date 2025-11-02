---
name: design-check
type: command
description: Comprehensive design and UX excellence check inspired by award-winning SaaS products
version: 3.0.0
mcp_required: chrome-devtools-mcp@latest
language: russian
---

# /design-check Command

Комплексная проверка дизайна и UX с анализом по стандартам лучших SaaS продуктов (Strava, Headspace, Notion, Canva).

## Использование

```
/design-check [URL] [OPTIONS]
```

## Аргументы

- `URL` (опционально) - URL для проверки. По умолчанию: `http://localhost:3000`

## Опции

- `--mode <type>` - Режим проверки:
  - `full` - Полный анализ (default)
  - `quick` - Быстрая проверка критичных проблем
  - `visual` - Визуальный анализ и эмоциональное воздействие
  - `ux` - UX проблемы и фрикшн-поинты
  - `performance` - Только Core Web Vitals
  - `accessibility` - WCAG compliance
  - `competitive` - Сравнение с лучшими в классе

- `--benchmark <product>` - Сравнить с эталонным продуктом:
  - `strava` - Динамичный, мотивационный дизайн
  - `headspace` - Спокойный, mindful интерфейс
  - `notion` - Гибкость и мощность
  - `canva` - Креативность и простота

- `--fix` - Применить автоматические исправления
- `--report` - Генерировать детальный отчет
- `--russian` - Отчет на русском языке (default)

## Примеры

```bash
# Полная проверка с эталоном Notion
/design-check --benchmark notion

# Быстрый UX аудит
/design-check --mode ux --quick

# Визуальный анализ с исправлениями
/design-check --mode visual --fix
```

## Этапы выполнения

### Этап 1: Подготовка и подключение

```javascript
// 1. Проверка доступности сервера
await validateServerAccess(url);

// 2. Создание структуры отчетов
await createReportStructure({
  base: '.claude/reports/design-check',
  screenshots: '.claude/reports/screenshots',
  comparisons: '.claude/reports/benchmarks'
});

// 3. Подключение Chrome DevTools
await chrome.connect({
  url: url,
  headless: false
});

// 4. Начальная загрузка и стабилизация
await chrome.waitForPageLoad();
await chrome.wait(2000); // Ждем завершения анимаций
```

### Этап 2: Визуальное воздействие (Visual Impact)

Анализ первого впечатления и эмоционального отклика:

```javascript
// Захват скриншота для анализа
const screenshot = await chrome.fullPageScreenshot();

// Оценка визуального воздействия
const visualImpact = await analyzeVisualImpact({
  screenshot: screenshot,
  metrics: {
    firstImpression: evaluateIn3Seconds(),      // Что бросается в глаза?
    emotionalResponse: detectEmotion(),          // Спокойный/энергичный/профессиональный
    brandAlignment: checkBrandConsistency(),     // Соответствие бренду
    visualHierarchy: analyzeFocusPoints(),       // Правильная иерархия?
    colorPsychology: evaluateColorImpact(),      // Психология цвета
    whiteSpaceBalance: calculateBreathingRoom()  // Баланс пространства
  }
});

// Сравнение с эталонными продуктами
if (options.benchmark) {
  const comparison = await compareToBenchmark({
    current: screenshot,
    benchmark: options.benchmark,
    aspects: [
      'visual_energy',      // Strava: динамика
      'calm_clarity',       // Headspace: спокойствие
      'functional_beauty',  // Notion: функциональность
      'creative_freedom'    // Canva: креативность
    ]
  });
}
```

### Этап 3: UX Excellence Check

Поиск фрикшн-поинтов и возможностей улучшения:

```javascript
// Анализ пользовательского опыта
const uxAnalysis = await chrome.evaluate(`
  (() => {
    const issues = {
      friction: [],
      opportunities: [],
      patterns: []
    };
    
    // Фрикшн-поинты
    // 1. Когнитивная нагрузка
    const buttons = document.querySelectorAll('button, a[role="button"]');
    if (buttons.length > 7) {
      issues.friction.push({
        type: 'cognitive-overload',
        severity: 'major',
        description: 'Слишком много действий на экране (${buttons.length})',
        solution: 'Приоритизировать основные действия, скрыть вторичные',
        benchmark: 'Notion использует максимум 3-5 основных действий'
      });
    }
    
    // 2. Неясная навигация
    const nav = document.querySelector('nav, [role="navigation"]');
    if (!nav || nav.children.length > 7) {
      issues.friction.push({
        type: 'navigation-complexity',
        severity: 'major',
        description: 'Навигация перегружена или отсутствует',
        solution: 'Группировка в категории как в Notion'
      });
    }
    
    // 3. Формы без умных дефолтов
    const inputs = document.querySelectorAll('input, select, textarea');
    inputs.forEach(input => {
      if (!input.placeholder && !input.value && !input.defaultValue) {
        issues.friction.push({
          type: 'missing-smart-defaults',
          field: input.name || input.id,
          solution: 'Добавить умные подсказки как в Canva'
        });
      }
    });
    
    // Возможности для улучшения
    // 1. Персонализация
    if (!document.querySelector('[data-personalized], .user-specific')) {
      issues.opportunities.push({
        type: 'personalization',
        potential: 'high',
        description: 'Добавить персонализированный контент',
        example: 'Strava показывает личный прогресс'
      });
    }
    
    // 2. Геймификация
    const hasProgress = document.querySelector('.progress, [role="progressbar"]');
    if (!hasProgress) {
      issues.opportunities.push({
        type: 'gamification',
        potential: 'medium',
        description: 'Добавить элементы прогресса',
        example: 'Duolingo streak counter'
      });
    }
    
    // 3. AI-ассистент
    if (!document.querySelector('[data-ai], .ai-powered, .smart-suggestion')) {
      issues.opportunities.push({
        type: 'ai-integration',
        potential: 'high',
        description: 'Интегрировать AI-помощника',
        example: 'Notion AI для автозаполнения'
      });
    }
    
    return issues;
  })()
`);
```

### Этап 4: Design System Audit

Проверка системности дизайна:

```javascript
const designSystem = await chrome.evaluate(`
  (() => {
    const system = {
      colors: new Set(),
      fonts: new Set(),
      spacings: new Set(),
      borderRadii: new Set(),
      shadows: new Set(),
      animations: new Set()
    };
    
    // Сбор всех стилей
    const elements = document.querySelectorAll('*');
    elements.forEach(el => {
      const style = getComputedStyle(el);
      
      // Цвета
      ['color', 'backgroundColor', 'borderColor'].forEach(prop => {
        if (style[prop] && style[prop] !== 'transparent') {
          system.colors.add(style[prop]);
        }
      });
      
      // Шрифты
      if (style.fontFamily) {
        system.fonts.add(style.fontFamily.split(',')[0].trim());
      }
      
      // Отступы (проверка на 8px grid)
      ['padding', 'margin'].forEach(prop => {
        ['Top', 'Right', 'Bottom', 'Left'].forEach(side => {
          const value = parseInt(style[prop + side]);
          if (value > 0) system.spacings.add(value);
        });
      });
      
      // Скругления
      if (style.borderRadius && style.borderRadius !== '0px') {
        system.borderRadii.add(style.borderRadius);
      }
      
      // Тени
      if (style.boxShadow && style.boxShadow !== 'none') {
        system.shadows.add(style.boxShadow);
      }
      
      // Анимации
      if (style.transition && style.transition !== 'none') {
        system.animations.add(style.transition);
      }
    });
    
    // Анализ консистентности
    const analysis = {
      colorConsistency: system.colors.size <= 12 ? 'good' : 'needs-work',
      colorCount: system.colors.size,
      fontConsistency: system.fonts.size <= 3 ? 'good' : 'poor',
      fontCount: system.fonts.size,
      spacingGrid: checkSpacingGrid(Array.from(system.spacings)),
      animationConsistency: system.animations.size <= 5 ? 'good' : 'chaotic'
    };
    
    function checkSpacingGrid(spacings) {
      const grid8 = spacings.filter(s => s % 8 === 0).length;
      const total = spacings.length;
      return grid8 / total > 0.8 ? 'following-8px-grid' : 'inconsistent';
    }
    
    return analysis;
  })()
`);
```

### Этап 5: Component Pattern Analysis

Анализ компонентных паттернов:

```javascript
const componentPatterns = await chrome.evaluate(`
  (() => {
    const patterns = {
      buttons: analyzeButtons(),
      forms: analyzeForms(),
      navigation: analyzeNavigation(),
      feedback: analyzeFeedback(),
      emptyStates: analyzeEmptyStates()
    };
    
    function analyzeButtons() {
      const buttons = document.querySelectorAll('button, [role="button"]');
      const analysis = {
        total: buttons.length,
        hierarchy: [],
        issues: []
      };
      
      buttons.forEach(btn => {
        const style = getComputedStyle(btn);
        
        // Проверка иерархии
        if (style.backgroundColor !== 'transparent') {
          analysis.hierarchy.push('primary');
        } else if (style.border !== 'none') {
          analysis.hierarchy.push('secondary');
        } else {
          analysis.hierarchy.push('tertiary');
        }
        
        // Проверка состояний
        if (!btn.disabled && !style.cursor.includes('pointer')) {
          analysis.issues.push('missing-hover-state');
        }
        
        // Loading states
        if (!btn.querySelector('.spinner, .loading')) {
          analysis.issues.push('no-loading-state');
        }
      });
      
      // Оценка по эталону (Notion/Canva)
      analysis.score = analysis.issues.length === 0 ? 10 : 
                      10 - (analysis.issues.length * 2);
      
      return analysis;
    }
    
    function analyzeForms() {
      const forms = document.querySelectorAll('form');
      const inputs = document.querySelectorAll('input, select, textarea');
      
      return {
        formCount: forms.length,
        inputCount: inputs.length,
        hasFloatLabels: document.querySelector('.float-label, [data-float]'),
        hasInlineValidation: document.querySelector('.error-message, .validation'),
        hasSmartDefaults: document.querySelector('[placeholder], [value]'),
        hasProgressiveDisclosure: document.querySelector('[data-step], .wizard')
      };
    }
    
    function analyzeNavigation() {
      return {
        hasStickyHeader: document.querySelector('header[style*="sticky"], .sticky-header'),
        hasBreadcrumbs: document.querySelector('.breadcrumb, [aria-label*="breadcrumb"]'),
        hasMobileMenu: document.querySelector('.mobile-menu, .hamburger'),
        hasFAB: document.querySelector('.fab, [data-fab]')
      };
    }
    
    function analyzeFeedback() {
      return {
        hasToasts: document.querySelector('.toast, .notification'),
        hasAlerts: document.querySelector('.alert, [role="alert"]'),
        hasSkeletons: document.querySelector('.skeleton, [data-skeleton]'),
        hasEmptyStates: document.querySelector('.empty-state, .no-data')
      };
    }
    
    function analyzeEmptyStates() {
      const emptyStates = document.querySelectorAll('.empty, .no-results, .zero-state');
      return {
        count: emptyStates.length,
        hasIllustration: !!document.querySelector('.empty img, .empty svg'),
        hasAction: !!document.querySelector('.empty button, .empty a'),
        hasGuidance: !!document.querySelector('.empty p, .empty-description')
      };
    }
    
    return patterns;
  })()
`);
```

### Этап 6: Responsive & Mobile Excellence

Проверка мобильной оптимизации:

```javascript
const viewports = [
  { name: 'mobile', width: 375, height: 667, benchmark: 'duolingo' },
  { name: 'tablet', width: 768, height: 1024, benchmark: 'notability' },
  { name: 'desktop', width: 1440, height: 900, benchmark: 'notion' },
  { name: 'wide', width: 1920, height: 1080, benchmark: 'figma' }
];

const responsiveAnalysis = {};

for (const viewport of viewports) {
  await chrome.setViewport(viewport.width, viewport.height);
  await chrome.wait(500);
  
  // Screenshot
  const screenshotPath = `.claude/reports/screenshots/${viewport.name}-${Date.now()}.png`;
  await chrome.screenshot({ path: screenshotPath });
  
  // Mobile-specific checks
  const mobileChecks = await chrome.evaluate(`
    (() => {
      const checks = {
        touchTargets: [],
        textReadability: [],
        scrollIssues: [],
        gestureSupport: []
      };
      
      // Touch targets (Apple HIG: 44x44px)
      if (${viewport.width} <= 768) {
        document.querySelectorAll('button, a, input, [onclick]').forEach(el => {
          const rect = el.getBoundingClientRect();
          if (rect.width < 44 || rect.height < 44) {
            checks.touchTargets.push({
              element: el.tagName,
              size: \`\${rect.width}x\${rect.height}\`,
              required: '44x44px',
              severity: 'critical'
            });
          }
        });
        
        // Text readability
        document.querySelectorAll('p, span, div').forEach(el => {
          const fontSize = parseInt(getComputedStyle(el).fontSize);
          if (fontSize < 16) {
            checks.textReadability.push({
              fontSize: fontSize,
              minimum: 16,
              severity: 'major'
            });
          }
        });
        
        // Gesture support
        const hasSwipe = document.querySelector('[data-swipe], .swipeable');
        const hasPinch = document.querySelector('[data-zoom], .zoomable');
        checks.gestureSupport = {
          swipe: !!hasSwipe,
          pinch: !!hasPinch,
          recommendation: !hasSwipe ? 'Add swipe navigation like Tinder' : null
        };
      }
      
      // Scroll issues
      if (document.body.scrollWidth > window.innerWidth) {
        checks.scrollIssues.push({
          type: 'horizontal-overflow',
          severity: 'critical'
        });
      }
      
      return checks;
    })()
  `);
  
  responsiveAnalysis[viewport.name] = {
    screenshot: screenshotPath,
    issues: mobileChecks,
    benchmark: viewport.benchmark
  };
}
```

### Этап 7: Performance & Core Web Vitals

```javascript
// Запуск performance trace
await chrome.startTrace();

// Перезагрузка для чистых метрик
await chrome.reload();
await chrome.waitForPageLoad();

// Сбор метрик
const metrics = await chrome.getPerformanceMetrics();
const vitals = await chrome.evaluate(`
  (() => {
    return {
      LCP: performance.getEntriesByType('largest-contentful-paint')[0]?.renderTime || 0,
      FID: 0, // Будет измерен при взаимодействии
      CLS: 0, // Накапливается в течение сессии
      FCP: performance.getEntriesByType('paint').find(e => e.name === 'first-contentful-paint')?.startTime || 0,
      TTFB: performance.timing.responseStart - performance.timing.requestStart,
      TTI: 0 // Time to Interactive
    };
  })()
`);

// Остановка trace
const trace = await chrome.stopTrace();

// Сравнение с эталонами
const performanceBenchmarks = {
  strava: { LCP: 1500, FID: 50, CLS: 0.05 },    // Супер быстрый
  notion: { LCP: 2000, FID: 75, CLS: 0.08 },    // Сбалансированный
  canva: { LCP: 2500, FID: 100, CLS: 0.1 }      // Приемлемый для сложных
};
```

### Этап 8: Accessibility Excellence

```javascript
const accessibilityAudit = await chrome.evaluate(`
  (() => {
    const audit = {
      wcag: checkWCAGCompliance(),
      keyboard: checkKeyboardNavigation(),
      screenReader: checkScreenReaderSupport(),
      colorBlind: checkColorBlindFriendly()
    };
    
    function checkWCAGCompliance() {
      const issues = [];
      
      // Контраст (WCAG AAA для критичного текста)
      document.querySelectorAll('*').forEach(el => {
        const style = getComputedStyle(el);
        if (style.color && style.backgroundColor !== 'transparent') {
          const contrast = calculateContrast(style.color, style.backgroundColor);
          const fontSize = parseInt(style.fontSize);
          const required = fontSize >= 18 ? 4.5 : 7; // AAA standards
          
          if (contrast < required) {
            issues.push({
              type: 'contrast',
              element: el.tagName,
              current: contrast,
              required: required,
              standard: 'WCAG AAA'
            });
          }
        }
      });
      
      return issues;
    }
    
    function checkKeyboardNavigation() {
      const focusables = document.querySelectorAll(
        'a, button, input, select, textarea, [tabindex]:not([tabindex="-1"])'
      );
      
      return {
        totalFocusable: focusables.length,
        hasSkipLink: !!document.querySelector('[href="#main"], .skip-link'),
        hasFocusIndicators: Array.from(focusables).every(el => {
          const style = getComputedStyle(el);
          return style.outlineStyle !== 'none' || style.boxShadow !== 'none';
        }),
        tabOrder: Array.from(focusables).map(el => el.tabIndex).every(i => i >= 0)
      };
    }
    
    function checkScreenReaderSupport() {
      return {
        hasLandmarks: !!document.querySelector('main, nav, header, footer'),
        hasHeadingHierarchy: checkHeadingOrder(),
        hasAriaLabels: document.querySelectorAll('[aria-label]').length,
        hasAltTexts: Array.from(document.querySelectorAll('img')).every(
          img => img.alt || img.getAttribute('aria-label')
        )
      };
    }
    
    function checkColorBlindFriendly() {
      // Проверка не полагается только на цвет
      const colorOnlyElements = [];
      document.querySelectorAll('.error, .success, .warning').forEach(el => {
        if (!el.querySelector('svg, .icon') && !el.textContent.trim()) {
          colorOnlyElements.push(el.className);
        }
      });
      
      return {
        usesColorAlone: colorOnlyElements.length > 0,
        problematicElements: colorOnlyElements
      };
    }
    
    function checkHeadingOrder() {
      const headings = Array.from(document.querySelectorAll('h1,h2,h3,h4,h5,h6'));
      let lastLevel = 0;
      let valid = true;
      
      headings.forEach(h => {
        const level = parseInt(h.tagName[1]);
        if (level - lastLevel > 1) valid = false;
        lastLevel = level;
      });
      
      return valid;
    }
    
    function calculateContrast(fg, bg) {
      // Simplified contrast calculation
      return 4.5; // Placeholder - use real WCAG formula
    }
    
    return audit;
  })()
`);
```

### Этап 9: Генерация отчета

```javascript
async function generateReport(analysis) {
  const timestamp = new Date().toISOString();
  const score = calculateOverallScore(analysis);
  
  const report = `
# Дизайн-ревью: ${analysis.url}

**Дата:** ${timestamp}
**Общий балл:** ${score}/100
**Эталонный продукт:** ${analysis.benchmark || 'Не указан'}

## 🎯 Краткое резюме

${generateExecutiveSummary(analysis)}

## 🎨 Визуальное воздействие

### Первое впечатление (0-3 секунды)
- **Оценка:** ${analysis.visual.firstImpression}/10
- **Эмоциональный отклик:** ${analysis.visual.emotionalResponse}
- **Соответствие бренду:** ${analysis.visual.brandAlignment}

${analysis.visual.issues.map(i => `- ⚠️ ${i.description}`).join('\\n')}

### Сравнение с эталоном
${analysis.benchmark ? generateBenchmarkComparison(analysis) : 'Не выполнено'}

## 🚀 UX Excellence

### Выявленные фрикшн-поинты
${analysis.ux.friction.map(f => `
**${f.type}**
- Проблема: ${f.description}
- Влияние: ${f.severity}
- Решение: ${f.solution}
- Пример из ${f.benchmark}
`).join('\\n')}

### Возможности для улучшения
${analysis.ux.opportunities.map(o => `
**${o.type}** (Потенциал: ${o.potential})
- ${o.description}
- Пример: ${o.example}
`).join('\\n')}

## 💎 Design System

- **Цветов используется:** ${analysis.designSystem.colorCount} (рекомендуется ≤12)
- **Шрифтов:** ${analysis.designSystem.fontCount} (рекомендуется ≤3)
- **Spacing Grid:** ${analysis.designSystem.spacingGrid}
- **Консистентность анимаций:** ${analysis.designSystem.animationConsistency}

## 📱 Mobile Excellence

${Object.entries(analysis.responsive).map(([viewport, data]) => `
### ${viewport} (${data.benchmark})
- Touch targets < 44px: ${data.issues.touchTargets.length}
- Проблемы с текстом: ${data.issues.textReadability.length}
- Горизонтальный скролл: ${data.issues.scrollIssues.length > 0 ? '❌' : '✅'}
- Поддержка жестов: ${data.issues.gestureSupport.swipe ? '✅' : '❌'}
[Скриншот](${data.screenshot})
`).join('\\n')}

## ⚡ Performance

| Метрика | Значение | Статус | ${analysis.benchmark} для сравнения |
|---------|----------|--------|---------------------|
| LCP | ${analysis.performance.LCP}ms | ${getLCPStatus(analysis.performance.LCP)} | ${getBenchmarkMetric('LCP', analysis.benchmark)} |
| FID | ${analysis.performance.FID}ms | ${getFIDStatus(analysis.performance.FID)} | ${getBenchmarkMetric('FID', analysis.benchmark)} |
| CLS | ${analysis.performance.CLS} | ${getCLSStatus(analysis.performance.CLS)} | ${getBenchmarkMetric('CLS', analysis.benchmark)} |

## ♿ Accessibility

- **WCAG уровень:** ${analysis.accessibility.wcag.length === 0 ? 'AAA ✅' : 'Требует работы'}
- **Keyboard навигация:** ${analysis.accessibility.keyboard.hasFocusIndicators ? '✅' : '❌'}
- **Screen reader:** ${analysis.accessibility.screenReader.hasAriaLabels} ARIA labels
- **Color blind friendly:** ${analysis.accessibility.colorBlind.usesColorAlone ? '❌' : '✅'}

## 🎯 Рекомендации

### 🔴 Критические (Немедленно)
${generateCriticalRecommendations(analysis)}

### 🟡 Важные (Этот спринт)
${generateMajorRecommendations(analysis)}

### 🟢 Желательные (Следующий квартал)
${generateMinorRecommendations(analysis)}

## 📊 Сравнение с лучшими в классе

${generateCompetitiveAnalysis(analysis)}

## ✅ Следующие шаги

1. Исправить критические проблемы с контрастом и touch targets
2. Внедрить паттерны из ${analysis.benchmark || 'Notion'}
3. Добавить персонализацию и AI-ассистента
4. Оптимизировать производительность до уровня Strava
5. Провести A/B тестирование улучшений

## 🏆 Потенциал для наград

**Webby Award readiness:** ${calculateWebbyReadiness(analysis)}%
- Visual Appeal: ${analysis.visual.score}/10
- UX Excellence: ${analysis.ux.score}/10
- Innovation: ${analysis.innovation}/10
- Mobile Experience: ${analysis.mobile.score}/10

---
*Сгенерировано Design Excellence Checker v3.0*
*Вдохновлено лучшими SaaS продуктами 2024-2025*
`;

  const reportPath = `.claude/reports/design-check-${timestamp}.md`;
  await saveFile(reportPath, report);
  
  return reportPath;
}
```

### Этап 10: Применение исправлений

```javascript
if (options.fix) {
  const fixes = generateSmartFixes(analysis);
  
  console.log(`
🔧 Предложенные исправления (вдохновлены лучшими практиками)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

${fixes.map((fix, i) => `
${i+1}. ${fix.description}
   
   Файл: ${fix.file}
   
   БЫЛО:
   ${fix.before}
   
   СТАНЕТ:
   ${fix.after}
   
   Вдохновение: ${fix.inspiration}
   Влияние: ${fix.impact}
`).join('\\n')}

Применить эти исправления? (y/n/selective):
  `);
  
  const response = await getUserInput();
  
  if (response === 'y') {
    for (const fix of fixes) {
      await applyFix(fix);
    }
    
    await createGitCommit({
      message: `feat(design): implement ${fixes.length} UX improvements inspired by ${options.benchmark}`,
      description: fixes.map(f => `- ${f.description}`).join('\\n')
    });
  }
}
```

## Форматы вывода

### Успешное выполнение

```
🎨 Design Excellence Check
━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 Анализирую по стандартам Notion...

✨ Визуальное воздействие
  Первое впечатление: 8/10
  Эмоциональный отклик: Профессиональный
  Соответствие бренду: Сильное

🚀 UX Excellence  
  ✅ Четкая иерархия действий
  ⚠️ 3 фрикшн-поинта найдено
  💡 5 возможностей для улучшения

📱 Mobile Experience
  ✅ Все touch targets ≥ 44px
  ✅ Текст читаемый (≥16px)
  ⚠️ Жесты не поддерживаются

⚡ Performance vs Strava
  LCP: Ваш 2.1s vs Strava 1.5s
  FID: Ваш 75ms vs Strava 50ms
  CLS: Ваш 0.08 vs Strava 0.05

🏆 Webby Award Readiness: 78%

Итоговый балл: 85/100 - Хорошо!

📝 Отчет: .claude/reports/design-check-2025-11-02.md

Применить улучшения из Notion? (y/n):
```

### При обнаружении проблем

```
⚠️ Design Excellence Check - Требует внимания
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

❌ Критические проблемы (3):
1. Низкий контраст текста (3.2:1 vs 7:1 AAA)
2. Touch targets 32px (требуется 44px)
3. Нет персонализации (Strava показывает личный прогресс)

🔧 Могу исправить автоматически:
- Контраст: изменить цвета по стандарту Headspace
- Touch targets: увеличить как в Apple Fitness+
- Добавить skeleton screens как в Notion

Исправить сейчас? (y/n):
```

## Обработка ошибок

```javascript
try {
  await executeDesignCheck();
} catch (error) {
  if (error.type === 'MCP_NOT_FOUND') {
    console.log(`
❌ Chrome DevTools MCP не установлен

Установите командой:
claude mcp add chrome-devtools npx chrome-devtools-mcp@latest

Затем перезапустите Claude Code
    `);
  } else if (error.type === 'SERVER_NOT_RUNNING') {
    console.log(`
❌ Сервер не доступен на ${url}

Запустите dev server:
npm run dev

Или укажите другой URL:
/design-check https://your-site.com
    `);
  } else if (error.type === 'BENCHMARK_NOT_FOUND') {
    console.log(`
⚠️ Эталонный продукт не найден

Доступные эталоны:
- strava - Динамичный, мотивационный
- headspace - Спокойный, mindful
- notion - Мощный и гибкий
- canva - Креативный и простой
    `);
  }
}
```

## Интеграция с другими командами

```bash
# После design-check можно запустить:
/ux-research - Глубокий UX анализ
/competitive-analysis - Сравнение с конкурентами
/user-testing - Тестирование с пользователями
/design-system - Создание дизайн-системы
```

## Best Practices

1. **Всегда сравнивайте с лучшими** - Используйте --benchmark
2. **Фокус на эмоциях** - Дизайн должен вызывать чувства
3. **Mobile-first** - Начинайте проверку с мобильных
4. **Персонализация** - Ищите возможности для AI/ML
5. **Измеряйте влияние** - Связывайте дизайн с метриками бизнеса

---

**Агент:** design-excellence-checker
**MCP:** chrome-devtools-mcp@latest
**Вдохновение:** Strava, Headspace, Notion, Canva, Duolingo
**Язык отчетов:** Русский
