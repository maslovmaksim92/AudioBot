"""
Модель задач - управление задачами сотрудников
"""
from sqlalchemy import Column, String, DateTime, Boolean, Text, JSON, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import enum

from backend.app.config.database import Base

class TaskStatus(str, enum.Enum):
    """Статусы задач"""
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    CANCELLED = "cancelled"

class TaskPriority(str, enum.Enum):
    """Приоритеты задач"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class Task(Base):
    """Модель задачи"""
    __tablename__ = 'tasks'
    
    id = Column(String, primary_key=True)  # UUID
    
    # Основная информация
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    
    # Статус и приоритет
    status = Column(SQLEnum(TaskStatus), default=TaskStatus.TODO)
    priority = Column(SQLEnum(TaskPriority), default=TaskPriority.MEDIUM)
    
    # Исполнитель и автор
    assigned_to_id = Column(String, ForeignKey('users.id'), nullable=True)
    created_by_id = Column(String, ForeignKey('users.id'), nullable=True)
    
    # Связь с домом (если задача привязана к объекту)
    house_id = Column(String, ForeignKey('houses.id'), nullable=True)
    
    # Чек-лист
    checklist = Column(JSON, nullable=True)
    # Формат: [{"id": "1", "text": "...", "done": false}, ...]
    
    # Mind-map (JSON структура)
    mindmap = Column(JSON, nullable=True)
    # Формат: {"nodes": [...], "edges": [...]}
    
    # Дедлайн
    due_date = Column(DateTime, nullable=True)
    
    # AI предложенная задача
    ai_proposed = Column(Boolean, default=False)
    ai_reasoning = Column(Text, nullable=True)  # Обоснование AI
    
    # Метаданные
    created_at = Column(DateTime, default=lambda: datetime.utcnow())
    updated_at = Column(DateTime, default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow())
    completed_at = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<Task(id={self.id}, title={self.title}, status={self.status})>"