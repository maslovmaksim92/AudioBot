# 🚀 AI Ассистент - Деплой на Render

## 📋 Инструкция по деплою

### 1. Подготовка файлов для деплоя
Убедитесь что у вас есть эти файлы в корне репозитория:
- `requirements.txt` - Python зависимости
- `main.py` - Точка входа приложения  
- `Procfile` - Команда запуска для Render
- `backend/server_render.py` - Версия без emergentintegrations

### 2. Настройка на Render.com

#### Создание Web Service:
1. Зайдите на https://render.com
2. Нажмите "New" → "Web Service"
3. Подключите ваш GitHub репозиторий
4. Настройте:
   - **Name**: `ai-assistant-vasdom`
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python main.py`

#### Environment Variables:
```env
MONGO_URL=mongodb+srv://ai-assistant:password@cluster.mongodb.net/ai_assistant
DB_NAME=ai_assistant
CORS_ORIGINS=*
EMERGENT_LLM_KEY=sk-emergent-0A408AfAeF26aCd5aB
TELEGRAM_BOT_TOKEN=8327964029:AAHBMI1T1Y8ZWLn34wpg92d1-Cb-8RXTSmQ
BITRIX24_WEBHOOK_URL=https://vas-dom.bitrix24.ru/rest/1/gq2ixv9nypiimwi9/
BITRIX24_DOMAIN=vas-dom.bitrix24.ru
PYTHON_VERSION=3.11.0
```

### 3. Деплой
После настройки Render автоматически:
1. Склонирует репозиторий
2. Установит зависимости из requirements.txt
3. Запустит приложение через main.py
4. Приложение будет доступно на: https://audiobot-qci2.onrender.com

### 4. Проверка деплоя
После деплоя проверьте:
- `GET /` - Основная страница
- `GET /api/` - API статус
- `GET /api/dashboard` - Дашборд данные
- `GET /docs` - Swagger документация

## 🎯 Функционал готовый к использованию:

### ✅ Веб-интерфейс:
- 📊 Дашборд с метриками
- 👥 Управление сотрудниками  
- 🤖 AI чат с GPT-4o-mini
- 📞 Live голосовой чат
- 🎙️ Запись и анализ планерок
- 🔄 Система знакомства с пользователем

### ✅ API Endpoints:
- `/api/dashboard` - Бизнес метрики
- `/api/ai/chat` - AI чат
- `/api/bitrix24/*` - Интеграция с Bitrix24
- `/api/user/profile/*` - Профили пользователей
- `/api/company/*` - Информация о компании

### ✅ Интеграции:
- 🔗 Bitrix24 API (4M+ руб оборот)
- 📱 Telegram Bot готов к запуску
- 🧠 AI с контекстом клининговой компании
- 🗣️ Голосовые технологии (Speech-to-text/Text-to-speech)

## 🚨 Важные заметки:

1. **База данных**: Используется MongoDB Atlas (облачная)
2. **AI модель**: Mock AI для демо (без emergentintegrations на продакшене)  
3. **Статика**: Render автоматически обслуживает статические файлы
4. **Логирование**: Логи доступны в Render Dashboard

## 🔧 Troubleshooting:

### Ошибка "No module named emergentintegrations":
- Используется `server_render.py` с Mock AI
- Mock AI предоставляет умные ответы без внешних зависимостей

### Ошибка подключения к MongoDB:
- Проверьте MONGO_URL в environment variables
- Убедитесь что IP адрес Render добавлен в whitelist MongoDB Atlas

### Ошибка Bitrix24 API:
- Проверьте BITRIX24_WEBHOOK_URL
- Убедитесь что webhook активен в Bitrix24

## 📞 Контакты:
- Техподдержка: через GitHub Issues
- Документация API: https://your-app.onrender.com/docs