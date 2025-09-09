"""
AI сервис с поддержкой самообучения
Интегрирует Emergent LLM, локальные модели и систему поиска похожих ответов
"""
import os
import time
import json
import logging
from typing import Optional, Dict, List
from datetime import datetime

try:
    from emergentintegrations import EmergentLLM
    EMERGENT_AVAILABLE = True
except ImportError:
    EMERGENT_AVAILABLE = False
    logging.warning("emergentintegrations не установлен")

from sqlalchemy import func
from app.config.database import SessionLocal
from app.models.database import VoiceLogDB
from app.models.schemas import ChatRequest, ChatResponse, SimilarResponse
from app.services.embedding_service import embedding_service
from app.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class AIService:
    """Сервис для работы с AI моделями и самообучением"""
    
    def __init__(self):
        self.emergent_client = None
        self.local_model = None
        self.use_local_model = settings.USE_LOCAL_MODEL
        self._initialize_models()
    
    def _initialize_models(self):
        """Инициализация AI моделей"""
        # Инициализация Emergent LLM
        if EMERGENT_AVAILABLE and settings.EMERGENT_LLM_KEY:
            try:
                self.emergent_client = EmergentLLM(api_key=settings.EMERGENT_LLM_KEY)
                logger.info("Emergent LLM клиент инициализирован")
            except Exception as e:
                logger.error(f"Ошибка инициализации Emergent LLM: {str(e)}")
        
        # Загрузка локальной модели (если настроена)
        if self.use_local_model:
            self._load_local_model()
    
    def _load_local_model(self):
        """Загрузка локально дообученной модели"""
        try:
            model_path = settings.LOCAL_MODEL_PATH
            if os.path.exists(model_path):
                # Здесь будет загрузка локальной модели
                # Пока заглушка для будущей реализации
                logger.info(f"Локальная модель будет загружена из: {model_path}")
                # self.local_model = load_model(model_path)
            else:
                logger.warning(f"Локальная модель не найдена: {model_path}")
                self.use_local_model = False
        except Exception as e:
            logger.error(f"Ошибка загрузки локальной модели: {str(e)}")
            self.use_local_model = False
    
    def _build_context_prompt(self, user_message: str, similar_responses: List[SimilarResponse]) -> str:
        """
        Построение промпта с контекстом из похожих ответов
        
        Args:
            user_message: Сообщение пользователя
            similar_responses: Похожие ответы из истории
            
        Returns:
            Расширенный промпт с контекстом
        """
        base_prompt = """Ты — AI помощник VasDom AudioBot для управления клининговой компанией в Калуге. 
Отвечай профессионально, кратко и по делу на русском языке.

У тебя есть опыт работы с похожими вопросами. Вот примеры из истории:

"""
        
        # Добавляем похожие ответы как контекст
        context_examples = []
        for i, response in enumerate(similar_responses[:3], 1):  # Используем топ-3
            rating_text = f" (оценка: {response.rating}★)" if response.rating else ""
            context_examples.append(
                f"Пример {i}{rating_text}:\n"
                f"Вопрос: {response.user_message}\n"
                f"Ответ: {response.ai_response}\n"
            )
        
        if context_examples:
            base_prompt += "\n".join(context_examples)
            base_prompt += "\n\nИспользуй этот опыт для ответа на новый вопрос.\n\n"
        else:
            base_prompt += "Похожих вопросов в истории не найдено. Отвечай на основе своих знаний.\n\n"
        
        base_prompt += f"Текущий вопрос пользователя: {user_message}\n\nОтвет:"
        
        return base_prompt
    
    async def process_message(self, request: ChatRequest) -> ChatResponse:
        """
        Обработка сообщения пользователя с поддержкой самообучения
        
        Args:
            request: Запрос с сообщением пользователя
            
        Returns:
            Ответ AI с ID лога для обратной связи
        """
        start_time = time.time()
        
        try:
            # 1. Поиск похожих ответов в истории
            similar_responses = await embedding_service.find_similar_responses(
                query_text=request.message,
                limit=5,
                similarity_threshold=0.7
            )
            
            logger.debug(f"Найдено {len(similar_responses)} похожих ответов")
            
            # 2. Построение промпта с контекстом
            enhanced_prompt = self._build_context_prompt(request.message, similar_responses)
            
            # 3. Генерация ответа
            ai_response = await self._generate_response(enhanced_prompt)
            model_used = "local-model" if self.use_local_model else "gpt-4-mini"
            
            # 4. Вычисление времени ответа
            response_time = time.time() - start_time
            
            # 5. Сохранение взаимодействия в БД
            log_id = await self._save_to_db(
                user_message=request.message,
                ai_response=ai_response,
                session_id=request.session_id,
                model_used=model_used,
                response_time=response_time
            )
            
            # 6. Асинхронное создание эмбеддинга для нового сообщения
            if log_id:
                await embedding_service.store_embedding(log_id, request.message)
            
            return ChatResponse(
                response=ai_response,
                log_id=log_id,
                session_id=request.session_id,
                model_used=model_used,
                response_time=response_time
            )
            
        except Exception as e:
            logger.error(f"Ошибка обработки сообщения: {str(e)}")
            
            # Возвращаем ошибку с фиктивным log_id
            return ChatResponse(
                response="Извините, произошла ошибка при обработке вашего запроса. Попробуйте позже.",
                log_id=0,
                session_id=request.session_id,
                model_used="error",
                response_time=time.time() - start_time
            )
    
    async def _generate_response(self, prompt: str) -> str:
        """
        Генерация ответа через AI модель
        
        Args:
            prompt: Промпт для модели
            
        Returns:
            Ответ модели
        """
        try:
            if self.use_local_model and self.local_model:
                # Использование локальной модели
                # Пока заглушка для будущей реализации
                return "Ответ от локальной модели (в разработке)"
            
            elif self.emergent_client:
                # Использование Emergent LLM
                response = await self.emergent_client.chat_completion(
                    messages=[
                        {"role": "system", "content": "Ты AI помощник VasDom AudioBot."},
                        {"role": "user", "content": prompt}
                    ],
                    model="gpt-4o-mini",
                    max_tokens=1000,
                    temperature=0.7
                )
                return response.choices[0].message.content
            
            else:
                return "AI сервис временно недоступен. Обратитесь к администратору."
                
        except Exception as e:
            logger.error(f"Ошибка генерации ответа: {str(e)}")
            return "Извините, не удалось сгенерировать ответ. Попробуйте переформулировать вопрос."
    
    async def _save_to_db(
        self,
        user_message: str,
        ai_response: str,
        session_id: str,
        model_used: str = "gpt-4-mini",
        response_time: Optional[float] = None,
        token_count: Optional[int] = None
    ) -> int:
        """
        Сохранение взаимодействия в базу данных
        
        Returns:
            ID созданной записи
        """
        try:
            async with SessionLocal() as db:
                log_entry = VoiceLogDB(
                    session_id=session_id,
                    user_message=user_message,
                    ai_response=ai_response,
                    model_used=model_used,
                    response_time=response_time,
                    token_count=token_count
                )
                
                db.add(log_entry)
                await db.commit()
                await db.refresh(log_entry)
                
                logger.debug(f"Взаимодействие сохранено с ID: {log_entry.id}")
                return log_entry.id
                
        except Exception as e:
            logger.error(f"Ошибка сохранения в БД: {str(e)}")
            return 0
    
    async def update_log_rating(
        self,
        log_id: int,
        rating: int,
        feedback_text: Optional[str] = None
    ) -> bool:
        """
        Обновление рейтинга и отзыва для лога взаимодействия
        
        Args:
            log_id: ID лога
            rating: Оценка от 1 до 5
            feedback_text: Опциональный текст отзыва
            
        Returns:
            True если успешно обновлено
        """
        try:
            async with SessionLocal() as db:
                log_entry = await db.query(VoiceLogDB).filter(
                    VoiceLogDB.id == log_id
                ).first()
                
                if not log_entry:
                    logger.warning(f"Лог с ID {log_id} не найден")
                    return False
                
                log_entry.rating = rating
                log_entry.feedback_text = feedback_text
                log_entry.updated_at = datetime.utcnow()
                
                await db.commit()
                logger.info(f"Рейтинг {rating} сохранен для лога {log_id}")
                return True
                
        except Exception as e:
            logger.error(f"Ошибка обновления рейтинга: {str(e)}")
            return False
    
    async def get_learning_statistics(self) -> Dict:
        """Получение статистики самообучения"""
        try:
            async with SessionLocal() as db:
                # Общее количество взаимодействий
                total_interactions = await db.query(VoiceLogDB).count()
                
                # Взаимодействия с оценками
                rated_interactions = await db.query(VoiceLogDB).filter(
                    VoiceLogDB.rating.isnot(None)
                ).count()
                
                # Средняя оценка
                avg_rating_result = await db.query(
                    func.avg(VoiceLogDB.rating)
                ).filter(VoiceLogDB.rating.isnot(None)).scalar()
                
                avg_rating = float(avg_rating_result) if avg_rating_result else None
                
                # Положительные и отрицательные оценки
                positive_ratings = await db.query(VoiceLogDB).filter(
                    VoiceLogDB.rating >= 4
                ).count()
                
                negative_ratings = await db.query(VoiceLogDB).filter(
                    VoiceLogDB.rating <= 2
                ).count()
                
                return {
                    "total_interactions": total_interactions,
                    "rated_interactions": rated_interactions,
                    "avg_rating": avg_rating,
                    "positive_ratings": positive_ratings,
                    "negative_ratings": negative_ratings,
                    "current_model": "local-model" if self.use_local_model else "gpt-4-mini",
                    "embedding_service_available": embedding_service.model is not None
                }
                
        except Exception as e:
            logger.error(f"Ошибка получения статистики: {str(e)}")
            return {}

# Глобальный экземпляр сервиса
ai_service = AIService()