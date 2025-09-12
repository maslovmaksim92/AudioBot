import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
ROOT_DIR = Path(__file__).parent.parent.parent  # Go up to backend/ directory
load_dotenv(ROOT_DIR / '.env')

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

# CORS settings - убираем '*' и читаем из переменных окружения
CORS_ORIGINS_RAW = os.environ.get('CORS_ORIGINS', 'https://audio-management.preview.emergentagent.com,https://audiobot-qci2.onrender.com')
CORS_ORIGINS = [origin.strip() for origin in CORS_ORIGINS_RAW.split(',') if origin.strip()]

# Безопасные дефолтные origins если переменная пустая
if not CORS_ORIGINS:
    CORS_ORIGINS = [
        "https://audio-management.preview.emergentagent.com",
        "https://audiobot-qci2.onrender.com"
    ]

# Frontend redirect URLs - вынос в конфигурацию
FRONTEND_DASHBOARD_URL = os.environ.get(
    'FRONTEND_DASHBOARD_URL', 
    'https://audio-management.preview.emergentagent.com'
)

# API Keys with validation
BITRIX24_WEBHOOK_URL = os.environ.get('BITRIX24_WEBHOOK_URL', '')

# Проверяем что Bitrix24 URL корректный
if BITRIX24_WEBHOOK_URL and not (BITRIX24_WEBHOOK_URL.startswith('http://') or BITRIX24_WEBHOOK_URL.startswith('https://')):
    print(f"⚠️ Warning: BITRIX24_WEBHOOK_URL seems invalid: {BITRIX24_WEBHOOK_URL[:50]}...")
    BITRIX24_WEBHOOK_URL = f"https://{BITRIX24_WEBHOOK_URL}" if BITRIX24_WEBHOOK_URL else ''

EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY')
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_WEBHOOK_URL = os.environ.get('TELEGRAM_WEBHOOK_URL')
OPENROUTER_API_KEY = os.environ.get('OPENROUTER_API_KEY')

# Security settings
API_SECRET_KEY = os.environ.get('API_SECRET_KEY', 'vasdom-secret-key-change-in-production')
REQUIRE_AUTH_FOR_PUBLIC_API = os.environ.get('REQUIRE_AUTH_FOR_PUBLIC_API', 'false').lower() == 'true'
