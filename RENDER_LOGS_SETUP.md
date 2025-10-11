# Настройка интеграции с Render для получения логов

## 1. Получение Render API Key

1. Зайдите на https://dashboard.render.com/
2. Перейдите в **Account Settings** → **API Keys**
3. Создайте новый API ключ или используйте существующий
4. Скопируйте ключ

## 2. Получение Service ID

### Через Dashboard:
1. Откройте ваш сервис на Render
2. В URL вы увидите: `https://dashboard.render.com/web/srv-XXXXX`
3. `srv-XXXXX` - это ваш Service ID

### Через API:
```bash
curl -H "Authorization: Bearer YOUR_RENDER_API_KEY" \
  https://api.render.com/v1/services
```

## 3. Настройка переменных окружения

### Локально (для разработки):
Добавьте в `/app/backend/.env`:
```bash
RENDER_API_KEY=rnd_XXXXXXXXXXXXXXXXXXXX
RENDER_SERVICE_ID=srv-XXXXXXXXXXXXXXXXXXXXX
```

### На Render (production):
1. Откройте настройки вашего сервиса
2. Перейдите в **Environment** → **Environment Variables**
3. Добавьте:
   - `RENDER_API_KEY` = ваш API ключ
   - `RENDER_SERVICE_ID` = ID вашего сервиса

## 4. Проверка работы

### Через API:
```bash
# Получить список сервисов
curl http://localhost:8001/api/render-logs/services

# Получить логи с Render (последние 100 строк)
curl "http://localhost:8001/api/render-logs/stream?tail=100"

# Получить локальные логи
curl "http://localhost:8001/api/render-logs/local?log_file=backend&lines=100"
```

### Через UI:
1. Откройте https://money-tracker-1172.preview.emergentagent.com/#/logs
2. Выберите источник: **Render** или **Local**
3. Настройте количество строк и период
4. Нажмите **Обновить**
5. Используйте кнопку **Копировать** для копирования логов

## 5. Особенности

### Render API Limits:
- Максимум 1000 строк логов за запрос
- Rate limit: 100 запросов/минуту
- Логи хранятся 7 дней

### Локальные логи:
- Доступны файлы: `backend.err.log`, `frontend.err.log`
- Максимум 1000 строк
- Только для development окружения

## 6. Troubleshooting

### Ошибка: "RENDER_API_KEY not configured"
- Проверьте что ключ добавлен в `.env`
- Перезапустите backend: `supervisorctl restart backend`

### Ошибка: "Service not found"
- Проверьте правильность `RENDER_SERVICE_ID`
- Убедитесь что у API ключа есть доступ к сервису

### Логи не загружаются с Render:
- Проверьте что сервис задеплоен на Render
- Убедитесь что API ключ валидный
- Попробуйте получить список сервисов: `/api/render-logs/services`

## 7. Автоматическая настройка

Если `RENDER_API_KEY` не настроен, UI автоматически переключится на локальные логи.

## 8. API Documentation

### GET /api/render-logs/stream
Получить логи с Render
- `service_id` (optional) - ID сервиса
- `tail` (default: 100) - количество строк

### GET /api/render-logs/local
Получить локальные логи
- `log_file` (required) - "backend" или "frontend"
- `lines` (default: 100) - количество строк

### GET /api/render-logs/services
Получить список всех сервисов на Render

## 9. Пример использования в коде

```javascript
// Получить логи с Render
const response = await axios.get(`${BACKEND_URL}/api/render-logs/stream`, {
  params: { tail: 500 }
});

// Копировать в буфер обмена
navigator.clipboard.writeText(response.data.logs_text);

// Скачать как файл
const blob = new Blob([response.data.logs_text], { type: 'text/plain' });
const url = URL.createObjectURL(blob);
```

## 10. Security

⚠️ **Важно:**
- Никогда не коммитьте `.env` файлы с реальными ключами
- Используйте разные API ключи для development и production
- Регулярно ротируйте API ключи
- Ограничьте права доступа API ключа только на чтение логов
