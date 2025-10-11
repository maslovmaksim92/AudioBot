# VasDom AudioBot - API Reference

**Base URL:** Backend доступен через переменную окружения (см. frontend/.env: `REACT_APP_BACKEND_URL`). Для Kubernetes/Ingress все backend маршруты начинаются с `/api` и проксируются на 0.0.0.0:8001. Не хардкодьте URL/порты в коде.

**Все endpoints начинаются с `/api`**

**Swagger UI:** `/docs`

## Authentication

JWT токен в заголовке:
```
Authorization: Bearer <token>
```

## Health & System

### `GET /api/health`

Проверка работы системы

**Response:**
```json
{
  "ok": true,
  "ts": 1760173025
}
```

## Houses (Дома)

Нормализация адресов: поддерживаются формы "ул/улица", "д/дом", "к/корпус", "стр/строение", "лит/литера". Свободные формы типа "к1", "стр 2", "лит А" распознаются.

### `GET /api/cleaning/houses`

Список домов с фильтрами

**Query params:**
- `brigade` - Фильтр по бригаде
- `management_company` - По УК
- `cleaning_date` - Точная дата (YYYY-MM-DD)
- `date_from`, `date_to` - Диапазон
- `page`, `limit` - Пагинация

**Response:**
```json
{
  "houses": [
    {
      "id": "uuid",
      "address": "ул. Ленина, 123",
      "brigade": "Бригада №1",
      "management_company": "УК Комфорт",
      "apartments": 48,
      "next_cleaning": "2025-01-17"
    }
  ],
  "total": 499,
  "page": 1
}
```

### `GET /api/cleaning/filters`

Опции для фильтров

**Response:**
```json
{
  "brigades": ["Бригада №1", "Бригада №2"],
  "management_companies": ["УК Комфорт", "УК Сервис"]
}
```

## Dashboard

### `GET /api/dashboard/stats`

Статистика

**Response:**
```json
{
  "today": {
    "scheduled": 12,
    "completed": 7
  },
  "total_houses": 499,
  "total_employees": 19,
  "active_tasks": 4
}
```

## AI Chat

### `POST /api/ai/chat`

Отправить сообщение ассистенту. Внутри сначала используется "Единый мозг" (быстрые правила), затем fallback к LLM.

Включение debug в запросе добавляет мини-хинт в ответ (для админов): `rule: <правило> · <elapsed_ms>ms · src: <кэш-hit/miss>`

**Request:**
```json
{
  "message": "Когда уборка на Билибина 6 в октябре?",
  "user_id": "7be8f89e-f2bd-4f24-9798-286fddc58358",
  "debug": true
}
```

**Response:**
```json
{
  "message": "🏠 Адрес: Билибина 6\n2025-10-02 — Полная уборка\n2025-10-16 — Подметание\n\nrule: cleaning_month · 126ms · src: houses:hit, cleaning:hit",
  "function_calls": []
}
```

Примеры запросов:
- "Контакты старшего Кибальчича 1 стр 2"
- "Какая бригада на Билибина 6?"
- "Категорийная разбивка расходов за месяц"

## Voice (OpenAI Realtime)

### `POST /api/realtime/sessions`

Создать голосовую сессию

**Request:**
```json
{
  "voice": "marin",
  "instructions": "Вы - ассистент VasDom"
}
```

**Response:**
```json
{
  "client_secret": "secret",
  "session_id": "uuid",
  "expires_at": 1234567890
}
```

### `POST /api/voice/ai-call`

AI звонок

**Request:**
```json
{
  "phone_number": "+79991234567",
  "voice": "marin",
  "greeting": "Здравствуйте!"
}
```

**Response:**
```json
{
  "call_id": "uuid",
  "status": "ringing"
}
```

## Brain (Единый мозг)

### `POST /api/brain/ask`

Универсальная точка быстрых ответов по данным приложения без использования LLM. Поддерживаемые запросы:

**Адресные запросы:**
- Контакты старшего по адресу
- График уборок по адресу и месяцу
- Бригада по адресу

**Финансовые запросы:**
- Базовая статистика (доходы/расходы/прибыль)
- Разбивка по категориям
- Динамика месяц к месяцу (М/М)
- Динамика год к году (Г/Г)
- Тренды категорий

**Структурные запросы:**
- Общая статистика домов/квартир/этажей/подъездов

При `debug: true` возвращает подробную диагностику: `matched_rule`, `elapsed_ms`, `trace`, `sources` (с информацией о cache hit/miss).

**Примеры запросов:**

1. **Контакты старшего:**
```json
{
  "message": "Контакты старшего Кибальчича 3",
  "debug": true
}
```

Response:
```json
{
  "success": true,
  "answer": "🏠 Адрес: Кибальчича 3\nСтарший: Иванов И.И.\nТелефон(ы): +7...\nEmail: elder@vasdom.ru\nСсылка в Bitrix: https://...",
  "rule": "elder_contact",
  "sources": {
    "addr": "кибальчича 3",
    "elder": {"cache": "hit"},
    "houses": {"cache": "miss"}
  },
  "debug": {
    "matched_rule": "elder_contact",
    "elapsed_ms": 85,
    "trace": [{"rule":"elder_contact","status":"hit","elapsed_ms":85}]
  }
}
```

2. **График уборок:**
```json
{
  "message": "График уборок Билибина 6 октябрь",
  "debug": true
}
```

3. **Финансы:**
```json
{
  "message": "Финансы компании",
  "debug": true
}
```

Response:
```json
{
  "success": true,
  "answer": "💰 Финансы:\nДоходы: 150,000.00 ₽\nРасходы: 0.00 ₽\nПрибыль: 150,000.00 ₽\nТранзакций: 1",
  "rule": "finance_basic",
  "sources": {"finance": {"cache": "miss"}},
  "data": {"income": 150000.0, "expense": 0.0, "transactions": 1}
}
```

4. **Структурная статистика:**
```json
{
  "message": "Сколько всего домов?",
  "debug": true
}
```

Response:
```json
{
  "success": true,
  "answer": "📊 Общая статистика:\nДомов: 499\nКвартир: 30621\nЭтажей: 2918\nПодъездов: 1592",
  "rule": "structural_totals",
  "sources": {"db": "houses"}
}
```

### `GET /api/brain/metrics`

Метрики “мозга”: `resolver_counts`, `resolver_times_ms`, `cache_hits`, `cache_misses`.

---

## Knowledge Base

### `POST /api/knowledge/upload`

Загрузить файл

**Request:** multipart/form-data
- `file` - Файл (PDF, DOCX, TXT)

**Response:**
```json
{
  "id": "uuid",
  "filename": "doc.pdf",
  "status": "pending"
}
```

### `GET /api/knowledge/search?q=текст`

Поиск по базе знаний

**Response:**
```json
{
  "results": [
    {
      "content": "Релевантный текст...",
      "score": 0.92,
      "source": "doc.pdf"
    }
  ]
}
```

## AI Tasks

### `POST /api/ai-tasks`

Создать задачу

**Request:**
```json
{
  "title": "Ежедневная сводка",
  "schedule": {
    "type": "daily",
    "time": "18:00"
  },
  "action": {
    "type": "telegram",
    "message_template": "Сегодня {completed} уборок"
  }
}
```

### `GET /api/ai-tasks`

Список задач

### `PUT /api/ai-tasks/{id}`

Обновить задачу

### `DELETE /api/ai-tasks/{id}`

Удалить задачу

## Meetings (Планёрки)

### `POST /api/meetings`

Начать планёрку

**Request:**
```json
{
  "title": "Планёрка 11.10.2025",
  "participants": ["user1", "user2"]
}
```

### `POST /api/meetings/{id}/transcribe`

Транскрибировать аудио

**Request:** multipart/form-data
- `audio` - Аудио файл

### `GET /api/meetings/{id}/summary`

Получить саммари

## Employees

### `GET /api/employees`

Список сотрудников

### `POST /api/employees`

Добавить сотрудника

## Telegram

### `POST /api/telegram/send`

Отправить сообщение

**Request:**
```json
{
  "chat_id": "-1002384210149",
  "message": "Текст"
}
```

## Logs & Observability

### `GET /api/brain/metrics`
Снимок метрик единого мозга (resolver_counts, resolver_times_ms, cache_hits/misses)

### `GET /api/logs`

Системные логи

**Query params:**
- `level` - info, warning, error
- `from`, `to` - Временной диапазон
- `limit` - Количество

## Error Responses

Все ошибки в формате:
```json
{
  "detail": "Описание ошибки"
}
```

**HTTP коды:**
- 200 - OK
- 400 - Bad Request
- 401 - Unauthorized
- 404 - Not Found
- 422 - Validation Error
- 500 - Internal Server Error

## Rate Limiting

- Стандартные endpoints: 100 req/min
- AI Chat: 10 req/min
- File Upload: 5 req/min

## Webhooks

### Bitrix24
`POST /api/webhooks/bitrix24`

### LiveKit
`POST /api/voice/webhooks/livekit`

## WebSocket

### Real-time updates
`ws://localhost:8001/ws`

---

**Полная интерактивная документация:** `/docs` (Swagger UI)