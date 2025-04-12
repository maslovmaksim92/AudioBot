# AudioBot

🎤 Telegram-бот на FastAPI, который:

1. Получает голосовое сообщение.
2. Распознаёт его через **Yandex SpeechKit** (STT).
3. Отправляет текст пользователю.
4. Генерирует ответ голосом через **TTS (Text-To-Speech)**.
5. Отправляет голосовое сообщение обратно.

## 🚀 Как развернуть

### 1. Переменные окружения `.env`

```env
BOT_TOKEN=your_telegram_bot_token
YANDEX_API_KEY=your_yandex_api_key
FOLDER_ID=b1g82mk09fb4f18hap3b
VOICE=oksana
LANGUAGE=ru-RU
```

### 2. Запуск локально
```bash
make install  # установка зависимостей
make run      # запуск приложения
```

### 3. Docker
```bash
docker build -t audiobot .
docker run --env-file .env -p 8000:8000 audiobot
```

## 🧠 Возможности
- Распознавание речи (Speech-To-Text)
- Синтез речи (Text-To-Speech)
- Отправка текста и голоса в Telegram

---

## 📦 Стек:
- FastAPI
- Telegram Bot API
- Yandex SpeechKit
- Docker
- Render (деплой)

Проект создан автоматически — backend генерация идёт далее.
