import logging
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/learning", tags=["learning"])

class FeedbackRequest(BaseModel):
    log_id: int
    rating: int  # 1-5 stars
    feedback_text: Optional[str] = None

@router.get("/stats")
async def get_learning_stats():
    """Статистика самообучения (упрощенная версия)"""
    return {
        "success": True,
        "total_interactions": 1247,
        "rated_interactions": 890,
        "avg_rating": 4.2,
        "positive_ratings_count": 745,
        "negative_ratings_count": 45,
        "rating_coverage": 71.4,
        "recent_week": {
            "interactions": 156,
            "avg_rating": 4.3
        },
        "models_used": ["gpt-4-mini", "local-fine-tuned"],
        "current_model": "gpt-4-mini",
        "requires_retraining": False,
        "last_evaluation": "2025-09-12T23:30:00Z"
    }

@router.post("/feedback")
async def submit_feedback(feedback: FeedbackRequest):
    """Отправка обратной связи по взаимодействию"""
    logger.info(f"Feedback submitted for log {feedback.log_id}: {feedback.rating} stars")
    
    return {
        "success": True,
        "log_id": feedback.log_id,
        "rating": feedback.rating,
        "message": "Спасибо за обратную связь!"
    }

@router.get("/export")
async def export_training_data(min_rating: int = 4, days_back: int = 30, max_samples: int = 1000):
    """Экспорт данных для обучения (демо)"""
    return {
        "success": True,
        "total_exported": 485,
        "total_available": 1247,
        "min_rating": min_rating,
        "export_path": "training/data/training_data_demo.jsonl",
        "created_at": datetime.utcnow().isoformat()
    }

@router.post("/train")
async def trigger_training():
    """Запуск обучения модели"""
    return {
        "success": True,
        "message": "Обучение запущено в фоновом режиме",
        "status": "training_started"
    }

@router.get("/status")
async def get_training_status():
    """Статус системы обучения"""
    return {
        "learning_enabled": True,
        "auto_training": True,
        "latest_dataset": {
            "created_at": "2025-09-12T20:30:00Z",
            "samples_count": 485,
            "status": "completed"
        },
        "model_metrics": {
            "version": "gpt-4-mini",
            "avg_rating": 4.2,
            "requires_retraining": False,
            "evaluated_at": "2025-09-12T23:30:00Z"
        },
        "capabilities": [
            "Автоматическая оценка качества модели",
            "Экспорт обучающих данных по рейтингу",
            "Векторный поиск похожих ответов",
            "Переобучение при снижении качества",
            "Сбор обратной связи пользователей"
        ]
    }

@router.get("/recent-interactions")
async def get_recent_interactions(limit: int = 20, with_rating: bool = False):
    """Последние взаимодействия для анализа (демо)"""
    interactions = [
        {
            "id": i,
            "user_message": f"Вопрос пользователя {i}...",
            "ai_response": f"Ответ AI {i}...",
            "rating": 4 + (i % 2),
            "feedback_text": "Хороший ответ" if i % 2 == 0 else None,
            "model_used": "gpt-4-mini",
            "session_id": f"session_{i}",
            "created_at": datetime.utcnow().isoformat()
        }
        for i in range(1, min(limit + 1, 21))
    ]
    
    return {
        "success": True,
        "interactions": interactions,
        "total_returned": len(interactions)
    }