# 🏠 VasDom AI Assistant

AI-powered assistant для компании ВасДом с интеграцией Telegram бота и Bitrix24 CRM.

## 🚀 Особенности системы

- **🤖 Telegram Bot**: @aitest123432_bot с умными AI-ответами
- **🏢 Bitrix24 CRM**: Интеграция с vas-dom.bitrix24.ru
- **🤖 AI Сервис**: Emergent LLM (GPT-4o-mini) для генерации ответов
- **📊 Web Dashboard**: Мониторинг системы в реальном времени
- **📈 Analytics**: Отслеживание метрик и активности

## 🏗️ Архитектура

- **Backend**: FastAPI + Python 3.11
- **Frontend**: React 19 + Tailwind CSS + shadcn/ui
- **Database**: MongoDB
- **Bot**: aiogram 3.20
- **AI**: Emergent LLM
- **Deploy**: Render.com

## 🔑 Переменные окружения

### Backend (.env)
```bash
# Telegram Bot
TELEGRAM_BOT_TOKEN=8327964029:AAHBMI1T1Y8ZWLn34wpg92d1-Cb-8RXTSmQ
TELEGRAM_WEBHOOK_URL=https://audiobot-qci2.onrender.com/telegram/webhook

# Bitrix24 CRM
BITRIX24_WEBHOOK_URL=https://vas-dom.bitrix24.ru/rest/1/bi0kv4y9ym8quxpa/

# AI Service
EMERGENT_LLM_KEY=sk-emergent-0A408AfAeF26aCd5aB

# Database
MONGO_URL=mongodb://localhost:27017
DB_NAME=vasdom_db

# App
DEBUG=false
APP_ENV=production
LOG_LEVEL=INFO
```

## 🌐 Production URLs

- **Main URL**: https://audiobot-qci2.onrender.com
- **Health Check**: https://audiobot-qci2.onrender.com/healthz
- **Dashboard**: https://audiobot-qci2.onrender.com/dashboard

## 📱 API Endpoints

### Системные
- `GET /` - информация о сервисе
- `GET /health` - базовый health check
- `GET /healthz` - детальный health check всех сервисов
- `GET /dashboard` - данные dashboard
- `GET /logs` - системные логи

### Telegram
- `GET /telegram/set-webhook` - установка webhook
- `POST /telegram/webhook` - обработка сообщений

### Bitrix24
- `GET /api/bitrix24/test` - тест подключения
- `GET /api/bitrix24/deals` - получение сделок
- `GET /api/bitrix24/cleaning-houses` - адреса для уборки

## 🤖 Telegram Bot

- **Bot**: @aitest123432_bot
- **Features**: AI-powered responses, Service information, Price inquiries

### Команды бота
- `/start` - приветствие и меню
- `/help` - справка по командам
- `/menu` - главное меню

## 🏢 Bitrix24 Integration

- **Portal**: https://vas-dom.bitrix24.ru
- **User**: Максим Маслов (maslovmaksim92@yandex.ru)
- **Features**: 50+ сделок синхронизированы

## 📊 System Status

### ✅ Рабочие компоненты (100% готовности)
- ✅ Backend API: все endpoints работают
- ✅ Telegram Bot: @aitest123432_bot активен
- ✅ Bitrix24: 50 сделок синхронизированы  
- ✅ AI Service: GPT-4o-mini готов к работе
- ✅ Web Dashboard: React интерфейс готов
- ✅ Logging: полное логирование

**System Status**: 🟢 PRODUCTION READY
