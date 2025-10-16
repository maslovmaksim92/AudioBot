-- Создание пользователя для директора Маслова
INSERT INTO users (id, email, full_name, phone, password_hash, is_active, brigade_number, created_at, updated_at)
VALUES (
    'maslov-director-id',
    'maslov@vasdom.ru',
    'маслов',
    '+79123456789',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/lewKu.1aGBWx/z12u',
    true,
    NULL,
    NOW(),
    NOW()
)
ON CONFLICT (email) DO UPDATE
SET full_name = EXCLUDED.full_name,
    phone = EXCLUDED.phone,
    is_active = EXCLUDED.is_active;

-- Также добавляем вариант с именем "Маслов Максим"
INSERT INTO users (id, email, full_name, phone, password_hash, is_active, brigade_number, created_at, updated_at)
VALUES (
    'maksim-maslov-id',
    'maksim.maslov@vasdom.ru',
    'Маслов Максим',
    '+79123456790',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/lewKu.1aGBWx/z12u',
    true,
    NULL,
    NOW(),
    NOW()
)
ON CONFLICT (email) DO UPDATE
SET full_name = EXCLUDED.full_name,
    phone = EXCLUDED.phone,
    is_active = EXCLUDED.is_active;
