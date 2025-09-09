"""
VasDom AudioBot с модулем самообучения - Cloud Native для Render
Убрана зависимость от MongoDB, только PostgreSQL
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

# Pydantic модели для статуса (без MongoDB)
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

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения - только PostgreSQL"""
    # Startup
    logger.info("🚀 Запуск VasDom AudioBot с самообучением на Render")
    
    # Подключение к Render PostgreSQL
    try:
        if database is not None:
            await database.connect()
            logger.info("✅ Render PostgreSQL подключен для самообучения")
        else:
            logger.warning("⚠️ PostgreSQL недоступен - запуск в базовом режиме")
    except Exception as e:
        logger.error(f"❌ Ошибка подключения к PostgreSQL: {str(e)}")
    
    # Инициализация сервисов самообучения
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
        logger.info("✅ PostgreSQL отключен")
    except Exception as e:
        logger.error(f"❌ Ошибка при завершении: {str(e)}")

# Создание приложения
app = FastAPI(
    title="VasDom AudioBot API",
    description="AI-система управления клининговой компанией с самообучением на Render",
    version="2.0.0",
    lifespan=lifespan
)

# CORS для Render
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

# Основные эндпоинты
@api_router.get("/")
async def root():
    """Главная страница API с информацией о самообучении"""
    return {
        "message": "VasDom AudioBot API v2.0 с модулем самообучения на Render",
        "platform": "Render Cloud",
        "database": "PostgreSQL" if DATABASE_AVAILABLE else "Недоступна",
        "features": [
            "AI голосовой помощник с Emergent LLM",
            "Система самообучения",
            "Поиск похожих ответов через эмбеддинги",
            "Обратная связь пользователей (1-5 звезд)",
            "Автоматическая переоценка качества",
            "Fine-tuning локальных моделей"
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
    """Проверка состояния системы на Render"""
    try:
        # Проверка компонентов
        components = {
            "api": True,
            "postgres": DATABASE_AVAILABLE and database is not None and database.is_connected,
            "render_platform": True,  # Мы на Render
        }
        
        # Проверка сервисов самообучения
        try:
            from app.services.ai_service import ai_service
            from app.services.embedding_service import embedding_service
            components.update({
                "ai_service": ai_service.emergent_client is not None,
                "embedding_service": embedding_service.model is not None,
                "emergent_llm": bool(settings.EMERGENT_LLM_KEY)
            })
        except:
            components.update({
                "ai_service": False,
                "embedding_service": False,
                "emergent_llm": False
            })
        
        # Общий статус
        critical_components = ["api", "postgres", "emergent_llm"]
        critical_healthy = all(components.get(comp, False) for comp in critical_components)
        status = "healthy" if critical_healthy else "degraded"
        
        return {
            "status": status,
            "platform": "Render",
            "components": components,
            "version": "2.0.0",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Ошибка проверки здоровья: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "platform": "Render",
            "timestamp": datetime.utcnow().isoformat()
        }

# Простые status endpoints для совместимости (без MongoDB)
class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    platform: str = "Render"

class StatusCheckCreate(BaseModel):
    client_name: str

# In-memory storage для демонстрации (в production использовался бы PostgreSQL)
status_checks = []

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    """Создание проверки статуса (in-memory для демо)"""
    try:
        status_obj = StatusCheck(**input.dict())
        status_checks.append(status_obj)
        # В продакшене сохранялось бы в PostgreSQL
        return status_obj
    except Exception as e:
        logger.error(f"Ошибка создания status check: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    """Получение проверок статуса (последние 10)"""
    try:
        # Возвращаем последние 10 записей
        return status_checks[-10:]
    except Exception as e:
        logger.error(f"Ошибка получения status checks: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Подключение API роутера
app.include_router(api_router)

# Главная страница - информация о системе
@app.get("/")
async def root_redirect():
    """Главная страница с информацией о системе на Render"""
    return {
        "name": "VasDom AudioBot",
        "version": "2.0.0", 
        "description": "AI-система управления клининговой компанией с модулем самообучения",
        "platform": "Render Cloud",
        "documentation": "/docs",
        "api_prefix": "/api",
        "github": "https://github.com/maslovmaksim92/AudioBot",
        "features": {
            "self_learning": True,
            "voice_processing": True,
            "embedding_search": True,
            "user_feedback": True,
            "automatic_retraining": True,
            "cloud_native": True
        },
        "infrastructure": {
            "hosting": "Render",
            "database": "Render PostgreSQL",
            "ai_provider": "Emergent LLM"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8001)),
        reload=False,  # В production отключаем reload
        log_level="info"
    )