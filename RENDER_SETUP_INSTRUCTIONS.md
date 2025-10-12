# 🚀 Инструкция по настройке VasDom на Render

## 1. Environment Variables (на Render)

Добавьте следующие переменные в настройках Render:

### Обязательные:
```bash
# База данных (уже должна быть)
DATABASE_URL=postgresql://...

# OpenAI для AI подписей (уже есть)
OPENAI_API_KEY=sk-proj-kh1D...SODQA

# Telegram бот для бригад
TELEGRAM_BOT_TOKEN=<ваш_токен_бота>

# Telegram группа для отправки фото с подписями
TELEGRAM_TARGET_CHAT_ID=<ID_группы>

# Bitrix24 (уже должны быть)
BITRIX24_WEBHOOK_URL=https://...
BITRIX24_CLIENT_ID=...
BITRIX24_CLIENT_SECRET=...
```

### Опциональные:
```bash
# Для LiveKit (если используется)
LIVEKIT_API_KEY=...
LIVEKIT_API_SECRET=...
LIVEKIT_URL=...
```

---

## 2. Как получить TELEGRAM_BOT_TOKEN

### Шаг 1: Создать бота через BotFather

1. Откройте Telegram, найдите **@BotFather**
2. Отправьте команду `/newbot`
3. Введите имя бота (например: `VasDom Cleaning Bot`)
4. Введите username бота (например: `vasdom_cleaning_bot`)
5. BotFather выдаст токен вида: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`

### Шаг 2: Добавить токен на Render

1. Зайдите в Dashboard Render → ваш сервис
2. Environment → Add Environment Variable
3. Key: `TELEGRAM_BOT_TOKEN`
4. Value: (вставьте токен от BotFather)
5. Нажмите Save Changes

---

## 3. Как получить TELEGRAM_TARGET_CHAT_ID

### Вариант 1: Через userinfobot

1. Создайте группу в Telegram для фото уборок
2. Добавьте вашего бота в группу (сделайте его админом)
3. Добавьте бота **@userinfobot** в группу
4. Бот пришлёт ID группы (например: `-1001234567890`)
5. Скопируйте ID и добавьте на Render

### Вариант 2: Через API

1. Добавьте бота в группу
2. Отправьте любое сообщение в группу
3. Откройте в браузере:
   ```
   https://api.telegram.org/bot<ВАШ_ТОКЕН>/getUpdates
   ```
4. Найдите `"chat":{"id":-1001234567890,...}`
5. Это и есть TELEGRAM_TARGET_CHAT_ID

### Шаг 3: Добавить на Render

1. Render Dashboard → Environment
2. Key: `TELEGRAM_TARGET_CHAT_ID`
3. Value: (ID группы с минусом, например `-1001234567890`)
4. Save Changes

---

## 4. Настройка Webhook для Telegram бота

После деплоя на Render выполните:

```bash
curl -X POST "https://api.telegram.org/bot<ВАШ_ТОКЕН>/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://ai-brain-hub-2.onrender.com/api/telegram-webhook/",
    "allowed_updates": ["message", "callback_query"]
  }'
```

**Замените:**
- `<ВАШ_ТОКЕН>` на ваш `TELEGRAM_BOT_TOKEN`
- `ai-brain-hub-2.onrender.com` на ваш домен Render

### Проверка webhook:

```bash
curl "https://api.telegram.org/bot<ВАШ_ТОКЕН>/getWebhookInfo"
```

**Ожидаемый результат:**
```json
{
  "ok": true,
  "result": {
    "url": "https://ai-brain-hub-2.onrender.com/api/telegram-webhook/",
    "has_custom_certificate": false,
    "pending_update_count": 0,
    "last_error_date": 0,
    "max_connections": 40
  }
}
```

---

## 5. Проверка работы приложения

### 5.1 Backend работает?
```bash
curl https://ai-brain-hub-2.onrender.com/health
```

Ожидаемый ответ:
```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2025-10-12T12:00:00"
}
```

### 5.2 Таблица cleaning_photos создана?

Таблица создаётся автоматически при старте приложения через миграции.

Логи на Render:
```
✅ Database initialized successfully
✅ Migration executed: create_cleaning_photos_table.sql
✅ Database migrations completed
```

### 5.3 Telegram бот отвечает?

1. Откройте Telegram, найдите вашего бота
2. Отправьте `/start`
3. Должен прийти список домов:

```
🏠 Выберите дом для загрузки фото:

📅 Сегодня: 12.10.2025
📍 Домов на сегодня: 3

[Кнопки с адресами]
```

---

## 6. Тестирование бота (Бригада 1, дата 13.10)

### Сценарий:

1. **Пользователь (вы)** = Бригада 1
2. **Дата уборки**: 13 октября 2025
3. **Дома для уборки**: 3 адреса (моковые)

### Шаги:

#### Шаг 1: `/start`
→ Выбираете дом из списка

#### Шаг 2: Загружаете 1-3 фото
→ Бот подтверждает: "✅ Фото 1 сохранено"

#### Шаг 3: `/done`
→ Бот:
1. Генерирует AI подпись через GPT-4o-mini
2. **Отправляет в группу** (TELEGRAM_TARGET_CHAT_ID)
3. Сохраняет в БД (cleaning_photos)
4. Подтверждает: "✅ Уборка завершена! 📨 Отправлено в группу"

### Что происходит в группе:

В группу приходит пост:
```
[Фото 1]
[Фото 2] (если больше одного)

🧹 Уборка завершена
🏠 Адрес: ул. Ленина, д. 10, подъезд 1
📅 Дата: 13 октября 2025
👷 Бригада: #1

🌿🧹✨ Сегодня на улице Ленина 10 мы сделали мир немного чище! 
Благодарим наших уборщиков за труд и внимание к деталям...
#Чистота #Благодарность #СоциальнаяОтветственность #Калуга
```

---

## 7. Что дальше? (Итерация 2 продолжение)

После успешного тестирования:

### 7.1 Вебхук в Bitrix24
Добавить отправку вебхука после завершения уборки:
```python
# В handle_done_command после сохранения в БД
await send_bitrix24_webhook(
    house_id=session.selected_house_id,
    cleaning_date=datetime.now().date(),
    photo_urls=[...],
    status="completed"
)
```

Bitrix24 получает данные → запускает БП → отправляет email УК

### 7.2 Реальные данные из БД
Заменить моковые данные:
- Получать список домов из PostgreSQL/Bitrix24 по графику бригады
- Определять тип уборки по дате
- Связать telegram_user_id с brigade_id в БД

### 7.3 Множественные бригады
Добавить таблицу `brigades`:
```sql
CREATE TABLE brigades (
    id UUID PRIMARY KEY,
    name VARCHAR(100),
    telegram_group_chat_id BIGINT,  -- своя группа для каждой бригады
    ...
);
```

---

## 8. Troubleshooting

### Бот не отвечает

**Проверка 1: Webhook установлен?**
```bash
curl "https://api.telegram.org/bot<TOKEN>/getWebhookInfo"
```

**Проверка 2: Backend получает запросы?**
Логи Render → поиск "telegram_webhook"

**Проверка 3: TELEGRAM_BOT_TOKEN правильный?**
Render Dashboard → Environment → проверить значение

### Фото не отправляются в группу

**Проверка 1: TELEGRAM_TARGET_CHAT_ID установлен?**
```bash
# На Render
echo $TELEGRAM_TARGET_CHAT_ID
```

**Проверка 2: Бот админ в группе?**
Telegram группа → Participants → Ваш бот → должен быть Admin

**Проверка 3: Логи backend**
```
grep "telegram_cleaning_bot" /var/log/supervisor/backend.out.log
```

### AI подпись не генерируется

**Проверка: OPENAI_API_KEY установлен?**
```bash
curl https://ai-brain-hub-2.onrender.com/api/health
```

Если ключ неверный → fallback подпись всё равно отправится

### База данных не работает

**Проверка: DATABASE_URL правильный?**
Render Dashboard → Environment → DATABASE_URL

**Проверка: Таблица создалась?**
Логи при старте:
```
✅ Migration executed: create_cleaning_photos_table.sql
```

---

## 9. Мониторинг

### Логи на Render

**Backend:**
- Render Dashboard → Logs → Backend
- Фильтр: `telegram` или `cleaning_photos`

**База данных:**
```sql
-- Сколько фото загружено
SELECT COUNT(*) FROM cleaning_photos;

-- Последние 5 уборок
SELECT house_address, cleaning_date, photo_count, status 
FROM cleaning_photos 
ORDER BY created_at DESC 
LIMIT 5;
```

### Метрики

- **Количество уборок в день**: `COUNT(*) WHERE cleaning_date = CURRENT_DATE`
- **Фото в день**: `SUM(photo_count) WHERE cleaning_date = CURRENT_DATE`
- **Статусы**: `COUNT(*) GROUP BY status`

---

## 10. Безопасность

⚠️ **Важно:**

1. **Никогда не коммитить токены** в Git
2. Использовать только Environment Variables на Render
3. Webhook должен быть по HTTPS
4. Бот должен быть админом только в рабочих группах
5. Регулярно ротировать токены (через BotFather → /revoke)

---

## Готово! 🎉

После выполнения всех шагов:
- ✅ Бот работает
- ✅ Фото отправляются в группу с AI подписями
- ✅ Данные сохраняются в PostgreSQL
- ✅ Готово к интеграции с Bitrix24

**Следующий шаг**: Протестировать полный цикл и добавить вебхук в Bitrix24!
