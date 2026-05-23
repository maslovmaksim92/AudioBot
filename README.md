# VasDom AudioBot

ERP-платформа для клининговой компании: операционное управление (дома,
бригады, календарь уборок), финансы, AI-ассистент с базой знаний по
компании, интеграции с Bitrix24, Telegram и голосовой телефонией
(LiveKit SIP + Novofon).

**Стек:** FastAPI · PostgreSQL + pgvector · React (CRA + Tailwind/shadcn) ·
OpenAI · LiveKit · APScheduler · Alembic.

---

## Структура

```
.
├── backend/          FastAPI-приложение (точка входа: backend/server.py)
│   ├── app/          роутеры, сервисы, модели, миграции (alembic)
│   ├── alembic/      Alembic-миграции
│   └── requirements.txt
├── frontend/         React (Create React App + Craco)
├── archive/          архив исторических артефактов (отчёты, разовые скрипты, дампы) — не используется в рантайме
└── .env.example      шаблон переменных окружения
```

## Быстрый старт (локально)

### 1. Зависимости

```bash
# Backend
cd backend
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Frontend
cd ../frontend
yarn install
```

### 2. PostgreSQL + pgvector

```bash
sudo apt install postgresql-16 postgresql-16-pgvector
sudo -u postgres createuser -P audiobot     # задайте пароль
sudo -u postgres createdb -O audiobot audiobot
sudo -u postgres psql -d audiobot -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

### 3. Конфигурация

```bash
cp .env.example .env
# Отредактируйте .env — как минимум DATABASE_URL и OPENAI_API_KEY
```

### 4. Миграции

```bash
cd backend
alembic upgrade head
```

### 5. Запуск

```bash
# Backend
cd backend
uvicorn server:app --host 127.0.0.1 --port 8011

# Frontend (dev)
cd frontend
yarn start
```

## Основные модули

- **Дашборд** — графики и сводки по операциям.
- **Дома / бригады / календарь** — операционное планирование клининга.
- **AI-чат + база знаний** (`ai_knowledge`, pgvector) — ассистент по
  данным компании. В работе два режима: для сотрудников (полный доступ)
  и для клиентов (ограниченный).
- **AI-агенты** — конструктор агентов, сводки звонков, AI-задачи.
- **Финансы** — транзакции, выручка, долги, бюджет план-факт.
- **Интеграции** — Bitrix24 (CRM, звонки, сделки), Telegram (боты,
  фотоотчёты), LiveKit + Novofon (исходящий SIP-обзвон).

## Деплой

Основное развёртывание — на VPS под доменом `https://ai.vd40.ru`.
Nginx проксирует `/api` на uvicorn (127.0.0.1:8011) и отдаёт собранный
фронтенд из `frontend/build`. Подробности — в `docs/DEPLOY.md` (после
завершения переноса).
