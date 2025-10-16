-- Создание тестовых аккаунтов для бригад 1-7
-- Логин: тест1, тест2, ... тест7
-- Пароль: test123 (хеш: $2b$12$KIXn3qhNWz5z9YhN.CqLfuZJ5L8xYzN6Z8W0j6hN5J8L9xYzN6Z8W)

-- Бригада 1
INSERT INTO users (id, email, full_name, phone, password_hash, is_active, brigade_number, created_at, updated_at)
VALUES (
    'test-brigade-1-id',
    'test1@vasdom.ru',
    'тест1',
    '+79001111111',
    '$2b$12$KIXn3qhNWz5z9YhN.CqLfuZJ5L8xYzN6Z8W0j6hN5J8L9xYzN6Z8W',
    true,
    '1',
    NOW(),
    NOW()
)
ON CONFLICT (email) DO UPDATE
SET full_name = EXCLUDED.full_name,
    brigade_number = EXCLUDED.brigade_number,
    is_active = EXCLUDED.is_active;

-- Бригада 2
INSERT INTO users (id, email, full_name, phone, password_hash, is_active, brigade_number, created_at, updated_at)
VALUES (
    'test-brigade-2-id',
    'test2@vasdom.ru',
    'тест2',
    '+79002222222',
    '$2b$12$KIXn3qhNWz5z9YhN.CqLfuZJ5L8xYzN6Z8W0j6hN5J8L9xYzN6Z8W',
    true,
    '2',
    NOW(),
    NOW()
)
ON CONFLICT (email) DO UPDATE
SET full_name = EXCLUDED.full_name,
    brigade_number = EXCLUDED.brigade_number,
    is_active = EXCLUDED.is_active;

-- Бригада 3
INSERT INTO users (id, email, full_name, phone, password_hash, is_active, brigade_number, created_at, updated_at)
VALUES (
    'test-brigade-3-id',
    'test3@vasdom.ru',
    'тест3',
    '+79003333333',
    '$2b$12$KIXn3qhNWz5z9YhN.CqLfuZJ5L8xYzN6Z8W0j6hN5J8L9xYzN6Z8W',
    true,
    '3',
    NOW(),
    NOW()
)
ON CONFLICT (email) DO UPDATE
SET full_name = EXCLUDED.full_name,
    brigade_number = EXCLUDED.brigade_number,
    is_active = EXCLUDED.is_active;

-- Бригада 4
INSERT INTO users (id, email, full_name, phone, password_hash, is_active, brigade_number, created_at, updated_at)
VALUES (
    'test-brigade-4-id',
    'test4@vasdom.ru',
    'тест4',
    '+79004444444',
    '$2b$12$KIXn3qhNWz5z9YhN.CqLfuZJ5L8xYzN6Z8W0j6hN5J8L9xYzN6Z8W',
    true,
    '4',
    NOW(),
    NOW()
)
ON CONFLICT (email) DO UPDATE
SET full_name = EXCLUDED.full_name,
    brigade_number = EXCLUDED.brigade_number,
    is_active = EXCLUDED.is_active;

-- Бригада 5
INSERT INTO users (id, email, full_name, phone, password_hash, is_active, brigade_number, created_at, updated_at)
VALUES (
    'test-brigade-5-id',
    'test5@vasdom.ru',
    'тест5',
    '+79005555555',
    '$2b$12$KIXn3qhNWz5z9YhN.CqLfuZJ5L8xYzN6Z8W0j6hN5J8L9xYzN6Z8W',
    true,
    '5',
    NOW(),
    NOW()
)
ON CONFLICT (email) DO UPDATE
SET full_name = EXCLUDED.full_name,
    brigade_number = EXCLUDED.brigade_number,
    is_active = EXCLUDED.is_active;

-- Бригада 6
INSERT INTO users (id, email, full_name, phone, password_hash, is_active, brigade_number, created_at, updated_at)
VALUES (
    'test-brigade-6-id',
    'test6@vasdom.ru',
    'тест6',
    '+79006666666',
    '$2b$12$KIXn3qhNWz5z9YhN.CqLfuZJ5L8xYzN6Z8W0j6hN5J8L9xYzN6Z8W',
    true,
    '6',
    NOW(),
    NOW()
)
ON CONFLICT (email) DO UPDATE
SET full_name = EXCLUDED.full_name,
    brigade_number = EXCLUDED.brigade_number,
    is_active = EXCLUDED.is_active;

-- Бригада 7
INSERT INTO users (id, email, full_name, phone, password_hash, is_active, brigade_number, created_at, updated_at)
VALUES (
    'test-brigade-7-id',
    'test7@vasdom.ru',
    'тест7',
    '+79007777777',
    '$2b$12$KIXn3qhNWz5z9YhN.CqLfuZJ5L8xYzN6Z8W0j6hN5J8L9xYzN6Z8W',
    true,
    '7',
    NOW(),
    NOW()
)
ON CONFLICT (email) DO UPDATE
SET full_name = EXCLUDED.full_name,
    brigade_number = EXCLUDED.brigade_number,
    is_active = EXCLUDED.is_active;
