# VasDom AudioBot - API Reference

**Base URL:** `http://localhost:8001` (dev) или `https://your-backend.onrender.com` (prod)

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

Отправить сообщение

**Request:**
```json
{
  "message": "Сколько домов на сегодня?",
  "session_id": "uuid"
}
```

**Response:**
```json
{
  "response": "На сегодня запланировано 12 домов.",
  "confidence": 0.95
}
```

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

## Logs

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