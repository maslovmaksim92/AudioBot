from fastapi import FastAPI, APIRouter
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")


# Define Models
class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class StatusCheckCreate(BaseModel):
    client_name: str

# Add your routes to the router instead of directly to app
@api_router.get("/")
async def root():
    return {"message": "Hello World"}

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.dict()
    status_obj = StatusCheck(**status_dict)
    _ = await db.status_checks.insert_one(status_obj.dict())
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find().to_list(1000)
    return [StatusCheck(**status_check) for status_check in status_checks]

# 🚀 ДОРАБОТКИ ДЛЯ ВАСДОМ - ДОБАВЛЯЕМ НОВЫЕ ФУНКЦИИ К СУЩЕСТВУЮЩЕМУ КОДУ

# Новые модели для управления сотрудниками
class Employee(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    full_name: str
    phone: str
    role: str
    department: str
    telegram_id: Optional[str] = None
    active: bool = True
    performance_score: float = 0.0
    created_at: datetime = Field(default_factory=datetime.utcnow)

class EmployeeCreate(BaseModel):
    full_name: str
    phone: str
    role: str
    department: str

# Новые endpoints для дашборда
@api_router.get("/dashboard")
async def get_dashboard():
    """Дашборд с основной статистикой"""
    try:
        total_employees = await db.employees.count_documents({"active": True})
        return {
            "total_employees": total_employees,
            "active_projects": 0,  # Пока заглушка
            "completed_tasks_today": 0,  # Пока заглушка 
            "revenue_month": 0.0,  # Пока заглушка
            "system_health": "good",
            "ai_suggestions": []
        }
    except Exception as e:
        logger.error(f"Dashboard error: {str(e)}")
        return {"error": str(e)}

@api_router.get("/employees")
async def get_employees():
    """Получение списка сотрудников"""
    try:
        employees = await db.employees.find({"active": True}).to_list(1000)
        return [Employee(**emp) for emp in employees]
    except Exception as e:
        logger.error(f"Employees error: {str(e)}")
        return {"error": str(e)}

@api_router.post("/employees")
async def create_employee(employee: EmployeeCreate):
    """Создание нового сотрудника"""
    try:
        employee_dict = employee.dict()
        employee_obj = Employee(**employee_dict)
        await db.employees.insert_one(employee_obj.dict())
        return employee_obj
    except Exception as e:
        logger.error(f"Create employee error: {str(e)}")
        return {"error": str(e)}

# Include the router in the main app - ПЕРЕНЕСЕНО В КОНЕЦ
app.include_router(api_router)

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

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()

# Инициализация базовых сотрудников при запуске
@app.on_event("startup")
async def startup_event():
    """Инициализация системы"""
    logger.info("🚀 Starting VasDom AudioBot System...")
    
    # Инициализируем базовых сотрудников из задания
    try:
        base_employees = [
            # Руководство
            {"full_name": "Маслов Максим Валерьевич", "phone": "89200924550", "role": "director", "department": "Администрация"},
            {"full_name": "Маслова Валентина Михайловна", "phone": "89208701769", "role": "general_director", "department": "Администрация"},
            {"full_name": "Филиппов Сергей Сергеевич", "phone": "89056400212", "role": "construction_head", "department": "Строительный отдел"},
            {"full_name": "Черкасов Ярослав Артурович", "phone": "89208855883", "role": "construction_manager", "department": "Строительный отдел"},
            
            # Остальные сотрудники
            {"full_name": "Колосов Дмитрий Сергеевич", "phone": "89105489113", "role": "accountant", "department": "Бухгалтерия"},
            {"full_name": "Маслова Арина Алексеевна", "phone": "89533150101", "role": "construction_manager", "department": "Строительный отдел"},
            {"full_name": "Илья Николаевич", "phone": "", "role": "foreman", "department": "Строительный отдел"},
            {"full_name": "Ольга Андреевна", "phone": "89106058454", "role": "hr_director", "department": "УФИЦ"},
            {"full_name": "Попов Никита Валерьевич", "phone": "89105447777", "role": "hr_manager", "department": "УФИЦ"},
            {"full_name": "Наталья Викторовна", "phone": "89206148777", "role": "cleaning_head", "department": "Клининг"},
            {"full_name": "Ильиных Алексей Владимирович", "phone": "89206188414", "role": "cleaning_manager", "department": "Клининг"},
            {"full_name": "Шадоба Елена Михайловна", "phone": "89103330355", "role": "client_manager", "department": "Маркетинг"},
            {"full_name": "Коцефан Даниела", "phone": "89775278413", "role": "client_manager", "department": "Маркетинг"}
        ]
        
        for emp_data in base_employees:
            # Проверяем, есть ли уже такой сотрудник
            existing = await db.employees.find_one({"phone": emp_data["phone"]}) if emp_data["phone"] else None
            
            if not existing:
                employee_obj = Employee(**emp_data)
                await db.employees.insert_one(employee_obj.dict())
                logger.info(f"✅ Created employee: {emp_data['full_name']}")
        
        logger.info("👥 Base employees initialized")
        
    except Exception as e:
        logger.error(f"Error initializing employees: {str(e)}")
    
    logger.info("✅ System startup completed!")