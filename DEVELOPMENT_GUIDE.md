# VasDom AudioBot - Руководство разработчика

## Введение

Этот документ содержит руководства и best practices для разработки VasDom AudioBot.

## Требования к окружению

### Обязательные
- **Python**: 3.10+
- **Node.js**: 18+
- **yarn**: 1.22+
- **PostgreSQL**: 14+ (с pgvector расширением)
- **Git**: 2.30+

### Опциональные
- **Docker**: для контейнеризации
- **Redis**: для кэширования (планируется)

## Установка и настройка

### 1. Клонирование репозитория

```bash
git clone https://github.com/maslovmaksim92/AudioBot.git
cd AudioBot
```

### 2. Настройка Backend

```bash
cd backend

# Создание виртуального окружения
python -m venv venv

# Активация (Linux/Mac)
source venv/bin/activate

# Активация (Windows)
venv\Scripts\activate

# Установка зависимостей
pip install -r requirements.txt

# Создание .env файла
cp .env.example .env
# Редактируйте .env и добавьте свои ключи
```

### 3. Настройка Frontend

```bash
cd frontend

# Установка зависимостей
yarn install

# Создание .env файла
cp .env.example .env
# Редактируйте .env
```

### 4. Настройка базы данных

```bash
# Создайте PostgreSQL базу
createdb vasdom_audiobot

# Установите pgvector расширение
psql vasdom_audiobot -c "CREATE EXTENSION vector;"

# Примените миграции (если есть)
# alembic upgrade head
```

## Запуск приложения

### Development mode

#### Backend
```bash
cd backend
source venv/bin/activate  # или venv\Scripts\activate на Windows
uvicorn server:app --reload --host 0.0.0.0 --port 8001
```

Backend будет доступен на `http://localhost:8001`

#### Frontend
```bash
cd frontend
yarn start
```

Frontend будет доступен на `http://localhost:3000`

### Production mode

См. раздел Deployment в README.md

## Структура кода

### Backend

#### Модульная структура роутеров

Каждый роутер отвечает за свою область:

```python
# backend/app/routers/houses.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.config.database import get_db

router = APIRouter(tags=["houses"])

@router.get("/houses")
async def get_houses(db: AsyncSession = Depends(get_db)):
    # Логика получения домов
    pass
```

Подключение в `server.py`:

```python
from app.routers import houses

app.include_router(houses.router, prefix="/api")
```

#### Pydantic модели

Все модели данных определяются через Pydantic:

```python
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class HouseCreate(BaseModel):
    address: str
    brigade: str
    management_company: str
    
class HouseResponse(BaseModel):
    id: str
    address: str
    brigade: str
    management_company: str
    created_at: datetime
    
    class Config:
        from_attributes = True  # Для SQLAlchemy моделей
```

#### Асинхронные операции

Все I/O операции должны быть асинхронными:

```python
# ✅ Правильно
async def fetch_from_bitrix():
    async with httpx.AsyncClient() as client:
        response = await client.get("https://api.bitrix24.com/...")
        return response.json()

# ❌ Неправильно (блокирующий код)
def fetch_from_bitrix():
    response = requests.get("https://api.bitrix24.com/...")
    return response.json()
```

#### Обработка ошибок

```python
from fastapi import HTTPException

@router.get("/houses/{house_id}")
async def get_house(house_id: str, db: AsyncSession = Depends(get_db)):
    house = await db.get(House, house_id)
    if not house:
        raise HTTPException(status_code=404, detail="House not found")
    return house
```

### Frontend

#### Компоненты

Каждый компонент в своей папке:

```
src/components/Dashboard/
├── Dashboard.jsx
├── Dashboard.module.css  # Если нужны локальные стили
└── components/           # Дочерние компоненты
    ├── StatsCard.jsx
    └── ChartWidget.jsx
```

#### Пример компонента

```jsx
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

function Dashboard() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${BACKEND_URL}/api/dashboard/stats`);
      setStats(response.data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div>Загрузка...</div>;
  if (error) return <div>Ошибка: {error}</div>;

  return (
    <div className="p-6">
      <h1 className="text-3xl font-bold mb-6">Dashboard</h1>
      <div className="grid grid-cols-3 gap-4">
        {/* Статистика */}
      </div>
    </div>
  );
}

export default Dashboard;
```

#### API вызовы

Используйте axios и правильно обрабатывайте ошибки:

```javascript
// ✅ Правильно
try {
  const response = await axios.post(`${BACKEND_URL}/api/ai/chat`, {
    message: userInput
  });
  return response.data;
} catch (error) {
  if (error.response) {
    // Сервер ответил с кодом ошибки
    console.error('Server error:', error.response.status, error.response.data);
  } else if (error.request) {
    // Запрос отправлен, но ответа нет
    console.error('No response from server');
  } else {
    // Ошибка при создании запроса
    console.error('Request error:', error.message);
  }
  throw error;
}
```

#### Использование shadcn/ui

Всегда используйте компоненты из библиотеки:

```jsx
// ✅ Правильно
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Dialog } from '@/components/ui/dialog';

<Button variant="primary" onClick={handleClick}>
  Отправить
</Button>

// ❌ Неправильно (обычный HTML)
<button onClick={handleClick}>Отправить</button>
```

## Стандарты кодирования

### Python (Backend)

#### Именование

```python
# Переменные и функции: snake_case
user_name = "John"
def get_user_data():
    pass

# Классы: PascalCase
class UserModel:
    pass

# Константы: UPPER_CASE
MAX_RETRY_COUNT = 3
API_TIMEOUT = 30

# Приватные методы: _leading_underscore
def _internal_helper():
    pass
```

#### Imports

```python
# Стандартная библиотека
import os
import sys
from datetime import datetime, timezone

# Сторонние библиотеки
from fastapi import FastAPI, HTTPException
import httpx

# Локальные импорты
from app.config.database import get_db
from app.models.user import User
```

#### Типизация

```python
from typing import List, Optional, Dict, Any

def process_data(
    items: List[Dict[str, Any]], 
    user_id: str,
    options: Optional[Dict] = None
) -> List[str]:
    """
    Обрабатывает данные.
    
    Args:
        items: Список элементов для обработки
        user_id: ID пользователя
        options: Опциональные параметры
    
    Returns:
        Список обработанных ID
    """
    pass
```

### JavaScript/React (Frontend)

#### Именование

```javascript
// Переменные и функции: camelCase
const userName = "John";
function getUserData() {}

// Компоненты: PascalCase
function Dashboard() {}
const UserCard = () => {};

// Константы: UPPER_CASE или camelCase
const MAX_ITEMS = 100;
const apiBaseUrl = process.env.REACT_APP_BACKEND_URL;

// Приватные: _leadingUnderscore (опционально)
function _helperFunction() {}
```

#### Компоненты

```jsx
// ✅ Functional components с hooks
import React, { useState, useEffect } from 'react';

function MyComponent({ prop1, prop2 }) {
  const [state, setState] = useState(initialValue);
  
  useEffect(() => {
    // Side effect
  }, [dependency]);
  
  return <div>...</div>;
}

export default MyComponent;
```

#### PropTypes (опционально)

```jsx
import PropTypes from 'prop-types';

MyComponent.propTypes = {
  prop1: PropTypes.string.isRequired,
  prop2: PropTypes.number,
  onAction: PropTypes.func
};
```

## Тестирование

### Backend

```python
# tests/test_api.py
import pytest
from httpx import AsyncClient
from backend.server import app

@pytest.mark.asyncio
async def test_get_houses():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/houses")
        assert response.status_code == 200
        data = response.json()
        assert "houses" in data
```

Запуск тестов:
```bash
pytest tests/
```

### Frontend

```javascript
// src/components/Dashboard/Dashboard.test.jsx
import { render, screen, waitFor } from '@testing-library/react';
import Dashboard from './Dashboard';

test('renders dashboard title', () => {
  render(<Dashboard />);
  const title = screen.getByText(/Dashboard/i);
  expect(title).toBeInTheDocument();
});

test('fetches and displays stats', async () => {
  render(<Dashboard />);
  await waitFor(() => {
    expect(screen.getByText(/Запланировано/i)).toBeInTheDocument();
  });
});
```

Запуск тестов:
```bash
yarn test
```

## Линтинг и форматирование

### Backend

```bash
# Установка инструментов
pip install ruff black mypy

# Линтинг
ruff check backend/

# Форматирование
black backend/

# Проверка типов
mypy backend/
```

### Frontend

```bash
# ESLint уже настроен через Create React App
yarn lint

# Исправление автоматически
yarn lint --fix
```

## Git Workflow

### Ветки

```
main              # Production
  ├── develop     # Development
      ├── feature/new-feature
      ├── bugfix/fix-something
      └── hotfix/critical-fix
```

### Commit messages

```
feat: добавлен фильтр по бригадам в Works
fix: исправлена ошибка в AI Chat при пустом ответе
docs: обновлена документация API
refactor: рефакторинг компонента Dashboard
test: добавлены тесты для houses router
chore: обновление зависимостей
```

### Pull Request процесс

1. Создайте feature branch от `develop`
2. Разработайте фичу
3. Напишите тесты
4. Создайте PR в `develop`
5. Code review
6. Merge после approval

## Debugging

### Backend

```python
# Добавление логов
import logging
logger = logging.getLogger(__name__)

@router.get("/houses")
async def get_houses():
    logger.info("Fetching houses from database")
    logger.debug(f"Filters: {filters}")
    logger.error(f"Error occurred: {error}")
```

Уровни логирования:
- DEBUG: Детальная информация для диагностики
- INFO: Общая информация о работе
- WARNING: Предупреждения
- ERROR: Ошибки
- CRITICAL: Критические ошибки

### Frontend

```javascript
// Console logging
console.log('Data:', data);
console.error('Error:', error);
console.warn('Warning:', warning);
console.table(arrayOfObjects);  // Красивый вывод массивов

// React DevTools
// Установите расширение React Developer Tools для браузера
```

## Частые проблемы и решения

### CORS ошибки

**Проблема**: `Access to fetch at '...' has been blocked by CORS policy`

**Решение**: Убедитесь, что CORS настроен правильно в backend:

```python
# backend/server.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://your-frontend.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Database connection errors

**Проблема**: `asyncpg.exceptions.InvalidPasswordError`

**Решение**: Проверьте DATABASE_URL в .env файле. Формат:
```
postgresql+asyncpg://user:password@host:5432/database
```

### Frontend не подключается к backend

**Проблема**: `Network Error` или `ERR_CONNECTION_REFUSED`

**Решение**:
1. Проверьте, что backend запущен (`curl http://localhost:8001/api/health`)
2. Проверьте REACT_APP_BACKEND_URL в frontend/.env
3. Убедитесь, что все API пути начинаются с `/api`

### OpenAI Realtime ошибки

**Проблема**: `401 Unauthorized` или `Invalid API key`

**Решение**: 
1. Проверьте OPENAI_API_KEY в backend/.env
2. Убедитесь, что у ключа есть доступ к Realtime API
3. Проверьте баланс аккаунта OpenAI

## Производительность

### Backend оптимизация

1. **Используйте индексы БД**
```sql
CREATE INDEX idx_houses_brigade ON houses(brigade);
CREATE INDEX idx_cleaning_date ON cleaning_schedules(cleaning_date);
```

2. **Кэшируйте частые запросы**
```python
from functools import lru_cache
from datetime import datetime, timedelta

_cache = {}
_cache_ttl = {}

async def get_houses_cached():
    now = datetime.now()
    if 'houses' in _cache and now < _cache_ttl.get('houses', now):
        return _cache['houses']
    
    houses = await fetch_houses_from_db()
    _cache['houses'] = houses
    _cache_ttl['houses'] = now + timedelta(minutes=5)
    return houses
```

3. **Используйте select/load_only для БД**
```python
# Загружать только нужные поля
houses = await db.execute(
    select(House).options(load_only(House.id, House.address))
)
```

### Frontend оптимизация

1. **Lazy loading компонентов**
```javascript
import React, { lazy, Suspense } from 'react';

const Dashboard = lazy(() => import('./components/Dashboard/Dashboard'));

function App() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <Dashboard />
    </Suspense>
  );
}
```

2. **Мемоизация**
```javascript
import { useMemo, useCallback } from 'react';

const MyComponent = ({ data }) => {
  const processedData = useMemo(() => {
    return expensiveOperation(data);
  }, [data]);
  
  const handleClick = useCallback(() => {
    // handler
  }, [/* dependencies */]);
};
```

3. **Виртуализация длинных списков**
```javascript
import { FixedSizeList } from 'react-window';

const Row = ({ index, style }) => (
  <div style={style}>Row {index}</div>
);

<FixedSizeList
  height={600}
  itemCount={1000}
  itemSize={50}
  width="100%"
>
  {Row}
</FixedSizeList>
```

## Безопасность

### Never commit secrets

```bash
# Добавьте в .gitignore
.env
.env.local
*.pem
*.key
secrets.json
```

### Валидация входных данных

```python
from pydantic import BaseModel, validator

class HouseCreate(BaseModel):
    address: str
    phone: str
    
    @validator('phone')
    def validate_phone(cls, v):
        if not v.startswith('+'):
            raise ValueError('Phone must start with +')
        return v
```

### Rate limiting

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/ai/chat")
@limiter.limit("10/minute")
async def ai_chat(request: Request):
    pass
```

## Deployment

См. README.md для полных инструкций по деплою на Render.

## Поддержка

- **Issues**: https://github.com/maslovmaksim92/AudioBot/issues
- **Документация**: См. файлы в корне проекта
- **Вопросы**: Создайте issue с тегом `question`

## Контрибьюция

1. Fork проекта
2. Создайте feature branch
3. Commit изменения
4. Push в branch
5. Создайте Pull Request

Спасибо за вклад в VasDom AudioBot! 🚀