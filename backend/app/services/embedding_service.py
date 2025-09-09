"""
Сервис для работы с эмбеддингами и поиска похожих ответов
Использует sentence-transformers для векторного представления текста
"""
import numpy as np
import pickle
from typing import List, Tuple, Optional, Dict
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
import logging

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logging.warning("sentence-transformers не установлен. Эмбеддинги недоступны.")

from app.config.database import SessionLocal
from app.models.database import VoiceLogDB, VoiceEmbeddingDB
from app.models.schemas import SimilarResponse
from app.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class EmbeddingService:
    """Сервис для создания и поиска эмбеддингов"""
    
    def __init__(self):
        self.model = None
        self.model_name = settings.EMBEDDING_MODEL
        self._initialize_model()
    
    def _initialize_model(self):
        """Инициализация модели эмбеддингов"""
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            logger.error("sentence-transformers не доступен")
            return
        
        try:
            self.model = SentenceTransformer(self.model_name)
            logger.info(f"Модель эмбеддингов загружена: {self.model_name}")
        except Exception as e:
            logger.error(f"Ошибка загрузки модели эмбеддингов: {str(e)}")
            self.model = None
    
    def generate_embeddings(self, text: str) -> Optional[np.ndarray]:
        """
        Генерация эмбеддинга для текста
        
        Args:
            text: Входной текст
            
        Returns:
            numpy array с эмбеддингом или None при ошибке
        """
        if not self.model:
            logger.warning("Модель эмбеддингов недоступна")
            return None
        
        try:
            # Очистка и подготовка текста
            cleaned_text = text.strip()
            if not cleaned_text:
                return None
            
            # Генерация эмбеддинга
            embedding = self.model.encode(cleaned_text, convert_to_numpy=True)
            return embedding
            
        except Exception as e:
            logger.error(f"Ошибка генерации эмбеддинга: {str(e)}")
            return None
    
    async def store_embedding(self, log_id: int, user_message: str) -> bool:
        """
        Сохранение эмбеддинга в базу данных
        
        Args:
            log_id: ID лога взаимодействия
            user_message: Сообщение пользователя
            
        Returns:
            True если успешно сохранено
        """
        try:
            # Генерируем эмбеддинг
            embedding = self.generate_embeddings(user_message)
            if embedding is None:
                return False
            
            # Сериализуем numpy array
            embedding_bytes = pickle.dumps(embedding)
            
            async with SessionLocal() as db:
                # Проверяем, есть ли уже эмбеддинг для этого лога
                existing = await db.query(VoiceEmbeddingDB).filter(
                    VoiceEmbeddingDB.log_id == log_id
                ).first()
                
                if existing:
                    # Обновляем существующий
                    existing.vector = embedding_bytes
                    existing.embedding_model = self.model_name
                else:
                    # Создаем новый
                    new_embedding = VoiceEmbeddingDB(
                        log_id=log_id,
                        vector=embedding_bytes,
                        embedding_model=self.model_name
                    )
                    db.add(new_embedding)
                
                await db.commit()
                logger.debug(f"Эмбеддинг сохранен для лога {log_id}")
                return True
                
        except Exception as e:
            logger.error(f"Ошибка сохранения эмбеддинга: {str(e)}")
            return False
    
    def cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Вычисление косинусного сходства между векторами"""
        try:
            dot_product = np.dot(a, b)
            norm_a = np.linalg.norm(a)
            norm_b = np.linalg.norm(b)
            
            if norm_a == 0 or norm_b == 0:
                return 0.0
            
            similarity = dot_product / (norm_a * norm_b)
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Ошибка вычисления косинусного сходства: {str(e)}")
            return 0.0
    
    async def find_similar_responses(
        self,
        query_text: str,
        limit: int = 5,
        similarity_threshold: float = 0.7,
        exclude_log_id: Optional[int] = None
    ) -> List[SimilarResponse]:
        """
        Поиск похожих вопросов и ответов
        
        Args:
            query_text: Текст запроса для поиска
            limit: Максимальное количество результатов
            similarity_threshold: Минимальный порог сходства
            exclude_log_id: ID лога для исключения из поиска
            
        Returns:
            Список похожих ответов
        """
        if not self.model:
            logger.warning("Модель эмбеддингов недоступна для поиска")
            return []
        
        try:
            # Генерируем эмбеддинг для запроса
            query_embedding = self.generate_embeddings(query_text)
            if query_embedding is None:
                return []
            
            similar_responses = []
            
            async with SessionLocal() as db:
                # Получаем все эмбеддинги с логами
                query = db.query(VoiceEmbeddingDB, VoiceLogDB).join(
                    VoiceLogDB, VoiceEmbeddingDB.log_id == VoiceLogDB.id
                ).filter(
                    VoiceLogDB.ai_response.isnot(None)
                )
                
                if exclude_log_id:
                    query = query.filter(VoiceLogDB.id != exclude_log_id)
                
                results = await query.all()
                
                # Вычисляем сходство для каждого эмбеддинга
                similarities = []
                for embedding_record, log_record in results:
                    try:
                        # Десериализуем эмбеддинг
                        stored_embedding = pickle.loads(embedding_record.vector)
                        
                        # Вычисляем сходство
                        similarity = self.cosine_similarity(query_embedding, stored_embedding)
                        
                        if similarity >= similarity_threshold:
                            similarities.append((similarity, log_record))
                    
                    except Exception as e:
                        logger.debug(f"Ошибка обработки эмбеддинга {embedding_record.id}: {str(e)}")
                        continue
                
                # Сортируем по убыванию сходства
                similarities.sort(key=lambda x: x[0], reverse=True)
                
                # Формируем результат
                for similarity, log in similarities[:limit]:
                    similar_response = SimilarResponse(
                        log_id=log.id,
                        user_message=log.user_message,
                        ai_response=log.ai_response,
                        similarity_score=similarity,
                        rating=log.rating,
                        created_at=log.created_at
                    )
                    similar_responses.append(similar_response)
                
                logger.debug(f"Найдено {len(similar_responses)} похожих ответов для запроса")
                return similar_responses
                
        except Exception as e:
            logger.error(f"Ошибка поиска похожих ответов: {str(e)}")
            return []
    
    async def update_embeddings_batch(self, batch_size: int = 100) -> Dict:
        """
        Массовое обновление эмбеддингов для логов без векторных представлений
        
        Args:
            batch_size: Размер батча для обработки
            
        Returns:
            Статистика обновления
        """
        if not self.model:
            return {"success": False, "error": "Модель эмбеддингов недоступна"}
        
        try:
            processed = 0
            errors = 0
            
            async with SessionLocal() as db:
                # Находим логи без эмбеддингов
                logs_without_embeddings = await db.query(VoiceLogDB).outerjoin(
                    VoiceEmbeddingDB, VoiceLogDB.id == VoiceEmbeddingDB.log_id
                ).filter(
                    VoiceEmbeddingDB.id.is_(None),
                    VoiceLogDB.user_message.isnot(None)
                ).limit(batch_size).all()
                
                for log in logs_without_embeddings:
                    success = await self.store_embedding(log.id, log.user_message)
                    if success:
                        processed += 1
                    else:
                        errors += 1
                
                return {
                    "success": True,
                    "processed": processed,
                    "errors": errors,
                    "total_found": len(logs_without_embeddings)
                }
                
        except Exception as e:
            logger.error(f"Ошибка массового обновления эмбеддингов: {str(e)}")
            return {"success": False, "error": str(e)}

# Глобальный экземпляр сервиса
embedding_service = EmbeddingService()