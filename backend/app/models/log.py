"""
Модель логов - журнал событий системы
"""
from sqlalchemy import Column, String, DateTime, Text, JSON, Enum as SQLEnum
from datetime import datetime, timezone
import enum

from backend.app.config.database import Base

class LogLevel(str, enum.Enum):
    """Уровни логирования"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class LogCategory(str, enum.Enum):
    """Категории логов"""
    SYSTEM = "system"  # Системные события
    AUTH = "auth"  # Аутентификация
    CLEANING = "cleaning"  # Уборки
    TASK = "task"  # Задачи
    AI = "ai"  # AI действия
    INTEGRATION = "integration"  # Интеграции (Bitrix, Telegram)
    VOICE = "voice"  # Звонки
    USER = "user"  # Действия пользователей

class Log(Base):
    """Модель лога"""
    __tablename__ = 'logs'
    
    id = Column(String, primary_key=True)  # UUID
    
    # Основная информация
    level = Column(SQLEnum(LogLevel), default=LogLevel.INFO)
    category = Column(SQLEnum(LogCategory), default=LogCategory.SYSTEM)
    
    message = Column(Text, nullable=False)
    
    # Пользователь (если применимо)
    user_id = Column(String, nullable=True)
    user_email = Column(String, nullable=True)
    
    # Дополнительные данные (JSON)
    extra_data = Column(JSON, nullable=True)
    # Формат: {"ip": "...", "action": "...", "details": {...}}
    
    # IP адрес и user agent
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    
    # Метаданные
    created_at = Column(DateTime, default=lambda: datetime.utcnow(), index=True)
    
    def __repr__(self):
        return f"<Log(id={self.id}, level={self.level}, category={self.category}, message={self.message[:50]})>"