from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

# Pydantic Models for API
class VoiceMessage(BaseModel):
    text: str
    user_id: str = "user"

class ChatResponse(BaseModel):
    response: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class Meeting(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    transcription: Optional[str] = None
    summary: Optional[str] = None
    status: str = "active"
    created_at: datetime = Field(default_factory=datetime.utcnow)

class AITask(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    scheduled_time: Optional[datetime] = None
    recurring: bool = False
    status: str = "pending"
    chat_messages: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class DashboardStats(BaseModel):
    employees: int
    houses: int
    entrances: int
    apartments: int
    floors: int
    meetings: int
    ai_tasks: int
    won_houses: Optional[int] = 0
    problem_houses: Optional[int] = 0

class CleaningSchedule(BaseModel):
    cleaning_date_1: Optional[List[str]] = None  # Даты первого типа уборки
    cleaning_type_1: Optional[str] = None        # Тип уборки 1
    cleaning_date_2: Optional[List[str]] = None  # Даты второго типа уборки  
    cleaning_type_2: Optional[str] = None        # Тип уборки 2
    frequency: Optional[str] = None              # Периодичность (например "2 // 140")

class House(BaseModel):
    address: str
    deal_id: str
    stage: str
    brigade: str
    status_text: str
    status_color: str
    created_date: Optional[str] = None
    opportunity: Optional[str] = None
    last_sync: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    
    # Расширенная информация о доме
    apartments_count: Optional[int] = None       # Количество квартир
    floors_count: Optional[int] = None           # Количество этажей  
    entrances_count: Optional[int] = None        # Количество подъездов
    tariff: Optional[str] = None                 # Тариф
    
    # График уборки на сентябрь 2025
    september_schedule: Optional[CleaningSchedule] = None
    
    # Дополнительные поля для фильтрации
    cleaning_days: Optional[List[str]] = None    # Дни недели уборки для фильтра