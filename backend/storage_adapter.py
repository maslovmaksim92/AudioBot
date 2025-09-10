"""
Адаптер хранилища для VasDom AudioBot
Поддерживает как PostgreSQL, так и in-memory хранилище
"""
from typing import List, Dict, Optional, Any
from datetime import datetime
import uuid
import numpy as np
from loguru import logger
import os

class StorageAdapter:
    """Унифицированный адаптер для работы с разными типами хранилищ"""
    
    def __init__(self):
        self.database_available = self._check_database_availability()
        self.in_memory_storage = SafeInMemoryStorage()
        
        if self.database_available:
            logger.success("🗄️ Используем PostgreSQL для персистентного хранения")
        else:
            logger.info("💾 Используем in-memory хранилище")
    
    def _check_database_availability(self) -> bool:
        """Проверяем доступность PostgreSQL"""
        try:
            database_url = os.getenv("DATABASE_URL", "")
            return bool(database_url and database_url.startswith("postgresql"))
        except Exception:
            return False
    
    async def add_conversation(self, log_id: str, user_msg: str, ai_response: str, session_id: str) -> Dict:
        """Добавляем диалог в выбранное хранилище"""
        if self.database_available:
            return await self._add_conversation_db(log_id, user_msg, ai_response, session_id)
        else:
            return self.in_memory_storage.add_conversation(log_id, user_msg, ai_response, session_id)
    
    async def _add_conversation_db(self, log_id: str, user_msg: str, ai_response: str, session_id: str) -> Dict:
        """Добавляем диалог в PostgreSQL"""
        try:
            from app.config.database import SessionLocal
            from app.models.database import VoiceLogDB
            from sqlalchemy import select
            
            async with SessionLocal() as db:
                new_log = VoiceLogDB(
                    id=log_id,
                    user_message=user_msg,
                    ai_response=ai_response,
                    session_id=session_id,
                    model_used="gpt-4o-mini",
                    created_at=datetime.utcnow()
                )
                
                db.add(new_log)
                await db.commit()
                
                logger.debug(f"Диалог сохранен в PostgreSQL: {log_id}")
                
                return {
                    "log_id": log_id,
                    "user_message": user_msg,
                    "ai_response": ai_response,
                    "session_id": session_id,
                    "timestamp": datetime.utcnow(),
                    "rating": None,
                    "feedback": None,
                    "model_used": "gpt-4o-mini"
                }
                
        except Exception as e:
            logger.error(f"Ошибка сохранения в PostgreSQL: {e}")
            # Fallback на in-memory
            logger.info("Fallback на in-memory хранилище")
            return self.in_memory_storage.add_conversation(log_id, user_msg, ai_response, session_id)
    
    async def update_rating(self, log_id: str, rating: int, feedback: str = None) -> bool:
        """Обновляем рейтинг диалога"""
        if self.database_available:
            return await self._update_rating_db(log_id, rating, feedback)
        else:
            return self.in_memory_storage.update_rating(log_id, rating, feedback)
    
    async def _update_rating_db(self, log_id: str, rating: int, feedback: str = None) -> bool:
        """Обновляем рейтинг в PostgreSQL"""
        try:
            from app.config.database import SessionLocal
            from app.models.database import VoiceLogDB
            from sqlalchemy import select
            
            async with SessionLocal() as db:
                stmt = select(VoiceLogDB).where(VoiceLogDB.id == log_id)
                result = await db.execute(stmt)
                log_entry = result.scalar_one_or_none()
                
                if log_entry:
                    log_entry.rating = rating
                    log_entry.feedback_text = feedback
                    log_entry.updated_at = datetime.utcnow()
                    await db.commit()
                    logger.debug(f"Рейтинг обновлен в PostgreSQL: {log_id}")
                    return True
                else:
                    logger.warning(f"Диалог не найден в PostgreSQL: {log_id}")
                    return False
                    
        except Exception as e:
            logger.error(f"Ошибка обновления рейтинга в PostgreSQL: {e}")
            # Fallback на in-memory
            return self.in_memory_storage.update_rating(log_id, rating, feedback)
    
    async def get_rated_conversations(self, min_rating: int = 4) -> List[Dict]:
        """Получаем диалоги с хорошим рейтингом"""
        if self.database_available:
            return await self._get_rated_conversations_db(min_rating)
        else:
            return self.in_memory_storage.get_rated_conversations(min_rating)
    
    async def _get_rated_conversations_db(self, min_rating: int = 4) -> List[Dict]:
        """Получаем диалоги с хорошим рейтингом из PostgreSQL"""
        try:
            from app.config.database import SessionLocal
            from app.models.database import VoiceLogDB
            from sqlalchemy import select
            
            async with SessionLocal() as db:
                stmt = select(VoiceLogDB).where(
                    VoiceLogDB.rating >= min_rating,
                    VoiceLogDB.rating.isnot(None)
                ).order_by(VoiceLogDB.created_at.desc())
                
                result = await db.execute(stmt)
                logs = result.scalars().all()
                
                conversations = []
                for log in logs:
                    conversations.append({
                        "log_id": log.id,
                        "user_message": log.user_message,
                        "ai_response": log.ai_response,
                        "session_id": log.session_id,
                        "timestamp": log.created_at,
                        "rating": log.rating,
                        "feedback": log.feedback_text,
                        "model_used": log.model_used or "gpt-4o-mini"
                    })
                
                return conversations
                
        except Exception as e:
            logger.error(f"Ошибка получения диалогов из PostgreSQL: {e}")
            # Fallback на in-memory
            return self.in_memory_storage.get_rated_conversations(min_rating)
    
    async def get_stats(self) -> Dict:
        """Получаем статистику диалогов"""
        if self.database_available:
            return await self._get_stats_db()
        else:
            return self.in_memory_storage.get_stats()
    
    async def _get_stats_db(self) -> Dict:
        """Получаем статистику из PostgreSQL"""
        try:
            from app.config.database import SessionLocal
            from app.models.database import VoiceLogDB
            from sqlalchemy import select, func
            
            async with SessionLocal() as db:
                # Общее количество
                total_stmt = select(func.count()).select_from(VoiceLogDB)
                total_result = await db.execute(total_stmt)
                total = total_result.scalar() or 0
                
                # С рейтингами
                rated_stmt = select(func.count()).select_from(VoiceLogDB).where(
                    VoiceLogDB.rating.isnot(None)
                )
                rated_result = await db.execute(rated_stmt)
                rated = rated_result.scalar() or 0
                
                # Средний рейтинг
                avg_stmt = select(func.avg(VoiceLogDB.rating)).where(
                    VoiceLogDB.rating.isnot(None)
                )
                avg_result = await db.execute(avg_stmt)
                avg_rating = avg_result.scalar()
                
                # Положительные и отрицательные
                pos_stmt = select(func.count()).select_from(VoiceLogDB).where(VoiceLogDB.rating >= 4)
                pos_result = await db.execute(pos_stmt)
                positive = pos_result.scalar() or 0
                
                neg_stmt = select(func.count()).select_from(VoiceLogDB).where(VoiceLogDB.rating <= 2)
                neg_result = await db.execute(neg_stmt)
                negative = neg_result.scalar() or 0
                
                return {
                    "total_interactions": total,
                    "avg_rating": float(avg_rating) if avg_rating else None,
                    "positive_ratings": positive,
                    "negative_ratings": negative,
                    "rated_interactions": rated
                }
                
        except Exception as e:
            logger.error(f"Ошибка получения статистики из PostgreSQL: {e}")
            # Fallback на in-memory
            return self.in_memory_storage.get_stats()
    
    @property
    def conversations(self) -> List[Dict]:
        """Получаем все диалоги (для совместимости)"""
        if self.database_available:
            # Для PostgreSQL возвращаем пустой список, чтобы не загружать всю БД
            return []
        else:
            return self.in_memory_storage.conversations
    
    @property
    def embeddings(self) -> Dict:
        """Получаем эмбеддинги (для совместимости)"""
        return self.in_memory_storage.embeddings
    
    @property
    def max_conversations(self) -> int:
        """Максимальное количество диалогов"""
        if self.database_available:
            return 100000  # PostgreSQL может хранить намного больше
        else:
            return self.in_memory_storage.max_conversations


class SafeInMemoryStorage:
    """Безопасное in-memory хранилище (оригинальная реализация)"""
    
    def __init__(self):
        self.conversations = []  # Все диалоги
        self.embeddings = {}     # ID -> эмбеддинг (безопасно сериализованный)
        self.learning_data = {}  # Данные для обучения
        self.max_conversations = 10000  # Лимит для предотвращения утечки памяти
        
    def add_conversation(self, log_id: str, user_msg: str, ai_response: str, session_id: str):
        conv = {
            "log_id": log_id,
            "user_message": user_msg,
            "ai_response": ai_response,
            "session_id": session_id,
            "timestamp": datetime.utcnow(),
            "rating": None,
            "feedback": None,
            "model_used": "gpt-4o-mini"
        }
        
        self.conversations.append(conv)
        
        # Ограничиваем размер для предотвращения утечки памяти
        if len(self.conversations) > self.max_conversations:
            # Удаляем старые неоцененные диалоги
            self.conversations = [c for c in self.conversations if c.get("rating") is not None][-self.max_conversations//2:]
            logger.info(f"Очищено старых диалогов, осталось: {len(self.conversations)}")
        
        return conv
    
    def update_rating(self, log_id: str, rating: int, feedback: str = None):
        for conv in self.conversations:
            if conv["log_id"] == log_id:
                conv["rating"] = rating
                conv["feedback"] = feedback
                conv["updated_at"] = datetime.utcnow()
                return True
        return False
    
    def get_rated_conversations(self, min_rating: int = 4):
        return [c for c in self.conversations if c.get("rating") is not None and c.get("rating", 0) >= min_rating]
    
    def get_stats(self):
        total = len(self.conversations)
        rated = [c for c in self.conversations if c.get("rating") is not None]
        avg_rating = sum(c["rating"] for c in rated) / len(rated) if rated else None
        positive = len([c for c in rated if c["rating"] >= 4])
        negative = len([c for c in rated if c["rating"] <= 2])
        
        return {
            "total_interactions": total,
            "avg_rating": avg_rating,
            "positive_ratings": positive,
            "negative_ratings": negative,
            "rated_interactions": len(rated)
        }
    
    def store_embedding_safe(self, log_id: str, embedding: np.ndarray):
        """Безопасное сохранение эмбеддинга без pickle"""
        try:
            # Используем безопасную сериализацию через bytes
            embedding_bytes = embedding.astype(np.float32).tobytes()
            self.embeddings[log_id] = {
                "data": embedding_bytes,
                "shape": embedding.shape,
                "dtype": str(embedding.dtype)
            }
            return True
        except Exception as e:
            logger.error(f"Ошибка сохранения эмбеддинга: {e}")
            return False
    
    def load_embedding_safe(self, log_id: str) -> Optional[np.ndarray]:
        """Безопасная загрузка эмбеддинга без pickle"""
        try:
            if log_id not in self.embeddings:
                return None
            
            emb_data = self.embeddings[log_id]
            embedding = np.frombuffer(emb_data["data"], dtype=np.float32)
            return embedding.reshape(emb_data["shape"])
        except Exception as e:
            logger.error(f"Ошибка загрузки эмбеддинга: {e}")
            return None