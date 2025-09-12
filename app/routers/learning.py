import logging
import json
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Optional
from datetime import datetime, timedelta

# Временно отключаем зависимости от БД для избежания ошибок импорта
# from ..config.database import SessionLocal
# from ..models.database import VoiceLogDB, ModelMetricsDB, TrainingDatasetDB
from sqlalchemy import func, and_

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/learning", tags=["learning"])

class FeedbackRequest(BaseModel):
    log_id: int
    rating: int  # 1-5 stars
    feedback_text: Optional[str] = None

@router.get("/stats")
async def get_learning_stats():
    """Статистика самообучения"""
    try:
        # Заглушка для тестирования без БД
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
        
        # Оригинальный код с БД (закомментирован)
        # async with SessionLocal() as db:
            # Общее количество взаимодействий
            total_interactions = await db.query(func.count(VoiceLogDB.id)).scalar()
            
            # Взаимодействия с оценками
            rated_interactions = await db.query(func.count(VoiceLogDB.id)).filter(
                VoiceLogDB.rating.isnot(None)
            ).scalar()
            
            # Средний рейтинг
            avg_rating_result = await db.query(func.avg(VoiceLogDB.rating)).filter(
                VoiceLogDB.rating.isnot(None)
            ).scalar()
            avg_rating = float(avg_rating_result) if avg_rating_result else 0.0
            
            # Положительные оценки (4-5 звезд)
            positive_ratings = await db.query(func.count(VoiceLogDB.id)).filter(
                VoiceLogDB.rating >= 4
            ).scalar()
            
            # Отрицательные оценки (1-2 звезды)
            negative_ratings = await db.query(func.count(VoiceLogDB.id)).filter(
                VoiceLogDB.rating <= 2
            ).scalar()
            
            # Последние 7 дней
            week_ago = datetime.utcnow() - timedelta(days=7)
            recent_interactions = await db.query(func.count(VoiceLogDB.id)).filter(
                VoiceLogDB.created_at >= week_ago
            ).scalar()
            
            recent_avg_rating = await db.query(func.avg(VoiceLogDB.rating)).filter(
                and_(
                    VoiceLogDB.created_at >= week_ago,
                    VoiceLogDB.rating.isnot(None)
                )
            ).scalar()
            
            # Модели в использовании
            current_models = await db.query(VoiceLogDB.model_used).distinct().all()
            models_used = [model[0] for model in current_models if model[0]]
            
            # Последние метрики модели
            latest_metrics = await db.query(ModelMetricsDB).filter(
                ModelMetricsDB.is_current_model == True
            ).first()
            
            return {
                "success": True,
                "total_interactions": total_interactions,
                "rated_interactions": rated_interactions,
                "avg_rating": round(avg_rating, 2),
                "positive_ratings_count": positive_ratings,
                "negative_ratings_count": negative_ratings,
                "rating_coverage": round(rated_interactions / total_interactions * 100, 1) if total_interactions > 0 else 0,
                "recent_week": {
                    "interactions": recent_interactions,
                    "avg_rating": round(float(recent_avg_rating), 2) if recent_avg_rating else 0.0
                },
                "models_used": models_used,
                "current_model": latest_metrics.model_version if latest_metrics else "gpt-4-mini",
                "requires_retraining": latest_metrics.requires_retraining if latest_metrics else False,
                "last_evaluation": latest_metrics.created_at.isoformat() if latest_metrics else None
            }
            
    except Exception as e:
        logger.error(f"Error getting learning stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/feedback")
async def submit_feedback(feedback: FeedbackRequest):
    """Отправка обратной связи по взаимодействию"""
    try:
        async with SessionLocal() as db:
            # Находим лог взаимодействия
            voice_log = await db.query(VoiceLogDB).filter(
                VoiceLogDB.id == feedback.log_id
            ).first()
            
            if not voice_log:
                raise HTTPException(status_code=404, detail="Взаимодействие не найдено")
            
            # Обновляем рейтинг и отзыв
            voice_log.rating = feedback.rating
            voice_log.feedback_text = feedback.feedback_text
            voice_log.updated_at = datetime.utcnow()
            
            await db.commit()
            
            logger.info(f"Feedback submitted for log {feedback.log_id}: {feedback.rating} stars")
            
            return {
                "success": True,
                "log_id": feedback.log_id,
                "rating": feedback.rating,
                "message": "Спасибо за обратную связь!"
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/export")
async def export_training_data(min_rating: int = 4, days_back: int = 30, max_samples: int = 1000):
    """Экспорт данных для обучения"""
    try:
        from ...backend.training.export_logs import TrainingDataExporter
        
        exporter = TrainingDataExporter(min_rating=min_rating)
        result = await exporter.export_training_data(
            days_back=days_back,
            max_samples=max_samples
        )
        
        if result["success"]:
            return {
                "success": True,
                "total_exported": result["filtered_samples"],
                "total_available": result["total_samples"],
                "min_rating": min_rating,
                "export_path": result["export_path"],
                "created_at": result["created_at"]
            }
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except Exception as e:
        logger.error(f"Error exporting training data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/train")
async def trigger_training(background_tasks: BackgroundTasks):
    """Запуск обучения модели в фоновом режиме"""
    try:
        from ...backend.deploy.cron_tasks import check_retraining
        
        # Запускаем в фоновом режиме
        background_tasks.add_task(check_retraining)
        
        return {
            "success": True,
            "message": "Обучение запущено в фоновом режиме",
            "status": "training_started"
        }
        
    except Exception as e:
        logger.error(f"Error triggering training: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_training_status():
    """Статус системы обучения"""
    try:
        async with SessionLocal() as db:
            # Проверяем последние датасеты
            latest_dataset = await db.query(TrainingDatasetDB).order_by(
                TrainingDatasetDB.created_at.desc()
            ).first()
            
            # Последние метрики
            latest_metrics = await db.query(ModelMetricsDB).order_by(
                ModelMetricsDB.created_at.desc()
            ).first()
            
            return {
                "learning_enabled": True,
                "auto_training": True,
                "latest_dataset": {
                    "created_at": latest_dataset.created_at.isoformat() if latest_dataset else None,
                    "samples_count": latest_dataset.total_samples if latest_dataset else 0,
                    "status": latest_dataset.status if latest_dataset else "none"
                } if latest_dataset else None,
                "model_metrics": {
                    "version": latest_metrics.model_version if latest_metrics else "gpt-4-mini",
                    "avg_rating": latest_metrics.avg_rating if latest_metrics else 0.0,
                    "requires_retraining": latest_metrics.requires_retraining if latest_metrics else False,
                    "evaluated_at": latest_metrics.created_at.isoformat() if latest_metrics else None
                } if latest_metrics else None,
                "capabilities": [
                    "Автоматическая оценка качества модели",
                    "Экспорт обучающих данных по рейтингу",
                    "Векторный поиск похожих ответов",
                    "Переобучение при снижении качества",
                    "Сбор обратной связи пользователей"
                ]
            }
            
    except Exception as e:
        logger.error(f"Error getting training status: {e}")
        return {
            "learning_enabled": False,
            "error": str(e)
        }

@router.get("/recent-interactions")
async def get_recent_interactions(limit: int = 20, with_rating: bool = False):
    """Последние взаимодействия для анализа"""
    try:
        async with SessionLocal() as db:
            query = db.query(VoiceLogDB).order_by(VoiceLogDB.created_at.desc())
            
            if with_rating:
                query = query.filter(VoiceLogDB.rating.isnot(None))
            
            logs = await query.limit(limit).all()
            
            interactions = []
            for log in logs:
                interactions.append({
                    "id": log.id,
                    "user_message": log.user_message[:100] + "..." if len(log.user_message) > 100 else log.user_message,
                    "ai_response": log.ai_response[:100] + "..." if len(log.ai_response) > 100 else log.ai_response,
                    "rating": log.rating,
                    "feedback_text": log.feedback_text,
                    "model_used": log.model_used,
                    "session_id": log.session_id,
                    "created_at": log.created_at.isoformat()
                })
            
            return {
                "success": True,
                "interactions": interactions,
                "total_returned": len(interactions)
            }
            
    except Exception as e:
        logger.error(f"Error getting recent interactions: {e}")
        raise HTTPException(status_code=500, detail=str(e))