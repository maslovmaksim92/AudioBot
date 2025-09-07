from fastapi import FastAPI, APIRouter, Request
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

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app
app = FastAPI(title="VasDom AudioBot", version="2.0.0")
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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
    
    async def get_deals_detailed(self, limit: int = 50):
        """Получение сделок с полной информацией"""
        params = {
            "SELECT": [
                "ID", "TITLE", "STAGE_ID", "OPPORTUNITY", "CONTACT_ID", "DATE_CREATE", "ASSIGNED_BY_ID",
                "UF_CRM_*"  # Все пользовательские поля
            ],
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

async def get_ai_response(message: str, context: str = "", department: str = "") -> str:
    try:
        # Сначала получаем релевантные знания из базы
        knowledge_context = ""
        if department:
            try:
                training_files = await db.training_files.find({"department": department}).to_list(10)
                if training_files:
                    knowledge_context = f"\n\nБАЗА ЗНАНИЙ ОТДЕЛА {department}:\n"
                    for file in training_files[:3]:  # Берем топ 3 файла
                        knowledge_context += f"- {file['filename']}: {file['content'][:200]}...\n"
            except:
                pass
        
        openai_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("EMERGENT_LLM_KEY")
        if not openai_key:
            return f"🤖 Сообщение получено: '{message}'. AI сервис настраивается..."
        
        url = "https://api.openai.com/v1/chat/completions"
        if openai_key.startswith("sk-or-"):
            url = "https://openrouter.ai/api/v1/chat/completions"
        elif openai_key.startswith("sk-emergent-"):
            url = "https://emergentmethods.ai/v1/chat/completions"
        
        headers = {"Authorization": f"Bearer {openai_key}", "Content-Type": "application/json"}
        
        system_message = f"""Ты AI-ассистент компании ВасДом - лидера в уборке подъездов и строительстве в Калуге.

КОНТЕКСТ: {context}

КОМПАНИЯ ВАСДОМ:
- Уборка подъездов в 400+ домах Калуги
- Строительные работы
- 13+ сотрудников в команде  
- Bitrix24 CRM интеграция

{knowledge_context}

Используй информацию из базы знаний для точных ответов. Отвечай профессионально, кратко и по делу на русском языке."""
        
        data = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": system_message},
                {"role": "user", "content": message}
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
                    return f"🤖 AI временно недоступен. Ваше сообщение: '{message}'"
                    
    except Exception as e:
        return f"🤖 Сообщение обработано: '{message}'. AI ответ будет доступен позже."


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

# Новые модели для дополнительных функций
class VoiceCall(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    caller_id: str
    duration: int = 0  # секунды
    transcript: Optional[str] = None
    ai_response_text: Optional[str] = None
    status: str = "active"  # active, ended, failed
    created_at: datetime = Field(default_factory=datetime.utcnow)

class AITask(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    schedule: str  # cron-style или описание "каждый день в 9:00"
    recurring: bool = True
    next_run: Optional[datetime] = None
    last_run: Optional[datetime] = None
    active: bool = True
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class TrainingFile(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    filename: str
    department: str
    content: str
    file_type: str  # "pdf", "doc", "txt"
    uploaded_by: str
    processed: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

class CleaningHouse(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    address: str
    stage: str
    contact_info: Optional[str] = None
    bitrix24_deal_id: str
    last_cleaning: Optional[datetime] = None
    next_cleaning: Optional[datetime] = None
    notes: List[str] = []

# Add your routes to the router instead of directly to app
@api_router.get("/")
async def root():
    return {"message": "VasDom AudioBot API", "version": "2.0.0", "status": "🚀 Интеграции активны"}

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

# ============= DASHBOARD & EMPLOYEES =============

@api_router.get("/dashboard")
async def get_dashboard():
    """Дашборд с основной статистикой"""
    try:
        total_employees = await db.employees.count_documents({"active": True})
        total_meetings = await db.meetings.count_documents({})
        total_messages = await db.chat_messages.count_documents({})
        
        # Последние логи
        recent_logs = await db.system_logs.find(
            {"level": {"$in": ["WARNING", "ERROR"]}}, 
            sort=[("timestamp", -1)]
        ).limit(5).to_list(length=None)
        
        return {
            "total_employees": total_employees,
            "total_meetings": total_meetings,
            "total_messages": total_messages,
            "active_projects": 0,
            "completed_tasks_today": 0,
            "revenue_month": 0.0,
            "system_health": "good",
            "ai_suggestions": [],
            "recent_alerts": len(recent_logs)
        }
    except Exception as e:
        await log_system_event("ERROR", "Dashboard error", "backend", {"error": str(e)})
        return {"error": str(e)}

@api_router.get("/employees")
async def get_employees(department: Optional[str] = None):
    """Получение списка сотрудников"""
    try:
        filter_dict = {"active": True}
        if department:
            filter_dict["department"] = department
            
        employees = await db.employees.find(filter_dict).to_list(1000)
        return [Employee(**emp) for emp in employees]
    except Exception as e:
        await log_system_event("ERROR", "Get employees error", "backend", {"error": str(e)})
        return {"error": str(e)}

@api_router.post("/employees")
async def create_employee(employee: EmployeeCreate):
    """Создание нового сотрудника"""
    try:
        employee_dict = employee.dict()
        employee_obj = Employee(**employee_dict)
        await db.employees.insert_one(employee_obj.dict())
        
        await log_system_event("INFO", f"Создан сотрудник: {employee_obj.full_name}", "backend")
        return employee_obj
    except Exception as e:
        await log_system_event("ERROR", "Create employee error", "backend", {"error": str(e)})
        return {"error": str(e)}

# ============= BITRIX24 INTEGRATION =============

@api_router.get("/bitrix24/test")
async def test_bitrix24():
    """Тест подключения к Bitrix24"""
    try:
        result = await bitrix_service._make_request("app.info")
        if "error" in result:
            await log_system_event("ERROR", "Bitrix24 connection failed", "bitrix24", result)
            return {"status": "error", "message": result["error"]}
        
        await log_system_event("INFO", "Bitrix24 connection successful", "bitrix24")
        return {"status": "success", "bitrix_info": result.get("result", {})}
    except Exception as e:
        await log_system_event("ERROR", "Bitrix24 test error", "bitrix24", {"error": str(e)})
        return {"status": "error", "error": str(e)}

@api_router.get("/bitrix24/deals")
async def get_bitrix24_deals():
    """Получение сделок из Bitrix24"""
    try:
        deals = await bitrix_service.get_deals_detailed()
        await log_system_event("INFO", f"Получено {len(deals)} сделок из Bitrix24", "bitrix24")
        return {"status": "success", "deals": deals, "count": len(deals)}
    except Exception as e:
        await log_system_event("ERROR", "Bitrix24 deals error", "bitrix24", {"error": str(e)})
        return {"status": "error", "error": str(e)}

@api_router.post("/bitrix24/create-task")
async def create_bitrix24_task(task_data: Dict[str, Any]):
    """Создание задачи в Bitrix24"""
    try:
        result = await bitrix_service.create_task(task_data)
        
        if result.get("result"):
            task_id = result["result"]
            await log_system_event("INFO", f"Создана задача в Bitrix24: {task_id}", "bitrix24", {"task_id": task_id})
            return {"status": "success", "task_id": task_id}
        else:
            await log_system_event("ERROR", "Не удалось создать задачу в Bitrix24", "bitrix24", result)
            return {"status": "error", "error": result}
    except Exception as e:
        await log_system_event("ERROR", "Bitrix24 create task error", "bitrix24", {"error": str(e)})
        return {"status": "error", "error": str(e)}

# ============= CHAT & LIVE COMMUNICATION =============

@api_router.post("/chat/send")
async def send_chat_message(message_data: Dict[str, Any]):
    """Отправка сообщения в чате (живой разговор)"""
    try:
        # Получаем AI ответ
        ai_response = await get_ai_response(
            message_data["content"], 
            f"Пользователь: {message_data.get('sender_id', 'Unknown')}"
        )
        
        # Сохраняем сообщение и ответ
        chat_message = ChatMessage(
            sender_id=message_data["sender_id"],
            content=message_data["content"],
            ai_response=ai_response,
            chat_type="dashboard"
        )
        
        await db.chat_messages.insert_one(chat_message.dict())
        await log_system_event("INFO", "Обработано сообщение в чате", "ai", {"user": message_data["sender_id"]})
        
        return {
            "status": "success",
            "message": chat_message.dict(),
            "ai_response": ai_response
        }
    except Exception as e:
        await log_system_event("ERROR", "Chat message error", "ai", {"error": str(e)})
        return {"status": "error", "error": str(e)}

@api_router.get("/chat/history")
async def get_chat_history(limit: int = 50, chat_type: str = "dashboard"):
    """История сообщений чата"""
    try:
        messages = await db.chat_messages.find(
            {"chat_type": chat_type},
            sort=[("timestamp", -1)]
        ).limit(limit).to_list(length=None)
        
        # Convert ObjectId to string for JSON serialization
        for message in messages:
            if "_id" in message:
                message["_id"] = str(message["_id"])
        
        return {"status": "success", "messages": messages[::-1]}  # Reverse для хронологии
    except Exception as e:
        return {"status": "error", "error": str(e)}

# ============= MEETINGS & PLANNING =============

@api_router.post("/meetings")
async def create_meeting(meeting_data: Dict[str, Any]):
    """Создание планерки"""
    try:
        meeting = Meeting(**meeting_data)
        await db.meetings.insert_one(meeting.dict())
        
        await log_system_event("INFO", f"Создана планерка: {meeting.title}", "backend")
        return {"status": "success", "meeting": meeting.dict()}
    except Exception as e:
        await log_system_event("ERROR", "Create meeting error", "backend", {"error": str(e)})
        return {"status": "error", "error": str(e)}

@api_router.get("/meetings")
async def get_meetings(limit: int = 20):
    """Получение списка планерок"""
    try:
        meetings = await db.meetings.find(
            {}, sort=[("start_time", -1)]
        ).limit(limit).to_list(length=None)
        
        # Convert ObjectId to string for JSON serialization
        for meeting in meetings:
            if "_id" in meeting:
                meeting["_id"] = str(meeting["_id"])
        
        return {"status": "success", "meetings": meetings}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@api_router.post("/meetings/{meeting_id}/analyze")
async def analyze_meeting(meeting_id: str):
    """AI анализ планерки и создание задач"""
    try:
        meeting = await db.meetings.find_one({"id": meeting_id})
        if not meeting:
            return {"status": "error", "error": "Meeting not found"}
        
        # AI анализ записи планерки
        if meeting.get("recording_text"):
            analysis_prompt = f"""
            Проанализируй запись планерки и выдели:
            1. Ключевые решения
            2. Поставленные задачи
            3. Ответственных
            4. Дедлайны
            
            Запись планерки:
            {meeting['recording_text']}
            
            Верни результат в формате JSON:
            {
                "summary": "Краткое резюме",
                "decisions": ["решение1", "решение2"],
                "tasks": [
                    {"title": "Задача", "responsible": "ФИО", "deadline": "дата", "description": "описание"}
                ]
            }
            """
            
            ai_response = await get_ai_response(analysis_prompt, "Анализ планерки")
            
            # Сохраняем анализ
            analysis_update = {
                "ai_summary": ai_response,
                "analyzed_at": datetime.utcnow()
            }
            await db.meetings.update_one({"id": meeting_id}, {"$set": analysis_update})
            
            # Пытаемся создать задачи в Bitrix24
            tasks_created = []
            try:
                # Парсим AI ответ для извлечения задач
                if "tasks" in ai_response.lower():
                    # Создаем задачи в Bitrix24
                    task_result = await bitrix_service.create_task({
                        "title": f"Задачи с планерки: {meeting['title']}",
                        "description": ai_response,
                        "responsible_id": "1"  # ID администратора
                    })
                    
                    if task_result.get("result"):
                        tasks_created.append(task_result["result"])
                        await log_system_event("INFO", f"Создана задача в Bitrix24: {task_result['result']}", "bitrix24")
                        
            except Exception as task_error:
                await log_system_event("WARNING", f"Не удалось создать задачи в Bitrix24: {str(task_error)}", "bitrix24")
            
            return {
                "status": "success",
                "analysis": ai_response,
                "bitrix_tasks": tasks_created
            }
        else:
            return {"status": "error", "error": "No recording text to analyze"}
            
    except Exception as e:
        await log_system_event("ERROR", "Meeting analysis error", "ai", {"error": str(e)})
        return {"status": "error", "error": str(e)}

# ============= SYSTEM LOGS =============

@api_router.get("/logs")
async def get_system_logs(limit: int = 100, level: Optional[str] = None, component: Optional[str] = None):
    """Получение системных логов"""
    try:
        filter_dict = {}
        if level:
            filter_dict["level"] = level
        if component:
            filter_dict["component"] = component
            
        logs = await db.system_logs.find(
            filter_dict, 
            sort=[("timestamp", -1)]
        ).limit(limit).to_list(length=None)
        
        # Конвертируем ObjectId в строки для JSON сериализации
        for log in logs:
            if "_id" in log:
                log["_id"] = str(log["_id"])
        
        return {"status": "success", "logs": logs, "count": len(logs)}
    except Exception as e:
        logger.error(f"Get logs error: {str(e)}")
        return {"status": "error", "error": str(e)}

async def log_system_event(level: str, message: str, component: str, data: Dict = None):
    """Функция логирования системных событий"""
    try:
        log_entry = SystemLog(
            level=level,
            message=message,
            component=component,
            data=data or {}
        )
        await db.system_logs.insert_one(log_entry.dict())
        
        # Также логируем в Python logger
        if level == "ERROR":
            logger.error(f"[{component}] {message}")
        elif level == "WARNING":
            logger.warning(f"[{component}] {message}")
        else:
            logger.info(f"[{component}] {message}")
            
    except Exception as e:
        logger.error(f"Failed to log system event: {str(e)}")

# ============= TELEGRAM BOT ENDPOINTS =============

@app.post("/telegram/webhook")
async def telegram_webhook(request: Request):
    """Webhook для Telegram бота"""
    try:
        data = await request.json()
        await log_system_event("INFO", "Получен webhook от Telegram", "telegram", {"update_id": data.get("update_id")})
        
        if "message" in data:
            message = data["message"]
            chat_id = str(message["chat"]["id"])
            text = message.get("text", "")
            user_id = str(message["from"]["id"])
            username = message["from"].get("username", "Unknown")
            
            # Сохраняем сообщение
            chat_msg = ChatMessage(
                sender_id=user_id,
                content=text,
                chat_type="telegram"
            )
            await db.chat_messages.insert_one(chat_msg.dict())
            
            # Обрабатываем команды
            if text.startswith("/start"):
                # Проверяем есть ли пользователь в системе
                employee = await db.employees.find_one({"telegram_id": user_id})
                
                if employee:
                    welcome_text = f"👋 Привет, {employee['full_name']}!\n\n🤖 AudioBot готов к работе!\n\n📋 Команды:\n/tasks - мои задачи\n/help - помощь"
                else:
                    # Ищем по имени пользователя или регистрируем
                    welcome_text = f"👋 Добро пожаловать в VasDom AudioBot!\n\n🔍 Вы пока не зарегистрированы в системе.\n\n📞 Обратитесь к администратору:\n• Максим: +7 920 092 4550\n• Валентина: +7 920 870 1769"
                
                await telegram_service.send_message(chat_id, welcome_text)
                
            elif text.startswith("/tasks"):
                employee = await db.employees.find_one({"telegram_id": user_id})
                if employee:
                    tasks_text = f"📋 Задачи для {employee['full_name']}:\n\n🔄 Функция в разработке...\n\nСкоро вы сможете:\n• Получать задачи\n• Отмечаться на объектах\n• Отправлять отчеты"
                else:
                    tasks_text = "❌ Сначала зарегистрируйтесь в системе (/start)"
                
                await telegram_service.send_message(chat_id, tasks_text)
                
            elif text.startswith("/help"):
                help_text = """🤖 <b>VasDom AudioBot - Помощь</b>

📋 <b>Команды:</b>
• /start - запуск бота
• /tasks - мои задачи  
• /help - эта справка

🏢 <b>Возможности:</b>
• AI-ассистент для сотрудников
• Интеграция с Bitrix24 CRM
• Управление задачами
• Отчеты и аналитика

📞 <b>Поддержка:</b>
• Максим: +7 920 092 4550
• Email: maslovmaksim92@yandex.ru"""

                await telegram_service.send_message(chat_id, help_text)
                
            else:
                # AI обработка обычного сообщения
                ai_response = await get_ai_response(text, f"Telegram пользователь: {username}")
                
                # Сохраняем AI ответ
                await db.chat_messages.update_one(
                    {"id": chat_msg.id},
                    {"$set": {"ai_response": ai_response}}
                )
                
                await telegram_service.send_message(chat_id, f"🤖 {ai_response}")
                await log_system_event("INFO", "AI ответ отправлен в Telegram", "ai", {"user": username})
        
        return {"status": "ok"}
        
    except Exception as e:
        await log_system_event("ERROR", "Telegram webhook error", "telegram", {"error": str(e)})
        return {"status": "error", "message": str(e)}

@app.get("/telegram/set-webhook")
async def set_telegram_webhook():
    """Установка webhook"""
    try:
        result = await telegram_service.set_webhook()
        await log_system_event("INFO", "Telegram webhook установлен", "telegram", result)
        return result
    except Exception as e:
        await log_system_event("ERROR", "Telegram webhook error", "telegram", {"error": str(e)})
        return {"error": str(e)}

# Include API router and configure app
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

# App events
# ============= НОВЫЕ ENDPOINTS ДЛЯ ДОРАБОТОК =============

@api_router.get("/cleaning/houses") 
async def get_cleaning_houses():
    """Получение домов для уборки из Bitrix24"""
    try:
        deals = await bitrix_service.get_deals(limit=500)
        houses = [{"address": deal.get("TITLE", ""), "stage": deal.get("STAGE_ID", ""), "bitrix24_deal_id": deal["ID"]} for deal in deals]
        return {"status": "success", "houses": houses, "total": len(houses)}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@api_router.get("/ai-tasks")
async def get_ai_tasks():
    """Получение AI задач"""
    try:
        tasks = await db.ai_tasks.find({"active": True}).to_list(1000)
        for task in tasks:
            if "_id" in task:
                task["_id"] = str(task["_id"])
        return {"status": "success", "tasks": tasks}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@api_router.post("/ai-tasks")
async def create_ai_task(task_data: Dict[str, Any]):
    """Создание AI задачи"""
    try:
        task = {
            "id": str(uuid.uuid4()),
            "title": task_data["title"],
            "description": task_data["description"],
            "schedule": task_data.get("schedule", ""),
            "recurring": task_data.get("recurring", False),
            "active": True,
            "created_by": "admin",
            "created_at": datetime.utcnow()
        }
        await db.ai_tasks.insert_one(task)
        return {"status": "success", "task": task}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@api_router.get("/training/files")
async def get_training_files(department: Optional[str] = None):
    """Получение файлов обучения"""
    try:
        filter_dict = {}
        if department:
            filter_dict["department"] = department
        files = await db.training_files.find(filter_dict).to_list(1000)
        for file in files:
            if "_id" in file:
                file["_id"] = str(file["_id"])
        return {"status": "success", "files": files}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@api_router.post("/training/upload-file")
async def upload_training_file(file_data: Dict[str, Any]):
    """Загрузка файла обучения"""
    try:
        file_obj = {
            "id": str(uuid.uuid4()),
            "filename": file_data["filename"],
            "department": file_data["department"],
            "content": file_data["content"],
            "file_type": file_data.get("file_type", "txt"),
            "uploaded_by": "admin",
            "created_at": datetime.utcnow()
        }
        await db.training_files.insert_one(file_obj)
        return {"status": "success", "file_id": file_obj["id"]}
    except Exception as e:
        return {"status": "error", "error": str(e)}

# Include the router ПЕРЕД startup event
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Инициализация системы"""
    await log_system_event("INFO", "Система запускается", "backend")
    logger.info("🚀 Starting VasDom AudioBot System...")
    
    # Устанавливаем Telegram webhook
    try:
        webhook_result = await telegram_service.set_webhook()
        if webhook_result.get("ok"):
            await log_system_event("INFO", "Telegram webhook настроен успешно", "telegram")
        else:
            await log_system_event("WARNING", "Проблема с Telegram webhook", "telegram", webhook_result)
    except Exception as e:
        await log_system_event("ERROR", "Ошибка настройки Telegram webhook", "telegram", {"error": str(e)})
    
    # Инициализируем базовых сотрудников из задания
    try:
        base_employees = [
            # Руководство  
            {"full_name": "Маслов Максим Валерьевич", "phone": "89200924550", "role": "director", "department": "Администрация"},
            {"full_name": "Маслова Валентина Михайловна", "phone": "89208701769", "role": "general_director", "department": "Администрация"},
            {"full_name": "Филиппов Сергей Сергеевич", "phone": "89056400212", "role": "construction_head", "department": "Строительный отдел"},
            {"full_name": "Черкасов Ярослав Артурович", "phone": "89208855883", "role": "construction_manager", "department": "Строительный отдел"},
            
            # Остальные отделы
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
                await log_system_event("INFO", f"Создан сотрудник: {emp_data['full_name']}", "backend")
        
        await log_system_event("INFO", "Базовые сотрудники инициализированы", "backend")
        
    except Exception as e:
        await log_system_event("ERROR", "Ошибка инициализации сотрудников", "backend", {"error": str(e)})
    
    # Тестируем Bitrix24 подключение
    try:
        bitrix_test = await bitrix_service._make_request("app.info")
        if "error" not in bitrix_test:
            await log_system_event("INFO", "Bitrix24 подключение успешно", "bitrix24")
        else:
            await log_system_event("WARNING", "Проблема с Bitrix24 подключением", "bitrix24", bitrix_test)
    except Exception as e:
        await log_system_event("ERROR", "Ошибка подключения к Bitrix24", "bitrix24", {"error": str(e)})
    
    await log_system_event("INFO", "Система запущена успешно", "backend")
    logger.info("✅ System startup completed!")

@app.on_event("shutdown")
async def shutdown_db_client():
    await log_system_event("INFO", "Система завершает работу", "backend")
    client.close()