"""
Backward compatibility entry point для Render
Полностью переписан под PostgreSQL без MongoDB
"""

try:
    # Try to import the new modular app
    from app.main import app
    print("✅ Using modular VasDom AudioBot with self-learning v2.0 on Render")
except ImportError as e:
    print(f"⚠️ Modular app not available: {e}")
    print("🔄 Using minimal implementation")
    
    # Минимальная реализация без зависимостей
    from fastapi import FastAPI, APIRouter
    from pydantic import BaseModel, Field
    from typing import List
    import uuid
    from datetime import datetime
    import os

    # Создание минимального приложения
    app = FastAPI(
        title="VasDom AudioBot API (Minimal Mode)",
        description="Базовый режим для Render без внешних зависимостей",
        version="1.0.0"
    )

    # CORS
    from fastapi.middleware.cors import CORSMiddleware
    app.add_middleware(
        CORSMiddleware,
        allow_credentials=True,
        allow_origins=["*"],  # В production указать конкретные домены
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # API роутер
    api_router = APIRouter(prefix="/api")

    # Модели
    class StatusCheck(BaseModel):
        id: str = Field(default_factory=lambda: str(uuid.uuid4()))
        client_name: str
        timestamp: datetime = Field(default_factory=datetime.utcnow)
        platform: str = "Render"

    class StatusCheckCreate(BaseModel):
        client_name: str

    # In-memory storage
    status_checks = []

    @api_router.get("/")
    async def root():
        return {
            "message": "VasDom AudioBot API - Minimal Mode on Render",
            "status": "running",
            "platform": "Render",
            "note": "Модуль самообучения будет доступен после настройки PostgreSQL"
        }

    @api_router.get("/health")
    async def health():
        return {
            "status": "healthy",
            "platform": "Render",
            "mode": "minimal",
            "timestamp": datetime.utcnow().isoformat()
        }

    @api_router.post("/status", response_model=StatusCheck)
    async def create_status_check(input: StatusCheckCreate):
        status_obj = StatusCheck(**input.dict())
        status_checks.append(status_obj)
        return status_obj

    @api_router.get("/status", response_model=List[StatusCheck])
    async def get_status_checks():
        return status_checks[-10:]

    # Подключение роутера
    app.include_router(api_router)

    @app.get("/")
    async def root_minimal():
        return {
            "name": "VasDom AudioBot",
            "version": "1.0.0",
            "platform": "Render",
            "mode": "minimal",
            "message": "Готов к настройке модуля самообучения"
        }