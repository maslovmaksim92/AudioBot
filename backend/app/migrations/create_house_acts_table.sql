-- Таблица для учета подписанных актов по домам
CREATE TABLE IF NOT EXISTS house_acts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Идентификаторы
    house_id VARCHAR(100) NOT NULL,    -- ID дома из Bitrix24
    house_address TEXT NOT NULL,        -- Адрес для отображения
    
    -- Данные акта
    act_month VARCHAR(7) NOT NULL,      -- Месяц в формате YYYY-MM (например, "2025-10")
    act_signed_date DATE NOT NULL,      -- Дата подписания акта
    signed_by VARCHAR(200),             -- Кто подписал (ФИО, УК)
    
    -- Связи
    brigade_id VARCHAR(50),             -- Бригада ответственная за этот дом
    cleaning_count INTEGER DEFAULT 0,   -- Сколько уборок было в этом месяце
    
    -- Метаданные
    notes TEXT,                         -- Примечания
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Ограничение: один акт на дом в месяц
    CONSTRAINT house_acts_house_month_unique UNIQUE (house_id, act_month)
);

-- Индексы для быстрого поиска
CREATE INDEX IF NOT EXISTS idx_house_acts_house ON house_acts(house_id);
CREATE INDEX IF NOT EXISTS idx_house_acts_month ON house_acts(act_month);
CREATE INDEX IF NOT EXISTS idx_house_acts_signed_date ON house_acts(act_signed_date);
CREATE INDEX IF NOT EXISTS idx_house_acts_brigade ON house_acts(brigade_id);

-- Триггер для автоматического обновления updated_at
CREATE OR REPLACE FUNCTION update_house_acts_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_house_acts_updated_at
    BEFORE UPDATE ON house_acts
    FOR EACH ROW
    EXECUTE FUNCTION update_house_acts_updated_at();

-- Комментарии
COMMENT ON TABLE house_acts IS 'Учет подписанных актов по домам (ключевой показатель)';
COMMENT ON COLUMN house_acts.act_month IS 'Месяц акта в формате YYYY-MM';
COMMENT ON COLUMN house_acts.act_signed_date IS 'Дата фактического подписания акта';
