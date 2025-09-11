# VasDom AudioBot - AI-система управления клининговой компанией

🤖 **Интеллектуальный помощник для управления 348 многоквартирными домами, 82 сотрудниками и 6 бригадами в Калуге**

[![FastAPI](https://img.shields.io/badge/FastAPI-0.110.1-009688.svg?style=flat&logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18.2.0-61DAFB.svg?style=flat&logo=react)](https://reactjs.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-336791.svg?style=flat&logo=postgresql)](https://postgresql.org)
[![Render](https://img.shields.io/badge/Deployed%20on-Render-46E3B7.svg?style=flat)](https://render.com)

## 📊 Назначение проекта

VasDom AudioBot - это комплексная система управления клининговой компанией, которая автоматизирует:
- **Управление CRM**: 348 домов из Bitrix24 с полной интеграцией
- **Планирование работ**: 6 бригад по районам Калуги с оптимизацией маршрутов
- **AI-помощник**: GPT-4 mini через Emergent LLM для ответов на вопросы
- **Голосовые функции**: Диктофон для планерок, живой голосовой чат с AI
- **Telegram-бот**: Уведомления сотрудникам, создание задач в Bitrix24
- **Контроль качества**: Фото-отчеты, GPS-отметки, автоматическая оценка

## 🏗️ Архитектура

### Backend (FastAPI)
```
backend/app/
├── config/           # Конфигурация и настройки
│   ├── settings.py   # Переменные окружения и CORS
│   └── database.py   # PostgreSQL подключение
├── models/           # Данные и схемы
│   ├── schemas.py    # Pydantic модели для API
│   ├── telegram.py   # Telegram webhook модели
│   └── database.py   # SQLAlchemy ORM модели
├── services/         # Бизнес-логика
│   ├── ai_service.py     # GPT-4 mini + Emergent LLM
│   ├── bitrix_service.py # Интеграция с Bitrix24 CRM
│   └── telegram_service.py # Telegram Bot API
├── routers/          # API endpoints
│   ├── dashboard.py  # Статистика и дашборд
│   ├── telegram.py   # Webhook + валидация данных
│   ├── voice.py      # Голосовой AI чат
│   ├── meetings.py   # Планерки и диктофон
│   ├── cleaning.py   # Управление домами/работами
│   └── logs.py       # Системные логи
├── security.py       # Аутентификация для API
└── tests/           # Unit тесты
```

### Frontend (React + Tailwind)
```
frontend/src/
├── App.js           # Главный компонент с роутингом
├── components/      # React компоненты для разделов
└── assets/         # Статические файлы
```

### База данных (PostgreSQL)
- `voice_logs` - История AI взаимодействий для самообучения
- `meetings` - Планерки с транскрипцией и задачами
- `ai_tasks` - Календарь задач с AI-менеджером

## 🚀 Зависимости и версии

### Python (Backend)
- **FastAPI 0.110.1** - Web framework
- **SQLAlchemy 2.0+** - ORM для PostgreSQL
- **Databases** - Async database support
- **Alembic 1.13+** - Database migrations
- **Pydantic 2.6+** - Data validation
- **httpx** - HTTP client для интеграций
- **emergentintegrations** - Emergent LLM доступ

### Node.js (Frontend)
- **React 18.2+**
- **Tailwind CSS** - Styling
- **Axios** - HTTP client

### Внешние сервисы
- **Bitrix24** - CRM система (348 домов)
- **Telegram Bot API** - Уведомления сотрудникам
- **Emergent LLM** - GPT-4 mini доступ
- **PostgreSQL** - Основная база данных

## ⚙️ Настройка окружения

### 1. Переменные окружения

#### Backend (.env)
```bash
# Database
DATABASE_URL=postgresql://user:password@host:port/database

# Bitrix24 CRM
BITRIX24_WEBHOOK_URL=https://your-domain.bitrix24.ru/rest/1/webhook_code/

# Telegram Bot
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_WEBHOOK_URL=https://your-app.com/api/telegram/webhook

# AI
EMERGENT_LLM_KEY=your_emergent_key

# Security
API_SECRET_KEY=your-secret-key
REQUIRE_AUTH_FOR_PUBLIC_API=false

# CORS (список доменов через запятую)
CORS_ORIGINS=https://audiobot-qci2.onrender.com,https://your-frontend.com

# Frontend Redirects
FRONTEND_DASHBOARD_URL=https://your-frontend.com
```

#### Frontend (.env)
```bash
REACT_APP_BACKEND_URL=https://your-backend.com
```

### 2. Установка зависимостей

#### Backend
```bash
cd backend
pip install -r requirements.txt
```

#### Frontend
```bash
cd frontend
yarn install
```

## 🗄️ Миграции базы данных

Система использует **Alembic** для управления схемой PostgreSQL:

```bash
cd backend

# Создать новую миграцию
alembic revision --autogenerate -m "Description"

# Применить миграции
alembic upgrade head

# Откатить миграцию
alembic downgrade -1

# История миграций
alembic history --verbose
```

**⚠️ Важно**: `Base.metadata.create_all` удален из инициализации - используйте только миграции!

## 🏃‍♂️ Запуск сервера

### Локальная разработка

#### Backend
```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

#### Frontend
```bash
cd frontend
yarn start
# Доступен на http://localhost:3000
```

### Production (Render)
- Backend автоматически запускается через `Procfile`: `uvicorn app.main:app`
- Frontend собирается и деплоится статически

## 🧪 Запуск тестов

```bash
cd backend

# Все тесты
pytest

# Конкретный модуль
pytest app/tests/test_telegram.py -v

# С покрытием
pytest --cov=app --cov-report=html
```

## 🔌 Внешние сервисы

### Bitrix24 CRM
- **Воронка**: "Уборка подъездов" (CATEGORY_ID=2)
- **Поля**: ID, TITLE, STAGE_ID, DATE_CREATE, OPPORTUNITY
- **Лимит**: 600 домов через batch-загрузку

### Telegram Bot
- **Webhooks**: `/api/telegram/webhook` с валидацией
- **Команды**: `/задача` для создания задач в Bitrix24
- **Уведомления**: Ежедневные отчеты бригадам

### PostgreSQL
- **Cloud-ready**: Heroku, Render, AWS RDS
- **Async**: databases + asyncpg driver
- **Migrations**: Alembic для схемы

## 📱 API Endpoints

### Основные
- `GET /` - Редирект на React дашборд
- `GET /api/dashboard` - Статистика (348 домов, 82 сотрудника)
- `GET /api/health` - Проверка состояния системы

### CRM и работы
- `GET /api/bitrix24/test` - Тест интеграции с Bitrix24
- `GET /api/cleaning/houses` - Список всех домов из CRM

### AI и голос
- `POST /api/voice/process` - Голосовой AI чат 🔒
- `GET /api/logs` - История AI взаимодействий

### Планерки
- `POST /api/meetings/start-recording` - Начать запись планерки
- `POST /api/meetings/stop-recording` - Остановить и обработать
- `GET /api/meetings` - История планерок

### Telegram
- `POST /api/telegram/webhook` - Webhook для бота 🔒
- `GET /api/telegram/status` - Статус подключения бота

🔒 = Требует аутентификации (при `REQUIRE_AUTH_FOR_PUBLIC_API=true`)

## 🔒 Security

### Аутентификация
- **Bearer Token**: `Authorization: Bearer your_api_key`
- **Custom Header**: `X-API-Key: your_api_key`
- **Настройка**: `REQUIRE_AUTH_FOR_PUBLIC_API` environment variable

### CORS Policy
- **Конфигурация**: Читается из `CORS_ORIGINS` environment variable
- **Формат**: Список доменов через запятую
- **Дефолт**: Безопасные production домены

### Telegram Webhook
- **Валидация**: Pydantic модели для всех данных
- **Проверки**: Обязательные поля message, chat_id, text
- **Errors**: HTTPException при некорректных данных

## 📈 Мониторинг и логи

### Системные логи
- **Endpoint**: `/api/logs`
- **Формат**: JSON с временными метками
- **Хранение**: PostgreSQL + File (cloud-friendly)

### AI Самообучение
- **Таблица**: `voice_logs`
- **Данные**: Все AI взаимодействия для улучшения ответов
- **Контекст**: Пользователь, сессия, временные метки

### Ошибки Telegram
- **Логирование**: Все неудачные отправки сообщений
- **Возврат**: `status: "failed"` с деталями ошибки
- **Retry**: Автоматические повторы при временных сбоях

## 🏠 Данные компании

### География работы
- **Центральный район**: Пролетарская, Баррикад, Ленина (1 бригада)
- **Никитинский район**: Чижевского, Никитина, Телевизионная (2 бригада)  
- **Жилетово**: Молодежная, Широкая (3 бригада)
- **Северный район**: Жукова, Хрустальная, Гвардейская (4 бригада)
- **Пригород**: Кондрово, Пушкина (5 бригада)
- **Окраины**: Остальные районы (6 бригада)

### Статистика
- **🏠 Домов**: 348 (только из CRM Bitrix24)
- **👥 Сотрудников**: 82 человека в 6 бригадах
- **🚪 Подъездов**: ~1,044 (3 на дом)
- **🏠 Квартир**: ~26,100 (75 на дом)
- **📏 Этажей**: ~1,740 (5 на дом)

## 🔄 CI/CD и деплой

### Render.com
```yaml
# render.yaml
services:
  - type: web
    name: vasdom-audiobot
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

### Environment Variables
Все секретные данные через Render Environment Variables:
- Database credentials
- API keys (Bitrix24, Telegram, Emergent)
- CORS origins для production

## 🤝 Contribute

1. **Fork** репозиторий
2. **Feature branch**: `git checkout -b feature/amazing-feature`
3. **Commit**: `git commit -m 'Add amazing feature'`
4. **Push**: `git push origin feature/amazing-feature`
5. **Pull Request**

### Code Style
- **Backend**: Black + isort для Python
- **Frontend**: Prettier для JS/CSS
- **Tests**: Обязательно для новых API endpoints

---

## 📞 Support

- **GitHub Issues**: [Create Issue](https://github.com/maslovmaksim92/AudioBot/issues)
- **Telegram**: @vasdom_support
- **Email**: support@vasdom.ru

---

**🚀 Сделано с ❤️ для VasDom - лучшей клининговой компании Калуги!**
