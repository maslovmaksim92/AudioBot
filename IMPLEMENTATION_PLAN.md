# 🎯 План реализации VasDom - полная версия

## 📊 Текущее состояние (после очистки)

### ✅ Что работает:
- Backend API (server.py) - все endpoints активны
- Frontend UI (Dashboard, основные модули)
- PostgreSQL база данных (499 домов, 21 сотрудник, 1592 подъезда)
- Single Brain архитектура (интенты, резолверы, кэш)
- APScheduler (3 задачи запланированы)
- Bitrix24 синхронизация (30 мин интервал)
- Telegram bot интеграция (частично)

### ❌ Критические проблемы:
1. **Баг с месяцем**: система иногда возвращает November вместо October
   - **Причина**: нужно проверить Bitrix24 данные и логику extract_month
   - **Приоритет**: ВЫСОКИЙ

2. **Баг в периодичности**: неправильный расчёт типов уборок в карточке дома
   - **Причина**: логика расчёта не учитывает 3 типа уборок
   - **Приоритет**: ВЫСОКИЙ

3. **Баг КПИ бригад**: страница белая при смене даты
   - **Причина**: нет пересчёта статистики при изменении даты
   - **Приоритет**: ВЫСОКИЙ

---

## 🚀 ФАЗА 1: Исправление критических багов (1-2 дня)

### 1.1. Исправить баг с определением месяца

**Задачи:**
- [x] Проверить функцию `extract_month` в brain_intents.py (РАБОТАЕТ КОРРЕКТНО)
- [ ] Проверить данные в PostgreSQL: реальные даты уборок
- [ ] Проверить данные из Bitrix24: проверить что возвращает API
- [ ] Добавить логирование в `resolve_cleaning_month` для отладки
- [ ] Проверить timezone - может быть сдвиг UTC vs Moscow time
- [ ] Добавить fallback на текущий месяц ТОЛЬКО если явно не указан

**Файлы для изменения:**
- `backend/app/services/brain_resolvers.py` (строки 123-180)
- `backend/app/services/brain_intents.py` (строки 103-136)
- `backend/app/services/bitrix24_service.py` (метод collect_month)

**Тесты:**
```bash
# Тестовые запросы:
"когда уборка по адресу Ленина 10?"  # должен определить текущий месяц (October)
"когда уборка по адресу Ленина 10 в ноябре?"  # должен вернуть November
"график уборок Ленина 10"  # должен вернуть текущий месяц
```

---

### 1.2. Исправить логику периодичности в карточке дома

**Текущая проблема:** система не правильно определяет периодичность по 3 типам уборок

**3 типа уборок:**
1. **Тип 1**: Влажная уборка лестничных площадок всех этажей и лифта (при наличии); Профилактическая дезинфекция МОП
2. **Тип 2**: Подметание лестничных площадок и маршей всех этажей, влажная уборка 1 этажа и лифта (при наличии); Профилактическая дезинфекция МОП
3. **Тип 3**: Влажная уборка 1 этажа и лифта (при наличии); Профилактическая дезинфекция МОП

**Логика расчёта периодичности:**
- Если 2 даты в месяц Тип 1 → периодичность: "2 раза"
- Если 4 даты в месяц Тип 1 → периодичность: "4 раза"
- Если 2 даты Тип 1 + 2 даты Тип 2 → периодичность: "2 раза + 2 подметания"
- Если 2 даты Тип 1 + 2 даты Тип 3 → периодичность: "2 раза + 1 этаж"
- Если другая комбинация → периодичность: "индивидуальная"
- Если нет дат → периодичность: "не указана"

**Задачи:**
- [ ] Создать функцию `calculate_periodicity(cleaning_dates)` в `brain.py`
- [ ] Обновить модель `CleaningSchedule` с полем `periodicity_type`
- [ ] Обновить компонент `HouseCard.js` для отображения периодичности
- [ ] Добавить endpoint `/api/houses/{house_id}/periodicity` для расчёта

**Файлы для изменения:**
- `backend/app/services/brain.py` - добавить функцию расчёта
- `backend/app/models/house.py` - добавить поле periodicity
- `frontend/src/components/Works/HouseCard.js` - отображение
- `backend/app/routers/houses.py` - новый endpoint

**Пример кода:**
```python
def calculate_periodicity(cleaning_dates: CleaningSchedule) -> str:
    """Расчёт периодичности на основе типов уборок"""
    if not cleaning_dates:
        return "не указана"
    
    # Подсчитываем даты по типам
    type1_count = 0
    type2_count = 0
    type3_count = 0
    
    for period in ['october_1', 'october_2', 'november_1', 'november_2']:
        period_data = getattr(cleaning_dates, period, None)
        if period_data and isinstance(period_data, dict):
            cleaning_type = period_data.get('type', '')
            dates_count = len(period_data.get('dates', []))
            
            if 'всех этажей' in cleaning_type and 'Влажная' in cleaning_type:
                type1_count += dates_count
            elif 'Подметание' in cleaning_type:
                type2_count += dates_count
            elif 'Влажная уборка 1 этажа' in cleaning_type:
                type3_count += dates_count
    
    # Логика определения периодичности
    if type1_count > 0 and type2_count == 0 and type3_count == 0:
        return f"{type1_count} раза" if type1_count > 1 else f"{type1_count} раз"
    elif type1_count > 0 and type2_count > 0 and type3_count == 0:
        return f"{type1_count} раза + {type2_count} подметания"
    elif type1_count > 0 and type3_count > 0 and type2_count == 0:
        return f"{type1_count} раза + 1 этаж"
    elif type1_count > 0 or type2_count > 0 or type3_count > 0:
        return "индивидуальная"
    else:
        return "не указана"
```

---

### 1.3. Исправить баг пересчёта КПИ бригад

**Проблема:** при выборе даты страница становится белой, не происходит пересчёт статистики

**Задачи:**
- [ ] Найти компонент `BrigadeKPI.js` или аналогичный
- [ ] Добавить обработчик onChange для date picker
- [ ] Создать функцию `recalculateKPI(date)` 
- [ ] Добавить loading state во время перерасчёта
- [ ] Обновить endpoint `/api/employees/brigades/kpi` для приёма параметра date

**Файлы для изменения:**
- `frontend/src/components/Employees/BrigadeKPI.js` (или Employees.js)
- `backend/app/routers/employees.py` - endpoint для КПИ по дате

**Пример кода (Frontend):**
```javascript
const [selectedDate, setSelectedDate] = useState(new Date());
const [kpiData, setKpiData] = useState(null);
const [loading, setLoading] = useState(false);

const handleDateChange = async (date) => {
    setSelectedDate(date);
    setLoading(true);
    try {
        const formattedDate = date.toISOString().split('T')[0];
        const response = await fetch(`/api/employees/brigades/kpi?date=${formattedDate}`);
        const data = await response.json();
        setKpiData(data);
    } catch (error) {
        console.error('Error fetching KPI:', error);
    } finally {
        setLoading(false);
    }
};

return (
    <div>
        <DatePicker 
            selected={selectedDate} 
            onChange={handleDateChange} 
        />
        {loading ? <Spinner /> : <KPITable data={kpiData} />}
    </div>
);
```

---

## 🚀 ФАЗА 2: Works модуль - Telegram бот для фото (2-3 дня)

### Цель: 
Бригада загружает фото уборки через Telegram бота → фото отправляются в группу с AI подписью → вебхук в Bitrix24 → email в УК

### 2.1. Telegram бот для бригад

**Функционал:**
1. Бригада открывает бота → видит список домов на сегодня
2. Выбирает дом → загружает фото
3. Нажимает "Уборка завершена"
4. Фото отправляются в Telegram группу с AI подписью
5. Вебхук отправляет данные в Bitrix24
6. Bitrix24 отправляет email в УК

**Задачи:**
- [ ] Создать Telegram bot команду `/start` - показать список домов на сегодня
- [ ] Создать inline keyboard с адресами домов
- [ ] Обработчик загрузки фото (callback_query handler)
- [ ] Интеграция с PostingFotoTG (AI подпись)
- [ ] Отправка фото в целевую группу
- [ ] Вебхук в Bitrix24 для email уведомлений
- [ ] Сохранение данных в PostgreSQL (cleaning_photos таблица)

**Файлы для создания:**
- `backend/app/services/telegram_cleaning_bot.py` - логика бота для бригад
- `backend/app/models/cleaning_photo.py` - модель для фото
- `backend/app/routers/telegram_webhook.py` - вебхук обработчик (уже есть, расширить)
- `backend/app/services/photo_ai_caption.py` - генерация AI подписей

**Структура БД (cleaning_photos):**
```sql
CREATE TABLE cleaning_photos (
    id UUID PRIMARY KEY,
    house_id UUID REFERENCES houses(id),
    brigade_id UUID REFERENCES brigades(id),
    photo_url TEXT,
    photo_telegram_id TEXT,
    caption TEXT,
    ai_caption TEXT,
    created_at TIMESTAMP,
    cleaning_date DATE,
    cleaning_type VARCHAR(255),
    sent_to_bitrix BOOLEAN DEFAULT FALSE,
    bitrix_deal_id TEXT
);
```

**Пример Telegram bot кода:**
```python
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler, MessageHandler, filters

async def start_cleaning(update: Update, context):
    """Показать список домов на сегодня"""
    user_id = update.effective_user.id
    
    # Получить бригаду пользователя
    brigade = await get_brigade_by_telegram_id(user_id)
    if not brigade:
        await update.message.reply_text("Вы не зарегистрированы в системе")
        return
    
    # Получить дома на сегодня для бригады
    today = datetime.now().date()
    houses = await get_houses_for_brigade_by_date(brigade.id, today)
    
    # Создать клавиатуру
    keyboard = []
    for house in houses:
        button = InlineKeyboardButton(
            text=house.address,
            callback_data=f"house_{house.id}"
        )
        keyboard.append([button])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Выберите дом для загрузки фото:",
        reply_markup=reply_markup
    )

async def handle_house_selection(update: Update, context):
    """Обработка выбора дома"""
    query = update.callback_query
    await query.answer()
    
    house_id = query.data.replace("house_", "")
    context.user_data['selected_house'] = house_id
    
    await query.edit_message_text(
        "Отправьте фото уборки. Когда закончите, нажмите /done"
    )

async def handle_photo(update: Update, context):
    """Обработка загруженного фото"""
    if 'selected_house' not in context.user_data:
        await update.message.reply_text("Сначала выберите дом командой /start")
        return
    
    photo = update.message.photo[-1]  # Largest size
    file_id = photo.file_id
    
    # Сохранить временно
    if 'photos' not in context.user_data:
        context.user_data['photos'] = []
    context.user_data['photos'].append(file_id)
    
    await update.message.reply_text(
        f"Фото {len(context.user_data['photos'])} сохранено. "
        "Отправьте ещё или нажмите /done"
    )

async def complete_cleaning(update: Update, context):
    """Завершить уборку и отправить фото"""
    house_id = context.user_data.get('selected_house')
    photos = context.user_data.get('photos', [])
    
    if not house_id or not photos:
        await update.message.reply_text("Нет данных для отправки")
        return
    
    await update.message.reply_text("Обрабатываю фото...")
    
    # 1. Получить информацию о доме
    house = await get_house_by_id(house_id)
    
    # 2. Сгенерировать AI подпись
    ai_caption = await generate_ai_caption(house.address, len(photos))
    
    # 3. Отправить фото в целевую группу
    target_chat_id = os.getenv('TELEGRAM_TARGET_CHAT_ID')
    for photo_id in photos:
        await context.bot.send_photo(
            chat_id=target_chat_id,
            photo=photo_id,
            caption=ai_caption
        )
    
    # 4. Сохранить в БД
    for photo_id in photos:
        await save_cleaning_photo(
            house_id=house_id,
            photo_telegram_id=photo_id,
            ai_caption=ai_caption
        )
    
    # 5. Вебхук в Bitrix24
    await send_to_bitrix24(house_id, photos, ai_caption)
    
    # Очистить данные
    context.user_data.clear()
    
    await update.message.reply_text(
        f"✅ Уборка завершена!\n"
        f"📸 Отправлено {len(photos)} фото\n"
        f"🏠 Адрес: {house.address}"
    )

# Регистрация хендлеров
app.add_handler(CommandHandler("start", start_cleaning))
app.add_handler(CommandHandler("done", complete_cleaning))
app.add_handler(CallbackQueryHandler(handle_house_selection, pattern="^house_"))
app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
```

---

### 2.2. Интеграция PostingFotoTG (AI подпись)

**Задача:** использовать код из https://github.com/maslovmaksim92/PostingFotoTG для генерации AI подписей

**Что нужно:**
- [ ] Склонировать репозиторий PostingFotoTG
- [ ] Извлечь функцию генерации AI подписей
- [ ] Адаптировать под формат VasDom (адрес дома, дата, тип уборки)
- [ ] Интегрировать в `photo_ai_caption.py`

---

### 2.3. Кнопка "Акт подписан" в Dashboard

**Задачи:**
- [ ] Добавить кнопку "Акт подписан" в HouseCard компонент
- [ ] Создать endpoint `/api/houses/{house_id}/sign_act`
- [ ] Добавить поле `act_signed` в таблицу cleaning_records
- [ ] Создать статистику подписанных актов на месяц
- [ ] Добавить виджет на Dashboard "Подписанные акты: X/Y"

**Файлы:**
- `frontend/src/components/Works/HouseCard.js` - кнопка
- `backend/app/routers/houses.py` - endpoint
- `frontend/src/components/Dashboard/ActsWidget.js` - виджет статистики

---

## 🚀 ФАЗА 3: AI Chat синхронизация с Telegram (2 дня)

### Цель:
Диалоги из дашборда и Telegram бота синхронизированы. 1 чат = 1 диалог. История для каждого сотрудника.

### 3.1. Унификация чатов

**Задачи:**
- [ ] Создать таблицу `chat_messages` в PostgreSQL
- [ ] Каждое сообщение имеет: user_id, platform (web/telegram), content, timestamp
- [ ] При отправке из web → сохранить в БД + отправить в Telegram
- [ ] При получении из Telegram → сохранить в БД + отправить в web (WebSocket)
- [ ] Implement WebSocket для realtime синхронизации

**Структура БД (chat_messages):**
```sql
CREATE TABLE chat_messages (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    platform VARCHAR(20), -- 'web' or 'telegram'
    content TEXT,
    role VARCHAR(20), -- 'user' or 'assistant'
    created_at TIMESTAMP,
    telegram_message_id BIGINT,
    brain_metadata JSONB -- sources, intent, etc
);
```

**Файлы:**
- `backend/app/models/chat.py` - модель
- `backend/app/services/chat_sync_service.py` - логика синхронизации
- `backend/app/routers/chat.py` - WebSocket endpoint
- `frontend/src/components/AIChat/ChatSync.js` - WebSocket клиент

---

### 3.2. Ответы на рекламации

**Функционал:**
- Клиент пишет: "не было уборки 9 числа"
- AI отвечает: "Уборка была проведена 9.10.2025. Вот ссылки на фото: [ссылка1, ссылка2, ...]"
- Клиент пишет: "когда уборка по адресу Ленина 10?"
- AI отвечает: "График уборки на месяц: 5.10, 12.10, 19.10, 26.10"

**Задачи:**
- [ ] Добавить intent "рекламация" в brain_intents.py
- [ ] Создать resolver `resolve_complaint` в brain_resolvers.py
- [ ] Resolver должен:
  - Извлечь адрес и дату
  - Найти фото уборки на эту дату
  - Вернуть ссылки на фото и статус уборки

---

## 🚀 ФАЗА 4: Employees - Календарь бригад + KPI (1-2 дня)

### 4.1. Календарь бригад

**Задача:** состав бригады может меняться по дням

**Структура БД (brigade_calendar):**
```sql
CREATE TABLE brigade_calendar (
    id UUID PRIMARY KEY,
    brigade_id UUID REFERENCES brigades(id),
    employee_id UUID REFERENCES employees(id),
    date DATE,
    role VARCHAR(100), -- 'бригадир', 'рабочий'
    status VARCHAR(50) -- 'active', 'sick', 'vacation'
);
```

**Файлы:**
- `backend/app/models/brigade.py` - модель календаря
- `frontend/src/components/Employees/BrigadeCalendar.js` - календарь
- `backend/app/routers/brigades.py` - CRUD endpoints

---

### 4.2. KPI по каждому сотруднику

**Задача:** показать KPI отдельно по каждому сотруднику и бригаде

**Метрики:**
- Влажная уборка: количество подъездов, этажей, домов
- Подметание: количество подъездов, этажей, домов

**Файлы:**
- `backend/app/routers/employees.py` - endpoint `/api/employees/{id}/kpi`
- `frontend/src/components/Employees/EmployeeKPI.js` - компонент

---

## 🚀 ФАЗА 5: Meetings с realtime транскрибацией (2-3 дня)

### Технология: OpenAI Realtime API + LiveKit

**Задачи:**
- [ ] Использовать существующий код LiveKit интеграции из server.py
- [ ] Создать endpoint `/api/meetings/start` - начать запись
- [ ] Realtime транскрибация через OpenAI Realtime API
- [ ] Сохранение текста в БД (meetings таблица)
- [ ] Генерация саммари после окончания встречи
- [ ] Автоматическая постановка задач из протокола

**Файлы:**
- `backend/app/services/meeting_service.py` - логика встреч
- `backend/app/models/meeting.py` - модель
- `frontend/src/components/Meetings/MeetingRoom.js` - UI

---

## 🚀 ФАЗА 6: Дополнительные модули (по приоритету)

### 6.1. Tasks + AI-предложенные задачи
- Утренняя планерка → автораспределение задач
- AI предлагает задачи на основе истории

### 6.2. Бизнес-процессы (визуальные воронки)
- React Flow для визуализации
- Канбан-доски с DnD

### 6.3. Training (Barin)
- Загрузка Word/Excel → AI саммари → добавление в знания
- Лента уроков с квизами

### 6.4. Кнопка "Улучшить раздел"
- Prompt для GPT-5 для онлайн улучшений
- Emergent LLM key интеграция

---

## 📅 Временная оценка

| Фаза | Задачи | Время | Приоритет |
|------|--------|-------|-----------|
| Фаза 1 | Исправление багов | 1-2 дня | 🔴 ВЫСОКИЙ |
| Фаза 2 | Works + Telegram бот | 2-3 дня | 🔴 ВЫСОКИЙ |
| Фаза 3 | AI Chat синхронизация | 2 дня | 🟡 СРЕДНИЙ |
| Фаза 4 | Employees улучшения | 1-2 дня | 🟡 СРЕДНИЙ |
| Фаза 5 | Meetings realtime | 2-3 дня | 🟢 НИЗКИЙ |
| Фаза 6 | Дополнительные | по запросу | 🟢 НИЗКИЙ |

**Общее время: 8-12 дней**

---

## 🎯 Следующие шаги

1. **Немедленно начать с Фазы 1** - исправить критические баги
2. После исправления багов → демо пользователю
3. Приоритизировать Фазу 2 или Фазу 3 по выбору пользователя
4. Итеративная разработка: реализовать → тестировать → получить фидбек

**Готов начать! С какой фазы начинаем?**
