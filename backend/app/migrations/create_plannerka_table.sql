-- Создание таблицы для хранения планёрок
CREATE TABLE IF NOT EXISTS plannerka_meetings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    date DATE NOT NULL DEFAULT CURRENT_DATE,
    start_time TIMESTAMP NOT NULL DEFAULT NOW(),
    end_time TIMESTAMP,
    transcription TEXT,
    summary TEXT,
    tasks JSONB DEFAULT '[]'::jsonb,
    participants TEXT[],
    created_by VARCHAR(100),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Индексы для быстрого поиска
CREATE INDEX IF NOT EXISTS idx_plannerka_meetings_date ON plannerka_meetings(date DESC);
CREATE INDEX IF NOT EXISTS idx_plannerka_meetings_created_at ON plannerka_meetings(created_at DESC);

-- Комментарии
COMMENT ON TABLE plannerka_meetings IS 'Планёрки с транскрипциями и задачами';
COMMENT ON COLUMN plannerka_meetings.transcription IS 'Полный текст транскрипции речи';
COMMENT ON COLUMN plannerka_meetings.summary IS 'AI-саммари планёрки';
COMMENT ON COLUMN plannerka_meetings.tasks IS 'Извлечённые задачи в формате JSON [{title, assignee, deadline}]';
