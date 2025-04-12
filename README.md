# AudioBot

🎤 Telegram-бот на FastAPI, который:

1. Получает голосовое сообщение.
2. Распознаёт его через **Whisper (локально, offline)**.
3. Отправляет текст пользователю.
4. (TBD) Генерирует голосовой ответ.
5. Отправляет его обратно.

---

## 📁 Структура проекта

```
audiobot/
├── app/
│   ├── api/
│   │   └── bot.py              # Telegram webhook, обработка голоса
│   ├── services/
│   │   └── whisper_service.py  # Распознавание речи через faster-whisper
│   └── main.py                 # FastAPI приложение
│
├── requirements.txt            # Зависимости
├── .env.example                # Пример переменных окружения
├── Dockerfile                  # Docker-образ для Render
└── README.md                   # Документация
```

---

## 🚀 Как запустить

### 1. Переменные окружения `.env`
```env
BOT_TOKEN=your_telegram_bot_token
```

### 2. Установка и запуск
```bash
make install  # установка зависимостей
make run      # запуск FastAPI
```

---

## 📦 Стек:
- FastAPI
- Telegram Bot API
- [faster-whisper](https://github.com/guillaumekln/faster-whisper)
- Docker
- Render (деплой)

---

## 🧩 В планах
- Подключение TTS (Coqui TTS / edge-tts)
- Поддержка кастомных голосов
- Автоматическая генерация речи в ответ
