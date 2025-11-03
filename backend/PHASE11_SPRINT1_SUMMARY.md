# Phase 11 Sprint 1: Backend - Profile Name & Optional Profile

## Выполненные задачи

### T119: Добавить поле `name` в модель StyleProfileDB ✅

**Файл**: `backend/src/db/models.py`

**Изменения**:
- Добавлен столбец `name VARCHAR(100) NOT NULL DEFAULT 'Профиль'` после поля `id`
- Обновлен метод `to_dict()` для включения поля `name` в API ответы
- Добавлены AICODE комментарии для объяснения назначения поля

**Код**:
```python
# AICODE-NOTE: T119 - Human-readable profile name (e.g. "Профиль Habr")
# Generated from first source URL domain, used for UI display
name = Column(
    String(100),
    nullable=False,
    default="Профиль",
    comment="Human-readable profile name (e.g. 'Профиль Habr')",
)
```

---

### T120: Создать функцию `generate_profile_name()` ✅

**Файл**: `backend/src/api/profiles.py`

**Функциональность**:
1. Извлекает домен из первого URL
2. Убирает префикс "www." если присутствует
3. Берет первую часть домена до точки (например, "habr" из "habr.com")
4. Делает первую букву заглавной
5. Возвращает "Профиль {SiteName}"

**Особые случаи**:
- `localhost` → "Профиль Local"
- IP адреса (192.168.x.x, 10.x.x.x, 127.0.0.1) → "Профиль Local"
- Невалидные URLs → "Профиль" (fallback)

**Примеры**:
```
https://habr.com/article → "Профиль Habr"
https://www.example.com/page → "Профиль Example"
http://localhost:8000 → "Профиль Local"
https://192.168.1.1 → "Профиль Local"
```

**Тестирование**: Все 7 тестовых случаев прошли успешно ✓

---

### T121: Добавить миграцию в `database.py` ✅

**Файл**: `backend/src/db/database.py`

**Функция**: `_migrate_add_name_column()`

**Логика миграции**:
1. Проверка наличия столбца 'name' через `PRAGMA table_info`
2. Если столбец отсутствует:
   - Добавление через `ALTER TABLE` с default 'Профиль'
   - Загрузка всех существующих записей
   - Генерация имен для каждой записи через `generate_profile_name()`
   - Обновление записей с сгенерированными именами
3. Если столбец существует - пропуск миграции

**Безопасность**:
- Можно вызывать многократно - идемпотентная операция
- Использует SQLAlchemy 2.0 `text()` для сырых SQL запросов
- Обрабатывает ошибки с fallback на "Профиль"

**Интеграция**: Миграция вызывается автоматически в `init_db()` при старте приложения

**Тестирование**:
```sql
-- До миграции:
PRAGMA table_info(style_profiles);
-- Результат: 6 столбцов (без name)

-- После миграции:
PRAGMA table_info(style_profiles);
-- Результат: 7 столбцов (с name VARCHAR(100) NOT NULL DEFAULT 'Профиль')
```

---

### T122: Обновить POST /api/profiles для генерации имени ✅

**Файл**: `backend/src/api/profiles.py`

**Изменения в `create_profile()`**:
1. Вызов `generate_profile_name(url_strings)` сразу после конвертации URLs
2. Логирование сгенерированного имени
3. Сохранение имени в БД при создании `StyleProfileDB`

**Код**:
```python
# AICODE-NOTE: T122 - Generate human-readable profile name before extraction
profile_name = generate_profile_name(url_strings)
logger.info(f"Generated profile name: {profile_name}")

# ...

new_profile = StyleProfileDB(
    name=profile_name,  # T122: Human-readable name for UI
    urls_hash=urls_hash,
    profile_text=profile_text,
    source_urls=url_strings,
)
```

**Обновлена модель**: `ProfileResponse` теперь включает поле `name: str`

---

### T123: Сделать `profileId` опциональным ✅

**Файл**: `backend/src/models/request.py`

**Изменения в `GenerateArticleRequestV2`**:
```python
# До:
profileId: Annotated[
    int,
    Field(gt=0, description="Style profile ID from database (required)")
]

# После:
profileId: Annotated[
    int | None,
    Field(
        default=None,
        gt=0,
        description="Style profile ID from database (optional, None for free style)"
    )
]
```

**Обновлен docstring**: Указано, что `profileId` опционален для free-style генерации

---

### T124: Обновить `generate_article_v2()` для опциональной загрузки профиля ✅

**Файл**: `backend/src/api/generate.py`

**Изменения**:

#### 1. Endpoint `stream_generation_v2()`:
```python
# AICODE-NOTE: T124 - Load style profile from database if profileId provided
profile_text = None
if body.profileId is not None:
    # Load profile from database
    profile = db.query(StyleProfileDB).filter(...).first()
    if not profile:
        raise HTTPException(404, detail=f"Profile {body.profileId} not found")
    profile_text = profile.profile_text
    logger.info(f"Loaded profile {profile.id}")
else:
    # No profile specified, use free-style generation
    logger.info("No profile specified, using free-style generation")
```

#### 2. Stream функция `generate_article_stream_v2()`:
- Изменен тип параметра: `profile_text: str | None`
- Обновлен docstring для T124
- Обновлена генерация промпта:

```python
# AICODE-NOTE: T124 - Handle optional profile_text
generation_prompt = f"Title: {title}\n\n"
if key_points:
    generation_prompt += f"Key Points:\n{key_points}\n\n"
if profile_text:
    generation_prompt += f"Style Profile:\n{profile_text}"
else:
    generation_prompt += "Style: Free-style (no specific style constraints)"
```

**Поведение**:
- `profileId = 123` → Загрузка профиля из БД, styled генерация
- `profileId = null` → Free-style генерация без ограничений стиля
- `profileId = 999` (не существует) → HTTP 404 ошибка

---

## Сводка изменений

### Измененные файлы:
1. `backend/src/db/models.py` (+11 строк)
   - Добавлено поле `name` в модель
   - Обновлен метод `to_dict()`

2. `backend/src/api/profiles.py` (+107 строк)
   - Функция `generate_profile_name()` (66 строк)
   - Обновлен `create_profile()` для генерации имени
   - Обновлена модель `ProfileResponse`

3. `backend/src/db/database.py` (+90 строк)
   - Функция миграции `_migrate_add_name_column()` (84 строки)
   - Вызов миграции в `init_db()`

4. `backend/src/models/request.py` (~10 строк изменений)
   - `profileId: int | None = None` в `GenerateArticleRequestV2`

5. `backend/src/api/generate.py` (~30 строк изменений)
   - Опциональная загрузка профиля в `stream_generation_v2()`
   - Обработка `None` profile_text в `generate_article_stream_v2()`

### Всего: ~248 строк нового кода + AICODE комментарии

---

## Тестирование

### 1. Генерация имен профилей
✅ Все 7 тестовых случаев пройдены:
- Обычные домены (habr.com, example.com)
- Домены с www. префиксом
- localhost и IP адреса
- Поддомены (blog.techcrunch.com)

### 2. Миграция базы данных
✅ Успешно:
- Столбец добавлен в пустую БД
- Миграция идемпотентна (повторный вызов безопасен)
- Используется SQLAlchemy 2.0 text() API

### 3. Синтаксис Python
✅ Все файлы компилируются без ошибок:
```bash
python3 -m py_compile src/db/models.py src/api/profiles.py \
  src/db/database.py src/api/generate.py src/models/request.py
```

---

## AICODE Coverage

Все ключевые решения задокументированы:

**AICODE-NOTE**:
- T119: Назначение поля `name`
- T120: Логика генерации имени профиля
- T121: Шаги миграции БД
- T122: Генерация имени при создании профиля
- T123: Опциональность `profileId`
- T124: Обработка free-style генерации

**Примеры**:
```python
# AICODE-NOTE: T119 - Human-readable profile name (e.g. "Профиль Habr")
# Generated from first source URL domain, used for UI display

# AICODE-NOTE: T124 - Load style profile from database if profileId provided
profile_text = None
if body.profileId is not None:
    ...
```

---

## API Changes

### GET /api/profiles/current
**Новое поле в ответе**:
```json
{
  "id": 1,
  "name": "Профиль Habr",  // NEW
  "urls_hash": "abc123...",
  "profile_text": "...",
  "source_urls": ["https://habr.com/..."],
  "created_at": "2025-10-30T...",
  "updated_at": "2025-10-30T..."
}
```

### POST /api/profiles
**Автоматическая генерация имени**:
- Принимает: `{"source_urls": ["https://habr.com/..."]}`
- Возвращает: профиль с сгенерированным `name: "Профиль Habr"`

### POST /api/generate
**Опциональный profileId**:
```json
// С профилем (styled):
{
  "title": "Заголовок",
  "keyPoints": "...",
  "profileId": 1,
  "enableResearch": true
}

// Без профиля (free-style):
{
  "title": "Заголовок",
  "keyPoints": "...",
  "profileId": null,  // или отсутствует
  "enableResearch": false
}
```

---

## Обратная совместимость

✅ **Полная обратная совместимость**:
- Поле `name` имеет default значение 'Профиль'
- Миграция автоматическая при старте приложения
- Существующие API endpoints продолжают работать
- `profileId` теперь опционален (ранее был обязателен)

---

## Следующие шаги

**Готово для интеграции с frontend**:
1. Frontend может отображать `profile.name` вместо `profile.id`
2. При создании профиля имя генерируется автоматически
3. Поддержка free-style генерации (profileId = null)

**Рекомендации для тестирования**:
1. Создать профиль через POST /api/profiles
2. Проверить наличие читаемого имени в ответе
3. Протестировать генерацию с profileId и без него
4. Убедиться, что миграция работает на существующих БД

---

## Статус

✅ **Все задачи T119-T124 выполнены**
✅ **Тесты пройдены**
✅ **AICODE комментарии добавлены**
✅ **Обратная совместимость сохранена**

**Готово к коммиту и тестированию**
