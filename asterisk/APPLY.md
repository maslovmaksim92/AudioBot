# Как Применить Конфигурацию Asterisk

## Шаг 1: Подключитесь к VM

```bash
ssh root@51.250.74.43
```

## Шаг 2: Откройте pjsip.conf

```bash
nano /etc/asterisk/pjsip.conf
```

**Действия в nano:**
1. Нажмите `Ctrl+K` много раз, чтобы удалить весь текст
2. Скопируйте содержимое `pjsip_ready.conf` с вашего компьютера
3. Нажмите `Ctrl+V` для вставки
4. Нажмите `Ctrl+X`, затем `Y`, затем `Enter` для сохранения

## Шаг 3: Откройте extensions.conf

```bash
nano /etc/asterisk/extensions.conf
```

**Действия в nano:**
1. Нажмите `Ctrl+K` много раз, чтобы удалить весь текст
2. Скопируйте содержимое `extensions_ready.conf` с вашего компьютера
3. Нажмите `Ctrl+V` для вставки
4. Нажмите `Ctrl+X`, затем `Y`, затем `Enter` для сохранения

## Шаг 4: Перезагрузите Asterisk

```bash
asterisk -rx "core reload"
```

## Шаг 5: Проверьте статус

```bash
asterisk -rx "pjsip show endpoints"
asterisk -rx "pjsip show registrations"
```

**Ожидаемый результат:**
```
novofon-endpoint: Registered
livekit-endpoint: Not in use (это нормально)
```

## Шаг 6: Тестовый звонок

Из вашего приложения сделайте AI звонок. Вы должны услышать AI голос вместо эха!

## Важные Изменения:

✅ **LiveKit endpoint** настроен для приема звонков из LiveKit Cloud
✅ **Context from-livekit** правильно маршрутизирует звонки на PSTN через Novofon
✅ **Answer + Wait(0.5)** дает время AI агенту для подключения перед Dial
✅ **Поддержка всех форматов номеров**: +7XXXXXXXXXX, 7XXXXXXXXXX, и других

## Отладка:

Если звонок не работает, смотрите логи в реальном времени:

```bash
tail -f /var/log/asterisk/full
```

Ищите строки с "from-livekit" и проверяйте, как обрабатывается звонок.