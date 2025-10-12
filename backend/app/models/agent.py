"""
Модель Agent - AI агенты и автоматизации
"""
from sqlalchemy import Column, String, Boolean, JSON, DateTime, Integer
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

Base = declarative_base()

class Agent(Base):
    """Модель агента в базе данных"""
    __tablename__ = 'agents'
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String)
    type = Column(String, nullable=False)  # scheduler, integration, bot, workflow, ai_agent
    status = Column(String, default='active')  # active, inactive, error
    
    # Конфигурация
    triggers = Column(JSON, default=list)  # [{type: 'cron', config: {...}}]
    actions = Column(JSON, default=list)  # [{type: 'telegram', config: {...}}]
    config = Column(JSON, default=dict)  # Дополнительная конфигурация
    
    # Статистика
    executions_total = Column(Integer, default=0)
    executions_success = Column(Integer, default=0)
    executions_failed = Column(Integer, default=0)
    last_execution = Column(DateTime(timezone=True), nullable=True)
    
    # Метаданные
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    created_by = Column(String)
    
    def to_dict(self):
        """Преобразование в словарь"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'type': self.type,
            'status': self.status,
            'triggers': self.triggers or [],
            'actions': self.actions or [],
            'config': self.config or {},
            'executions_total': self.executions_total or 0,
            'executions_success': self.executions_success or 0,
            'executions_failed': self.executions_failed or 0,
            'last_execution': self.last_execution.isoformat() if self.last_execution else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by': self.created_by
        }


# Pydantic модели для API
class TriggerConfig(BaseModel):
    """Конфигурация триггера"""
    type: str  # cron, webhook, telegram, bitrix, manual
    config: Dict[str, Any] = Field(default_factory=dict)
    name: Optional[str] = None

class ActionConfig(BaseModel):
    """Конфигурация действия"""
    type: str  # telegram_send, ai_call, email_send, bitrix_create, log_create
    config: Dict[str, Any] = Field(default_factory=dict)
    name: Optional[str] = None

class AgentCreate(BaseModel):
    """Создание агента"""
    name: str
    description: Optional[str] = None
    type: str  # scheduler, integration, bot, workflow, ai_agent
    triggers: List[TriggerConfig] = Field(default_factory=list)
    actions: List[ActionConfig] = Field(default_factory=list)
    config: Dict[str, Any] = Field(default_factory=dict)
    status: str = "active"

class AgentUpdate(BaseModel):
    """Обновление агента"""
    name: Optional[str] = None
    description: Optional[str] = None
    type: Optional[str] = None
    triggers: Optional[List[TriggerConfig]] = None
    actions: Optional[List[ActionConfig]] = None
    config: Optional[Dict[str, Any]] = None
    status: Optional[str] = None

class AgentResponse(BaseModel):
    """Ответ с информацией об агенте"""
    id: str
    name: str
    description: Optional[str]
    type: str
    status: str
    triggers: List[Dict[str, Any]]
    actions: List[Dict[str, Any]]
    config: Dict[str, Any]
    executions_total: int
    executions_success: int
    executions_failed: int
    last_execution: Optional[str]
    created_at: str
    updated_at: str
    created_by: Optional[str]
    
    class Config:
        from_attributes = True

class AgentStats(BaseModel):
    """Статистика агентов"""
    total_agents: int
    active_agents: int
    inactive_agents: int
    executions_today: int
    executions_success_rate: float
    total_users: int
