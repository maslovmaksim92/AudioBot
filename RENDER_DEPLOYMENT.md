# 🚀 Деплой VasDom AudioBot с самообучением на Render

## 📋 Обзор

VasDom AudioBot теперь полностью адаптирован для **Render Cloud** с модулем самообучения. Используется только PostgreSQL (без MongoDB) для максимальной простоты и облачной совместимости.

## 🏗️ Архитектура на Render

### **Сервисы:**
- **Web Service**: VasDom AudioBot API (FastAPI)
- **Database**: Render PostgreSQL (автоматически предоставляется)

### **Переменные окружения:**
- `DATABASE_URL` - автоматически создается Render PostgreSQL
- `EMERGENT_LLM_KEY` - ключ для AI (sk-emergent-0A408AfAeF26aCd5aB)
- `PORT` - автоматически назначается Render

## 🔧 Настройка деплоя

### 1. Создание сервиса на Render

1. **Подключите GitHub репозиторий:**
   ```
   https://github.com/maslovmaksim92/AudioBot
   ```

2. **Настройки Web Service:**
   - **Environment**: Python 3.11
   - **Build Command**: 
     ```bash
     cd backend && pip install --upgrade pip && pip install -r requirements.txt
     ```
   - **Start Command**:
     ```bash
     cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT
     ```

### 2. Добавление PostgreSQL

1. В Render Dashboard → **Databases** → **New PostgreSQL**
2. **Database Name**: `vasdom-audiobot-db`
3. **User**: `vasdom_user`
4. **Database**: `vasdom_audio`
5. **Plan**: Free (для начала)

### 3. Переменные окружения

В **Environment Variables** добавить:

```bash
# AI и самообучение
EMERGENT_LLM_KEY=sk-emergent-0A408AfAeF26aCd5aB
USE_LOCAL_MODEL=false
EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L6-v2

# Параметры самообучения
MIN_RATING_THRESHOLD=4
RETRAINING_THRESHOLD=3.5
EVALUATION_SCHEDULE_DAYS=7

# Безопасность
REQUIRE_AUTH_FOR_PUBLIC_API=false
API_SECRET_KEY=vasdom-audiobot-secret-key-2025

# CORS (замените на ваш домен)
CORS_ORIGINS=https://your-app.onrender.com
```

**📝 Примечание:** `DATABASE_URL` создается автоматически при добавлении PostgreSQL

## 🗄️ Инициализация базы данных

После деплоя выполните миграции:

```bash
# В Render Console или локально
cd backend
alembic upgrade head
```

Или через Render Shell:
1. Откройте **Shell** в веб-сервисе
2. Выполните:
   ```bash
   cd backend
   python -c "
   import asyncio
   from app.models.database import Base, engine
   async def create_tables():
       async with engine.begin() as conn:
           await conn.run_sync(Base.metadata.create_all)
   asyncio.run(create_tables())
   "
   ```

## 🧪 Тестирование деплоя

### Проверка основных эндпоинтов:

```bash
# Базовая проверка
curl https://your-app.onrender.com/

# Проверка здоровья
curl https://your-app.onrender.com/api/health

# Статус самообучения
curl https://your-app.onrender.com/api/voice/self-learning/status

# Тест AI чата
curl -X POST https://your-app.onrender.com/api/voice/process \
  -H "Content-Type: application/json" \
  -d '{"message": "Привет! Как дела с уборкой?", "session_id": "test123"}'
```

### Ожидаемые ответы:

✅ **Здоровая система:**
```json
{
  "status": "healthy",
  "platform": "Render",
  "components": {
    "api": true,
    "postgres": true,
    "ai_service": true,
    "embedding_service": true,
    "emergent_llm": true
  }
}
```

## 📊 Мониторинг на Render

### **Логи приложения:**
- Render Dashboard → Logs
- Поиск по ключевым словам: `✅`, `❌`, `ERROR`

### **Метрики:**
- CPU и Memory usage
- Response times
- Error rates

### **База данных:**
- PostgreSQL Dashboard → Metrics
- Connection counts
- Query performance

## 🔄 Автоматические обновления

### **GitHub Integration:**
- Auto-deploy при push в `main` branch
- Build notifications в GitHub
- Rollback capabilities

### **Scheduled Tasks (Cron):**
Для автоматической переоценки модели создайте Cron Job:

```bash
# В Render Cron Jobs
0 2 * * 0 cd /app/backend && python -m deploy.cron_tasks evaluate_model
```

## 🚨 Troubleshooting

### **Проблема 1: PostgreSQL connection failed**
**Решение:**
```bash
# Проверьте DATABASE_URL в Environment Variables
echo $DATABASE_URL

# Должен выглядеть как:
# postgresql://user:password@host:5432/database
```

### **Проблема 2: Emergent LLM не работает**
**Решение:**
```bash
# Проверьте ключ
curl -X POST https://your-app.onrender.com/api/voice/process \
  -H "Content-Type: application/json" \
  -d '{"message": "test"}'

# Если ошибка - проверьте EMERGENT_LLM_KEY
```

### **Проблема 3: Build fails на ML зависимостях**
**Решение:**
Добавьте в `requirements.txt`:
```
--find-links https://download.pytorch.org/whl/cpu/torch-2.0.0-stable.html
torch==2.0.0+cpu
```

### **Проблема 4: Memory limit exceeded**
**Решение:**
- Upgrade на Starter план ($7/month)
- Или отключите тяжелые ML модели:
  ```
  USE_LOCAL_MODEL=false
  ```

## 📈 Масштабирование

### **Starter Plan ($7/month):**
- 512 MB RAM
- Подходит для самообучения
- Background workers

### **Standard Plan ($25/month):**
- 2 GB RAM
- Несколько воркеров
- Scheduled jobs

### **Pro Plan ($85/month):**
- 8 GB RAM
- Полноценное machine learning
- Multiple regions

## 🎯 Production Checklist

### **Перед запуском:**
- [ ] PostgreSQL подключен и мигрирован
- [ ] EMERGENT_LLM_KEY настроен
- [ ] CORS_ORIGINS указывает на правильный домен
- [ ] Health check возвращает `"status": "healthy"`
- [ ] AI чат отвечает на тестовые вопросы

### **После запуска:**
- [ ] Мониторинг настроен
- [ ] Backup БД настроен
- [ ] Cron jobs для переоценки работают
- [ ] Логи отслеживаются
- [ ] Error tracking настроен

## 🎉 Готово!

VasDom AudioBot с модулем самообучения готов к работе на Render! 

**🔗 Полезные ссылки:**
- **GitHub**: https://github.com/maslovmaksim92/AudioBot
- **Render Dashboard**: https://dashboard.render.com/
- **API Docs**: https://your-app.onrender.com/docs
- **Health Check**: https://your-app.onrender.com/api/health

---

**💡 Tip**: Render автоматически выдает SSL сертификаты, поэтому ваше приложение сразу доступно по HTTPS!