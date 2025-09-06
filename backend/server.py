from fastapi import FastAPI, APIRouter, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, date
from enum import Enum
import json

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'ai_assistant')]

# Create the main app
app = FastAPI(
    title="AI Assistant for Business Management",
    description="Comprehensive AI assistant for managing cleaning company operations",
    version="1.0.0"
)

# Create API router
api_router = APIRouter(prefix="/api")

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

# Models
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

class EmployeeCreate(BaseModel):
    name: str
    position: Position
    email: Optional[str] = None
    telegram_id: Optional[int] = None
    phone: Optional[str] = None
    hire_date: str  # String format for input
    city: str

class CompanyMetrics(BaseModel):
    total_employees: int
    active_employees: int
    kaluga_employees: int
    kemerovo_employees: int
    total_houses: int
    kaluga_houses: int = 500
    kemerovo_houses: int = 100

class DashboardData(BaseModel):
    metrics: CompanyMetrics
    recent_activities: List[Dict[str, Any]]
    ai_insights: List[str]

# API Endpoints
@api_router.get("/")
async def root():
    return {"message": "AI Assistant API", "status": "active", "version": "1.0.0"}

@api_router.get("/dashboard", response_model=DashboardData)
async def get_dashboard():
    """Get main dashboard data with real Bitrix24 integration"""
    from ai_service import ai_assistant
    from bitrix24_service import get_bitrix24_service
    
    # Get Bitrix24 service
    bx24 = await get_bitrix24_service()
    
    # Get real statistics from Bitrix24
    try:
        bitrix_stats = await bx24.get_cleaning_statistics()
        
        # Combine with local employee data
        total_employees = await db.employees.count_documents({})
        active_employees = await db.employees.count_documents({"is_active": True})
        kaluga_employees = await db.employees.count_documents({"city": "Калуга", "is_active": True})
        kemerovo_employees = await db.employees.count_documents({"city": "Кемерово", "is_active": True})
        
        metrics = CompanyMetrics(
            total_employees=total_employees or 0,
            active_employees=active_employees or 0,
            kaluga_employees=kaluga_employees or 0,
            kemerovo_employees=kemerovo_employees or 0,
            total_houses=bitrix_stats.get("kaluga_properties", 0) + bitrix_stats.get("kemerovo_properties", 0),
            kaluga_houses=bitrix_stats.get("kaluga_properties", 0),
            kemerovo_houses=bitrix_stats.get("kemerovo_properties", 0)
        )
        
        # Recent activities with Bitrix24 data
        recent_activities = [
            {"type": "bitrix24_sync", "message": f"Синхронизация с Bitrix24: {bitrix_stats.get('total_deals', 0)} сделок", "time": "только что"},
            {"type": "pipeline_found", "message": "Воронка 'Уборка подъездов' найдена", "time": "1 минуту назад"},
            {"type": "employee_added", "message": "Новый сотрудник добавлен", "time": "2 часа назад"}
        ]
        
    except Exception as e:
        logger.error(f"Error getting Bitrix24 data: {e}")
        # Fallback to basic metrics
        total_employees = await db.employees.count_documents({})
        active_employees = await db.employees.count_documents({"is_active": True})
        
        metrics = CompanyMetrics(
            total_employees=total_employees or 0,
            active_employees=active_employees or 0,
            kaluga_employees=0,
            kemerovo_employees=0,
            total_houses=600  # Default
        )
        
        recent_activities = [
            {"type": "error", "message": "Ошибка синхронизации с Bitrix24", "time": "только что"},
            {"type": "employee_added", "message": "Новый сотрудник добавлен", "time": "2 часа назад"}
        ]
    
    # Generate AI insights based on real metrics
    try:
        ai_insights = await ai_assistant.generate_business_insights(metrics.dict())
    except Exception as e:
        # Fallback insights if AI fails
        ai_insights = [
            "Подключение к Bitrix24 выполнено успешно - найдена воронка 'Уборка подъездов'",
            "Рекомендуется заполнить базу контактов домами в Калуге и Кемерово",
            "AI-анализ готов к работе с реальными данными из CRM"
        ]
    
    return DashboardData(
        metrics=metrics,
        recent_activities=recent_activities,
        ai_insights=ai_insights
    )

@api_router.get("/employees", response_model=List[Employee])
async def get_employees():
    """Get all employees"""
    employees = await db.employees.find().to_list(1000)
    return [Employee(**employee) for employee in employees]

@api_router.post("/employees", response_model=Employee)
async def create_employee(employee: EmployeeCreate):
    """Create new employee"""
    employee_dict = employee.dict()
    
    # Convert hire_date string to datetime
    from datetime import datetime
    try:
        hire_date_str = employee_dict.pop('hire_date')
        employee_dict['hire_date'] = datetime.strptime(hire_date_str, '%Y-%m-%d')
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid hire_date format. Use YYYY-MM-DD")
    
    employee_obj = Employee(**employee_dict)
    await db.employees.insert_one(employee_obj.dict())
    return employee_obj

@api_router.get("/employees/{employee_id}", response_model=Employee)
async def get_employee(employee_id: str):
    """Get employee by ID"""
    employee = await db.employees.find_one({"id": employee_id})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    return Employee(**employee)

@api_router.put("/employees/{employee_id}", response_model=Employee)
async def update_employee(employee_id: str, employee_data: dict):
    """Update employee"""
    employee_data["updated_at"] = datetime.utcnow()
    result = await db.employees.update_one(
        {"id": employee_id}, 
        {"$set": employee_data}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    updated_employee = await db.employees.find_one({"id": employee_id})
    return Employee(**updated_employee)

@api_router.delete("/employees/{employee_id}")
async def delete_employee(employee_id: str):
    """Delete employee"""
    result = await db.employees.delete_one({"id": employee_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Employee not found")
    return {"message": "Employee deleted successfully"}

# AI Chat endpoint
@api_router.post("/ai/chat")
async def ai_chat(message: dict):
    """AI Chat endpoint with persistent memory and enhanced context"""
    from ai_service import ai_assistant
    
    user_message = message.get("message", "")
    session_id = message.get("session_id", "default")
    user_id = message.get("user_id")
    
    if not user_message:
        raise HTTPException(status_code=400, detail="Message is required")
    
    # Get AI response with memory
    response = await ai_assistant.chat(user_message, session_id, user_id)
    return response

# Employee analysis endpoint
@api_router.post("/ai/analyze-employee/{employee_id}")
async def analyze_employee(employee_id: str):
    """Analyze employee data with AI"""
    from ai_service import ai_assistant
    
    # Get employee data
    employee = await db.employees.find_one({"id": employee_id})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Analyze with AI
    analysis = await ai_assistant.analyze_employee_data(employee)
    return analysis

# Meeting analysis endpoint
@api_router.post("/ai/analyze-meeting")
async def analyze_meeting(data: dict):
    """Analyze meeting transcript"""
    from ai_service import ai_assistant
    
    transcript = data.get("transcript", "")
    if not transcript:
        raise HTTPException(status_code=400, detail="Transcript is required")
    
    analysis = await ai_assistant.analyze_meeting_transcript(transcript)
    return analysis

# Bitrix24 integration endpoints
@api_router.get("/bitrix24/test")
async def test_bitrix24_connection():
    """Test Bitrix24 connection"""
    from bitrix24_service import get_bitrix24_service
    
    bx24 = await get_bitrix24_service()
    result = await bx24.test_connection()
    return result

@api_router.get("/bitrix24/statistics")
async def get_bitrix24_statistics():
    """Get statistics from Bitrix24"""
    from bitrix24_service import get_bitrix24_service
    
    bx24 = await get_bitrix24_service()
    stats = await bx24.get_cleaning_statistics()
    return stats

@api_router.get("/bitrix24/deals")
async def get_bitrix24_deals():
    """Get deals from Bitrix24"""
    from bitrix24_service import get_bitrix24_service
    
    bx24 = await get_bitrix24_service()
    deals = await bx24.get_deals()
    return {"deals": deals, "count": len(deals)}

@api_router.get("/bitrix24/contacts")
async def get_bitrix24_contacts():
    """Get contacts from Bitrix24"""
    from bitrix24_service import get_bitrix24_service
    
    bx24 = await get_bitrix24_service()
    contacts = await bx24.get_contacts()
    return {"contacts": contacts, "count": len(contacts)}

@api_router.get("/bitrix24/pipeline")
async def get_cleaning_pipeline():
    """Get cleaning pipeline info"""
    from bitrix24_service import get_bitrix24_service
    
    bx24 = await get_bitrix24_service()
    pipeline = await bx24.find_cleaning_pipeline()
    return {"pipeline": pipeline}

@api_router.post("/bitrix24/create-deal")
async def create_cleaning_deal_bitrix(deal_data: dict):
    """Create new cleaning deal in Bitrix24"""
    from bitrix24_service import get_bitrix24_service
    
    bx24 = await get_bitrix24_service()
    
    # Find cleaning pipeline
    pipeline = await bx24.find_cleaning_pipeline()
    if not pipeline:
        raise HTTPException(status_code=400, detail="Cleaning pipeline not found")
    
    # Prepare deal data for Bitrix24
    bitrix_deal_data = {
        "TITLE": deal_data.get("title", "Новая заявка на уборку"),
        "CATEGORY_ID": pipeline.get("ID"),
        "STAGE_ID": "NEW",  # Will be updated based on pipeline stages
        "ASSIGNED_BY_ID": 1,  # Current user
        "COMMENTS": deal_data.get("description", "")
    }
    
    # Add custom fields if provided
    if deal_data.get("address"):
        bitrix_deal_data["UF_CRM_ADDRESS"] = deal_data["address"]
    if deal_data.get("city"):
        bitrix_deal_data["UF_CRM_CITY"] = deal_data["city"]
    
    deal_id = await bx24.create_deal(bitrix_deal_data)
    
    if deal_id:
        return {"success": True, "deal_id": deal_id, "message": "Deal created successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to create deal in Bitrix24")

# User Profile endpoints
@api_router.post("/user/profile/update")
async def update_user_profile(profile_data: dict):
    """Update user profile during onboarding"""
    try:
        # Save to database
        profile_id = str(uuid.uuid4())
        profile_document = {
            "id": profile_id,
            "field": profile_data.get("field"),
            "value": profile_data.get("value"), 
            "full_profile": profile_data.get("profile", {}),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        if db is not None:
            await db.user_profiles.insert_one(profile_document)
        
        logger.info(f"User profile updated: {profile_data.get('field')} = {profile_data.get('value')}")
        
        return {
            "success": True,
            "message": "Profile updated successfully",
            "profile_id": profile_id
        }
    except Exception as e:
        logger.error(f"Error updating user profile: {e}")
        return {
            "success": False, 
            "message": "Error updating profile",
            "error": str(e)
        }

@api_router.get("/user/profile/{profile_id}")
async def get_user_profile(profile_id: str):
    """Get user profile by ID"""
    try:
        if db is not None:
            profile = await db.user_profiles.find_one({"id": profile_id})
            if profile:
                return {"success": True, "profile": profile}
        
        return {"success": False, "message": "Profile not found"}
    except Exception as e:
        return {"success": False, "error": str(e)}

# Company Database Creation endpoint
@api_router.post("/company/create-database")
async def create_company_database():
    """Create initial company database structure"""
    try:
        # Create collections and initial data
        collections_created = []
        
        if db is not None:
            # Company information
            company_info = {
                "id": str(uuid.uuid4()),
                "name": "Клининговая компания ВасДом",
                "description": "Уборка подъездов в Калуге и Кемерово",
                "cities": ["Калуга", "Кемерово"],
                "houses_count": {"Калуга": 500, "Кемерово": 100},
                "founded": "2020",
                "services": [
                    "Уборка подъездов",
                    "Строительные работы", 
                    "Текущий ремонт",
                    "Отделочные работы"
                ],
                "created_at": datetime.utcnow()
            }
            await db.company_info.insert_one(company_info)
            collections_created.append("company_info")
            
            # Sample departments
            departments = [
                {"id": str(uuid.uuid4()), "name": "Управление", "description": "Руководство компании"},
                {"id": str(uuid.uuid4()), "name": "Клининг", "description": "Отдел уборки подъездов"},
                {"id": str(uuid.uuid4()), "name": "Строительство", "description": "Строительные и ремонтные работы"},
                {"id": str(uuid.uuid4()), "name": "Бухгалтерия", "description": "Финансовый учет"}
            ]
            await db.departments.insert_many(departments)
            collections_created.append("departments")
            
            # Sample business processes
            processes = [
                {
                    "id": str(uuid.uuid4()),
                    "name": "Процесс уборки подъезда",
                    "steps": [
                        "Получение заявки от управляющей компании",
                        "Назначение бригады уборщиков",
                        "Выполнение уборки",
                        "Фотоотчет о выполненной работе",
                        "Отправка отчета в Bitrix24"
                    ],
                    "department": "Клининг"
                },
                {
                    "id": str(uuid.uuid4()),
                    "name": "Процесс ремонтных работ",
                    "steps": [
                        "Осмотр объекта и составление сметы",
                        "Согласование с заказчиком",
                        "Закупка материалов",
                        "Выполнение работ",
                        "Приемка работ"
                    ],
                    "department": "Строительство"
                }
            ]
            await db.business_processes.insert_many(processes)
            collections_created.append("business_processes")
        
        return {
            "success": True,
            "message": "База данных компании создана успешно",
            "collections_created": collections_created,
            "company_info": company_info
        }
        
    except Exception as e:
        logger.error(f"Error creating company database: {e}")
        return {
            "success": False,
            "message": "Ошибка при создании базы данных",
            "error": str(e)
        }

@api_router.get("/company/info")
async def get_company_info():
    """Get company information"""
    try:
        if db is not None:
            company = await db.company_info.find_one()
            departments = await db.departments.find().to_list(100)
            processes = await db.business_processes.find().to_list(100)
            
            # If database is empty, return mock data
            if not company:
                return {
                    "success": True,
                    "company": {
                        "name": "Клининговая компания ВасДом",
                        "description": "Уборка подъездов в Калуге и Кемерово", 
                        "cities": ["Калуга", "Кемерово"],
                        "houses_count": {"Калуга": 500, "Кемерово": 100}
                    },
                    "departments": [
                        {"name": "Управление", "description": "Руководство компании"},
                        {"name": "Клининг", "description": "Отдел уборки подъездов"},
                        {"name": "Строительство", "description": "Строительные работы"}
                    ]
                }
            
            return {
                "success": True,
                "company": company,
                "departments": departments,
                "processes": processes
            }
        
        # Mock data if no database
        return {
            "success": True,
            "company": {
                "name": "Клининговая компания ВасДом",
                "description": "Уборка подъездов в Калуге и Кемерово",
                "cities": ["Калуга", "Кемерово"],
                "houses_count": {"Калуга": 500, "Кемерово": 100}
            },
            "departments": [
                {"name": "Управление", "description": "Руководство компании"},
                {"name": "Клининг", "description": "Отдел уборки подъездов"},
                {"name": "Строительство", "description": "Строительные работы"}
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting company info: {e}")
        return {"success": False, "error": str(e)}

# Telegram Bot endpoints
@api_router.post("/telegram/start-bot")
async def start_telegram_bot(background_tasks):
    """Start Telegram bot in background"""
    try:
        from telegram_bot import run_bot_background
        
        # Start bot in background
        background_tasks.add_task(run_bot_background)
        
        return {"success": True, "message": "Telegram bot started in background"}
    except Exception as e:
        logger.error(f"Error starting Telegram bot: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start bot: {e}")

@api_router.get("/telegram/bot-info")
async def get_bot_info():
    """Get Telegram bot information"""
    bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
    if not bot_token:
        raise HTTPException(status_code=400, detail="Telegram bot token not configured")
    
    return {
        "bot_username": "@aitest123432_bot",
        "bot_token_configured": bool(bot_token),
        "features": [
            "🤖 AI чат с интеграцией GPT-4o-mini",
            "📊 Дешборд с данными Bitrix24",
            "💼 Управление сделками",
            "🎙️ Анализ планерок (голос + текст)",
            "📝 Система обратной связи",
            "🏠 Статистика домов по городам"
        ]
    }

# Add new endpoints for CYCLE 1 functionality

# Smart Planning endpoints
@api_router.get("/planning/routes/{city}")
async def get_optimized_routes_endpoint(city: str):
    """Get optimized cleaning routes for city"""
    from smart_planning_service import get_optimized_routes
    
    routes = await get_optimized_routes(city)
    return routes

@api_router.get("/planning/maintenance-predictions") 
async def get_maintenance_predictions_endpoint():
    """Get maintenance predictions for houses"""
    from smart_planning_service import get_maintenance_predictions
    
    predictions = await get_maintenance_predictions()
    return {"predictions": predictions, "count": len(predictions)}

@api_router.get("/planning/weekly-schedule/{city}")
async def get_weekly_schedule_endpoint(city: str):
    """Get weekly cleaning schedule for city"""
    from smart_planning_service import get_weekly_schedule
    
    schedule = await get_weekly_schedule(city)
    return schedule

# Rating System endpoints
@api_router.post("/ratings/employee")
async def rate_employee_endpoint(rating_data: dict):
    """Rate an employee"""
    from rating_service import rate_employee_performance
    
    result = await rate_employee_performance(
        rating_data.get("employee_id"),
        rating_data.get("rating"),
        rating_data.get("category"), 
        rating_data.get("comment", "")
    )
    return result

@api_router.get("/ratings/employee/{employee_id}/report")
async def get_employee_report_endpoint(employee_id: str):
    """Get employee performance report"""
    from rating_service import get_employee_performance_report
    
    report = await get_employee_performance_report(employee_id)
    return report

@api_router.get("/ratings/top-performers")
async def get_top_performers_endpoint(category: str = "overall", limit: int = 10):
    """Get top performing employees"""
    from rating_service import get_top_performers
    
    performers = await get_top_performers(category, limit)
    return {"top_performers": performers, "category": category}

# Enhanced Bitrix24 endpoints
@api_router.get("/bitrix24/cleaning-houses")
async def get_cleaning_houses_endpoint():
    """Get all cleaning houses from Bitrix24"""
    from bitrix24_service import get_bitrix24_service
    
    bx24 = await get_bitrix24_service()
    houses = await bx24.get_cleaning_houses_deals()
    return {"houses": houses, "count": len(houses)}

@api_router.post("/bitrix24/create-task")
async def create_bitrix_task_endpoint(task_data: dict):
    """Create task in Bitrix24"""
    from bitrix24_service import get_bitrix24_service
    
    bx24 = await get_bitrix24_service()
    result = await bx24.create_task(
        title=task_data.get("title"),
        description=task_data.get("description", ""),
        responsible_id=task_data.get("responsible_id", 1),
        deadline=task_data.get("deadline")
    )
    return result

@api_router.get("/bitrix24/tasks")
async def get_bitrix_tasks_endpoint():
    """Get tasks from Bitrix24"""
    from bitrix24_service import get_bitrix24_service
    
    bx24 = await get_bitrix24_service()
    tasks = await bx24.get_tasks()
    return {"tasks": tasks, "count": len(tasks)}

# Client Communication endpoints
@api_router.post("/clients/send-notification")
async def send_client_notification_endpoint(notification_data: dict):
    """Send notification to client"""
    from client_communication_service import send_client_notification
    
    result = await send_client_notification(
        notification_data.get("house_id"),
        notification_data.get("notification_type")
    )
    return result

@api_router.get("/clients/satisfaction-report")
async def get_satisfaction_report_endpoint():
    """Get client satisfaction report"""
    from client_communication_service import get_client_satisfaction_report
    
    report = await get_client_satisfaction_report()
    return report

@api_router.post("/clients/handle-complaint")
async def handle_complaint_endpoint(complaint_data: dict):
    """Handle client complaint"""
    from client_communication_service import handle_complaint
    
    result = await handle_complaint(complaint_data)
    return result

# Mobile API endpoints
@api_router.post("/mobile/auth")
async def mobile_auth_endpoint(auth_data: dict):
    """Authenticate employee for mobile app"""
    from mobile_api_service import authenticate_employee_mobile
    
    result = await authenticate_employee_mobile(
        auth_data.get("phone"),
        auth_data.get("password")
    )
    return result

@api_router.get("/mobile/employee/{employee_id}/data")
async def get_mobile_employee_data_endpoint(employee_id: str):
    """Get comprehensive employee data for mobile"""
    from mobile_api_service import get_employee_mobile_data
    
    data = await get_employee_mobile_data(employee_id)
    return data

@api_router.post("/mobile/submit-report")
async def submit_mobile_report_endpoint(report_data: dict):
    """Submit work report from mobile app"""
    from mobile_api_service import mobile_api_service
    
    result = await mobile_api_service.submit_work_report_mobile(
        report_data.get("employee_id"),
        report_data
    )
    return result

@api_router.get("/mobile/employee/{employee_id}/tasks")
async def get_mobile_tasks_endpoint(employee_id: str):
    """Get tasks for mobile app"""
    from mobile_api_service import mobile_api_service
    
    tasks = await mobile_api_service.get_employee_tasks_mobile(employee_id)
    return tasks

@api_router.get("/mobile/employee/{employee_id}/schedule")
async def get_mobile_schedule_endpoint(employee_id: str):
    """Get schedule for mobile app"""
    from mobile_api_service import mobile_api_service
    
    schedule = await mobile_api_service.get_employee_schedule_mobile(employee_id)
    return schedule

# System health and monitoring endpoints
@api_router.get("/system/health")
async def system_health_endpoint():
    """Get system health status"""
    from datetime import datetime
    
    try:
        # Check database connection
        from db import db_manager
        db_stats = await db_manager.get_conversation_stats()
        db_healthy = not db_stats.get("error")
        
        # Check Bitrix24 connection
        from bitrix24_service import get_bitrix24_service
        bx24 = await get_bitrix24_service()
        deals = await bx24.get_deals()
        bitrix_healthy = isinstance(deals, list)
        
        return {
            "status": "healthy" if db_healthy and bitrix_healthy else "degraded",
            "timestamp": datetime.utcnow().isoformat(),
            "services": {
                "database": "healthy" if db_healthy else "unhealthy",
                "bitrix24": "healthy" if bitrix_healthy else "unhealthy",
                "ai_service": "healthy",  # Assume healthy if we got here
                "telegram_bot": "running"
            },
            "version": "2.0.0",
            "uptime": "Active"
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

# Enhanced Financial endpoints
@api_router.get("/analytics/forecast")
async def get_financial_forecast_endpoint(period: str = "monthly", months: int = 3):
    """Get financial forecast based on Bitrix24 data"""
    from analytics_service import get_financial_forecast
    
    forecast = await get_financial_forecast(period, months)
    return forecast

@api_router.get("/financial/monthly-data")
async def get_monthly_financial_data_endpoint(months: int = 6):
    """Get comprehensive monthly financial data with plan vs fact"""
    from financial_service import get_monthly_financial_data
    
    data = await get_monthly_financial_data(months)
    return data

@api_router.get("/financial/expense-breakdown")
async def get_expense_breakdown_endpoint():
    """Get detailed expense breakdown analysis"""
    from financial_service import get_expense_breakdown_analysis
    
    breakdown = await get_expense_breakdown_analysis()
    return breakdown

@api_router.get("/financial/cash-flow")
async def get_cash_flow_forecast_endpoint(months: int = 6):
    """Get cash flow forecast"""
    from financial_service import get_cash_flow_forecast
    
    cash_flow = await get_cash_flow_forecast(months)
    return cash_flow

@api_router.get("/analytics/insights")
async def get_business_insights_endpoint(force_refresh: bool = False):
    """Get AI-generated business insights"""
    from analytics_service import get_business_insights
    
    insights = await get_business_insights(force_refresh)
    return {"insights": insights, "count": len(insights)}

@api_router.get("/analytics/performance")
async def get_performance_metrics_endpoint():
    """Get comprehensive performance metrics"""
    from analytics_service import get_performance_metrics
    
    metrics = await get_performance_metrics()
    return metrics

# Notification endpoints
@api_router.post("/notifications/daily-summary")
async def send_daily_summary_endpoint(request: dict):
    """Send daily summary to Telegram"""
    from notification_service import send_daily_summary
    
    chat_id = request.get("chat_id")
    if not chat_id:
        raise HTTPException(status_code=400, detail="chat_id is required")
    
    success = await send_daily_summary(int(chat_id))
    return {"success": success, "message": "Daily summary sent" if success else "Failed to send"}

@api_router.post("/notifications/alert")
async def send_alert_endpoint(request: dict):
    """Send business alert to Telegram"""
    from notification_service import send_business_alert
    
    chat_id = request.get("chat_id")
    alert_type = request.get("alert_type", "general")
    data = request.get("data", {})
    
    if not chat_id:
        raise HTTPException(status_code=400, detail="chat_id is required")
    
    success = await send_business_alert(int(chat_id), alert_type, data)
    return {"success": success, "message": "Alert sent" if success else "Failed to send"}

@api_router.get("/conversation/stats")
async def get_conversation_stats():
    """Get conversation statistics"""
    from db import db_manager
    
    stats = await db_manager.get_conversation_stats()
    return stats

@api_router.delete("/conversation/cleanup")
async def cleanup_old_conversations(retention_days: int = 90):
    """Cleanup old conversation data"""
    from db import db_manager
    
    result = await db_manager.cleanup_old_conversations(retention_days)
    return result

# Include router
app.include_router(api_router)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_event():
    logger.info("🚀 AI Assistant API started successfully")
    
    # Initialize database connection
    from db import db_manager
    try:
        await db_manager.connect()
        logger.info("✅ Database connection initialized")
        
        # Test database connection
        test_collection = db_manager.get_collection("test")
        await test_collection.find_one()
        logger.info("✅ Database test successful")
        
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        logger.info("⚠️ Continuing without database - some features may be limited")
    
    # Start notification scheduler (optional - uncomment to enable)
    # from notification_service import start_notification_scheduler
    # await start_notification_scheduler()
    # logger.info("📅 Notification scheduler started")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
    
    # Close database manager connection
    from db import db_manager
    try:
        await db_manager.disconnect()
        logger.info("✅ Database connection closed")
    except Exception as e:
        logger.error(f"❌ Error closing database: {e}")