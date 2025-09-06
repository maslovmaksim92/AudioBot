"""
Data models for the AI Assistant system with MongoDB integration
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
import uuid

# Employee positions enum
class Position(str, Enum):
    GENERAL_DIRECTOR = "general_director"
    DIRECTOR = "director"
    ACCOUNTANT = "accountant"
    HR_MANAGER = "hr_manager"
    CLEANING_MANAGER = "cleaning_manager"
    CONSTRUCTION_MANAGER = "construction_manager"
    ARCHITECT = "architect"
    CLEANER = "cleaner"
    OTHER = "other"

# Conversation models for AI memory
class ConversationMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    user_id: Optional[str] = None
    message_type: str  # "user", "assistant", "system"
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    ai_model: Optional[str] = None
    response_time_ms: Optional[int] = None

class ConversationSession(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None
    session_name: Optional[str] = None
    context: Dict[str, Any] = Field(default_factory=dict)  # Company context, user preferences, etc.
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_activity: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True
    message_count: int = 0
    total_tokens: int = 0  # For cost tracking

# Employee models
class Employee(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    position: Position
    email: Optional[str] = None
    telegram_id: Optional[int] = None
    phone: Optional[str] = None
    hire_date: datetime
    city: str  # Калуга или Кемерово
    is_active: bool = True
    profile_data: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    performance_metrics: Dict[str, Any] = Field(default_factory=dict)

class EmployeeCreate(BaseModel):
    name: str
    position: Position
    email: Optional[str] = None
    telegram_id: Optional[int] = None
    phone: Optional[str] = None
    hire_date: str  # String format for input
    city: str

# Company and business models
class CompanyMetrics(BaseModel):
    total_employees: int
    active_employees: int
    kaluga_employees: int
    kemerovo_employees: int
    total_houses: int
    kaluga_houses: int = 500
    kemerovo_houses: int = 100
    revenue: Optional[str] = None
    growth_rate: Optional[str] = None

class DashboardData(BaseModel):
    metrics: CompanyMetrics
    recent_activities: List[Dict[str, Any]]
    ai_insights: List[str]
    kpi: Optional[Dict[str, Any]] = None

# Financial models
class FinancialData(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    period: str  # "2024-01", "2024-Q1", etc.
    revenue: float
    expenses: float
    profit: float
    revenue_forecast: Optional[float] = None
    expense_forecast: Optional[float] = None
    profit_forecast: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    source: str = "manual"  # "manual", "bitrix24", "automated"

class FinancialForecast(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    period: str
    revenue_prediction: float
    confidence_score: float  # 0-1
    factors: List[str]  # Factors influencing the prediction
    created_at: datetime = Field(default_factory=datetime.utcnow)
    model_version: str = "v1.0"

# Meeting and analysis models
class MeetingRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    transcript: str
    participants: List[str]
    date: datetime
    duration_minutes: Optional[int] = None
    ai_summary: Optional[str] = None
    key_decisions: List[str] = Field(default_factory=list)
    action_items: List[Dict[str, Any]] = Field(default_factory=list)
    sentiment_score: Optional[float] = None  # -1 to 1
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Notification models
class NotificationTemplate(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    template: str
    trigger_conditions: Dict[str, Any]
    recipients: List[str]  # telegram_ids or user_ids
    is_active: bool = True
    frequency: str = "daily"  # "daily", "weekly", "monthly", "immediate"

class NotificationLog(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    template_id: str
    recipient: str
    message: str
    status: str = "pending"  # "pending", "sent", "failed"
    sent_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

# User profile models
class UserProfile(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    telegram_id: Optional[int] = None
    name: Optional[str] = None
    role: Optional[str] = None
    department: Optional[str] = None
    preferences: Dict[str, Any] = Field(default_factory=dict)
    ai_settings: Dict[str, Any] = Field(default_factory=dict)
    notification_settings: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_activity: datetime = Field(default_factory=datetime.utcnow)

# Integration models
class BitrixIntegration(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    data_type: str  # "deals", "contacts", "companies", "tasks"
    sync_timestamp: datetime
    records_synced: int
    success: bool
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

# Analytics models
class BusinessInsight(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    category: str  # "financial", "operational", "hr", "marketing"
    insight: str
    confidence_score: float  # 0-1
    data_sources: List[str]
    recommendations: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True

# Response models for API
class APIResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    data: Optional[Any] = None
    error: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ChatResponse(BaseModel):
    response: str
    timestamp: datetime
    status: str
    model: Optional[str] = None
    session_id: Optional[str] = None
    tokens_used: Optional[int] = None
    response_time_ms: Optional[int] = None