"""
Модель для логов выполнения агентов
"""
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

class AgentExecutionLog(BaseModel):
    """Лог выполнения агента"""
    id: str
    agent_id: str
    agent_name: str
    executed_at: str
    success: bool
    skipped: bool = False
    skip_reason: Optional[str] = None
    actions_executed: int
    results: List[Dict[str, Any]]
    error: Optional[str] = None
    duration_ms: Optional[int] = None
    
    class Config:
        from_attributes = True

class AgentExecutionStats(BaseModel):
    """Статистика выполнения агентов"""
    total_executions: int
    successful_executions: int
    failed_executions: int
    skipped_executions: int
    success_rate: float
    avg_duration_ms: float
    last_24h_executions: int
