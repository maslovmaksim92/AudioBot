# VasDom AudioBot - Интеллектуальная система управления компанией

## 📋 Описание

VasDom AudioBot - это единая платформа для управления объектами (дома), бригадами, графиками уборок, коммуникацией и отчётностью с интеграцией AI и голосовых технологий.

## 🚀 Быстрый старт

### Локальная разработка

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn server:app --reload --host 0.0.0.0 --port 8001

# Frontend (в новом терминале)
cd frontend
yarn install
yarn start
```

Приложение будет доступно:
- Backend: http://localhost:8001
- Frontend: http://localhost:3000
- API Docs: http://localhost:8001/docs

### Production Deployment

См. раздел Deployment ниже или файл `DEPLOY_INSTRUCTIONS.md`

## 📚 Документация

Полная документация проекта:

- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Архитектура приложения, технологический стек, структура проекта
- **[DEVELOPMENT_GUIDE.md](DEVELOPMENT_GUIDE.md)** - Руководство разработчика, best practices, coding standards
- **[API_DOCUMENTATION.md](API_DOCUMENTATION.md)** - Полная справка по API endpoints
- **[PREVENTION_POLICY.md](PREVENTION_POLICY.md)** - Политика предотвращения дубликатов и регрессии
- **[CLEANUP_REPORT.md](CLEANUP_REPORT.md)** - Отчёт о проверке проекта (11.01.2025)

## ✨ Основные возможности

### 1. Управление домами и графиками уборок
- Фильтры по бригадам, УК, датам
- Календарь с периодичностью уборок
- Интеграция с Bitrix24 CRM
- Детальная информация по каждому объекту

### 2. AI Ассистент
- **Текстовый чат** с Emergent LLM
- **Голосовые разговоры** через OpenAI Realtime API
- **База знаний** с RAG (Retrieval-Augmented Generation)
- **AI задачи** с автоматическим выполнением

### 3. Планёрки и встречи
- Live транскрипция разговоров
- Автоматическое саммари
- Экспорт в текстовые файлы
- История всех встреч

### 4. Телефония
- Исходящие AI-powered звонки через LiveKit
- SIP интеграция (Novofon)
- Автоматические отчёты по телефону
- Запланированные звонки сотрудникам

### 5. Dashboard и аналитика
- Метрики в реальном времени
- Графики по статусам работ
- Фильтры и быстрые пресеты
- Экспорт отчётов

### 6. Telegram уведомления
- Автоматические напоминания
- Отчёты по расписанию
- Взаимодействие с ботом

### 7. Логистика
- Планирование маршрутов (Google Maps)
- Оптимизация поездок бригад
- Расчёт времени и дистанций

## 🏗️ Технологический стек

### Backend
- **FastAPI** - асинхронный веб-фреймворк
- **PostgreSQL** + **pgvector** - БД с векторным поиском
- **APScheduler** - планировщик задач
- **OpenAI API** - AI и голосовые функции
- **LiveKit** - WebRTC и SIP шлюз

### Frontend
- **React 19** - UI библиотека
- **TailwindCSS** - стилизация
- **shadcn/ui** - компоненты
- **React Router** - маршрутизация
- **axios** - HTTP клиент

### Интеграции
- Bitrix24 CRM
- Emergent LLM
- OpenAI (GPT, Realtime, Whisper)
- LiveKit (Voice/Video)
- Telegram Bot API
- Google Maps API

## 📁 Структура проекта

```
/app/
├── backend/                    # FastAPI приложение
│   ├── server.py              # Главный файл
│   ├── requirements.txt       # Python зависимости
│   ├── .env                   # Переменные окружения (не в Git)
│   └── app/                   # Модульная структура
│       ├── config/            # Конфигурация
│       ├── routers/           # API эндпоинты
│       ├── models/            # Pydantic модели
│       ├── services/          # Бизнес-логика
│       ├── tasks/             # Фоновые задачи
│       └── utils/             # Утилиты
│
├── frontend/                   # React приложение
│   ├── src/
│   │   ├── App.js            # Главный компонент
│   │   ├── components/        # React компоненты
│   │   │   ├── Dashboard/
│   │   │   ├── Works/
│   │   │   ├── AIChat/
│   │   │   ├── Meetings/
│   │   │   ├── Training/
│   │   │   └── ui/           # shadcn/ui
│   │   ├── hooks/
│   │   └── lib/
│   ├── package.json
│   └── .env                   # Frontend env vars (не в Git)
│
├── tests/                      # Тесты
├── scripts/                    # Вспомогательные скрипты
├── ARCHITECTURE.md            # Архитектура
├── DEVELOPMENT_GUIDE.md       # Руководство разработчика
├── API_DOCUMENTATION.md       # API документация
├── PREVENTION_POLICY.md       # Политика качества
├── CLEANUP_REPORT.md          # Отчёт о проверке
├── Procfile                   # Heroku/Render
└── README.md                  # Этот файл
```

## 🔧 Переменные окружения

### Backend (backend/.env)
```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/dbname

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

### Frontend (frontend/.env)
```bash
REACT_APP_BACKEND_URL=http://localhost:8001
REACT_APP_FRONTEND_URL=http://localhost:3000
```

## 🚢 Deployment

### Render (рекомендуется)

1. **Backend Service** (Python Web)
   ```yaml
   buildCommand: pip install -r requirements.txt
   startCommand: uvicorn backend.server:app --host 0.0.0.0 --port $PORT
   ```

2. **Frontend Service** (Static Site)
   ```yaml
   buildCommand: cd frontend && yarn install && yarn build
   publishDirectory: frontend/build
   ```

3. Настройте environment variables через Render Dashboard

4. Подключите PostgreSQL database addon

См. подробности в `render.yaml` и `Procfile`

### Heroku

```bash
git push heroku main
```

### Docker (будущее)

```bash
docker-compose up --build
```

## 🧪 Тестирование

### Backend
```bash
cd backend
pytest tests/
```

### Frontend
```bash
cd frontend
yarn test
```

## 📊 API Endpoints

Основные эндпоинты (все начинаются с `/api`):

- **Health**: `GET /api/health` - проверка здоровья
- **Houses**: `GET /api/cleaning/houses` - список домов
- **Dashboard**: `GET /api/dashboard/stats` - статистика
- **AI Chat**: `POST /api/ai/chat` - текстовый чат
- **Voice**: `POST /api/voice/ai-call` - AI звонок
- **Knowledge**: `POST /api/knowledge/upload` - загрузка в БЗ
- **Tasks**: `POST /api/ai-tasks` - создание AI задачи
- **Meetings**: `POST /api/meetings` - начать планёрку

Полная документация: [API_DOCUMENTATION.md](API_DOCUMENTATION.md)

## 🔒 Безопасность

- JWT токены для аутентификации
- Валидация всех входных данных (Pydantic)
- CORS правильно настроен
- Секреты только в environment variables
- Rate limiting на критичные эндпоинты

## 🤝 Contributing

1. Fork проекта
2. Создайте feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit изменения (`git commit -m 'feat: Add AmazingFeature'`)
4. Push в branch (`git push origin feature/AmazingFeature`)
5. Создайте Pull Request

**Обязательно прочитайте:**
- [DEVELOPMENT_GUIDE.md](DEVELOPMENT_GUIDE.md) - стандарты кодирования
- [PREVENTION_POLICY.md](PREVENTION_POLICY.md) - как избежать дубликатов

## 📝 Changelog

### v1.1.0 (Текущая)
- ✅ Полная документация проекта
- ✅ Политика предотвращения дубликатов
- ✅ AI-powered исходящие звонки
- ✅ База знаний с RAG
- ✅ Планировщик AI задач
- ✅ Live транскрипция встреч

### v1.0.0
- ✅ Базовая функциональность
- ✅ Bitrix24 интеграция
- ✅ AI чат
- ✅ Dashboard
- ✅ Управление домами

## 🐛 Известные ограничения

- Логистика требует `GOOGLE_MAPS_API_KEY`
- Bitrix24 может временно отдавать 503 (реализованы retry и кэш)
- LiveKit SIP требует правильной конфигурации trunk

## 📞 Поддержка

- **GitHub Issues**: https://github.com/maslovmaksim92/AudioBot/issues
- **Документация**: См. файлы `*.md` в корне проекта
- **Email**: support@vasdom.ru

## 📄 Лицензия

Proprietary - VasDom © 2025

## 🙏 Благодарности

- FastAPI за отличный фреймворк
- OpenAI за AI и голосовые API
- LiveKit за WebRTC инфраструктуру
- shadcn за UI компоненты
- Bitrix24 за CRM платформу

---

**Статус проекта:** 🟢 Активная разработка

**Последнее обновление:** 11.01.2025

**Версия документации:** 1.0.0
