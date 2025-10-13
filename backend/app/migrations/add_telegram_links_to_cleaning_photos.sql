-- Добавляем поля для ссылок на посты в Telegram
ALTER TABLE cleaning_photos 
ADD COLUMN IF NOT EXISTS telegram_message_id BIGINT,
ADD COLUMN IF NOT EXISTS telegram_chat_id BIGINT,
ADD COLUMN IF NOT EXISTS telegram_post_url TEXT;

-- Индекс для быстрого поиска по message_id
CREATE INDEX IF NOT EXISTS idx_cleaning_photos_message_id ON cleaning_photos(telegram_message_id);

-- Комментарии
COMMENT ON COLUMN cleaning_photos.telegram_message_id IS 'ID сообщения в Telegram группе';
COMMENT ON COLUMN cleaning_photos.telegram_chat_id IS 'ID чата/группы в Telegram';
COMMENT ON COLUMN cleaning_photos.telegram_post_url IS 'Прямая ссылка на пост в Telegram';
