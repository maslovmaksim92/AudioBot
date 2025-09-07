from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
import uuid

# Base Model with common fields
class BaseEntity(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

# Employee Models
class EmployeeRole(str, Enum):
    DIRECTOR = "director"
    GENERAL_DIRECTOR = "general_director" 
    ACCOUNTANT = "accountant"
    CONSTRUCTION_HEAD = "construction_head"
    CONSTRUCTION_MANAGER = "construction_manager"
    FOREMAN = "foreman"
    HR_DIRECTOR = "hr_director"
    HR_MANAGER = "hr_manager"
    CLEANING_HEAD = "cleaning_head"
    CLEANING_MANAGER = "cleaning_manager"
    CLIENT_MANAGER = "client_manager"
    CLEANER = "cleaner"

class Employee(BaseEntity):
    full_name: str
    phone: str
    role: EmployeeRole
    department: str
    telegram_id: Optional[str] = None
    bitrix24_id: Optional[str] = None
    active: bool = True
    performance_score: float = 0.0
    last_activity: Optional[datetime] = None
    notes: List[str] = []

# Task Models
class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class TaskPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class Task(BaseEntity):
    title: str
    description: str
    assignee_id: str
    creator_id: str
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.MEDIUM
    due_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    project_id: Optional[str] = None
    recurring: bool = False
    recurring_pattern: Optional[str] = None  # "daily", "weekly", "monthly"
    
# Project Models (Cleaning & Construction)
class ProjectType(str, Enum):
    CLEANING = "cleaning"
    CONSTRUCTION = "construction"

class ProjectStatus(str, Enum):
    PLANNING = "planning"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class Project(BaseEntity):
    name: str
    description: str
    type: ProjectType
    status: ProjectStatus = ProjectStatus.PLANNING
    client_id: str
    manager_id: str
    team_members: List[str] = []
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    budget: float = 0.0
    actual_cost: float = 0.0
    progress: float = 0.0  # 0-100%
    location: Optional[Dict[str, Any]] = None  # GPS coordinates, address
    bitrix24_deal_id: Optional[str] = None

# Route & Schedule Models  
class Route(BaseEntity):
    name: str
    projects: List[str] = []  # Project IDs
    assigned_team: List[str] = []  # Employee IDs
    total_distance: float = 0.0
    estimated_time: int = 0  # minutes
    fuel_cost: float = 0.0
    optimized: bool = False
    date: datetime

class Meeting(BaseEntity):
    title: str
    description: str
    participants: List[str] = []  # Employee IDs
    start_time: datetime
    end_time: datetime
    location: Optional[str] = None
    recording_url: Optional[str] = None
    transcript: Optional[str] = None
    summary: Optional[str] = None
    action_items: List[str] = []

# Financial Models
class FinanceCategory(str, Enum):
    REVENUE = "revenue"
    EXPENSE = "expense"
    INVESTMENT = "investment"

class FinanceEntry(BaseEntity):
    category: FinanceCategory
    subcategory: str
    amount: float
    description: str
    project_id: Optional[str] = None
    date: datetime
    approved: bool = False
    approved_by: Optional[str] = None

# Analytics & Improvement Models
class ImprovementStatus(str, Enum):
    SUGGESTED = "suggested"
    APPROVED = "approved"
    IMPLEMENTING = "implementing"
    COMPLETED = "completed"
    REJECTED = "rejected"

class Improvement(BaseEntity):
    title: str
    description: str
    category: str  # "process", "technology", "training", etc.
    suggested_by: str  # "AI" or employee_id
    impact_score: float  # 0-10
    effort_score: float  # 0-10
    status: ImprovementStatus = ImprovementStatus.SUGGESTED
    implementation_date: Optional[datetime] = None
    result_description: Optional[str] = None

# System Learning Model
class SystemLearning(BaseEntity):
    event_type: str  # "error", "success", "feedback", "performance"
    data: Dict[str, Any]
    pattern_detected: Optional[str] = None
    action_taken: Optional[str] = None
    confidence_score: float = 0.0

# Chat & Communication Models
class ChatMessage(BaseEntity):
    sender_id: str
    recipient_id: Optional[str] = None  # None for group messages
    chat_type: str  # "telegram", "dashboard", "system"
    content: str
    message_type: str = "text"  # "text", "voice", "image", "document"
    ai_response: Optional[str] = None
    sentiment: Optional[str] = None

# Client Models
class Client(BaseEntity):
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    address: str
    building_info: Dict[str, Any] = {}  # floors, apartments, etc.
    service_history: List[str] = []  # Project IDs
    satisfaction_score: float = 0.0
    bitrix24_id: Optional[str] = None

# System Status Model
class SystemStatus(BaseEntity):
    service_name: str
    status: str  # "healthy", "warning", "error"
    last_check: datetime
    metrics: Dict[str, Any] = {}
    errors: List[str] = []

# Dashboard Models for API responses
class DashboardStats(BaseModel):
    total_employees: int
    active_projects: int
    completed_tasks_today: int
    revenue_month: float
    system_health: str
    ai_suggestions: List[Dict[str, Any]]

class EmployeePerformance(BaseModel):
    employee_id: str
    name: str
    score: float
    tasks_completed: int
    efficiency_trend: str  # "up", "down", "stable"
    suggestions: List[str]

# Request/Response Models
class EmployeeCreate(BaseModel):
    full_name: str
    phone: str
    role: EmployeeRole
    department: str
    telegram_id: Optional[str] = None

class TaskCreate(BaseModel):
    title: str
    description: str
    assignee_id: str
    priority: TaskPriority = TaskPriority.MEDIUM
    due_date: Optional[datetime] = None
    recurring: bool = False
    recurring_pattern: Optional[str] = None

class ProjectCreate(BaseModel):
    name: str
    description: str
    type: ProjectType
    client_id: str
    manager_id: str
    budget: float = 0.0
    location: Optional[Dict[str, Any]] = None

class AIFeedback(BaseModel):
    rating: int  # 1-5
    feedback: str
    suggestion: Optional[str] = None
    category: str = "general"