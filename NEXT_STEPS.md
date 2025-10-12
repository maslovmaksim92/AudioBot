# 📋 Следующие шаги для завершения

## ✅ Что уже сделано:

### Фаза 1: Баги (ИСПРАВЛЕНО)
- ✅ Баг месяца
- ✅ Баг периодичности  
- ✅ Баг КПИ бригад

### Фаза 2A: Telegram бот (РЕАЛИЗОВАНО)
- ✅ `photo_caption_service.py` - AI подписи
- ✅ `telegram_cleaning_bot.py` - бот для бригад
- ✅ Webhook обработка фото и callback

### UI улучшения:
- ✅ Меню очищено от дубликатов
- ✅ Убрано: "Живой разговор", "Логистика", "AI Задачи", "Мониторинг" из корневого меню
- ✅ Dashboard грузит данные корректно

---

## 🔄 Что нужно доработать:

### 1. Перенести компоненты во вкладки

#### Агенты (главный раздел `/agents`):
Добавить вкладки:
- **Агенты** - список/создание агентов (AgentBuilder)
- **Мониторинг** - AgentDashboard  
- **AI Задачи** - AITasks компонент
- **Telegram бот** - настройка бота для фото (новый)

#### Дома (`/works`):
Добавить вкладки:
- **Список домов** - текущая Works
- **Календарь** - календарь уборок
- **KPI Бригад** - BrigadeStats
- **Логистика** - Logistics компонент

#### AI Чат (`/ai`):
Добавить вкладки:
- **Чат** - текущий AIChat
- **Живой разговор** - LiveConversation компонент
- **История** - история диалогов

### 2. AI Chat синхронизация (Фаза 3)

**Backend:**
```sql
CREATE TABLE chat_messages (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    platform VARCHAR(20), -- 'web' or 'telegram'
    content TEXT,
    role VARCHAR(20), -- 'user' or 'assistant'
    created_at TIMESTAMP,
    telegram_message_id BIGINT,
    brain_metadata JSONB
);
```

**Создать:**
- `backend/app/services/chat_sync_service.py` - синхронизация
- `backend/app/routers/chat.py` - WebSocket endpoint
- `frontend/src/services/chatWebSocket.js` - WS клиент
- Обновить AIChat.js для WS

### 3. Ответы на рекламации

Добавить в `brain_resolvers.py`:
```python
async def resolve_complaint(text: str, ent: Dict) -> Dict:
    """
    Обработка рекламаций типа "не было уборки 9 числа"
    Возвращает ссылки на фото и график
    """
    address = extract_address(text)
    date = extract_date(text)
    
    # Найти фото на эту дату
    photos = await get_photos_by_address_date(address, date)
    
    return {
        "answer": f"Уборка была проведена {date}",
        "photos": photos,
        "schedule": "..."
    }
```

### 4. Добавить функцию в Агенты

В AgentBuilder добавить:
- Новый action type: "telegram_photo_bot"
- Параметры: список домов, бригада
- Триггер: расписание или ручной запуск

---

## 📦 Подготовка к GitHub Push

### Файлы для коммита:

**Backend (изменено):**
- `app/services/brain_intents.py`
- `app/services/brain_resolvers.py`
- `app/services/bitrix24_service.py`
- `app/routers/telegram_webhook.py`

**Backend (новые):**
- `app/services/photo_caption_service.py`
- `app/services/telegram_cleaning_bot.py`

**Frontend (изменено):**
- `src/components/Works/BrigadeStats.js`
- `src/components/Dashboard/Dashboard.js`
- `src/components/Layout/Layout.js`

### Команды для push:

```bash
cd /app

# Добавить все изменения
git add backend/app/services/brain_intents.py
git add backend/app/services/brain_resolvers.py
git add backend/app/services/bitrix24_service.py
git add backend/app/services/photo_caption_service.py
git add backend/app/services/telegram_cleaning_bot.py
git add backend/app/routers/telegram_webhook.py
git add frontend/src/components/Works/BrigadeStats.js
git add frontend/src/components/Dashboard/Dashboard.js
git add frontend/src/components/Layout/Layout.js

# Коммит
git commit -m "
feat: Phase 1 & 2A implementation

Phase 1 - Critical Bugs Fixed:
- Fixed month detection with fallback to current month
- Implemented cleaning type periodicity calculation (3 types)
- Added date selector for Brigade KPI with auto-recalculation

Phase 2A - Telegram Bot for Brigades:
- Created photo_caption_service.py for AI captions via GPT-3.5
- Implemented telegram_cleaning_bot.py with full workflow
- Added /start command with inline keyboard for house selection
- Added photo upload handler and /done command
- Test mode: sends photos back to user (not to group)
- Integrated with telegram_webhook.py

UI Improvements:
- Cleaned up navigation menu (removed duplicates)
- Fixed Dashboard data loading
- Added month selector in Brigade KPI
"

# Push в main
git push origin main
```

---

## 🚀 Deployment на Render

### Проверить перед деплоем:

1. **Environment Variables на Render:**
```
DATABASE_URL=postgresql://...
OPENAI_API_KEY=sk-...
TELEGRAM_BOT_TOKEN=...
LIVEKIT_URL=...
JWT_SECRET=...
```

2. **Dependencies:**
```bash
# Backend
cat backend/requirements.txt | grep -E "openai|httpx|telegram"

# Frontend  
cat frontend/package.json | grep -E "recharts|reactflow|datepicker"
```

3. **Build Commands:**
- Backend: `pip install -r backend/requirements.txt`
- Frontend: `cd frontend && yarn install && yarn build`

4. **Start Commands:**
- Backend: `uvicorn backend.server:app --host 0.0.0.0 --port 8001`
- Frontend: `cd frontend && yarn start`

### После деплоя:

1. **Установить Telegram webhook:**
```bash
curl -X POST https://your-app.onrender.com/api/telegram-webhook/set
```

2. **Протестировать бота:**
- Откр your Telegram бот
- `/start` - должен показать список домов
- Отправить фото
- `/done` - должен отправить фото с AI подписью

3. **Проверить Dashboard:**
- https://your-app.onrender.com
- Дома грузятся
- КПИ бригад работает с селектором месяца

---

## 📊 Метрики успеха:

✅ Все 3 бага исправлены  
✅ Telegram бот работает в тестовом режиме  
✅ Dashboard загружает данные  
✅ UI меню очищено  
⏳ AI Chat синхронизация (Фаза 3)  
⏳ Вкладки перенесены в подразделы  
⏳ Production интеграция (БД, группа, Bitrix24)  

---

## 🔗 Документация:

- `/app/PHASE1_BUGFIX_REPORT.md`
- `/app/PHASE2_TELEGRAM_BOT_REPORT.md`
- `/app/IMPLEMENTATION_PLAN.md`
- `/app/CLEANUP_REPORT.md`
