"""
Сервис для работы с эмбеддингами и поиска похожих ответов
Использует sentence-transformers для векторного представления текста
"""
import numpy as np
from typing import List, Tuple, Optional, Dict
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, select
from sqlalchemy.ext.asyncio import AsyncSession
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
        Сохранение эмбеддинга в базу данных (исправлено - асинхронные вызовы)
        
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
            
            # Безопасная сериализация без pickle
            embedding_bytes = embedding.astype(np.float32).tobytes()
            
            async with SessionLocal() as db:
                # Исправлено: используем select() вместо db.query()
                stmt = select(VoiceEmbeddingDB).where(VoiceEmbeddingDB.log_id == log_id)
                result = await db.execute(stmt)
                existing = result.scalar_one_or_none()
                
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
    
    def _load_embedding_safe(self, embedding_bytes: bytes, shape: tuple) -> Optional[np.ndarray]:
        """Безопасная загрузка эмбеддинга без pickle"""
        try:
            embedding = np.frombuffer(embedding_bytes, dtype=np.float32)
            return embedding.reshape(shape)
        except Exception as e:
            logger.error(f"Ошибка загрузки эмбеддинга: {e}")
            return None
    
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
        Поиск похожих вопросов и ответов (исправлено - асинхронные вызовы)
        
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
                # Исправлено: используем select() и join()
                stmt = select(VoiceEmbeddingDB, VoiceLogDB).join(
                    VoiceLogDB, VoiceEmbeddingDB.log_id == VoiceLogDB.id
                ).where(
                    VoiceLogDB.ai_response.isnot(None)
                )
                
                if exclude_log_id:
                    stmt = stmt.where(VoiceLogDB.id != exclude_log_id)
                
                result = await db.execute(stmt)
                results = result.all()
                
                # Вычисляем сходство для каждого эмбеддинга
                similarities = []
                for embedding_record, log_record in results:
                    try:
                        # Безопасная десериализация без pickle
                        stored_embedding = self._load_embedding_safe(
                            embedding_record.vector, 
                            query_embedding.shape  # Используем форму запроса как референс
                        )
                        
                        if stored_embedding is not None:
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
        Массовое обновление эмбеддингов для логов без векторных представлений (исправлено)
        
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
                # Исправлено: используем select() с outerjoin
                stmt = select(VoiceLogDB).outerjoin(
                    VoiceEmbeddingDB, VoiceLogDB.id == VoiceEmbeddingDB.log_id
                ).where(
                    VoiceEmbeddingDB.id.is_(None),
                    VoiceLogDB.user_message.isnot(None)
                ).limit(batch_size)
                
                result = await db.execute(stmt)
                logs_without_embeddings = result.scalars().all()
                
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

# Функция для создания сервиса по требованию (убираем глобальную инициализацию)
def get_embedding_service() -> EmbeddingService:
    """Получить экземпляр сервиса эмбеддингов"""
    return EmbeddingService()