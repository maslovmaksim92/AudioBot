"""
Модель истории чатов с AI агентом
"""
from sqlalchemy import Column, String, Text, DateTime, Boolean, ForeignKey, Integer
from datetime import datetime
import uuid

from backend.app.config.database import Base

class ChatHistory(Base):
    """История сообщений чата с AI агентом"""
    __tablename__ = 'chat_history'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Роль: 'user' или 'assistant' или 'system'
    role = Column(String(20), nullable=False)
    
    # Содержимое сообщения
    content = Column(Text, nullable=False)
    
    # Telegram message_id для синхронизации (опционально)
    telegram_message_id = Column(String, nullable=True)
    
    # Message metadata: function calls, tokens usage, etc.
    message_metadata = Column(Text, nullable=True)  # JSON string
    
    # Флаг синхронизации с Telegram
    synced_to_telegram = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<ChatHistory(id={self.id}, user_id={self.user_id}, role={self.role})>"
