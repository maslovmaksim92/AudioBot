# Деплой на VPS (`ai.vd40.ru`)

Эта инструкция предполагает Ubuntu 24.04, существующий nginx и certbot,
свободный порт 8011 на localhost. PostgreSQL 16 с pgvector должен быть
установлен (см. шаг 0).

> Все команды выполняются от root либо через `sudo`.

## 0. Предусловия

```bash
# PostgreSQL 16 + pgvector
sudo apt update
sudo apt install -y postgresql-16 postgresql-16-pgvector

# Создание БД (если ещё не создана)
sudo -u postgres psql <<SQL
CREATE USER audiobot WITH ENCRYPTED PASSWORD '__CHANGE_ME__';
CREATE DATABASE audiobot OWNER audiobot;
\c audiobot
CREATE EXTENSION IF NOT EXISTS vector;
SQL
```

## 1. Клон и установка

```bash
sudo mkdir -p /opt
sudo git clone https://github.com/maslovmaksim92/AudioBot.git /opt/audiobot
cd /opt/audiobot
sudo useradd --system --home /opt/audiobot --shell /usr/sbin/nologin audiobot || true
sudo chown -R audiobot:audiobot /opt/audiobot
```

## 2. Python venv + зависимости

```bash
cd /opt/audiobot/backend
sudo -u audiobot python3.12 -m venv venv
sudo -u audiobot ./venv/bin/pip install --upgrade pip
sudo -u audiobot ./venv/bin/pip install -r requirements.txt
```

## 3. Конфигурация

```bash
sudo cp /opt/audiobot/.env.example /opt/audiobot/.env
sudo nano /opt/audiobot/.env        # пропишите DATABASE_URL, OPENAI_API_KEY, ...
sudo chown audiobot:audiobot /opt/audiobot/.env
sudo chmod 600 /opt/audiobot/.env
```

## 4. Миграции

```bash
cd /opt/audiobot/backend
sudo -u audiobot bash -c "set -a && source /opt/audiobot/.env && set +a && ./venv/bin/alembic upgrade head"
```

## 5. Systemd-сервис

```bash
sudo cp /opt/audiobot/deploy/systemd/audiobot-backend.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now audiobot-backend
sudo systemctl status audiobot-backend --no-pager
```

Проверка:
```bash
curl -s http://127.0.0.1:8011/api/health
```

## 6. Сборка фронтенда

```bash
cd /opt/audiobot/frontend
sudo -u audiobot bash -c "REACT_APP_BACKEND_URL=https://ai.vd40.ru yarn install --frozen-lockfile && REACT_APP_BACKEND_URL=https://ai.vd40.ru yarn build"
sudo mkdir -p /var/www/audiobot
sudo cp -r build /var/www/audiobot/frontend
sudo chown -R www-data:www-data /var/www/audiobot
```

## 7. Nginx + SSL

```bash
sudo cp /opt/audiobot/deploy/nginx/ai.vd40.ru.conf /etc/nginx/sites-available/ai.vd40.ru
sudo ln -s /etc/nginx/sites-available/ai.vd40.ru /etc/nginx/sites-enabled/

# Получение сертификата (DNS A-запись ai.vd40.ru уже должна указывать на сервер)
sudo certbot --nginx -d ai.vd40.ru --non-interactive --agree-tos -m admin@vd40.ru

sudo nginx -t && sudo systemctl reload nginx
```

Проверка:
```bash
curl -sI https://ai.vd40.ru/
curl -s https://ai.vd40.ru/api/health
```

## 8. Обновление кода

```bash
cd /opt/audiobot
sudo -u audiobot git pull origin main
sudo -u audiobot ./backend/venv/bin/pip install -r backend/requirements.txt
sudo -u audiobot ./backend/venv/bin/alembic -c backend/alembic.ini upgrade head
sudo systemctl restart audiobot-backend

# Если менялся фронт:
cd /opt/audiobot/frontend
sudo -u audiobot yarn build
sudo cp -r build/* /var/www/audiobot/frontend/
```

## Откат

```bash
sudo systemctl stop audiobot-backend
cd /opt/audiobot && sudo -u audiobot git checkout <previous-commit>
sudo systemctl start audiobot-backend
```
