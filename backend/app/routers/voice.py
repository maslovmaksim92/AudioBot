"""
Роутер для голосового AI чата с поддержкой самообучения
Включает обработку сообщений, обратную связь и статистику
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
import logging

from app.models.schemas import (
    ChatRequest, ChatResponse, FeedbackRequest, FeedbackResponse,
    SelfLearningStatus, SimilarResponse
)
from app.services.ai_service import ai_service
from app.services.embedding_service import embedding_service
from app.config.database import get_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/voice", tags=["voice"])

@router.post("/process", response_model=ChatResponse)
async def process_voice_message(request: ChatRequest):
    """
    Обработка голосового сообщения с поддержкой самообучения
    
    - Ищет похожие вопросы в истории
    - Генерирует ответ с учетом контекста
    - Сохраняет взаимодействие для обучения
    - Создает эмбеддинг для будущего поиска
    """
    try:
        logger.info(f"Обработка сообщения: {request.message[:50]}...")
        
        # Обработка через AI сервис с самообучением
        response = await ai_service.process_message(request)
        
        logger.info(f"Ответ сгенерирован, log_id: {response.log_id}")
        
        return response
        
    except Exception as e:
        logger.error(f"Ошибка обработки голосового сообщения: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Ошибка обработки сообщения: {str(e)}"
        )

@router.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(request: FeedbackRequest):
    """
    Отправка обратной связи по качеству ответа AI
    
    - Сохраняет оценку пользователя (1-5 звезд)
    - Опциональный текстовый отзыв
    - Обновляет метрики для автоматической переоценки
    """
    try:
        logger.info(f"Получена обратная связь для лога {request.log_id}: {request.rating}★")
        
        # Валидация рейтинга
        if not 1 <= request.rating <= 5:
            raise HTTPException(
                status_code=400,
                detail="Рейтинг должен быть от 1 до 5"
            )
        
        # Обновление рейтинга в базе данных
        success = await ai_service.update_log_rating(
            log_id=request.log_id,
            rating=request.rating,
            feedback_text=request.feedback_text
        )
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Лог с ID {request.log_id} не найден"
            )
        
        # Определяем сообщение на основе рейтинга
        if request.rating >= 4:
            message = "Спасибо за положительную оценку! Это поможет улучшить AI."
        elif request.rating == 3:
            message = "Спасибо за оценку! Мы учтем ваши замечания."
        else:
            message = "Спасибо за оценку! Мы работаем над улучшением качества ответов."
        
        return FeedbackResponse(
            success=True,
            message=message,
            log_id=request.log_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка сохранения обратной связи: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка сохранения обратной связи: {str(e)}"
        )

@router.get("/similar/{log_id}", response_model=List[SimilarResponse])
async def get_similar_responses(log_id: int, limit: int = 5):
    """
    Получение похожих ответов для конкретного лога
    
    Полезно для анализа качества поиска и отладки
    """
    try:
        # Получаем исходное сообщение
        from app.config.database import SessionLocal
        from app.models.database import VoiceLogDB
        
        async with SessionLocal() as db:
            original_log = await db.query(VoiceLogDB).filter(
                VoiceLogDB.id == log_id
            ).first()
            
            if not original_log:
                raise HTTPException(
                    status_code=404,
                    detail=f"Лог с ID {log_id} не найден"
                )
            
            # Поиск похожих ответов
            similar_responses = await embedding_service.find_similar_responses(
                query_text=original_log.user_message,
                limit=limit,
                similarity_threshold=0.5,
                exclude_log_id=log_id
            )
            
            return similar_responses
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка поиска похожих ответов: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка поиска: {str(e)}"
        )

@router.get("/self-learning/status", response_model=SelfLearningStatus)
async def get_self_learning_status():
    """
    Получение статуса системы самообучения
    
    - Общая статистика взаимодействий
    - Средние оценки пользователей
    - Информация о текущей модели
    - Метрики качества
    """
    try:
        # Получаем статистику от AI сервиса
        stats = await ai_service.get_learning_statistics()
        
        if not stats:
            raise HTTPException(
                status_code=500,
                detail="Ошибка получения статистики"
            )
        
        return SelfLearningStatus(
            total_interactions=stats.get("total_interactions", 0),
            avg_rating=stats.get("avg_rating"),
            positive_ratings_count=stats.get("positive_ratings", 0),
            negative_ratings_count=stats.get("negative_ratings", 0),
            current_model=stats.get("current_model", "gpt-4-mini"),
            last_evaluation=None,  # Будет реализовано в следующей фазе
            next_training_scheduled=None,  # Будет реализовано в следующей фазе
            current_metrics={
                "embedding_service_available": stats.get("embedding_service_available", False),
                "rated_interactions": stats.get("rated_interactions", 0)
            },
            requires_retraining=False  # Будет реализовано в следующей фазе
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка получения статуса самообучения: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка получения статуса: {str(e)}"
        )

@router.post("/embeddings/update")
async def update_embeddings_batch(batch_size: int = 100):
    """
    Массовое обновление эмбеддингов для логов без векторных представлений
    
    Используется для первоначального заполнения или обновления существующих данных
    """
    try:
        result = await embedding_service.update_embeddings_batch(batch_size=batch_size)
        return result
        
    except Exception as e:
        logger.error(f"Ошибка массового обновления эмбеддингов: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка обновления: {str(e)}"
        )

@router.get("/health")
async def voice_health_check():
    """
    Проверка состояния голосового сервиса и компонентов самообучения
    """
    try:
        health_status = {
            "status": "healthy",
            "components": {
                "ai_service": ai_service.emergent_client is not None,
                "embedding_service": embedding_service.model is not None,
                "local_model": ai_service.use_local_model and ai_service.local_model is not None,
                "database": True  # Предполагаем, что если код выполняется, БД доступна
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Проверяем, все ли компоненты работают
        all_healthy = all(health_status["components"].values())
        if not all_healthy:
            health_status["status"] = "degraded"
        
        return health_status
        
    except Exception as e:
        logger.error(f"Ошибка проверки состояния: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }