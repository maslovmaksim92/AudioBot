import os
from functools import lru_cache
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://localhost:5432/vasdom_audio")
    
    # Mongo (backward compatibility)
    MONGO_URL: str = os.getenv("MONGO_URL", "mongodb://localhost:27017")
    DB_NAME: str = os.getenv("DB_NAME", "test_database")
    
    # AI and ML
    EMERGENT_LLM_KEY: str = os.getenv("EMERGENT_LLM_KEY", "")
    USE_LOCAL_MODEL: bool = os.getenv("USE_LOCAL_MODEL", "false").lower() == "true"
    LOCAL_MODEL_PATH: str = os.getenv("LOCAL_MODEL_PATH", "models/fine_tuned/")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "sentence-transformers/paraphrase-multilingual-MiniLM-L6-v2")
    
    # Self-learning parameters
    MIN_RATING_THRESHOLD: int = int(os.getenv("MIN_RATING_THRESHOLD", "4"))
    RETRAINING_THRESHOLD: float = float(os.getenv("RETRAINING_THRESHOLD", "3.5"))
    EVALUATION_SCHEDULE_DAYS: int = int(os.getenv("EVALUATION_SCHEDULE_DAYS", "7"))
    
    # Security
    API_SECRET_KEY: str = os.getenv("API_SECRET_KEY", "your-secret-key")
    REQUIRE_AUTH_FOR_PUBLIC_API: bool = os.getenv("REQUIRE_AUTH_FOR_PUBLIC_API", "false").lower() == "true"
    
    # CORS
    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "*")
    
    # Telegram
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_WEBHOOK_URL: str = os.getenv("TELEGRAM_WEBHOOK_URL", "")
    
    # Bitrix24
    BITRIX24_WEBHOOK_URL: str = os.getenv("BITRIX24_WEBHOOK_URL", "")

@lru_cache()
def get_settings():
    return Settings()