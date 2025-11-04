# TODO: Neutralizer Pipeline Implementation

## Текущее состояние

**Статус**: ❌ НЕ РЕАЛИЗОВАНО

Сейчас `topic.json` содержит generic placeholder:
```json
{
  "topic": "Literary work 1 by Charles Dickens",
  "theses": [
    "This is a classic literary work",
    "Written in the author's distinctive style",
    ...
  ]
}
```

## Требуемый пайплайн

### Цель
Из `ground_truth_article.txt` извлечь:
1. **Нейтральную формулировку основной идеи** (без авторского стиля)
2. **Список ключевых тезисов** (5-7 пунктов)
3. Сохранить в `topic.json` для подачи в generation prompt

### Пример желаемого результата

Для "A Tale of Two Cities" by Charles Dickens:

```json
{
  "topic": "Исследование революционных изменений в обществе через призму личных историй",
  "theses": [
    "Контраст между двумя городами как метафора социальных противоречий",
    "Тема самопожертвования ради любви и искупления",
    "Влияние революционных событий на судьбы отдельных людей",
    "Цикличность насилия и его последствия для общества",
    "Трансформация личности через испытания и моральный выбор",
    "Роль прошлого в формировании настоящего",
    "Поиск справедливости в эпоху социальных потрясений"
  ]
}
```

## Задачи для реализации

### Phase 1: Neutralizer Prompt Engineering
- [ ] Создать промпт для нейтрализации текста
- [ ] Промпт должен извлекать суть БЕЗ стилистических особенностей
- [ ] Тестировать на разных авторах (Dickens, Twain, etc.)
- [ ] Валидация: нейтральный язык, сохранение смысла
- [ ] Сохранить в `prompts/neutralizer.txt`

### Phase 2: Integration в prepare_dataset.py
- [ ] Добавить метод `neutralize_article()` в DatasetBuilder
- [ ] Использовать `neutralizer_model_id` из config
- [ ] Input: `ground_truth_article.txt` (полный текст)
- [ ] Output: нейтрализованные topic + theses
- [ ] Обработка ошибок LLM (retry, fallback)
- [ ] Логирование процесса нейтрализации

### Phase 3: Data Model Updates
- [ ] Обновить схему `topic.json`:
  ```json
  {
    "topic": "string (нейтральная формулировка)",
    "theses": ["список тезисов"],
    "neutralized_at": "timestamp",
    "neutralizer_model": "model_id",
    "source_hash": "hash ground_truth для версионирования"
  }
  ```
- [ ] Добавить валидацию в Pydantic models
- [ ] Backward compatibility для старых датасетов

### Phase 4: Configuration
- [ ] Обновить `dataset_config.yml`:
  ```yaml
  # Neutralizer settings
  neutralizer_model_id: "anthropic/claude-3-5-sonnet-20240620"
  max_tokens_for_neutralizer: 4000
  neutralizer_temperature: 0.3  # Low for consistency
  neutralizer_timeout: 120
  ```
- [ ] Добавить в EvalConfig validation для neutralizer settings

### Phase 5: Testing
- [ ] Unit tests для neutralizer prompt
- [ ] Integration tests: dataset generation с neutralizer
- [ ] Сравнить качество generation с neutral vs generic topics
- [ ] Метрика: насколько neutral topics улучшают style copying

### Phase 6: Documentation
- [ ] Обновить README.md с объяснением neutralizer
- [ ] Примеры нейтрализованных topics
- [ ] Troubleshooting для neutralizer issues

## Метрики успеха

1. **Neutrality**: Topic не содержит стилистических маркеров автора
2. **Completeness**: Все ключевые идеи ground_truth отражены в theses
3. **Usability**: Generation с neutral topic дает better style copying
4. **Consistency**: Повторный neutralize того же текста дает similar results

## Приоритет

**MEDIUM** - Neutralizer улучшит качество тестов, но текущий generic approach work-able для baseline testing.

## Зависимости

- LLM client (уже есть)
- prepare_dataset.py (уже есть)
- Новый промпт для neutralization
- Config updates

## Оценка времени

- Phase 1-2: ~4-6 hours (prompt + integration)
- Phase 3-4: ~2-3 hours (data models + config)
- Phase 5-6: ~2-3 hours (testing + docs)
- **Total**: ~8-12 hours

## Next Steps

1. Начать с Phase 1: создать и протестировать neutralizer prompt
2. Запустить на нескольких примерах вручную
3. Интегрировать в prepare_dataset.py
4. Regenerate test dataset с real neutralized topics
5. Сравнить quality с baseline

---

**Created**: 2025-11-04
**Status**: TODO (not started)
