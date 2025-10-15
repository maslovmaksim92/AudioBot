-- Добавление поля meeting_id в таблицу tasks
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS meeting_id VARCHAR;

-- Комментарий для поля
COMMENT ON COLUMN tasks.meeting_id IS 'ID планёрки, из которой создана задача';
