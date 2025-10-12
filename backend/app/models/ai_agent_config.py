"""
Модель для конфигурации AI агентов
"""
from sqlalchemy import Column, String, Boolean, Float, Text
from sqlalchemy.sql import func
from datetime import datetime
from backend.app.config.database import Base
from sqlalchemy import DateTime


class AIAgentConfig(Base):
    __tablename__ = "ai_agent_configs"
    
    id = Column(String, primary_key=True)
    agent_name = Column(String, unique=True, index=True, nullable=False)  # section_improver, code_reviewer, etc
    display_name = Column(String, nullable=False)  # "Улучшение разделов"
    description = Column(Text)  # Описание агента
    prompt = Column(Text, nullable=False)  # Системный промпт
    model = Column(String, default="gpt-4")  # gpt-4, gpt-4-turbo, etc
    temperature = Column(Float, default=0.7)
    enabled = Column(Boolean, default=True)
    
    # Метаданные
    created_at = Column(DateTime, default=lambda: datetime.utcnow())
    updated_at = Column(DateTime, default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow())
    
    def __repr__(self):
        return f"<AIAgentConfig(id={self.id}, name={self.agent_name}, enabled={self.enabled})>"
