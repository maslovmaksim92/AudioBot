import os
import logging
from typing import List

# Cloud-friendly logging
log_handlers = [logging.StreamHandler()]

# Добавляем файловое логирование только если возможно
try:
    log_file_path = os.environ.get('LOG_FILE', '/tmp/vasdom_audiobot.log')
    log_handlers.append(logging.FileHandler(log_file_path, encoding='utf-8'))
except Exception:
    # На Render может не быть прав на запись, используем только stdout
    pass

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=log_handlers
)

# App settings
APP_TITLE = "VasDom AudioBot API"
APP_VERSION = "3.0.0"
APP_DESCRIPTION = "🤖 AI-система управления клининговой компанией"

# CORS settings
CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*').split(',')
CORS_ORIGINS.extend(["https://audiobot-qci2.onrender.com", "*"])

# API Keys
BITRIX24_WEBHOOK_URL = os.environ.get('BITRIX24_WEBHOOK_URL', '')
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY')
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_WEBHOOK_URL = os.environ.get('TELEGRAM_WEBHOOK_URL')
OPENROUTER_API_KEY = os.environ.get('OPENROUTER_API_KEY')