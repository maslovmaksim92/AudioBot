"""
Главный файл приложения VasDom AudioBot
Объединяет все роутеры и настройки
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from backend.app.config.settings import settings
from backend.app.routers import auth, houses, telegram

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Создание приложения
app = FastAPI(
    title=settings.APP_TITLE,
    version=settings.APP_VERSION,
    description="Интеллектуальная система управления компанией"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение роутеров
app.include_router(auth.router, prefix="/api")
app.include_router(houses.router, prefix="/api")
app.include_router(telegram.router, prefix="/api")

@app.get("/")
async def root():
    """Корневой endpoint"""
    return {
        "app": settings.APP_TITLE,
        "version": settings.APP_VERSION,
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Проверка здоровья сервиса"""
    return {
        "status": "healthy",
        "database": "connected",  # TODO: проверка подключения к БД
        "integrations": {
            "bitrix24": bool(settings.BITRIX24_WEBHOOK_URL),
            "telegram": bool(settings.TELEGRAM_BOT_TOKEN),
            "emergent_llm": bool(settings.EMERGENT_LLM_KEY)
        }
    }

@app.on_event("startup")
async def startup_event():
    """Действия при запуске приложения"""
    logger.info("=" * 70)
    logger.info(f"🚀 {settings.APP_TITLE} v{settings.APP_VERSION}")
    logger.info("=" * 70)
    logger.info(f"✅ CORS origins: {', '.join(settings.cors_origins_list)}")
    logger.info(f"✅ Bitrix24: {'Configured' if settings.BITRIX24_WEBHOOK_URL else 'Not configured'}")
    logger.info(f"✅ Telegram: {'Configured' if settings.TELEGRAM_BOT_TOKEN else 'Not configured'}")
    logger.info(f"✅ Database: {'Configured' if settings.DATABASE_URL else 'Not configured'}")
    logger.info("=" * 70)

@app.on_event("shutdown")
async def shutdown_event():
    """Действия при остановке приложения"""
    logger.info("🛑 Shutting down VasDom AudioBot...")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8001,
        reload=True
    )
