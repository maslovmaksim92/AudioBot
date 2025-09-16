VasDom AudioBot — интеллектуальная система управления клинингом

Кратко
- Цель: единая платформа для работы с объектами (дома), бригадами, графиками уборок, коммуникацией и отчётностью
- Интеграции:
  - Bitrix24 CRM (сделки воронки «Уборка подъездов», компании/контакты, статусы)
  - AI (Emergent LLM) — текстовые ответы и аналитика, RAG-поиск по базе знаний
  - Голос (OpenAI Realtime, WebRTC) — онлайн-разговор и онлайн-транскрипция
  - Telegram — уведомления по задачам
- Интерфейс:
  - Dashboard — метрики, «Сегодня», графики по статусам, быстрые фильтры
  - Дома — список домов с фильтрами/периодичностью/графиком/деталями
  - AI Chat — чат + «Разговор онлайн» (текст + голос)
  - Планёрка — онлайн-транскрипция и саммари встреч
  - Обучение — загрузка файлов, «что понял ИИ», подтверждение и запись в базу знаний
  - AI Задачи — постановка задач ИИ с расписанием (в т.ч. отправка в Telegram)
  - Логистика — планирование маршрутов (Google Maps; подключается по ключу)

Архитектура
- Backend: FastAPI (backend/server.py), httpx, websockets, PyJWT, asyncpg, APScheduler, (pgvector подготовлено)
- Frontend: React 19, React Router, TailwindCSS, shadcn/ui, react-datepicker, (chart-библиотека для графиков)
- Деплой: Render (Procfile + render.yaml), uvicorn; фронт — static build
- Интеграции: Bitrix24 (webhook API), Emergent LLM SDK, OpenAI Realtime (WebRTC)

Основные возможности
1) Дома (Works)
- Фильтры: бригада, УК, точная дата, диапазон дат (yyyy-MM-dd)
- Быстрые пресеты: Сегодня, Завтра, Неделя (календарная), Месяц (календарный)
- Карточка: адрес, квартиры/подъезды/этажи, УК, бригада, Периодичность
- Действия: «Посмотреть график», «Детали», «Открыть в Bitrix24» (+ в модалке «График» также есть кнопка Bitrix24)
- Периодичность — по реальным датам (сентябрь как базовый месяц), без повторов
- Пагинация — только снизу, плавная прокрутка

2) Dashboard
- Верхние фильтры (бригада/УК/диапазон дат + пресеты)
- Блок «Сегодня»: запланировано/выполнено/в процессе (кэш + безопасные фоллбэки при 503)
- График статусов воронки 34 (Pie/Bar) с кэшированием (5–10 мин)

3) AI Chat
- Текстовые ответы (Emergent LLM)
- «Разговор онлайн»: WebRTC с OpenAI Realtime, всегда «текст + голос» в ответах

4) Планёрка
- Live-транскрипция (через OpenAI Realtime), авто-саммари, экспорт .txt
- Кнопки старт/стоп

5) Обучение (База знаний)
- Загрузка файлов, извлечение текста, «что понял ИИ», подтверждение и запись в базу знаний (PostgreSQL + pgvector)
- Поиск по знаниям (RAG)

6) AI Задачи
- Создание задач с расписанием (apscheduler), хранение в БД
- Отправка в Telegram по времени (при наличии токена)

7) Логистика (Google Maps)
- Эндпоинт и UI подготовлены; требуется GOOGLE_MAPS_API_KEY для включения реального расчёта маршрутов (ETA, дистанции)

API — основные маршруты (все начинаются с /api)
- Дома
  - GET /cleaning/houses — список домов, фильтры: brigade, management_company, cleaning_date, date_from, date_to, пагинация page/limit
  - GET /cleaning/filters — опции фильтров (бригады/УК/статусы)
  - GET /cleaning/house/{id}/details — детали дома (house.bitrix_url включён)
- Dashboard
  - GET /dashboard/stats — агрегаты для главной панели
- AI
  - POST /ai/chat — текстовый AI ответ (Emergent LLM)
- Voice (OpenAI Realtime)
  - POST /voice/token — эфемерный JWT (5 минут) для WebRTC
  - WS  /voice/ws/{session_id} — прокси браузер ↔ FastAPI ↔ OpenAI Realtime (стрим текст+аудио)
- Обучение (Knowledge; подготовлено)
  - POST /knowledge/upload — загрузка файла
  - GET  /knowledge/pending — список «что понял» для подтверждения
  - POST /knowledge/confirm — подтверждение записи в БЗ
  - GET  /knowledge/search?q=... — поиск по базе знаний
- Задачи ИИ (подготовлено)
  - POST /ai-tasks — создать задачу (текст, время)
  - GET  /ai-tasks — список задач, статусы
  - Webhook Telegram — отправка по времени (если задан TELEGRAM_BOT_TOKEN)
- Логистика (подготовлено)
  - POST /logistics/route — вход: адреса/ограничения, выход: оптимальный маршрут (после добавления ключа Google)

Роутинги фронтенда
- /dashboard — главная панель (фильтры, «Сегодня», график)
- /works — дома (фильтры + пресеты, карточки, график, детали, Bitrix24)
- /ai — AI Chat (кнопка «Разговор онлайн»)
- /meetings — Планёрка (live-транскрипция, саммари, экспорт)
- /training — Обучение (файлы, «что понял», подтверждение, статус «обучен»)
- /tasks — AI Задачи (создание, список, статусы)

Переменные окружения (Render)
- Frontend
  - REACT_APP_BACKEND_URL — URL бэкенда (например, https://audiobot-qci2.onrender.com)
  - REACT_APP_FRONTEND_URL — URL фронтенда (например, https://audiobot-1-cv3f.onrender.com)
- Backend
  - BITRIX24_WEBHOOK_URL — вебхук Bitrix24
  - EMERGENT_LLM_KEY — ключ Emergent LLM (для текстовых ответов)
  - OPENAI_API_KEY или OPEN_AI_KEY — ключ OpenAI (Realtime голос/стт/ттс)
  - JWT_SECRET — секрет для эфемерных JWT токенов (WebRTC)
  - DATABASE_URL — строка подключения к PostgreSQL (asyncpg)
  - TELEGRAM_BOT_TOKEN — (опц.) для уведомлений задач
  - GOOGLE_MAPS_API_KEY — (опц.) для логистических маршрутов
  - CORS_ORIGINS — по умолчанию "*"

Локальный запуск
Backend
1) python -m venv venv
2) source venv/bin/activate  (Windows: venv\\Scripts\\activate)
3) pip install -r backend/requirements.txt
4) uvicorn backend.server:app --reload --host 0.0.0.0 --port 8001

Frontend
1) cd frontend
2) yarn install
3) yarn start

Деплой на Render
- Procfile: web: uvicorn backend.server:app --host 0.0.0.0 --port=$PORT
- render.yaml: содержит два сервиса — backend (python web) и frontend (static)
- Корневой requirements.txt ссылается на backend/requirements.txt (исправляет ошибку build: "requirements.txt not found")
- Задайте ENV переменные, описанные выше, и перезапустите сервисы

Безопасность
- Не храните ключи в коде/README. Все секреты — только в ENV Render
- Ротация ключей при компрометации

Известные ограничения
- Логистика в проде заработает после добавления GOOGLE_MAPS_API_KEY
- Стабильность Bitrix24: реализованы ретраи и кэш, но при длительных 503 данные могут быть ограничены временно

Changelog (последний пакет)
- Works: периодичность, фильтры/пресеты, нижняя пагинация, Bitrix24 в карточке и модалке
- Dashboard: добавлена верхняя панель фильтров, блок «Сегодня», график статусов (с кэшом)
- AI Chat: добавлен «Разговор онлайн» (WebRTC + OpenAI Realtime), ответы текст+голос
- Планёрка: live-транскрипция, авто-саммари, экспорт
- Обучение: загрузка, «что понял», подтверждение, запись в БЗ (Postgres + pgvector)
- AI Задачи: задачи с расписанием (apscheduler), отправка в Telegram
- Логистика: эндпоинт и UI; включение реального расчёта после GOOGLE_MAPS_API_KEY
- Render: добавлены Procfile и render.yaml; requirements.txt в корне ссылается на backend/requirements.txt

Поддержка
- Вопросы по деплою: https://render.com/docs
- Вопросы по Bitrix24: https://dev.1c-bitrix.ru/rest_help/
- Вопросы по OpenAI Realtime: https://platform.openai.com/docs/guides/realtime
- По приложению: см. исходный код и комментарии в backend/server.py и frontend/src/components