// AICODE-NOTE: T081 - Russian translation dictionary for all UI strings (FR-026, FR-027)
// Contains all interface text: labels, buttons, messages, errors, placeholders
// Used by components to display Russian text instead of English

export const ru = {
  // InputForm component
  inputForm: {
    title: "Генерация статьи",
    description: "Введите тему и URL-источники для создания статьи в определённом стиле",
    topic: {
      label: "Тема",
      placeholder: "Введите тему статьи...",
    },
    sourceUrls: {
      label: "URL-источники",
      placeholder: "Введите URL-адреса (по одному на строку)...",
    },
    research: {
      label: "Включить режим исследования (будущая функция)",
    },
    button: {
      submit: "Сгенерировать",
      submitting: "Генерация...",
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
  let value: any = translations

  for (const key of keys) {
    value = value?.[key]
    if (value === undefined) {
      console.warn(`Translation not found for path: ${path}`)
      return path
    }
  }

  return typeof value === 'string' ? value : path
}
