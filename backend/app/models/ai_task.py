"""
Модель AI задач
"""
from sqlalchemy import Column, String, Text, DateTime, Boolean, ForeignKey, Enum as SQLEnum
from datetime import datetime
import enum
import uuid

from backend.app.config.database import Base

class AITaskStatus(str, enum.Enum):
    """Статусы AI задач"""
    PENDING = "pending"  # Ожидает выполнения
    IN_PROGRESS = "in_progress"  # В процессе
    COMPLETED = "completed"  # Завершена
    CANCELLED = "cancelled"  # Отменена

class AITaskType(str, enum.Enum):
    """Типы AI задач"""
    SEND_SCHEDULE = "send_schedule"  # Отправить график
    REMINDER = "reminder"  # Напоминание
    REPORT = "report"  # Создать отчет
    NOTIFICATION = "notification"  # Уведомление
    CUSTOM = "custom"  # Пользовательская задача

class AITask(Base):
    """AI задачи, созданные ассистентом"""
    __tablename__ = 'ai_tasks'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Создатель задачи (пользователь или система)
    created_by = Column(String, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Исполнитель задачи (может быть другой пользователь или система)
    assigned_to = Column(String, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    
    # Тип и статус задачи
    task_type = Column(SQLEnum(AITaskType), nullable=False)
    status = Column(SQLEnum(AITaskStatus), default=AITaskStatus.PENDING)
    
    # Заголовок и описание
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Дата и время выполнения
    scheduled_at = Column(DateTime, nullable=True)  # Когда задача должна быть выполнена
    completed_at = Column(DateTime, nullable=True)  # Когда задача была завершена
    
    # Связанные данные (JSON string)
    # Например: {"house_ids": [1,2,3], "brigade_number": "1", "email": "example@test.com"}
    related_data = Column(Text, nullable=True)
    
    # Результат выполнения
    result = Column(Text, nullable=True)
    
    # Флаги
    is_recurring = Column(Boolean, default=False)  # Повторяющаяся задача
    notify_telegram = Column(Boolean, default=True)  # Уведомлять в Telegram
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<AITask(id={self.id}, type={self.task_type}, status={self.status})>"
