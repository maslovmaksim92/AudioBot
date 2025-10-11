# VasDom AudioBot - Backend

FastAPI приложение с PostgreSQL, OpenAI, LiveKit, Bitrix24.

## Быстрый старт

```bash
# Активировать venv
source venv/bin/activate

# Установить зависимости
pip install -r requirements.txt

# Запустить
uvicorn server:app --reload --host 0.0.0.0 --port 8001
```

## Структура

```
backend/
├── server.py              # Главный файл FastAPI
├── requirements.txt       # 165 пакетов
├── .env                   # Переменные окружения (не в Git!)
└── app/
    ├── config/
    │   └── database.py    # PostgreSQL + pgvector
    ├── routers/           # 14 модульных роутеров
    │   ├── health.py
    │   ├── auth.py
    │   ├── houses.py
    │   ├── cleaning.py
    │   ├── dashboard.py
    │   ├── ai_chat.py
    │   ├── ai_agent.py
    │   ├── ai_knowledge.py
    │   ├── tasks.py
    │   ├── meetings.py
    │   ├── employees.py
    │   ├── telegram.py
    │   ├── notifications.py
    │   └── logs.py
    ├── services/          # Бизнес-логика
    │   ├── bitrix.py
    │   ├── ai.py
    │   └── voice.py
    ├── models/            # Pydantic модели
    ├── tasks/             # APScheduler
    │   └── scheduler.py
    └── utils/

```

## API

- http://localhost:8001/api/health
- http://localhost:8001/docs (Swagger)
- http://localhost:8001/redoc

## .env обязательные переменные

```bash
DATABASE_URL=postgresql://...
OPENAI_API_KEY=sk-...
JWT_SECRET=secret
CORS_ORIGINS=*
```

## Логи

```bash
tail -f /var/log/supervisor/backend.err.log
```

## Документация

См. корневой `/app/README.md` и `/app/SETUP_GUIDE.md`