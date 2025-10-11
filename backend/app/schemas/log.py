"""
Pydantic схемы для логов
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

from backend.app.models.log import LogLevel, LogCategory

class LogCreate(BaseModel):
    """Схема создания лога"""
    level: LogLevel = LogLevel.INFO
    category: LogCategory
    message: str
    user_id: Optional[str] = None
    user_email: Optional[str] = None
    extra_data: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

class LogResponse(BaseModel):
    """Схема ответа с логом"""
    id: str
    level: LogLevel
    category: LogCategory
    message: str
    user_id: Optional[str] = None
    user_email: Optional[str] = None
    extra_data: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True