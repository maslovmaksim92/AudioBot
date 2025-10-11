"""
Health check endpoint для мониторинга
"""
from fastapi import APIRouter
import os
from datetime import datetime

router = APIRouter(tags=["Health"])

@router.get("/health")
async def health_check():
    """
    Health check endpoint
    Проверяет что сервис запущен и работает
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "VasDom AudioBot",
        "version": "2.0.0",
        "environment": {
            "database": "PostgreSQL (Yandex Cloud)" if os.getenv("DATABASE_URL") else "Not configured",
            "bitrix24": "Connected" if os.getenv("BITRIX24_WEBHOOK_URL") else "Not configured",
            "telegram": "Connected" if os.getenv("TELEGRAM_BOT_TOKEN") else "Not configured",
            "livekit": "Connected" if os.getenv("LIVEKIT_WS_URL") else "Not configured",
            "openai": "Connected" if os.getenv("OPENAI_API_KEY") else "Not configured",
        },
        "features": [
            "Authentication (JWT)",
            "RBAC (10 roles)",
            "Bitrix24 Integration",
            "Telegram Bot",
            "AI Voice Calls (LiveKit)",
            "AI Chat (OpenAI)",
            "Meetings Transcription",
            "Sales Funnel",
            "Training System",
            "Logistics",
            "Logs System"
        ]
    }

@router.get("/")
async def root():
    """Root endpoint - redirect to health"""
    return {
        "message": "VasDom AudioBot API",
        "version": "2.0.0",
        "docs": "/docs",
        "health": "/api/health"
    }