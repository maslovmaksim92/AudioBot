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

-- Проверяем и создаем роль director если не существует
INSERT INTO roles (name, description, created_at)
VALUES ('director', 'Директор - полный доступ', NOW())
ON CONFLICT (name) DO NOTHING;

-- Добавляем роль director
INSERT INTO user_roles (user_id, role_name)
VALUES ('admin-user-id', 'director')
ON CONFLICT DO NOTHING;
