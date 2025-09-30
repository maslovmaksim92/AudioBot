# AI Voice Integration с OpenAI Realtime API

## Обзор

Интегрирована функция AI-powered исходящих звонков с использованием:
- **OpenAI Realtime API** с поддержкой stored prompts
- **LiveKit SIP Gateway** для звонков через Asterisk/Novofon
- **Prompt ID**: `pmpt_68b199151b248193a68a8c70861adf550e6f2509209ed3a5`

## Архитектура

```
Frontend (AIDialer) 
    ↓
Backend (/api/voice/ai-call)
    ↓
LiveKit SIP Gateway
    ↓
Asterisk Bridge (Yandex VM)
    ↓
Novofon SIP Trunk
    ↓
PSTN (реальный телефонный звонок)
```

## Backend API

### Новый Endpoint: `/api/voice/ai-call`

**Request:**
```json
POST /api/voice/ai-call
Content-Type: application/json

{
  "phone_number": "+79001234567",  // Обязательно
  "prompt_id": "pmpt_68b199151b248193a68a8c70861adf550e6f2509209ed3a5",  // По умолчанию
  "voice": "marin",  // По умолчанию
  "greeting": "Здравствуйте! Это VasDom AudioBot.",  // По умолчанию
  "trunk_id": null,  // Опционально (берется из env)
  "from_number": null  // Опционально (берется из env)
}
```

**Response (успех):**
```json
{
  "call_id": "3784bcec8bc848338bea3720c73bae45",
  "room_name": "ai_call_3784bcec8bc848338bea3720c73bae45",
  "status": "ringing"
}
```

**Response (ошибка):**
```json
{
  "detail": "Error message"
}
```

### Проверка статуса звонка: `/api/voice/call/{call_id}/status`

**Response:**
```json
{
  "call_id": "3784bcec8bc848338bea3720c73bae45",
  "status": "ringing",
  "details": {
    "room_name": "ai_call_...",
    "to": "+79001234567",
    "ai_enabled": true,
    "ai_agent_status": "active",  // starting, active, failed
    "prompt_id": "pmpt_...",
    "voice": "marin",
    "sip_participant_id": "..."
  }
}
```

## Frontend Component

### AIDialer Component

Обновленный компонент с новым UI:

**Расположение:** `/app/frontend/src/components/LiveConversation/AIDialer.js`

**Особенности:**
- 🤖 Визуальный индикатор AI-звонка
- Отображение статуса AI-агента
- Автоматическое обновление статуса
- Градиентный фон для выделения AI-функции

## Требуемые Переменные Окружения (Render)

### OpenAI
```
OPENAI_API_KEY=sk-proj-...
```

### LiveKit
```
LIVEKIT_WS_URL=wss://vasdom-cjzaim84.livekit.cloud
LIVEKIT_API_KEY=APIs9Saqppf7Qgk
LIVEKIT_API_SECRET=4dUG5rliFopYcPS3fE6hfDk0y6txX7MalJJbpqrB7Ma
LIVEKIT_SIP_TRUNK_ID=ST_Wf3tJUS5rRqM
DEFAULT_CALLER_ID=+79843330712
```

## Как Работает AI Agent

1. **Инициализация звонка:**
   - Создается LiveKit room
   - Создается SIP participant (исходящий звонок)
   - Запускается AI agent в background task

2. **AI Agent подключается:**
   - Подключается к LiveKit room через WebSocket
   - Инициализирует OpenAI Realtime Session
   - Отправляет `session.update` с prompt ID

3. **Обработка аудио:**
   - Подписывается на audio tracks от PSTN participant
   - Пересылает аудио в OpenAI Realtime API
   - Публикует AI-сгенерированный аудио ответ обратно в room

4. **Начало разговора:**
   - AI agent ждет подключения PSTN participant
   - Отправляет greeting через `generate_reply()`
   - AI начинает разговор первым

## Использование Prompt ID

### ⚠️ Важно: Ограничения LiveKit Realtime API

**Текущая реализация:**
LiveKit's `RealtimeModel` не поддерживает напрямую stored prompt IDs из OpenAI Platform. Код пытается отправить prompt ID через `session.send_event()`, но это может не работать.

**Рекомендуемые решения:**

**Вариант 1: Скопировать содержимое промпта (Рекомендуется)**
```python
realtime_model = lk_openai.realtime.RealtimeModel(
    model='gpt-4o-realtime-preview',
    voice='marin',
    temperature=0.8,
    api_key=openai_key,
    # Вставьте полное содержимое вашего prompt сюда
    instructions="""
    Вы - AI ассистент для клининговой компании VasDom.
    Ваша задача: принять заказ на уборку.
    - Поздоровайтесь с клиентом
    - Узнайте адрес и тип уборки
    - Уточните дату и время
    - Подтвердите заказ
    """
)
```

**Вариант 2: Попытка использовать prompt ID (Experimental)**
```python
# После создания session, отправить session.update
session.send_event({
    "type": "session.update",
    "session": {
        "prompt": {
            "id": "pmpt_68b199151b248193a68a8c70861adf550e6f2509209ed3a5",
            "variables": {
                # Если ваш prompt использует переменные
                "company_name": {"type": "input_text", "text": "VasDom"}
            }
        }
    }
})
```

**Вариант 3: Использовать прямой OpenAI Realtime WebSocket**
Для полной поддержки stored prompts, нужно использовать OpenAI Realtime API напрямую, без LiveKit обертки.

### Текущая Реализация
Код использует fallback механизм:
1. Пытается отправить prompt ID через `send_event()`
2. Если не работает - использует простые fallback instructions
3. Логирует все попытки для debugging

Prompt настраивается через [OpenAI Platform](https://platform.openai.com/prompts).

## Тестирование

### Локально (с тестовыми credentials):
```bash
curl -X POST http://localhost:8001/api/voice/ai-call \
  -H "Content-Type: application/json" \
  -d '{"phone_number":"8888"}'
```

### На Render (с реальными credentials):
```bash
curl -X POST https://audiobot-qci2.onrender.com/api/voice/ai-call \
  -H "Content-Type: application/json" \
  -d '{"phone_number":"+79001234567"}'
```

### Проверка конфигурации:
```bash
curl https://audiobot-qci2.onrender.com/api/voice/debug/check
```

## Debug/Monitoring

### Логи Backend
```bash
tail -f /var/log/supervisor/backend.err.log | grep "AI-CALL"
```

**Ключевые события:**
- `[AI-CALL {id}] Creating SIP participant`
- `[AI-CALL {id}] SIP participant created, starting AI agent`
- `[AI-CALL {id}] Connecting to LiveKit`
- `[AI-CALL {id}] Agent connected to room`
- `[AI-CALL {id}] Initializing OpenAI Realtime model`
- `[AI-CALL {id}] Sent session.update with prompt ID`
- `[AI-CALL {id}] AI agent is now active`

## Известные Ограничения

1. **Background Task Lifecycle**: AI agent работает в background task и останавливается при завершении звонка или ошибке
2. **Audio Processing**: Требует правильной настройки audio tracks и sample rate (24kHz)
3. **Prompt ID**: Должен быть валидным и существовать в OpenAI Platform
4. **LiveKit Room**: Автоматически создается для каждого звонка (`ai_call_{call_id}`)

## Следующие Шаги

- [ ] Добавить cleanup для завершенных звонков
- [ ] Реализовать мониторинг audio quality
- [ ] Добавить запись разговоров
- [ ] Интегрировать с Bitrix для сохранения истории звонков
- [ ] Добавить поддержку множественных prompt IDs
