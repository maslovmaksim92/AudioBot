-- Создание тестового пользователя admin для входа через Telegram
INSERT INTO users (id, email, full_name, phone, is_active, brigade_number, created_at, updated_at)
VALUES (
    'admin-user-id',
    'admin@vasdom.ru',
    'admin',
    '+79000000000',
    true,
    NULL,
    NOW(),
    NOW()
)
ON CONFLICT (id) DO NOTHING;

-- Добавляем роль admin
INSERT INTO user_roles (user_id, role)
VALUES ('admin-user-id', 'admin')
ON CONFLICT DO NOTHING;
