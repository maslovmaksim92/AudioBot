"""
Pydantic схемы для домов
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
from datetime import datetime

class HouseBase(BaseModel):
    """Базовая схема дома"""
    address: str
    apartments_count: Optional[int] = None
    entrances_count: Optional[int] = None
    floors_count: Optional[int] = None
    company_id: Optional[str] = None
    company_title: Optional[str] = None
    assigned_by_id: Optional[str] = None
    assigned_by_name: Optional[str] = None
    brigade_number: Optional[str] = None
    tariff: Optional[str] = None
    elder_contact: Optional[str] = None
    notes: Optional[str] = None

class HouseCreate(HouseBase):
    """Схема создания дома"""
    bitrix_id: Optional[str] = None

class HouseUpdate(BaseModel):
    """Схема обновления дома"""
    address: Optional[str] = None
    apartments_count: Optional[int] = None
    entrances_count: Optional[int] = None
    floors_count: Optional[int] = None
    company_title: Optional[str] = None
    brigade_number: Optional[str] = None
    tariff: Optional[str] = None
    cleaning_schedule: Optional[Dict[str, Any]] = None
    complaints: Optional[List[Dict[str, Any]]] = None
    notes: Optional[str] = None
    elder_contact: Optional[str] = None
    act_signed: Optional[datetime] = None
    last_cleaning: Optional[datetime] = None

class HouseResponse(HouseBase):
    """Схема ответа с домом"""
    id: str
    bitrix_id: Optional[str] = None
    cleaning_schedule: Optional[Dict[str, Any]] = None
    complaints: Optional[List[Dict[str, Any]]] = None
    act_signed: Optional[datetime] = None
    last_cleaning: Optional[datetime] = None
    periodicity: Optional[str] = None  # Вычисляемое поле - периодичность уборки
    created_at: datetime
    updated_at: datetime
    synced_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True