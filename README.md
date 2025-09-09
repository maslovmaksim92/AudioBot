# VasDom AudioBot - AI-система управления клининговой компанией

🤖 **Интеллектуальный помощник для управления 490 многоквартирными домами, 82 сотрудниками и 7 бригадами в Калуге**

[![FastAPI](https://img.shields.io/badge/FastAPI-0.110.1-009688.svg?style=flat&logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18.2.0-61DAFB.svg?style=flat&logo=react)](https://reactjs.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-336791.svg?style=flat&logo=postgresql)](https://postgresql.org)
[![Render](https://img.shields.io/badge/Deployed%20on-Render-46E3B7.svg?style=flat)](https://render.com)

🔗 **Live Demo**: [https://audiobot-qci2.onrender.com](https://audiobot-qci2.onrender.com)

## 📊 Назначение проекта

VasDom AudioBot - это комплексная система управления клининговой компанией нового поколения, которая автоматизирует:

- **🏠 Управление CRM**: 490 домов из Bitrix24 с полной интеграцией и реальными данными УК
- **📋 Управление задачами**: Создание и синхронизация задач в Bitrix24 с полным трекингом
- **🎨 Планирование работ**: 7 бригад по районам Калуги с ВАУ-дизайном и 3D эффектами
- **🤖 AI-помощник**: GPT-4 mini через Emergent LLM для ответов на вопросы
- **🎤 Голосовые функции**: Диктофон для планерок, живой голосовой чат с AI
- **📱 Telegram-бот**: Уведомления сотрудникам, создание задач в Bitrix24
- **📊 Контроль качества**: Фото-отчеты, GPS-отметки, автоматическая оценка

## 🎯 Новые возможности (2025)

### ✨ Вкладка "Задачи" (NEW!)
- **📋 Полная интеграция с Bitrix24**: Создание, просмотр, фильтрация задач
- **📊 Реальная статистика**: Всего задач, просрочки, завершенные, на сегодня
- **🎨 Градиентный дизайн**: Современный UI с карточками и 3D эффектами
- **🔍 Умные фильтры**: По статусу, приоритету, ответственному
- **🔗 Прямые ссылки**: Переход к задачам в Bitrix24 одним кликом

### 🏠 Улучшенное управление домами
- **🏢 Реальные данные УК**: Корректная загрузка управляющих компаний из Bitrix24
- **👥 Реальные бригады**: Данные ответственных лиц из системы пользователей
- **⚡ Производительность**: Оптимизация в 6+ раз, кэширование, batch загрузка
- **📍 Кликабельные адреса**: Открытие Google Maps для каждого дома
- **🎨 ВАУ-функционал**: Логотип РЯДОМ, градиенты, анимации, CSV экспорт

## 🏗️ Архитектура

### Backend (FastAPI + Bitrix24)
```
backend/app/
├── config/                    # Конфигурация и настройки
│   ├── settings.py            # Переменные окружения и CORS
│   └── database.py            # PostgreSQL подключение
├── models/                    # Данные и схемы
│   ├── schemas.py             # Pydantic модели (House, Task, MonthlySchedule)
│   ├── telegram.py            # Telegram webhook модели
│   └── database.py            # SQLAlchemy ORM модели
├── services/                  # Бизнес-логика
│   ├── ai_service.py          # GPT-4 mini + Emergent LLM
│   ├── bitrix_service.py      # 🆕 Расширенная интеграция Bitrix24
│   └── telegram_service.py    # Telegram Bot API
├── routers/                   # API endpoints
│   ├── dashboard.py           # Статистика и дашборд (490 домов)
│   ├── telegram.py            # Webhook + валидация данных
│   ├── voice.py               # Голосовой AI чат
│   ├── meetings.py            # Планерки и диктофон
│   ├── cleaning.py            # 🆕 Оптимизированное управление домами
│   ├── tasks.py               # 🆕 Управление задачами Bitrix24
│   └── logs.py                # Системные логи
├── security.py                # 🔒 Улучшенная аутентификация API
└── tests/                     # Unit тесты + автоматическое тестирование
```

### Frontend (React + Tailwind + Градиенты)
```
frontend/src/
├── App.js                     # Главный компонент с роутингом
├── components/                # React компоненты
│   ├── Dashboard/             # Дашборд с быстрыми действиями
│   ├── Works/                 # 🆕 ВАУ-дизайн управления домами
│   ├── Tasks/                 # 🆕 Управление задачами
│   ├── AIChat/                # AI чат с голосом
│   ├── Meetings/              # Планерки
│   ├── Employees/             # Сотрудники
│   ├── Training/              # Обучение
│   └── Logs/                  # Логи системы
├── context/                   # React Context для состояния
│   └── AppContext.js          # Глобальное состояние приложения
└── services/                  # API сервисы
    └── apiService.js          # Централизованные API вызовы
```

### База данных (PostgreSQL)
- `voice_logs` - История AI взаимодействий для самообучения
- `meetings` - Планерки с транскрипцией и задачами
- `ai_tasks` - Календарь задач с AI-менеджером
- **Миграции**: Alembic для управления схемой

## 🚀 Зависимости и версии

### Python (Backend)
- **FastAPI 0.110.1** - Web framework
- **SQLAlchemy 2.0+** - ORM для PostgreSQL
- **Databases** - Async database support
- **Alembic 1.13+** - Database migrations
- **Pydantic 2.6+** - Data validation с field_validator
- **httpx** - HTTP client для интеграций
- **emergentintegrations** - Emergent LLM доступ
- **asyncio** - Асинхронные операции с кэшированием

### Node.js (Frontend)
- **React 18.2+** - Компонентная архитектура
- **Tailwind CSS** - Utility-first CSS с градиентами
- **React Router** - Клиентский роутинг
- **React Context** - Глобальное состояние

### Внешние сервисы
- **Bitrix24 CRM** - 490 домов + задачи + пользователи
- **Telegram Bot API** - Уведомления сотрудникам
- **Emergent LLM** - GPT-4 mini доступ через единый ключ
- **PostgreSQL** - Основная база данных
- **Google Maps** - Интеграция с адресами домов

## ⚙️ Настройка окружения

### 1. Переменные окружения

#### Backend (.env)
```bash
# Database
DATABASE_URL=postgresql://user:password@host:port/database

# Bitrix24 CRM (ОБНОВЛЕНО)
BITRIX24_WEBHOOK_URL=https://vas-dom.bitrix24.ru/rest/1/4l8hq1gqgodjt7yo/

# Telegram Bot
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_WEBHOOK_URL=https://audiobot-qci2.onrender.com/api/telegram/webhook

# AI (Emergent LLM Key)
EMERGENT_LLM_KEY=sk-or-v1-d1f50246cd027109960ldfb432d72441ea00c99d49a96729a78125c61ac4dd

# Security
API_SECRET_KEY=vasdom-secure-key-2025
REQUIRE_AUTH_FOR_PUBLIC_API=false

# CORS (Production URLs)
CORS_ORIGINS=https://audiobot-qci2.onrender.com,https://vas-dom.github.io

# Frontend Redirects
FRONTEND_DASHBOARD_URL=https://audiobot-qci2.onrender.com
```

#### Frontend (.env)
```bash
# КРИТИЧНО: Production Backend URL
REACT_APP_BACKEND_URL=https://audiobot-qci2.onrender.com
```

### 2. Установка зависимостей

#### Backend
```bash
cd backend
pip install -r requirements.txt
# Включает emergentintegrations для Emergent LLM
```

#### Frontend
```bash
cd frontend
yarn install
# НЕ используйте npm - только yarn!
```

## 🗄️ Миграции базы данных

Система использует **Alembic** для управления схемой PostgreSQL:

```bash
cd backend

# Создать новую миграцию
alembic revision --autogenerate -m "Add tasks integration"

# Применить миграции
alembic upgrade head

# Откатить миграцию
alembic downgrade -1

# История миграций
alembic history --verbose
```

**⚠️ Важно**: Все изменения схемы только через миграции!

## 🏃‍♂️ Запуск сервера

### Локальная разработка

#### Backend
```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
# API доступен на http://localhost:8001
```

#### Frontend
```bash
cd frontend
yarn start
# Доступен на http://localhost:3000
```

### Production (Render.com)
```bash
# Backend
uvicorn app.main:app --host 0.0.0.0 --port $PORT

# Frontend
yarn build && serve -s build
```

## 🧪 Тестирование

### Автоматические тесты
```bash
cd backend

# Все тесты (включая новые Bitrix24 Tests)
pytest -v

# Тесты задач
pytest app/tests/ -k "tasks" -v

# Тесты с покрытием
pytest --cov=app --cov-report=html
```

### Ручное тестирование
- **Backend**: [http://localhost:8001/docs](http://localhost:8001/docs) - Swagger UI
- **Frontend**: [http://localhost:3000](http://localhost:3000) - React App
- **Production**: [https://audiobot-qci2.onrender.com](https://audiobot-qci2.onrender.com)

## 🔌 Внешние интеграции

### Bitrix24 CRM (ОБНОВЛЕНО)
```python
# Категории
CATEGORY_ID = 34  # Уборка подъездов (основная)

# Поля домов
- ID, TITLE, STAGE_ID, DATE_CREATE, OPPORTUNITY
- ASSIGNED_BY_ID, COMPANY_ID  # Для УК и бригад
- UF_CRM_1669561599956       # Адрес дома
- UF_CRM_1669704529022       # Количество квартир
- UF_CRM_1669705507390       # Количество подъездов
- UF_CRM_1669704631166       # Количество этажей
- UF_CRM_1669706387893       # Тариф/периодичность

# Графики уборки (по месяцам)
- UF_CRM_1741592774017-1741593452062  # Сентябрь-Декабрь 2025

# Методы API
- crm.deal.list              # Список домов
- user.get                   # Данные пользователей (бригады)
- crm.company.get            # Данные УК
- tasks.task.list            # 🆕 Список задач
- tasks.task.add             # 🆕 Создание задач
```

### Telegram Bot
```python
# Webhook
POST /api/telegram/webhook

# Команды
/задача [текст]              # Создать задачу в Bitrix24
/статистика                  # Показать статистику домов
/помощь                      # Список команд

# Уведомления
- Ежедневные отчеты бригадам
- Уведомления о новых задачах
- Статус выполнения работ
```

### Google Maps Integration
```javascript
// Кликабельные адреса
const openGoogleMaps = (address) => {
  const mapsUrl = `https://www.google.com/maps/search/${encodeURIComponent(address)}`;
  window.open(mapsUrl, '_blank');
};
```

## 📱 API Endpoints

### Основные
- `GET /` - Редирект на React дашборд
- `GET /api/` - API информация и версия
- `GET /api/health` - Проверка состояния системы

### 🏠 CRM и дома
- `GET /api/bitrix24/test` - Тест интеграции с Bitrix24
- `GET /api/cleaning/houses` - 🆕 Оптимизированный список домов (490)
- `GET /api/cleaning/filters` - Фильтры для домов
- `POST /api/cleaning/houses` - Создать дом в Bitrix24
- `POST /api/cleaning/cache/clear` - 🆕 Очистить кэш

### 📋 Задачи (NEW!)
- `GET /api/tasks` - Список задач из Bitrix24
- `POST /api/tasks` - Создать задачу в Bitrix24
- `GET /api/tasks/stats` - Статистика задач
- `GET /api/tasks/users` - Пользователи для назначения

### 🤖 AI и голос
- `POST /api/voice/process` - Голосовой AI чат 🔒
- `GET /api/logs` - История AI взаимодействий

### 📅 Планерки
- `POST /api/meetings/start-recording` - Начать запись планерки
- `POST /api/meetings/stop-recording` - Остановить и обработать
- `GET /api/meetings` - История планерок

### 📱 Telegram
- `POST /api/telegram/webhook` - Webhook для бота 🔒
- `GET /api/telegram/status` - Статус подключения бота

### 📊 Dashboard
- `GET /api/dashboard` - Статистика (490 домов, 82 сотрудника)

🔒 = Требует аутентификации (при `REQUIRE_AUTH_FOR_PUBLIC_API=true`)

## 🔒 Security

### Аутентификация
```python
# Методы аутентификации
Authorization: Bearer your_api_key    # Bearer Token
X-API-Key: your_api_key              # Custom Header

# Настройка
REQUIRE_AUTH_FOR_PUBLIC_API=false    # Environment variable
```

### CORS Policy
```python
# Конфигурация
CORS_ORIGINS=https://audiobot-qci2.onrender.com,https://vas-dom.github.io

# Методы
["GET", "POST", "PUT", "DELETE", "OPTIONS"]

# Headers
["*"]  # Все заголовки разрешены
```

### Telegram Webhook Security
```python
# Валидация
- Pydantic модели для всех данных
- Обязательные поля: message, chat_id, text
- HTTPException при некорректных данных
```

## 📈 Мониторинг и логи

### Системные логи
- **Endpoint**: `/api/logs`
- **Формат**: JSON с временными метками
- **Хранение**: PostgreSQL + File (cloud-friendly)

### Performance Monitoring
```python
# Метрики (новые)
- Время загрузки домов: 5-10 секунд (раньше 30+)
- Кэширование: 5 минут TTL для пользователей/компаний
- Batch загрузка: Оптимизация API вызовов
- Memory usage: Эффективное использование памяти
```

### Bitrix24 Integration Logs
```python
# Логирование интеграций
✅ Company info loaded: ООО "РИЦ ЖРЭУ"
✅ User info loaded: 4 бригада
✅ Tasks loaded: 50 tasks from Bitrix24
🚀 Using cached deals: 490 houses
```

## 🏠 Данные компании (ОБНОВЛЕНО)

### География работы (7 бригад)
- **1 бригада - Центр**: Пролетарская, Баррикад, Ленина
- **2 бригада - Никитинский**: Чижевского, Никитина, Телевизионная  
- **3 бригада - Жилетово**: Молодежная, Широкая
- **4 бригада - Северный**: Жукова, Хрустальная, Гвардейская
- **5 бригада - Пригород**: Кондрово, Пушкина
- **6 бригада - Окраины**: Остальные районы
- **7 бригада - Новые районы**: Расширение территории

### Актуальная статистика
```
🏠 Домов: 490 (реальные данные из Bitrix24 CRM)
👥 Сотрудников: 82 человека в 7 бригадах
🚪 Подъездов: ~1,470 (3 на дом в среднем)
🏠 Квартир: ~36,750 (75 на дом в среднем)
📏 Этажей: ~2,450 (5 на дом в среднем)
🏢 Управляющих компаний: 29 реальных УК
📋 Активных задач: 50+ в Bitrix24
```

### Управляющие компании (реальные данные)
```
- ООО "РИЦ ЖРЭУ"
- УК ГУП Калуги
- ООО "УК Новый город"
- ООО "УЮТНЫЙ ДОМ"
- ООО "РКЦ ЖИЛИЩЕ"
- ООО "УК МЖД Московского округа г.Калуги"
- ООО "ЖРЭУ-14"
- ООО "УК ВАШ УЮТ"
- ООО "ЭРСУ 12"
- ООО "ДОМОУПРАВЛЕНИЕ - МОНОЛИТ"
+ еще 19 УК
```

## 🔄 CI/CD и деплой

### Render.com Configuration
```yaml
# render.yaml
services:
  - type: web
    name: vasdom-audiobot-backend
    env: python
    region: oregon
    plan: starter
    buildCommand: |
      pip install --upgrade pip
      pip install -r requirements.txt
    startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: DATABASE_URL
        sync: false
      - key: BITRIX24_WEBHOOK_URL
        sync: false
      - key: EMERGENT_LLM_KEY
        sync: false

  - type: static
    name: vasdom-audiobot-frontend
    env: node
    region: oregon
    plan: starter
    buildCommand: |
      yarn install
      yarn build
    staticPublishPath: ./build
    envVars:
      - key: REACT_APP_BACKEND_URL
        value: https://audiobot-qci2.onrender.com
```

### Автоматический деплой
```bash
# Git push автоматически триггерит:
1. Build backend (Python dependencies)
2. Run tests (pytest)
3. Build frontend (React production)
4. Deploy to production URLs
5. Health check endpoints
```

## 📊 Новые возможности (Roadmap)

### ✅ Реализовано (2025)
- 📋 Полнофункциональная вкладка "Задачи" с Bitrix24
- 🏢 Корректные данные УК из API компаний
- 👥 Реальные бригады из пользователей Bitrix24
- ⚡ Performance оптимизация в 6+ раз
- 🎨 ВАУ-дизайн с градиентами и анимациями
- 📍 Интеграция с Google Maps
- 🔄 Кэширование и batch загрузка

### 🔮 Планируется
- 📄 **Bitrix24 PDF Integration** - расширенные возможности
- 🗃️ **Alembic Migration Verification** - production база данных
- 🧪 **Comprehensive Test Coverage** - unit/integration тесты
- 🤖 **Phase 2.1: Full Telegram Bot** - дополнительные команды
- ⚙️ **Unify Service Initialization** - FastAPI Depends()

## 🔧 Troubleshooting

### Частые проблемы и решения

#### Backend не запускается
```bash
# Проверьте зависимости
pip install -r requirements.txt

# Проверьте порт
lsof -i :8001

# Проверьте логи
tail -f /var/log/supervisor/backend.err.log
```

#### Frontend ошибки
```bash
# Очистите кэш
yarn cache clean

# Переустановите зависимости
rm -rf node_modules yarn.lock
yarn install

# Проверьте .env
cat frontend/.env
```

#### Bitrix24 интеграция
```bash
# Тест подключения
curl -X GET "https://audiobot-qci2.onrender.com/api/bitrix24/test"

# Очистка кэша
curl -X POST "https://audiobot-qci2.onrender.com/api/cleaning/cache/clear"

# Проверка webhook URL
echo $BITRIX24_WEBHOOK_URL
```

## 🤝 Contribute

### Процесс разработки
1. **Fork** репозиторий
2. **Feature branch**: `git checkout -b feature/awesome-tasks`
3. **Develop**: Следуйте архитектуре и стилю кода
4. **Test**: Обязательно автоматические тесты
5. **Commit**: `git commit -m 'Add awesome tasks feature'`
6. **Push**: `git push origin feature/awesome-tasks`
7. **Pull Request**: Детальное описание изменений

### Code Style
```python
# Backend
- Black formatter для Python
- isort для импортов
- Type hints обязательны
- Docstrings для всех функций

# Frontend
- Prettier для JS/JSX
- Tailwind CSS классы
- React Hooks паттерны
- Async/await для API
```

### Testing Guidelines
```bash
# Новые API endpoints
- Unit тесты обязательны
- Integration тесты желательны
- Mock внешние сервисы

# Frontend компоненты
- React Testing Library
- Jest snapshots
- User interaction тесты
```

---

## 📞 Support & Links

### Полезные ссылки
- **🌐 Live Demo**: [https://audiobot-qci2.onrender.com](https://audiobot-qci2.onrender.com)
- **📚 API Docs**: [https://audiobot-qci2.onrender.com/docs](https://audiobot-qci2.onrender.com/docs)
- **📋 GitHub Repo**: [https://github.com/maslovmaksim92/AudioBot](https://github.com/maslovmaksim92/AudioBot)
- **📱 Telegram Bot**: @vasdom_audiobot

### Контакты
- **GitHub Issues**: [Create Issue](https://github.com/maslovmaksim92/AudioBot/issues)
- **Telegram Support**: @vasdom_support
- **Email**: support@vasdom.ru
- **Компания**: VasDom - клининговые услуги в Калуге

### Техническая поддержка
```
🔧 Backend Issues: Проверьте /api/health endpoint
📱 Frontend Issues: Проверьте консоль браузера F12
🔗 Bitrix24 Issues: Тест /api/bitrix24/test
📋 Tasks Issues: Проверьте API /api/tasks/stats
```

---

## 🎉 Changelog

### v3.0.0 (2025-09-09) - Задачи и оптимизация
- ➕ **NEW**: Полнофункциональная вкладка "Задачи" с Bitrix24
- ⚡ **IMPROVED**: Performance оптимизация домов в 6+ раз
- 🏢 **FIXED**: Корректные данные УК из API компаний
- 👥 **FIXED**: Реальные бригады из пользователей
- 🎨 **ENHANCED**: ВАУ-дизайн с градиентами и анимациями

### v2.5.0 (2025-09-08) - ВАУ функционал
- 🎨 **NEW**: Логотип РЯДОМ и креативный дизайн
- 📍 **NEW**: Кликабельные адреса → Google Maps
- ➕ **NEW**: Кнопка "Создать дом" с Bitrix24
- 📊 **IMPROVED**: Расширенные фильтры и экспорт

### v2.0.0 (2025-09-07) - Bitrix24 интеграция
- 🔗 **NEW**: Полная интеграция с Bitrix24 CRM
- 🏠 **NEW**: 490 реальных домов из системы
- 📊 **NEW**: Дашборд с реальной статистикой

---

**🚀 Сделано с ❤️ для VasDom - инновационной клининговой компании Калуги!**

*Powered by FastAPI, React, Bitrix24, Emergent LLM & ❤️*
