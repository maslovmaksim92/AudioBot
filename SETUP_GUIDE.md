# VasDom AudioBot - Руководство по установке

## Требования

- Python 3.11+
- Node.js 18+
- yarn 1.22+
- PostgreSQL 14+ (с pgvector)

## Локальная установка

### 1. Клонирование

```bash
git clone https://github.com/maslovmaksim92/AudioBot.git
cd AudioBot
```

### 2. Backend

```bash
cd backend

# Создать виртуальное окружение
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Установить зависимости
pip install -r requirements.txt

# Создать .env из примера
cp .env.example .env
# Отредактировать .env с вашими ключами
```

**backend/.env минимум:**
```bash
DATABASE_URL=postgresql://user:pass@host:5432/dbname?sslmode=require
BITRIX24_WEBHOOK_URL=https://your.bitrix24.ru/rest/...
OPENAI_API_KEY=sk-...
JWT_SECRET=your-secret-key
CORS_ORIGINS=http://localhost:3000
```

**Запуск:**
```bash
uvicorn server:app --reload --host 0.0.0.0 --port 8001
```

### 3. Frontend

```bash
cd frontend

# Установить зависимости
yarn install

# Создать .env
echo "REACT_APP_BACKEND_URL=http://localhost:8001" > .env

# Запуск
yarn start
```

## Production (Render)

### Backend Service

**Тип:** Web Service (Python)

**Настройки:**
- Build Command: `pip install -r requirements.txt`
- Start Command: `uvicorn backend.server:app --host 0.0.0.0 --port $PORT`
- Environment: Python 3.11

**Environment Variables:** (скопировать все из backend/.env)

### Frontend Service

**Тип:** Static Site

**Настройки:**
- Build Command: `cd frontend && yarn install && yarn build`
- Publish Directory: `frontend/build`

**Environment Variables:**
```
REACT_APP_BACKEND_URL=https://your-backend.onrender.com
```

### PostgreSQL

**Рекомендуется:** Render PostgreSQL или Neon или Yandex Cloud

**Важно:** Должно быть установлено расширение `pgvector`:
```sql
CREATE EXTENSION vector;
```

## Переменные окружения

### Обязательные

```bash
DATABASE_URL=postgresql://...
OPENAI_API_KEY=sk-...
JWT_SECRET=random-secret
CORS_ORIGINS=*
```

### Для Bitrix24

```bash
BITRIX24_WEBHOOK_URL=https://...
```

### Для голосовых функций

```bash
LIVEKIT_URL=wss://...
LIVEKIT_API_KEY=...
LIVEKIT_API_SECRET=...
LIVEKIT_SIP_TRUNK_ID=...
NOVOFON_CALLER_ID=+7...
NOVOFON_SIP_USERNAME=...
NOVOFON_SIP_PASSWORD=...
```

### Для Telegram

```bash
TELEGRAM_BOT_TOKEN=...
TELEGRAM_TARGET_CHAT_ID=...
```

## Проверка работы

### Backend
```bash
curl http://localhost:8001/api/health
# Должно вернуть: {"ok": true, "ts": 1234567890}
```

### Frontend
Откройте http://localhost:3000 - должен загрузиться Dashboard

### Логи (supervisor)
```bash
tail -f /var/log/supervisor/backend.err.log
tail -f /var/log/supervisor/frontend.err.log
```

## Частые проблемы

### 1. Database connection error

**Проблема:** `Could not connect to database`

**Решение:**
- Проверьте DATABASE_URL
- Убедитесь, что PostgreSQL доступен
- Проверьте firewall и sslmode

### 2. CORS ошибки

**Проблема:** `Access blocked by CORS policy`

**Решение:**
- Добавьте frontend URL в CORS_ORIGINS
- Перезапустите backend

### 3. Module not found

**Проблема:** `ModuleNotFoundError: No module named 'xxx'`

**Решение:**
```bash
pip install -r requirements.txt  # backend
yarn install  # frontend
```

### 4. Port already in use

**Проблема:** `Address already in use`

**Решение:**
```bash
# Найти процесс
lsof -i :8001  # или :3000
# Убить
kill -9 <PID>
```

## Структура данных

### Инициализация БД

При первом запуске backend автоматически создаст таблицы:
- users
- employees  
- houses
- cleaning_schedules
- tasks
- ai_tasks
- knowledge_base
- meetings
- logs

### Миграции

Если нужны изменения схемы, используйте Alembic:
```bash
cd backend
alembic revision -m "description"
alembic upgrade head
```

## Мониторинг

### Health Check
```bash
curl http://localhost:8001/api/health
```

### Supervisor Status
```bash
supervisorctl status
```

### Логи приложения
```python
# В коде используется Python logging
import logging
logger = logging.getLogger(__name__)
logger.info("Message")
```

## Обновление

### Обновить код
```bash
git pull origin main
```

### Обновить зависимости
```bash
# Backend
cd backend && pip install -r requirements.txt

# Frontend  
cd frontend && yarn install
```

### Перезапустить
```bash
supervisorctl restart backend frontend
# или на Render: Deploy → Manual Deploy
```

## Безопасность

### Не коммитить .env!
```bash
# Проверьте .gitignore
cat .gitignore | grep .env
```

### Сгенерировать JWT_SECRET
```python
import secrets
print(secrets.token_urlsafe(64))
```

### Проверить права доступа
```bash
chmod 600 backend/.env
chmod 600 frontend/.env
```

## Производительность

### Backend
- Используется async/await везде
- PostgreSQL connection pooling
- APScheduler для фоновых задач

### Frontend
- React.lazy() для code splitting
- Оптимизированные изображения
- Минификация в production build

## Полезные команды

```bash
# Проверить версии
python --version
node --version
yarn --version

# Проверить зависимости Python
pip list | grep fastapi

# Проверить зависимости Node
yarn list --depth=0

# Очистить кэш
rm -rf backend/__pycache__
rm -rf frontend/node_modules frontend/build
```

---

Готово! Приложение должно работать.

Если проблемы - проверьте логи и переменные окружения.