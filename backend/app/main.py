"""
Основное FastAPI приложение VasDom AudioBot с модулем самообучения
Интегрирует существующую функциональность с новыми возможностями AI
"""
from fastapi import FastAPI, APIRouter, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import os

# Импорты для самообучения
from app.config.database import database, DATABASE_AVAILABLE
from app.config.settings import get_settings
from app.routers import voice

# Обратная совместимость с существующим кодом
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field
from typing import List
import uuid
from datetime import datetime

# Настройки
settings = get_settings()

# Логирование
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# MongoDB для обратной совместимости
if hasattr(settings, 'MONGO_URL') and settings.MONGO_URL:
    mongo_client = AsyncIOMotorClient(settings.MONGO_URL)
    mongo_db = mongo_client[settings.DB_NAME]
else:
    mongo_client = None
    mongo_db = None
    logger.warning("MongoDB не настроен - работа только с PostgreSQL")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения"""
    # Startup
    logger.info("🚀 Запуск VasDom AudioBot с модулем самообучения")
    
    # Подключение к PostgreSQL для самообучения
    try:
        if database is not None:
            await database.connect()
            logger.info("✅ PostgreSQL подключен для самообучения")
        else:
            logger.warning("⚠️ PostgreSQL недоступен - самообучение отключено")
    except Exception as e:
        logger.error(f"❌ Ошибка подключения к PostgreSQL: {str(e)}")
    
    # Инициализация сервисов
    try:
        from app.services.ai_service import ai_service
        from app.services.embedding_service import embedding_service
        logger.info("✅ AI и Embedding сервисы инициализированы")
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации сервисов: {str(e)}")
    
    yield
    
    # Shutdown
    logger.info("🛑 Завершение работы VasDom AudioBot")
    try:
        if database is not None:
            await database.disconnect()
        if mongo_client:
            mongo_client.close()
        logger.info("✅ Все подключения закрыты")
    except Exception as e:
        logger.error(f"❌ Ошибка при завершении: {str(e)}")

# Создание приложения
app = FastAPI(
    title="VasDom AudioBot API",
    description="AI-система управления клининговой компанией с модулем самообучения",
    version="2.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=settings.CORS_ORIGINS.split(',') if settings.CORS_ORIGINS != "*" else ["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Роутер для API
api_router = APIRouter(prefix="/api")

# Подключение роутеров самообучения
api_router.include_router(voice.router)

# Обратная совместимость - существующие эндпоинты
class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class StatusCheckCreate(BaseModel):
    client_name: str

@api_router.get("/")
async def root():
    """Главная страница API"""
    return {
        "message": "VasDom AudioBot API v2.0 с модулем самообучения",
        "features": [
            "AI голосовой помощник",
            "Система самообучения",
            "Поиск похожих ответов",
            "Обратная связь пользователей",
            "Автоматическая переоценка качества"
        ],
        "endpoints": {
            "voice_chat": "/api/voice/process",
            "feedback": "/api/voice/feedback", 
            "learning_status": "/api/voice/self-learning/status",
            "health": "/api/voice/health"
        }
    }

@api_router.get("/health")
async def health_check():
    """Проверка состояния системы"""
    try:
        # Проверка компонентов
        components = {
            "api": True,
            "postgres": DATABASE_AVAILABLE and database is not None and database.is_connected,
            "mongo": mongo_client is not None,
        }
        
        # Проверка сервисов самообучения
        try:
            from app.services.ai_service import ai_service
            from app.services.embedding_service import embedding_service
            components.update({
                "ai_service": ai_service.emergent_client is not None,
                "embedding_service": embedding_service.model is not None
            })
        except:
            components.update({
                "ai_service": False,
                "embedding_service": False
            })
        
        # Общий статус
        all_critical_healthy = components["api"] and components["postgres"]
        status = "healthy" if all_critical_healthy else "degraded"
        
        return {
            "status": status,
            "components": components,
            "version": "2.0.0",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Ошибка проверки здоровья: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

# Обратная совместимость - status endpoints
if mongo_db is not None:
    @api_router.post("/status", response_model=StatusCheck)
    async def create_status_check(input: StatusCheckCreate):
        """Создание проверки статуса (обратная совместимость с MongoDB)"""
        try:
            status_dict = input.dict()
            status_obj = StatusCheck(**status_dict)
            await mongo_db.status_checks.insert_one(status_obj.dict())
            return status_obj
        except Exception as e:
            logger.error(f"Ошибка создания status check: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    @api_router.get("/status", response_model=List[StatusCheck])
    async def get_status_checks():
        """Получение проверок статуса (обратная совместимость с MongoDB)"""
        try:
            status_checks = await mongo_db.status_checks.find().to_list(1000)
            return [StatusCheck(**status_check) for status_check in status_checks]
        except Exception as e:
            logger.error(f"Ошибка получения status checks: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

# Подключение API роутера
app.include_router(api_router)

# Главная страница - редирект на документацию
@app.get("/")
async def root_redirect():
    """Главная страница с информацией о системе"""
    return {
        "name": "VasDom AudioBot",
        "version": "2.0.0", 
        "description": "AI-система управления клининговой компанией с модулем самообучения",
        "documentation": "/docs",
        "api_prefix": "/api",
        "features": {
            "self_learning": True,
            "voice_processing": True,
            "embedding_search": True,
            "user_feedback": True,
            "automatic_retraining": True
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )