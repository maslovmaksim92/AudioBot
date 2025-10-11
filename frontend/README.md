# VasDom AudioBot - Frontend

React 19 + TailwindCSS + shadcn/ui приложение.

## Быстрый старт

```bash
# Установить зависимости
yarn install

# Запустить dev сервер
yarn start

# Собрать production
yarn build
```

## Структура

```
frontend/
├── src/
│   ├── App.js            # Главный компонент с роутингом
│   ├── App.css
│   ├── index.js
│   ├── index.css
│   ├── components/
│   │   ├── Layout/       # Sidebar, Layout
│   │   ├── Dashboard/    # Главная страница
│   │   ├── Works/        # Дома и объекты
│   │   ├── AIChat/       # AI чат
│   │   ├── Meetings/     # Планёрки
│   │   ├── Training/     # База знаний
│   │   ├── Tasks/        # Задачи
│   │   ├── AITasks/      # AI задачи
│   │   ├── Employees/    # Сотрудники
│   │   ├── Sales/        # Воронка продаж
│   │   ├── Logistics/    # Логистика
│   │   ├── Logs/         # Системные логи
│   │   ├── Finances/     # Финансовый модуль
│   │   └── ui/           # shadcn/ui компоненты
│   ├── hooks/
│   │   └── use-toast.js
│   └── lib/
│       └── utils.js
├── public/
├── package.json
├── tailwind.config.js
├── craco.config.js
└── .env                  # Frontend env vars (не в Git!)
```

## .env

```bash
REACT_APP_BACKEND_URL=http://localhost:8001
```

## Маршруты

- `/` - Dashboard
- `/agents` - AI Агенты
- `/works` - Дома
- `/sales` - Воронка продаж
- `/employees` - Сотрудники
- `/ai-chat` - AI Чат
- `/live-conversation` - Голосовой разговор
- `/agent-builder` - Конструктор агентов
- `/meetings` - Планёрки
- `/training` - База знаний
- `/tasks` - Задачи
- `/ai-tasks` - AI Задачи
- `/logistics` - Логистика
- `/logs` - Логи

## UI компоненты

Используем shadcn/ui из `@/components/ui`:
- Button, Card, Input, Dialog
- Select, Checkbox, Switch
- Table, Tabs, Toast
- и 50+ других

## Логи

```bash
tail -f /var/log/supervisor/frontend.err.log
```

## Документация

См. корневой `/app/README.md` и `/app/SETUP_GUIDE.md`