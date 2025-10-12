-- Таблица для хранения фото уборок от бригад через Telegram бота
CREATE TABLE IF NOT EXISTS cleaning_photos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Идентификаторы
    house_id VARCHAR(100) NOT NULL,  -- ID дома из Bitrix24
    house_address TEXT NOT NULL,      -- Адрес для отображения
    brigade_id VARCHAR(50),           -- ID бригады
    telegram_user_id BIGINT,          -- Telegram ID пользователя
    
    -- Данные уборки
    cleaning_date DATE NOT NULL,              -- Дата уборки
    cleaning_type VARCHAR(200),               -- Тип уборки
    photo_file_ids TEXT[] NOT NULL,           -- Массив file_id фотографий из Telegram
    photo_count INTEGER DEFAULT 0,            -- Количество фото
    
    -- AI подпись
    ai_caption TEXT,                          -- Полная подпись с мотивирующим текстом
    motivational_text TEXT,                   -- Только мотивирующая часть от GPT
    
    -- Статусы отправки
    status VARCHAR(50) DEFAULT 'uploaded',    -- uploaded, sent_to_group, sent_to_bitrix, completed
    sent_to_group_at TIMESTAMP,               -- Когда отправлено в группу
    sent_to_bitrix_at TIMESTAMP,              -- Когда отправлен webhook в Bitrix24
    
    -- Метаданные
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Индексы
    CONSTRAINT cleaning_photos_house_date_unique UNIQUE (house_id, cleaning_date, brigade_id)
);

-- Индексы для быстрого поиска
CREATE INDEX IF NOT EXISTS idx_cleaning_photos_house ON cleaning_photos(house_id);
CREATE INDEX IF NOT EXISTS idx_cleaning_photos_brigade ON cleaning_photos(brigade_id);
CREATE INDEX IF NOT EXISTS idx_cleaning_photos_date ON cleaning_photos(cleaning_date);
CREATE INDEX IF NOT EXISTS idx_cleaning_photos_status ON cleaning_photos(status);
CREATE INDEX IF NOT EXISTS idx_cleaning_photos_telegram_user ON cleaning_photos(telegram_user_id);

-- Триггер для автоматического обновления updated_at
CREATE OR REPLACE FUNCTION update_cleaning_photos_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_cleaning_photos_updated_at
    BEFORE UPDATE ON cleaning_photos
    FOR EACH ROW
    EXECUTE FUNCTION update_cleaning_photos_updated_at();

-- Комментарии к таблице
COMMENT ON TABLE cleaning_photos IS 'Фото уборок от бригад через Telegram бота';
COMMENT ON COLUMN cleaning_photos.house_id IS 'ID дома из Bitrix24';
COMMENT ON COLUMN cleaning_photos.photo_file_ids IS 'Массив Telegram file_id для отправки в группу';
COMMENT ON COLUMN cleaning_photos.status IS 'uploaded | sent_to_group | sent_to_bitrix | completed';
COMMENT ON COLUMN cleaning_photos.ai_caption IS 'Полная подпись с эмодзи, адресом, датой, мотивацией и хештегами';
