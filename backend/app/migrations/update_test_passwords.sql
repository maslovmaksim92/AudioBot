-- Обновление паролей для тестовых пользователей (test123)
UPDATE users 
SET password_hash = '$2b$12$SewYzyYHmZRdp6MjF6wAfeUKr7/YDarLjzMdb8xbSbfJrp6T0XuGG' 
WHERE email LIKE 'test%@vasdom.ru' OR full_name LIKE 'тест%';
