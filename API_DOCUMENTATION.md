# VasDom AudioBot - API Documentation

## Base URL

- Development: `http://localhost:8001`
- Production: `https://your-backend.onrender.com`

Все эндпоинты начинаются с префикса `/api`

## Authentication

Большинство эндпоинтов требуют JWT токен в заголовке:

```http
Authorization: Bearer <your_jwt_token>
```

## Health & System

### GET /api/health

Проверка здоровья системы

**Response:**
```json
{
  "ok": true,
  "ts": 1699999999
}
```

## Houses (Дома/Объекты)

### GET /api/cleaning/houses

Получить список домов с фильтрами

**Query Parameters:**
- `brigade` (string, optional) - Фильтр по бригаде
- `management_company` (string, optional) - Фильтр по УК
- `cleaning_date` (string, optional) - Точная дата (YYYY-MM-DD)
- `date_from` (string, optional) - Дата от (YYYY-MM-DD)
- `date_to` (string, optional) - Дата до (YYYY-MM-DD)
- `page` (integer, default=1) - Номер страницы
- `limit` (integer, default=20) - Кол-во элементов на странице

**Response:**
```json
{
  "houses": [
    {
      "id": "uuid-string",
      "address": "ул. Ленина, 123",
      "brigade": "Бригада №1",
      "management_company": "УК Комфорт",
      "apartments": 48,
      "entrances": 3,
      "floors": 9,
      "periodicity": "weekly",
      "last_cleaning": "2025-01-10",
      "next_cleaning": "2025-01-17",
      "bitrix_url": "https://bitrix24.ru/..."
    }
  ],
  "total": 150,
  "page": 1,
  "pages": 8
}
```

### GET /api/cleaning/filters

Получить опции для фильтров

**Response:**
```json
{
  "brigades": ["Бригада №1", "Бригада №2", "Бригада №3"],
  "management_companies": ["УК Комфорт", "УК Сервис", "УК Престиж"],
  "statuses": ["scheduled", "in_progress", "completed", "cancelled"]
}
```

### GET /api/cleaning/house/{id}/details

Получить детали конкретного дома

**Path Parameters:**
- `id` (string, required) - UUID дома

**Response:**
```json
{
  "id": "uuid-string",
  "address": "ул. Ленина, 123",
  "brigade": "Бригада №1",
  "management_company": "УК Комфорт",
  "apartments": 48,
  "entrances": 3,
  "floors": 9,
  "periodicity": "weekly",
  "cleaning_history": [
    {
      "date": "2025-01-10",
      "status": "completed",
      "notes": "Все выполнено в срок"
    },
    {
      "date": "2025-01-03",
      "status": "completed",
      "notes": ""
    }
  ],
  "upcoming_cleanings": [
    {
      "date": "2025-01-17",
      "status": "scheduled"
    },
    {
      "date": "2025-01-24",
      "status": "scheduled"
    }
  ],
  "bitrix_url": "https://bitrix24.ru/crm/deal/123/"
}
```

## Dashboard

### GET /api/dashboard/stats

Получить статистику для Dashboard

**Query Parameters:**
- `brigade` (string, optional) - Фильтр по бригаде
- `management_company` (string, optional) - Фильтр по УК
- `date_from` (string, optional) - Дата от
- `date_to` (string, optional) - Дата до

**Response:**
```json
{
  "today": {
    "scheduled": 12,
    "in_progress": 3,
    "completed": 7
  },
  "week": {
    "scheduled": 45,
    "in_progress": 8,
    "completed": 28
  },
  "statuses": {
    "scheduled": 120,
    "in_progress": 15,
    "completed": 340,
    "cancelled": 5
  },
  "by_brigade": {
    "Бригада №1": 25,
    "Бригада №2": 18,
    "Бригада №3": 22
  }
}
```

## AI Chat

### POST /api/ai/chat

Отправить сообщение в AI чат

**Request Body:**
```json
{
  "message": "Сколько домов запланировано на сегодня?",
  "context": {
    "user_id": "uuid-string",
    "session_id": "session-uuid"
  }
}
```

**Response:**
```json
{
  "response": "На сегодня запланировано 12 домов для уборки.",
  "confidence": 0.95,
  "sources": [
    {
      "type": "database",
      "reference": "cleaning_schedules"
    }
  ]
}
```

### GET /api/ai/chat/history

Получить историю чата

**Query Parameters:**
- `session_id` (string, optional) - ID сессии
- `limit` (integer, default=50) - Кол-во сообщений

**Response:**
```json
{
  "messages": [
    {
      "id": "msg-uuid",
      "role": "user",
      "content": "Привет!",
      "timestamp": "2025-01-10T10:00:00Z"
    },
    {
      "id": "msg-uuid",
      "role": "assistant",
      "content": "Здравствуйте! Чем могу помочь?",
      "timestamp": "2025-01-10T10:00:01Z"
    }
  ]
}
```

## Voice (OpenAI Realtime)

### POST /api/realtime/sessions

Создать Realtime session для голосового разговора

**Request Body:**
```json
{
  "voice": "marin",
  "instructions": "Вы — голосовой ассистент VasDom...",
  "temperature": 0.6,
  "max_response_output_tokens": 1024
}
```

**Response:**
```json
{
  "client_secret": "secret-string",
  "model": "gpt-realtime",
  "voice": "marin",
  "instructions": "...",
  "expires_at": 1699999999,
  "session_id": "session-uuid"
}
```

### POST /api/voice/ai-call

Создать AI-powered исходящий звонок

**Request Body:**
```json
{
  "phone_number": "+79991234567",
  "prompt_id": "pmpt_...",
  "voice": "marin",
  "greeting": "Здравствуйте! Это VasDom AudioBot.",
  "trunk_id": "optional-trunk-id",
  "from_number": "+79997654321"
}
```

**Response:**
```json
{
  "call_id": "call-uuid",
  "room_name": "ai_call_uuid",
  "status": "ringing"
}
```

### GET /api/voice/call/{call_id}/status

Получить статус звонка

**Response:**
```json
{
  "call_id": "call-uuid",
  "status": "connected",
  "details": {
    "to": "+79991234567",
    "from": "+79997654321",
    "duration": 120,
    "ai_agent_status": "active"
  }
}
```

### GET /api/voice/ai-call/{call_id}/logs

Получить логи AI звонка

**Response:**
```json
{
  "call_id": "call-uuid",
  "logs": [
    {
      "ts": 1699999999,
      "level": "info",
      "message": "Agent connected to LiveKit room"
    },
    {
      "ts": 1699999999,
      "level": "ai_text",
      "message": "Здравствуйте! Это VasDom..."
    }
  ]
}
```

## AI Invites (Ссылки для звонков)

### POST /api/ai-invite/create

Создать invite-ссылку для AI разговора

**Request Body:**
```json
{
  "start_at": "2025-01-10T16:00:00",
  "ttl_minutes": 30,
  "employee_id": "emp-uuid",
  "context": "Отчёт по уборкам",
  "voice": "marin"
}
```

**Response:**
```json
{
  "token": "invite-token",
  "start_at": "2025-01-10T16:00:00+03:00",
  "expires_at": "2025-01-10T16:30:00+03:00",
  "voice": "marin",
  "context": "Отчёт по уборкам"
}
```

### GET /api/ai-invite/{token}/status

Проверить статус invite

**Response:**
```json
{
  "token": "invite-token",
  "status": "available",
  "starts_in_sec": 0,
  "start_at": "2025-01-10T16:00:00+03:00",
  "expires_at": "2025-01-10T16:30:00+03:00",
  "context": "Отчёт по уборкам"
}
```

Статусы: `not_started`, `available`, `expired`

### POST /api/ai-invite/{token}/resolve

Использовать invite и получить Realtime session

**Response:**
```json
{
  "token": "invite-token",
  "start_at": "...",
  "expires_at": "...",
  "context": "...",
  "client_secret": "...",
  "model": "gpt-realtime",
  "voice": "marin",
  "instructions": "...",
  "expires_at": 1699999999,
  "session_id": "session-uuid"
}
```

## Knowledge Base (База знаний)

### POST /api/knowledge/upload

Загрузить файл в базу знаний

**Request:**
- Content-Type: multipart/form-data
- Field: `file` (File)

**Response:**
```json
{
  "id": "knowledge-uuid",
  "filename": "document.pdf",
  "status": "pending",
  "extracted_text": "Извлечённый текст из документа..."
}
```

### GET /api/knowledge/pending

Получить список документов, ожидающих подтверждения

**Response:**
```json
{
  "items": [
    {
      "id": "knowledge-uuid",
      "filename": "document.pdf",
      "extracted_text": "...",
      "ai_understanding": "ИИ понял, что это инструкция по...",
      "uploaded_at": "2025-01-10T10:00:00Z"
    }
  ]
}
```

### POST /api/knowledge/confirm

Подтвердить и добавить в базу знаний

**Request Body:**
```json
{
  "id": "knowledge-uuid",
  "confirmed": true,
  "corrections": "Необязательные правки текста"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Document added to knowledge base"
}
```

### GET /api/knowledge/search

Поиск по базе знаний (RAG)

**Query Parameters:**
- `q` (string, required) - Поисковый запрос

**Response:**
```json
{
  "results": [
    {
      "id": "knowledge-uuid",
      "content": "Релевантный текст из документа...",
      "score": 0.92,
      "source": "document.pdf"
    }
  ]
}
```

## AI Tasks (Задачи ИИ)

### POST /api/ai-tasks

Создать AI задачу с расписанием

**Request Body:**
```json
{
  "title": "Ежедневная сводка",
  "description": "Отправить сводку по уборкам",
  "schedule": {
    "type": "daily",
    "time": "18:00",
    "timezone": "Europe/Moscow"
  },
  "action": {
    "type": "telegram",
    "chat_id": "123456789",
    "message_template": "Сегодня выполнено {completed} уборок"
  }
}
```

**Response:**
```json
{
  "id": "task-uuid",
  "title": "Ежедневная сводка",
  "status": "active",
  "next_run": "2025-01-11T18:00:00+03:00"
}
```

### GET /api/ai-tasks

Получить список AI задач

**Response:**
```json
{
  "tasks": [
    {
      "id": "task-uuid",
      "title": "Ежедневная сводка",
      "status": "active",
      "last_run": "2025-01-10T18:00:00+03:00",
      "next_run": "2025-01-11T18:00:00+03:00",
      "success_count": 15,
      "fail_count": 0
    }
  ]
}
```

### PUT /api/ai-tasks/{task_id}

Обновить AI задачу

**Request Body:** (аналогично POST)

**Response:**
```json
{
  "success": true,
  "task": { /* обновлённая задача */ }
}
```

### DELETE /api/ai-tasks/{task_id}

Удалить AI задачу

**Response:**
```json
{
  "success": true,
  "message": "Task deleted"
}
```

## Meetings (Планёрки)

### POST /api/meetings

Начать новую планёрку (meeting)

**Request Body:**
```json
{
  "title": "Планёрка 10.01.2025",
  "participants": ["user-1", "user-2"]
}
```

**Response:**
```json
{
  "id": "meeting-uuid",
  "title": "Планёрка 10.01.2025",
  "status": "active",
  "started_at": "2025-01-10T10:00:00Z"
}
```

### POST /api/meetings/{meeting_id}/transcribe

Отправить аудио для транскрипции

**Request:**
- Content-Type: multipart/form-data
- Field: `audio` (File, WAV/MP3)

**Response:**
```json
{
  "text": "Транскрибированный текст...",
  "timestamp": "2025-01-10T10:05:00Z"
}
```

### GET /api/meetings/{meeting_id}/summary

Получить саммари встречи

**Response:**
```json
{
  "meeting_id": "meeting-uuid",
  "summary": "На встрече обсуждались...",
  "key_points": [
    "Пункт 1",
    "Пункт 2"
  ],
  "action_items": [
    "Задача 1",
    "Задача 2"
  ]
}
```

### GET /api/meetings/{meeting_id}/export

Экспортировать встречу в текстовый файл

**Response:** (file download)
- Content-Type: text/plain
- Filename: `meeting-{id}.txt`

## Employees (Сотрудники)

### GET /api/employees

Получить список сотрудников

**Response:**
```json
{
  "employees": [
    {
      "id": "emp-uuid",
      "name": "Иванов Иван",
      "phone": "+79991234567",
      "brigade": "Бригада №1",
      "role": "worker",
      "status": "active"
    }
  ]
}
```

### POST /api/employees

Добавить нового сотрудника

**Request Body:**
```json
{
  "name": "Петров Пётр",
  "phone": "+79991234567",
  "brigade": "Бригада №1",
  "role": "worker"
}
```

**Response:**
```json
{
  "id": "emp-uuid",
  "name": "Петров Пётр",
  "phone": "+79991234567",
  "brigade": "Бригада №1",
  "role": "worker",
  "status": "active"
}
```

## Telegram

### POST /api/telegram/send

Отправить сообщение в Telegram

**Request Body:**
```json
{
  "chat_id": "123456789",
  "message": "Текст сообщения"
}
```

**Response:**
```json
{
  "success": true,
  "message_id": 12345
}
```

## Logs

### GET /api/logs

Получить логи системы

**Query Parameters:**
- `level` (string, optional) - Уровень (info, warning, error)
- `from` (string, optional) - Дата от (ISO)
- `to` (string, optional) - Дата до (ISO)
- `limit` (integer, default=100) - Кол-во записей

**Response:**
```json
{
  "logs": [
    {
      "timestamp": "2025-01-10T10:00:00Z",
      "level": "info",
      "source": "bitrix_service",
      "message": "Synchronized 15 houses from Bitrix24"
    }
  ],
  "total": 1523
}
```

## Error Responses

Все ошибки возвращаются в формате:

```json
{
  "detail": "Error message here"
}
```

HTTP Status Codes:
- `200` OK - Успешный запрос
- `201` Created - Ресурс создан
- `400` Bad Request - Неверный запрос
- `401` Unauthorized - Не авторизован
- `403` Forbidden - Доступ запрещён
- `404` Not Found - Ресурс не найден
- `422` Unprocessable Entity - Ошибка валидации
- `500` Internal Server Error - Внутренняя ошибка сервера
- `502` Bad Gateway - Ошибка внешнего сервиса
- `503` Service Unavailable - Сервис недоступен

## Rate Limiting

- Большинство эндпоинтов: 100 requests/minute
- AI Chat: 10 requests/minute
- File Upload: 5 requests/minute

При превышении лимита вернётся:
```json
{
  "detail": "Rate limit exceeded. Try again in 60 seconds."
}
```

## Webhooks

### Bitrix24 Webhook

Настройте вебхук в Bitrix24, чтобы отправлять уведомления на:
`POST /api/webhooks/bitrix24`

### LiveKit Webhook

LiveKit отправляет события на:
`POST /api/voice/webhooks/livekit`

## Pagination

Все эндпоинты со списками поддерживают пагинацию:

**Query Parameters:**
- `page` (integer, default=1)
- `limit` (integer, default=20, max=100)

**Response:**
```json
{
  "items": [ /* массив элементов */ ],
  "total": 150,
  "page": 1,
  "pages": 8
}
```

## Versioning

Текущая версия API: **v1**

При изменении API будет добавлен префикс версии: `/api/v2/...`

## Support

- GitHub Issues: https://github.com/maslovmaksim92/AudioBot/issues
- Email: support@vasdom.ru