-- Создание тестового пользователя admin для входа через Telegram
-- password_hash для пустого пароля (не используется при Telegram входе)
INSERT INTO users (id, email, full_name, phone, password_hash, is_active, brigade_number, created_at, updated_at)
VALUES (
    'admin-user-id',
    'admin@vasdom.ru',
    'admin',
    '+79000000000',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/lewKu.1aGBWx/z12u',  -- хеш для "password" (не используется)
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
