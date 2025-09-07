from fastapi import FastAPI, APIRouter, HTTPException, Request
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime
import aiohttp
import json
import asyncio

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI(title="VasDom AudioBot - Business Management System", version="2.0.0")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# ============= BITRIX24 INTEGRATION SERVICE =============

class Bitrix24Service:
    def __init__(self):
        self.webhook_url = os.getenv("BITRIX24_WEBHOOK_URL", "").rstrip('/')
        
    async def _make_request(self, method: str, params: Dict = None):
        """Запрос к Bitrix24 API"""
        try:
            url = f"{self.webhook_url}/{method}"
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=params or {}, timeout=30) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        logger.error(f"Bitrix24 error {response.status}: {error_text}")
                        return {"error": f"HTTP {response.status}"}
        except Exception as e:
            logger.error(f"Bitrix24 request error: {str(e)}")
            return {"error": str(e)}
    
    async def get_deals(self, limit: int = 50):
        """Получение сделок"""
        params = {
            "SELECT": ["ID", "TITLE", "STAGE_ID", "OPPORTUNITY", "CONTACT_ID", "DATE_CREATE"],
            "start": 0,
            "limit": limit
        }
        result = await self._make_request("crm.deal.list", params)
        return result.get("result", [])
    
    async def create_task(self, task_data: Dict):
        """Создание задачи в Bitrix24"""
        params = {
            "fields": {
                "TITLE": task_data.get("title", ""),
                "DESCRIPTION": task_data.get("description", ""),
                "RESPONSIBLE_ID": task_data.get("responsible_id", "1"),
                "DEADLINE": task_data.get("deadline", ""),
            }
        }
        return await self._make_request("tasks.task.add", params)
    
    async def get_users(self):
        """Получение пользователей"""
        result = await self._make_request("user.get")
        return result.get("result", [])

# Initialize services
bitrix_service = Bitrix24Service()

# ============= TELEGRAM BOT SERVICE =============

class TelegramService:
    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}"
        
    async def send_message(self, chat_id: str, text: str, reply_markup: Dict = None):
        """Отправка сообщения в Telegram"""
        try:
            url = f"{self.api_url}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "HTML"
            }
            if reply_markup:
                payload["reply_markup"] = reply_markup
                
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, timeout=30) as response:
                    result = await response.json()
                    return result.get("ok", False)
        except Exception as e:
            logger.error(f"Telegram send error: {str(e)}")
            return False
    
    async def set_webhook(self):
        """Установка webhook"""
        try:
            webhook_url = os.getenv("TELEGRAM_WEBHOOK_URL")
            url = f"{self.api_url}/setWebhook"
            payload = {"url": webhook_url}
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    result = await response.json()
                    return result
        except Exception as e:
            return {"ok": False, "error": str(e)}

telegram_service = TelegramService()

# ============= AI CHAT SERVICE =============

async def get_ai_response(message: str, context: str = "") -> str:
    """AI ответ через Emergent LLM"""
    try:
        emergent_key = os.getenv("EMERGENT_LLM_KEY")
        if not emergent_key:
            return "AI сервис временно недоступен"
            
        url = "https://emergentmethods.ai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {emergent_key}",
            "Content-Type": "application/json"
        }
        
        prompt = f"""Ты AI-ассистент компании ВасДом, специализирующийся на уборке подъездов и строительстве.

Контекст: {context}

Сообщение пользователя: {message}

Отвечай профессионально, по-деловому, кратко и по существу."""
        
        data = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 500
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data, timeout=30) as response:
                if response.status == 200:
                    result = await response.json()
                    return result["choices"][0]["message"]["content"]
                else:
                    return "Извините, AI сервис временно недоступен."
                    
    except Exception as e:
        logger.error(f"AI response error: {str(e)}")
        return "Произошла ошибка при обращении к AI сервису."


# Define Models
class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class StatusCheckCreate(BaseModel):
    client_name: str

# Новые модели для полной функциональности
class Employee(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    full_name: str
    phone: str
    role: str
    department: str
    telegram_id: Optional[str] = None
    bitrix24_id: Optional[str] = None
    active: bool = True
    performance_score: float = 0.0
    created_at: datetime = Field(default_factory=datetime.utcnow)

class EmployeeCreate(BaseModel):
    full_name: str
    phone: str
    role: str
    department: str

class ChatMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    sender_id: str
    content: str
    ai_response: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    chat_type: str = "dashboard"  # "dashboard", "telegram", "meeting"

class Meeting(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    participants: List[str] = []
    start_time: datetime
    recording_text: Optional[str] = None
    ai_summary: Optional[str] = None
    action_items: List[str] = []
    bitrix_tasks_created: List[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)

class SystemLog(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    level: str  # INFO, WARNING, ERROR
    message: str
    component: str  # backend, telegram, bitrix24, ai
    data: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

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