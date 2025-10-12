"""
Pydantic схемы для задач
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
from datetime import datetime

from backend.app.models.task import TaskStatus, TaskPriority

class TaskBase(BaseModel):
    """Базовая схема задачи"""
    title: str
    description: Optional[str] = None
    status: TaskStatus = TaskStatus.TODO
    priority: TaskPriority = TaskPriority.MEDIUM
    assigned_to_id: Optional[str] = None
    house_id: Optional[str] = None
    due_date: Optional[datetime] = None

class TaskCreate(TaskBase):
    """Схема создания задачи"""
    checklist: Optional[List[Dict[str, Any]]] = None
    mindmap: Optional[Dict[str, Any]] = None
    ai_proposed: bool = False
    ai_reasoning: Optional[str] = None

class TaskUpdate(BaseModel):
    """Схема обновления задачи"""
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    assigned_to_id: Optional[str] = None
    house_id: Optional[str] = None
    checklist: Optional[List[Dict[str, Any]]] = None
    mindmap: Optional[Dict[str, Any]] = None
    due_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None

class TaskResponse(TaskBase):
    """Схема ответа с задачей"""
    id: str
    created_by_id: Optional[str] = None
    checklist: Optional[List[Dict[str, Any]]] = None
    mindmap: Optional[Dict[str, Any]] = None
    ai_proposed: bool
    ai_reasoning: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True