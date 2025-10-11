# VasDom AudioBot - Архитектура приложения

## Обзор

VasDom AudioBot - это интеллектуальная система управления компанией для организации работы с объектами (дома), бригадами, графиками уборок, коммуникацией и отчётностью.

## Стек технологий

### Backend
- **FastAPI** - современный асинхронный веб-фреймворк
- **PostgreSQL** + **asyncpg** - база данных с асинхронным драйвером
- **pgvector** - векторное расширение для RAG (Retrieval-Augmented Generation)
- **APScheduler** - планировщик задач
- **httpx** - асинхронный HTTP клиент
- **websockets** - WebSocket поддержка для real-time коммуникации
- **PyJWT** - JWT токены для аутентификации
- **python-multipart** - обработка файлов
- **uvicorn** - ASGI сервер

### Frontend
- **React 19** - UI библиотека
- **React Router** - маршрутизация
- **TailwindCSS** - utility-first CSS фреймворк
- **shadcn/ui** - компоненты UI
- **axios** - HTTP клиент
- **react-datepicker** - выбор дат
- **recharts** - графики и визуализация

### Интеграции
- **Bitrix24** - CRM интеграция через Webhook API
- **Emergent LLM** - AI текстовые ответы и аналитика
- **OpenAI Realtime API** - голосовые разговоры и транскрипция
- **LiveKit** - WebRTC и SIP шлюз для телефонии
- **Telegram Bot API** - уведомления
- **Google Maps API** - планирование маршрутов (опционально)

## Структура проекта

```
/app/
├── backend/
│   ├── server.py                 # Главный файл приложения FastAPI
│   ├── requirements.txt          # Python зависимости
│   ├── .env                      # Переменные окружения (не в Git)
│   └── app/                      # Модульная структура приложения
│       ├── __init__.py
│       ├── config/               # Конфигурация
│       │   ├── database.py       # Настройка БД
│       │   └── settings.py       # Общие настройки
│       ├── models/               # Pydantic модели и схемы БД
│       │   ├── user.py
│       │   ├── house.py
│       │   ├── task.py
│       │   └── knowledge.py
│       ├── routers/              # API эндпоинты (модульные роутеры)
│       │   ├── health.py         # Проверка здоровья
│       │   ├── auth.py           # Аутентификация
│       │   ├── houses.py         # Управление домами
│       │   ├── cleaning.py       # Графики уборки
│       │   ├── dashboard.py      # Метрики dashboard
│       │   ├── ai_chat.py        # AI чат
│       │   ├── ai_agent.py       # AI агенты
│       │   ├── ai_knowledge.py   # База знаний (RAG)
│       │   ├── tasks.py          # AI задачи
│       │   ├── meetings.py       # Планёрки (транскрипция)
│       │   ├── employees.py      # Сотрудники
│       │   ├── telegram.py       # Telegram интеграция
│       │   ├── notifications.py  # Уведомления
│       │   └── logs.py           # Логи системы
│       ├── services/             # Бизнес-логика
│       │   ├── bitrix.py         # Bitrix24 сервис
│       │   ├── ai.py             # AI сервис
│       │   ├── voice.py          # Голосовой сервис
│       │   └── scheduler.py      # Планировщик
│       ├── tasks/                # Фоновые задачи
│       │   ├── scheduler.py      # APScheduler
│       │   └── jobs.py           # Периодические задачи
│       └── utils/                # Утилиты
│           ├── logging.py
│           └── helpers.py
│
├── frontend/
│   ├── public/
│   │   └── index.html
│   ├── src/
│   │   ├── App.js                # Главный компонент с роутингом
│   │   ├── App.css
│   │   ├── index.js
│   │   ├── index.css
│   │   ├── components/           # React компоненты
│   │   │   ├── Layout/           # Основной layout
│   │   │   │   ├── Layout.jsx
│   │   │   │   └── Sidebar.jsx
│   │   │   ├── Dashboard/        # Главная панель
│   │   │   │   └── Dashboard.jsx
│   │   │   ├── Works/            # Дома и объекты
│   │   │   │   ├── Works.jsx
│   │   │   │   └── WorksConstructor.jsx
│   │   │   ├── Calendar/         # Календарь уборок
│   │   │   │   └── CleaningCalendar.jsx
│   │   │   ├── AIChat/           # AI чат
│   │   │   │   └── AIChat.jsx
│   │   │   ├── Meetings/         # Планёрки
│   │   │   │   └── Meetings.jsx
│   │   │   ├── LiveConversation/ # Голосовой разговор
│   │   │   │   └── LiveConversation.jsx
│   │   │   ├── Training/         # База знаний
│   │   │   │   └── Training.jsx
│   │   │   ├── Tasks/            # Задачи
│   │   │   │   └── Tasks.jsx
│   │   │   ├── AITasks/          # AI задачи
│   │   │   │   └── AITasks.jsx
│   │   │   ├── Employees/        # Сотрудники
│   │   │   │   └── Employees.jsx
│   │   │   ├── Sales/            # Воронка продаж
│   │   │   │   └── SalesFunnel.jsx
│   │   │   ├── Logistics/        # Логистика
│   │   │   │   └── Logistics.jsx
│   │   │   ├── Logs/             # Логи
│   │   │   │   └── Logs.jsx
│   │   │   ├── AgentBuilder/     # Конструктор агентов
│   │   │   │   └── AgentBuilder.jsx
│   │   │   ├── FunctionStudio/   # Студия функций
│   │   │   │   └── FunctionStudio.jsx
│   │   │   ├── AIImprovement/    # AI улучшения
│   │   │   │   └── AIImprovementModal.jsx
│   │   │   └── ui/               # shadcn/ui компоненты
│   │   │       ├── button.jsx
│   │   │       ├── card.jsx
│   │   │       ├── input.jsx
│   │   │       ├── dialog.jsx
│   │   │       ├── toast.jsx
│   │   │       └── ... (50+ компонентов)
│   │   ├── hooks/                # Custom React hooks
│   │   │   └── use-toast.js
│   │   └── lib/                  # Утилиты
│   │       └── utils.js
│   ├── package.json
│   ├── tailwind.config.js
│   ├── craco.config.js
│   ├── jsconfig.json
│   └── .env                      # Frontend env vars (не в Git)
│
├── scripts/                      # Вспомогательные скрипты
│   ├── setup.sh                  # Инициализация проекта
│   └── deploy.sh                 # Деплой скрипт
│
├── tests/                        # Тесты
│   ├── __init__.py
│   ├── test_api.py
│   └── test_integrations.py
│
├── .gitignore
├── .gitconfig
├── README.md                     # Основная документация
├── ARCHITECTURE.md              # Этот файл
├── DEVELOPMENT_GUIDE.md         # Руководство разработчика
├── API_DOCUMENTATION.md         # API документация
├── PREVENTION_POLICY.md         # Политика предотвращения дубликатов
├── Procfile                     # Heroku/Render deployment
├── render.yaml                  # Render конфигурация
└── requirements.txt             # Root requirements (ссылка на backend)
```

## Архитектурные принципы

### 1. Модульность
- Backend разделён на роутеры по функциональным областям
- Frontend компоненты изолированы по фичам
- Каждый модуль имеет свою ответственность

### 2. Асинхронность
- Все I/O операции асинхронные (async/await)
- Используется asyncpg для БД, httpx для HTTP
- WebSocket соединения для real-time функций

### 3. Типизация
- Pydantic модели для валидации данных
- Строгая типизация на backend
- PropTypes или TypeScript (опционально) на frontend

### 4. Безопасность
- JWT токены для аутентификации
- CORS правильно настроен
- Секреты только в переменных окружения
- Валидация всех входных данных

### 5. Масштабируемость
- Stateless backend (можно масштабировать горизонтально)
- Кэширование частых запросов
- Оптимизация запросов к БД
- CDN для статики frontend

## Потоки данных

### 1. Синхронизация с Bitrix24
```
Bitrix24 CRM
    ↓ (Webhook API)
Backend API (/api/cleaning/sync)
    ↓
PostgreSQL (houses, deals)
    ↓
Frontend (Dashboard, Works)
```

### 2. AI Чат
```
User Input (Frontend)
    ↓ (POST /api/ai/chat)
Backend
    ↓
Emergent LLM / OpenAI
    ↓
Response → Frontend
```

### 3. Голосовые вызовы
```
Backend (/api/voice/ai-call)
    ↓
LiveKit SIP Gateway
    ↓
Novofon/PSTN → Телефон пользователя
    ↑↓ (WebRTC)
OpenAI Realtime API
    ↓
Транскрипция + AI ответы
```

### 4. База знаний (RAG)
```
User Upload (файл)
    ↓ (POST /api/knowledge/upload)
Extract Text
    ↓
Generate Embeddings (OpenAI)
    ↓
Store in PostgreSQL + pgvector
    ↓
Search (/api/knowledge/search)
```

### 5. Планировщик задач
```
APScheduler (Backend)
    ↓ (Cron / Interval)
Execute Task
    ↓
Telegram Notification
    или
Update Database
```

## Переменные окружения

### Backend (.env)
```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/dbname
NEON_DATABASE_URL=postgresql+asyncpg://...  # Альтернатива

# Integrations
BITRIX24_WEBHOOK_URL=https://your-bitrix24.ru/rest/...
EMERGENT_LLM_KEY=your_emergent_key
OPENAI_API_KEY=sk-...
JWT_SECRET=your_secret_key

# LiveKit (Voice)
LIVEKIT_URL=wss://your-livekit.com
LIVEKIT_API_KEY=...
LIVEKIT_API_SECRET=...
LIVEKIT_SIP_TRUNK_ID=...
NOVOFON_CALLER_ID=+79991234567

# Optional
TELEGRAM_BOT_TOKEN=...
GOOGLE_MAPS_API_KEY=...
CORS_ORIGINS=*
```

### Frontend (.env)
```bash
REACT_APP_BACKEND_URL=http://localhost:8001
# или production:
REACT_APP_BACKEND_URL=https://your-backend.onrender.com

REACT_APP_FRONTEND_URL=http://localhost:3000
# или production:
REACT_APP_FRONTEND_URL=https://your-frontend.onrender.com
```

## База данных

### Схема
- **users** - пользователи системы
- **employees** - сотрудники компании
- **houses** - объекты (дома)
- **cleaning_schedules** - графики уборок
- **tasks** - задачи сотрудников
- **ai_tasks** - AI задачи с расписанием
- **knowledge_base** - база знаний (RAG)
- **meetings** - планёрки (записи)
- **logs** - логи системы

### Миграции
- Используется Alembic или ручные SQL скрипты
- Все datetime поля с timezone aware (timezone.utc)
- ID полей - UUID (не ObjectId)

## Deployment

### Render (Production)
1. **Backend Service** (Python Web)
   - Build: `pip install -r requirements.txt`
   - Start: `uvicorn backend.server:app --host 0.0.0.0 --port $PORT`
   - Env vars: все переменные выше

2. **Frontend Service** (Static Site)
   - Build: `cd frontend && yarn install && yarn build`
   - Publish: `frontend/build`

### Локальная разработка
```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn server:app --reload --host 0.0.0.0 --port 8001

# Frontend (другой терминал)
cd frontend
yarn install
yarn start
```

## Мониторинг и логирование

- **Backend**: Python logging с уровнем INFO
- **Frontend**: Console.log для разработки, Sentry для production
- **Health Check**: `/api/health` эндпоинт
- **Metrics**: `/api/dashboard/stats` для метрик

## Безопасность

1. **Аутентификация**: JWT токены
2. **Авторизация**: Role-based (admin, manager, worker)
3. **Валидация**: Pydantic модели на backend
4. **CORS**: Настроен для разрешённых origins
5. **Rate Limiting**: На критичные эндпоинты
6. **Secrets**: Только в env vars, никогда в коде

## Производительность

1. **Кэширование**: Bitrix24 ответы (5-10 мин)
2. **Database indexing**: На часто запрашиваемые поля
3. **Lazy loading**: Компоненты и данные
4. **Code splitting**: React.lazy() для больших компонентов
5. **CDN**: Для статических ассетов

## Расширения и будущие улучшения

- [ ] TypeScript миграция frontend
- [ ] Полное покрытие тестами
- [ ] CI/CD pipeline (GitHub Actions)
- [ ] Docker контейнеризация
- [ ] Kubernetes для масштабирования
- [ ] Redis для кэширования
- [ ] Elasticsearch для полнотекстового поиска
- [ ] GraphQL как альтернатива REST