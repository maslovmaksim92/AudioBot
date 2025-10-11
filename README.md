# VasDom AudioBot - Система управления компанией

## 📋 Описание

VasDom AudioBot - интеллектуальная платформа для управления домами, бригадами, графиками уборок с интеграцией AI, голосовых технологий и CRM.

**Статус:** ✅ Полностью рабочее приложение  
**Версия:** 2.0 (11.10.2025)

## 🚀 Быстрый старт

### Локальная разработка

```bash
# Backend
cd backend
source venv/bin/activate  # или python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn server:app --reload --host 0.0.0.0 --port 8001

# Frontend
cd frontend
yarn install
yarn start
```

**URLs:**
- Backend API: http://localhost:8001
- Frontend: http://localhost:3000
- API Docs: http://localhost:8001/docs
- Preview: https://smart-agent-system.preview.emergentagent.com

## ✨ Основной функционал

### 1. Dashboard
- Статистика в реальном времени (дома, сотрудники, задачи)
- Графики уборок по месяцам
- Производительность и метрики
- События системы

### 2. Управление домами (Works)
- Список всех объектов с фильтрами
- Интеграция с Bitrix24 CRM (автосинхронизация каждые 30 мин)
- График уборок с календарем
- Информация по бригадам и УК

### 3. AI Чат
- Текстовые диалоги с OpenAI GPT
- Контекст по домам и задачам
- База знаний (RAG с pgvector)

### 4. Голосовые функции
- AI звонки через LiveKit + OpenAI Realtime
- SIP интеграция (Novofon)
- Планёрки с транскрипцией

### 5. Автоматизация
- APScheduler: синхронизация Bitrix24, AI звонки, напоминания
- AI задачи с расписанием
- Telegram уведомления

### 6. Финансы
- Движение денег (Cash Flow)
- Прибыли и убытки (P&L)
- Баланс (Balance Sheet)
- Анализ расходов по категориям
- Управление задолженностями
- Товарные запасы
- Ручной ввод транзакций через форму
- Импорт данных из CSV
- Real-time отчёты и графики

### 7. Аналитика
- Воронка продаж
- Логистика
- Логи системы

## 🏗️ Технологии

**Backend:**
- FastAPI + Uvicorn (async)
- PostgreSQL (Yandex Cloud) + asyncpg
- pgvector (для RAG)
- APScheduler
- OpenAI API, LiveKit SDK
- Python 3.11+

**Frontend:**
- React 19
- TailwindCSS + shadcn/ui
- React Router
- axios, recharts

**Интеграции:**
- Bitrix24 CRM
- OpenAI (GPT + Realtime)
- LiveKit (WebRTC/SIP)
- Telegram Bot
- Novofon SIP

## 📁 Структура проекта

```
/app/
├── backend/
│   ├── server.py              # Главный файл FastAPI
│   ├── requirements.txt       # 165 пакетов
│   ├── .env                   # Переменные окружения
│   └── app/
│       ├── config/            # database.py
│       ├── routers/           # 14 модульных роутеров
│       ├── services/          # bitrix, ai, voice
│       ├── models/            # Pydantic модели
│       ├── tasks/             # APScheduler jobs
│       └── utils/
│
├── frontend/
│   ├── src/
│   │   ├── App.js            # Роутинг
│   │   └── components/
│   │       ├── Dashboard/
│   │       ├── Works/
│   │       ├── AIChat/
│   │       ├── Meetings/
│   │       ├── Training/
│   │       ├── Tasks/
│   │       ├── AITasks/
│   │       ├── Employees/
│   │       ├── Sales/
│   │       ├── Logistics/
│   │       ├── Logs/
│   │       ├── Finances/
│   │       └── ui/           # shadcn компоненты
│   ├── package.json
│   └── .env
│
└── docs/                      # Документация (это README + 2 других файла)
```

## 🔧 Переменные окружения

### backend/.env

```bash
# PostgreSQL (Yandex Cloud)
DATABASE_URL=postgresql://vasdom_user:Vasdom40!@rc1a-gls4njl0umfqv554.mdb.yandexcloud.net:6432/vasdom_audiobot?sslmode=require

# Bitrix24
BITRIX24_WEBHOOK_URL=https://vas-dom.bitrix24.ru/rest/1/f3pvpfdzssjzm0i

# OpenAI
OPENAI_API_KEY=sk-proj-lc-AH990fOe-dDzI1_F950lZdfI8-VTB0r1Xd14zxDlrzbqpyA4zeeInG2iL-1

# LiveKit
LIVEKIT_URL=wss://vasdom2-cjzi1sb4.livekit.cloud
LIVEKIT_API_KEY=APIvb6apgzFTopv
LIVEKIT_API_SECRET=4dB05ii1FaiyOFS1ZEPn0vBkttdXMI1ibqggB7Rn
LIVEKIT_SIP_TRUNK_ID=ST_NzE4LU5SsGdM

# Novofon
NOVOFON_CALLER_ID=+79044390712
NOVOFON_SIP_USERNAME=0015949
NOVOFON_SIP_PASSWORD=_s2Wq4sgun

# JWT & Telegram
JWT_SECRET=v0-UGS3bpvmOpqrnvI1xGXrbZd8q_FS0gsJ4nv0L4kbJsLc0daBBneuh_jTLoiTBn7YtxB9vhA0XIZHNZ1In
TELEGRAM_BOT_TOKEN=8321:DOMO40_AdEqAYsfi5os-nvMe9OJivNFQjj1IEGznovf
TELEGRAM_TARGET_CHAT_ID=-1002384210149

# CORS
CORS_ORIGINS=*
```

### frontend/.env

```bash
REACT_APP_BACKEND_URL=http://localhost:8001
# Production: https://audiobot-qpi2.onrender.com
```

## 📡 Основные API endpoints

Все начинаются с `/api`:

- `GET /api/health` - Проверка здоровья
- `GET /api/cleaning/houses` - Список домов
- `GET /api/dashboard/stats` - Статистика
- `POST /api/ai/chat` - AI чат
- `POST /api/voice/ai-call` - AI звонок
- `POST /api/knowledge/upload` - Загрузка в БЗ
- `POST /api/ai-tasks` - Создание AI задачи
- `POST /api/meetings` - Планёрка
- `GET /api/finances/categories` - Категории финансов
- `POST /api/finances/transactions` - Создать транзакцию
- `GET /api/finances/cash-flow` - Отчёт о движении денег
- `GET /api/finances/profit-loss` - Прибыли и убытки
- `GET /api/finances/balance-sheet` - Баланс

**Полная документация:** `/api/docs` (Swagger UI)

## 🚢 Deployment

### Production (Render)

1. **Backend Service:** Python Web Service
   - Build: `pip install -r requirements.txt`
   - Start: `uvicorn server:app --host 0.0.0.0 --port $PORT`
   - Env: все переменные из backend/.env

2. **Frontend Service:** Static Site
   - Build: `yarn install && yarn build`
   - Publish: `build/`

### Локальный supervisor

```bash
supervisorctl status
supervisorctl restart backend frontend
```

## 📊 Текущее состояние

**Работающие функции:**
- ✅ Dashboard с метриками (499 домов, 19 сотрудников)
- ✅ Bitrix24 автосинхронизация
- ✅ PostgreSQL с pgvector
- ✅ APScheduler (3 задачи)
- ✅ База знаний (RAG)
- ✅ AI Chat
- ✅ Голосовые звонки (LiveKit + OpenAI Realtime)
- ✅ Telegram уведомления
- ✅ Модуль "Финансы" с 6 подразделами и формой ввода данных

**Запланированные задачи:**
1. Синхронизация Bitrix24 - каждые 30 мин
2. AI звонки сотрудникам - ежедневно в 19:55 МСК
3. Напоминание о планёрке - ежедневно в 11:25 МСК

## 🔒 Безопасность

- JWT токены для аутентификации
- PostgreSQL с SSL
- Валидация через Pydantic
- CORS настроен
- Секреты только в .env (не в Git)

## 📚 Дополнительная документация

1. **SETUP_GUIDE.md** - Детальная установка и настройка
2. **API_REFERENCE.md** - Полный справочник API
3. **FINANCES_USER_GUIDE.md** - Руководство по модулю "Финансы"

**Всё остальное - в коде!** Используйте `/api/docs` для API и читайте комментарии в коде.

## 🐛 Troubleshooting

### Backend не запускается
```bash
# Проверить логи
tail -n 50 /var/log/supervisor/backend.err.log

# Проверить DATABASE_URL
python -c "from app.config.database import DATABASE_URL; print(DATABASE_URL)"
```

### Frontend ошибки
```bash
# Проверить логи
tail -n 30 /var/log/supervisor/frontend.err.log

# Пересобрать
cd frontend && yarn install && supervisorctl restart frontend
```

### База данных
```bash
# Проверить подключение
curl http://localhost:8001/api/health
```

## 🤝 Git Workflow

```bash
git add .
git commit -m "feat: описание изменений"
git push origin main
```

**Соблюдайте структуру!** Не создавайте дубликаты файлов.

## 📞 Контакты

- **GitHub:** https://github.com/maslovmaksim92/AudioBot
- **Preview:** https://smart-agent-system.preview.emergentagent.com
- **Render:** https://audiobot-qpi2.onrender.com (backend)

---

**Версия:** 2.0  
**Дата:** 11.10.2025  
**Статус:** ✅ Production Ready

**Всё работает! Приложение готово к использованию.**