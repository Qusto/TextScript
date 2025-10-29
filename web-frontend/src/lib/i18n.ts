// AICODE-NOTE: T081 - Russian translation dictionary for all UI strings (FR-026, FR-027)
// Contains all interface text: labels, buttons, messages, errors, placeholders
// Used by components to display Russian text instead of English

export const ru = {
  // InputForm component (updated for Phase 10)
  inputForm: {
    formTitle: "Генерация статьи",
    description: "Укажите детали для генерации статьи в вашем стиле",

    // AICODE-NOTE: T100 - Renamed "topic" to "title" for Phase 10
    title: {
      label: "Название статьи",
      placeholder: "Введите название статьи...",
    },

    // AICODE-NOTE: T101 - New field for key points/theses
    keyPoints: {
      label: "Ключевые тезисы",
      placeholder: "Тезис 1: Важность AI в современном мире\nТезис 2: Практическое применение ML\nТезис 3: Будущее автоматизации",
    },

    // Old fields (kept for backward compatibility during migration)
    topic: {
      label: "Тема",
      placeholder: "Введите тему статьи...",
    },
    sourceUrls: {
      label: "URL-источники",
      placeholder: "Введите URL-адреса (по одному на строку)...",
    },

    research: {
      label: "Включить режим исследования",
    },
    button: {
      submit: "Сгенерировать",
      submitting: "Генерация...",
    },

    // AICODE-NOTE: T103 - Accordion section titles
    sections: {
      content: "Контент",
      style: "Стиль",
      settings: "Настройки",
    },

    // AICODE-NOTE: T110 - Warning when no profile selected
    warnings: {
      noProfile: "⚠ Сначала создайте профиль стиля в разделе 'Стиль'",
    },
  },

  // ExecutionView component
  executionView: {
    title: "Выполнение",
    description: "Просмотр процесса генерации и финальной статьи",
    tabs: {
      log: "Лог",
      result: "Результат",
    },
    log: {
      waiting: "Ожидание начала генерации...",
    },
    result: {
      empty: "Статья ещё не сгенерирована.",
      buttons: {
        copy: "Копировать",
        copied: "Скопировано!",
        download: "Скачать",
      },
    },
  },

  // Theme toggle component
  themeToggle: {
    light: "Светлая тема",
    dark: "Тёмная тема",
  },

  // Error messages (page.tsx)
  errors: {
    connection: "Произошла ошибка потока",
    unknown: "Неизвестная ошибка",
    retry: "Попробуйте снова",
  },

  // Common UI
  common: {
    loading: "Загрузка...",
    error: "Ошибка",
    success: "Успешно",
    cancel: "Отмена",
    close: "Закрыть",
  },

  // Phase 10 additions - будут использоваться в будущих задачах
  styleProfile: {
    title: "Профиль стиля",
    status: {
      loaded: "Профиль загружен",
      notLoaded: "Профиль не загружен",
    },
    buttons: {
      view: "Посмотреть профиль",
      update: "Обновить профиль",
      create: "Создать профиль",
    },
    warning: "Сначала создайте профиль стиля",
  },

  // Article form (Phase 10)
  articleForm: {
    title: {
      label: "Название статьи",
      placeholder: "Введите название статьи...",
      required: "Обязательное поле",
    },
    keyPoints: {
      label: "Ключевые тезисы",
      placeholder: "Введите основные тезисы (по одному на строку)...\nПример:\n- Тезис 1\n- Тезис 2\n- Тезис 3",
    },
  },

  // Accordion sections (Phase 10)
  sections: {
    content: "Контент",
    style: "Стиль",
    settings: "Настройки",
  },
}

// Type for translations
export type Translations = typeof ru

// Export default translation
export const translations: Translations = ru

// Helper function to get nested translation
export function t(path: string): string {
  const keys = path.split('.')
  // AICODE-NOTE: Using Record type instead of any for type safety while allowing nested access
  let value: Record<string, unknown> | unknown = translations

  for (const key of keys) {
    value = (value as Record<string, unknown>)?.[key]
    if (value === undefined) {
      console.warn(`Translation not found for path: ${path}`)
      return path
    }
  }

  return typeof value === 'string' ? value : path
}
