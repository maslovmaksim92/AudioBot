-- Создание таблицы для хранения саммари звонков
CREATE TABLE IF NOT EXISTS call_summaries (
    id VARCHAR PRIMARY KEY,
    call_id VARCHAR UNIQUE,
    caller VARCHAR,
    called VARCHAR,
    direction VARCHAR,  -- 'in' или 'out'
    duration INTEGER,  -- Длительность в секундах
    record_url VARCHAR,  -- Ссылка на запись
    transcription TEXT,  -- Полная транскрипция
    summary TEXT,  -- Краткое саммари
    key_points JSONB,  -- Ключевые пункты
    action_items JSONB,  -- Задачи к выполнению
    sentiment VARCHAR,  -- positive/neutral/negative
    client_request TEXT,  -- Основной запрос клиента
    next_steps TEXT,  -- Следующие шаги
    telegram_sent BOOLEAN DEFAULT FALSE,
    bitrix_sent BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Индексы для быстрого поиска
CREATE INDEX IF NOT EXISTS idx_call_summaries_call_id ON call_summaries(call_id);
CREATE INDEX IF NOT EXISTS idx_call_summaries_caller ON call_summaries(caller);
CREATE INDEX IF NOT EXISTS idx_call_summaries_created_at ON call_summaries(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_call_summaries_direction ON call_summaries(direction);

-- Комментарии
COMMENT ON TABLE call_summaries IS 'Саммари телефонных звонков из Новофон';
COMMENT ON COLUMN call_summaries.call_id IS 'ID звонка из Новофон';
COMMENT ON COLUMN call_summaries.transcription IS 'Полная транскрипция через Whisper';
COMMENT ON COLUMN call_summaries.summary IS 'Краткое саммари через GPT-5';
COMMENT ON COLUMN call_summaries.key_points IS 'Ключевые пункты обсуждения';
COMMENT ON COLUMN call_summaries.action_items IS 'Задачи к выполнению';
