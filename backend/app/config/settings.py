"""
Настройки приложения - все переменные окружения в одном месте
"""
import os
from pathlib import Path
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).parent.parent.parent
load_dotenv(ROOT_DIR / '.env')

class Settings:
    """Централизованные настройки приложения"""
    
    # Database
    DATABASE_URL: str = os.getenv('DATABASE_URL', '')
    
    # Integrations
    BITRIX24_WEBHOOK_URL: str = os.getenv('BITRIX24_WEBHOOK_URL', '')
    TELEGRAM_BOT_TOKEN: str = os.getenv('TELEGRAM_BOT_TOKEN', '')
    EMERGENT_LLM_KEY: str = os.getenv('EMERGENT_LLM_KEY', '')
    
    # OpenAI / LiveKit (Voice)
    OPENAI_API_KEY: str = os.getenv('OPENAI_API_KEY', '')
    LIVEKIT_WS_URL: str = os.getenv('LIVEKIT_WS_URL', '')
    LIVEKIT_API_KEY: str = os.getenv('LIVEKIT_API_KEY', '')
    LIVEKIT_API_SECRET: str = os.getenv('LIVEKIT_API_SECRET', '')
    LIVEKIT_SIP_TRUNK_ID: str = os.getenv('LIVEKIT_SIP_TRUNK_ID', '')
    NOVOFON_CALLER_ID: str = os.getenv('NOVOFON_CALLER_ID', '')
    
    # CORS
    CORS_ORIGINS: str = os.getenv('CORS_ORIGINS', '*')
    
    # App
    APP_TITLE: str = "VasDom AudioBot API"
    APP_VERSION: str = "2.0.0"
    
    @property
    def cors_origins_list(self) -> list:
        """Возвращает список CORS origins"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(',')]

settings = Settings()