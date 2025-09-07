from fastapi import FastAPI, APIRouter, HTTPException, BackgroundTasks, Request
from fastapi.responses import JSONResponse, HTMLResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from datetime import datetime, timedelta
import asyncio
import json
from typing import Dict, Any, List, Optional

# Import our models and services
from models import *
from services.ai_service import AIReflectionService, continuous_learning_task
from services.bitrix_service import Bitrix24Service
from services.telegram_service import TelegramService

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Initialize services
ai_service = AIReflectionService(db)
bitrix_service = Bitrix24Service()
telegram_service = TelegramService(db)

# Create the main app
app = FastAPI(
    title="VasDom AI Business Management System",
    description="Умная система управления бизнесом с саморефлексией и самообучением",
    version="2.0.0"
)

# Create API router
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global variables for background tasks
learning_task = None

# ====== CORE SYSTEM ENDPOINTS ======

@app.get("/")
async def root():
    return {
        "service": "VasDom AI Business Management",
        "version": "2.0.0",
        "status": "🚀 Система саморефлексии активна",
        "features": [
            "AI самообучение",
            "Управление сотрудниками",
            "Планирование задач", 
            "Bitrix24 интеграция",
            "Telegram бот",
            "Финансовая аналитика",
            "Оптимизация маршрутов"
        ],
        "endpoints": {
            "dashboard": "/api/dashboard",
            "employees": "/api/employees",
            "projects": "/api/projects", 
            "ai_analysis": "/api/ai/analysis",
            "telegram": "/telegram/webhook"
        }
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.utcnow()}

@app.get("/healthz")
async def detailed_health():
    """Детальная проверка здоровья всех сервисов"""
    health_status = {
        "timestamp": datetime.utcnow(),
        "overall_status": "healthy",
        "services": {}
    }
    
    # Проверка MongoDB
    try:
        await db.list_collection_names()
        health_status["services"]["mongodb"] = {"status": "healthy", "message": "Connected"}
    except Exception as e:
        health_status["services"]["mongodb"] = {"status": "error", "message": str(e)}
        health_status["overall_status"] = "unhealthy"
    
    # Проверка Bitrix24
    try:
        bitrix_test = await bitrix_service.test_connection()
        health_status["services"]["bitrix24"] = bitrix_test
        if bitrix_test.get("status") != "success":
            health_status["overall_status"] = "warning"
    except Exception as e:
        health_status["services"]["bitrix24"] = {"status": "error", "message": str(e)}
    
    # Проверка AI сервиса
    try:
        ai_insights = await ai_service.get_ai_insights()
        health_status["services"]["ai_service"] = {
            "status": "healthy",
            "learning_status": ai_insights.get("ai_status", "unknown"),
            "active_suggestions": ai_insights.get("active_suggestions", 0)
        }
    except Exception as e:
        health_status["services"]["ai_service"] = {"status": "error", "message": str(e)}
    
    return health_status

# ====== DASHBOARD ENDPOINTS ======

@api_router.get("/dashboard")
async def get_dashboard():
    """Главный дашборд с общей статистикой"""
    try:
        # Основная статистика
        total_employees = await db.employees.count_documents({"active": True})
        active_projects = await db.projects.count_documents({"status": "active"}) 
        pending_tasks = await db.tasks.count_documents({"status": "pending"})
        completed_tasks_today = await db.tasks.count_documents({
            "status": "completed",
            "completed_at": {"$gte": datetime.utcnow().replace(hour=0, minute=0, second=0)}
        })
        
        # Финансовая статистика за месяц
        month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0)
        revenue_month = await db.finance_entries.aggregate([
            {"$match": {"category": "revenue", "date": {"$gte": month_start}}},
            {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
        ]).to_list(length=1)
        revenue_month = revenue_month[0]["total"] if revenue_month else 0
        
        # AI предложения
        ai_suggestions = await db.improvements.find(
            {"status": "suggested"}, 
            sort=[("impact_score", -1)]
        ).limit(5).to_list(length=None)
        
        # Система здоровья
        system_health = await ai_service.analyze_system_performance()
        
        return DashboardStats(
            total_employees=total_employees,
            active_projects=active_projects,
            completed_tasks_today=completed_tasks_today,
            revenue_month=revenue_month,
            system_health=system_health.get("performance", {}).get("overall_health", "unknown"),
            ai_suggestions=[{
                "title": s.get("title", ""),
                "description": s.get("description", ""),
                "impact_score": s.get("impact_score", 0)
            } for s in ai_suggestions]
        )
        
    except Exception as e:
        logger.error(f"Dashboard error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ====== EMPLOYEE MANAGEMENT ======

@api_router.post("/employees", response_model=Employee)
async def create_employee(employee: EmployeeCreate):
    """Создание нового сотрудника"""
    try:
        # Создаем сотрудника с базовыми данными из задания
        employee_dict = employee.dict()
        employee_obj = Employee(**employee_dict)
        
        await db.employees.insert_one(employee_obj.dict())
        
        # Логируем создание для AI обучения
        await db.system_learning.insert_one({
            "id": f"employee_created_{datetime.utcnow().timestamp()}",
            "event_type": "employee_created",
            "data": {"employee_id": employee_obj.id, "role": employee_obj.role},
            "created_at": datetime.utcnow(),
            "confidence_score": 1.0
        })
        
        return employee_obj
        
    except Exception as e:
        logger.error(f"Error creating employee: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/employees", response_model=List[Employee])
async def get_employees(department: Optional[str] = None, active: bool = True):
    """Получение списка сотрудников"""
    try:
        filter_dict = {"active": active}
        if department:
            filter_dict["department"] = department
            
        employees = await db.employees.find(filter_dict).to_list(length=None)
        return [Employee(**emp) for emp in employees]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/employees/{employee_id}")
async def get_employee(employee_id: str):
    """Получение конкретного сотрудника с детальной статистикой"""
    try:
        employee = await db.employees.find_one({"id": employee_id})
        if not employee:
            raise HTTPException(status_code=404, detail="Employee not found")
        
        # Статистика по задачам
        total_tasks = await db.tasks.count_documents({"assignee_id": employee_id})
        completed_tasks = await db.tasks.count_documents({"assignee_id": employee_id, "status": "completed"})
        overdue_tasks = await db.tasks.count_documents({
            "assignee_id": employee_id,
            "status": {"$in": ["pending", "in_progress"]},
            "due_date": {"$lt": datetime.utcnow()}
        })
        
        # Добавляем статистику к сотруднику
        employee_data = Employee(**employee)
        employee_stats = {
            **employee_data.dict(),
            "stats": {
                "total_tasks": total_tasks,
                "completed_tasks": completed_tasks,
                "overdue_tasks": overdue_tasks,
                "completion_rate": completed_tasks / max(total_tasks, 1) * 100
            }
        }
        
        return employee_stats
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/employees/sync-bitrix")
async def sync_employees_bitrix():
    """Синхронизация сотрудников с Bitrix24"""
    try:
        result = await bitrix_service.sync_employees_with_bitrix(db)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ====== TASK MANAGEMENT ======

@api_router.post("/tasks", response_model=Task)
async def create_task(task: TaskCreate, creator_id: str = "system"):
    """Создание новой задачи"""
    try:
        task_dict = task.dict()
        task_dict["creator_id"] = creator_id
        task_obj = Task(**task_dict)
        
        await db.tasks.insert_one(task_obj.dict())
        
        # Отправляем уведомление сотруднику в Telegram
        employee = await db.employees.find_one({"id": task.assignee_id})
        if employee and employee.get("telegram_id"):
            message = f"📋 <b>Новая задача!</b>\n\n<b>{task.title}</b>\n{task.description}\n\n⏰ Срок: {task.due_date.strftime('%d.%m.%Y %H:%M') if task.due_date else 'Не указан'}"
            await telegram_service.send_message(employee["telegram_id"], message)
        
        return task_obj
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/tasks")
async def get_tasks(assignee_id: Optional[str] = None, status: Optional[TaskStatus] = None):
    """Получение списка задач"""
    try:
        filter_dict = {}
        if assignee_id:
            filter_dict["assignee_id"] = assignee_id
        if status:
            filter_dict["status"] = status
            
        tasks = await db.tasks.find(filter_dict, sort=[("created_at", -1)]).to_list(length=None)
        return [Task(**task) for task in tasks]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.patch("/tasks/{task_id}")
async def update_task(task_id: str, update_data: Dict[str, Any]):
    """Обновление задачи"""
    try:
        update_data["updated_at"] = datetime.utcnow()
        
        # Если задача завершена, записываем время завершения
        if update_data.get("status") == "completed":
            update_data["completed_at"] = datetime.utcnow()
        
        result = await db.tasks.update_one(
            {"id": task_id},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Получаем обновленную задачу
        updated_task = await db.tasks.find_one({"id": task_id})
        return Task(**updated_task)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ====== PROJECT MANAGEMENT ======

@api_router.post("/projects", response_model=Project)
async def create_project(project: ProjectCreate):
    """Создание нового проекта"""
    try:
        project_dict = project.dict()
        project_obj = Project(**project_dict)
        
        await db.projects.insert_one(project_obj.dict())
        return project_obj
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/projects")
async def get_projects(type: Optional[ProjectType] = None, status: Optional[ProjectStatus] = None):
    """Получение списка проектов"""
    try:
        filter_dict = {}
        if type:
            filter_dict["type"] = type
        if status:
            filter_dict["status"] = status
            
        projects = await db.projects.find(filter_dict).to_list(length=None)
        return [Project(**project) for project in projects]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/projects/sync-bitrix")
async def sync_projects_bitrix():
    """Синхронизация проектов с Bitrix24"""
    try:
        result = await bitrix_service.sync_projects_with_deals(db)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ====== FINANCIAL MANAGEMENT ======

@api_router.post("/finances", response_model=FinanceEntry)
async def create_finance_entry(entry: Dict[str, Any]):
    """Создание финансовой записи"""
    try:
        finance_obj = FinanceEntry(**entry)
        await db.finance_entries.insert_one(finance_obj.dict())
        return finance_obj
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/finances/report")
async def get_financial_report(start_date: Optional[str] = None, end_date: Optional[str] = None):
    """Финансовый отчет"""
    try:
        # Устанавливаем диапазон дат (по умолчанию текущий месяц)
        if not start_date:
            start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            start = datetime.fromisoformat(start_date)
            
        if not end_date:
            end = datetime.utcnow()
        else:
            end = datetime.fromisoformat(end_date)
        
        # Агрегация данных
        pipeline = [
            {"$match": {"date": {"$gte": start, "$lte": end}}},
            {"$group": {
                "_id": {"category": "$category", "subcategory": "$subcategory"},
                "total": {"$sum": "$amount"},
                "count": {"$sum": 1}
            }},
            {"$sort": {"total": -1}}
        ]
        
        cursor = db.finance_entries.aggregate(pipeline)
        results = await cursor.to_list(length=None)
        
        # Группируем по категориям
        report = {"revenue": {}, "expense": {}, "investment": {}}
        totals = {"revenue": 0, "expense": 0, "investment": 0}
        
        for result in results:
            category = result["_id"]["category"]
            subcategory = result["_id"]["subcategory"]
            
            if category not in report:
                report[category] = {}
                
            report[category][subcategory] = {
                "amount": result["total"],
                "count": result["count"]
            }
            totals[category] += result["total"]
        
        return {
            "period": {"start": start, "end": end},
            "totals": totals,
            "profit": totals["revenue"] - totals["expense"],
            "breakdown": report
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ====== AI AND ANALYTICS ======

@api_router.get("/ai/analysis")
async def get_ai_analysis():
    """Получение AI анализа системы"""
    try:
        analysis = await ai_service.analyze_system_performance()
        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/ai/insights")
async def get_ai_insights():
    """Получение AI инсайтов и предложений"""
    try:
        insights = await ai_service.get_ai_insights()
        return insights
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/ai/feedback")
async def submit_ai_feedback(feedback: AIFeedback):
    """Отправка обратной связи для AI обучения"""
    try:
        feedback_data = feedback.dict()
        result = await ai_service.learn_from_feedback(feedback_data)
        
        # Сохраняем обратную связь
        await db.chat_messages.insert_one({
            "id": f"feedback_{datetime.utcnow().timestamp()}",
            "sender_id": "user",
            "chat_type": "feedback",
            "content": feedback_data["feedback"],
            "message_type": "feedback",
            "ai_response": result.get("status", "processed"),
            "created_at": datetime.utcnow()
        })
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/improvements")
async def get_improvements(status: Optional[ImprovementStatus] = None):
    """Получение предложений по улучшению"""
    try:
        filter_dict = {}
        if status:
            filter_dict["status"] = status
            
        improvements = await db.improvements.find(
            filter_dict, 
            sort=[("impact_score", -1), ("created_at", -1)]
        ).to_list(length=None)
        
        return [Improvement(**imp) for imp in improvements]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.patch("/improvements/{improvement_id}")
async def update_improvement(improvement_id: str, update_data: Dict[str, Any]):
    """Обновление статуса предложения по улучшению"""
    try:
        update_data["updated_at"] = datetime.utcnow()
        
        result = await db.improvements.update_one(
            {"id": improvement_id},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Improvement not found")
        
        # Уведомляем AI об изменении статуса
        await ai_service.learn_from_feedback({
            "improvement_id": improvement_id,
            "action": "status_updated",
            "new_status": update_data.get("status"),
            "rating": 5 if update_data.get("status") == "approved" else 3
        })
        
        return {"status": "updated"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ====== TELEGRAM INTEGRATION ======

@app.post("/telegram/webhook")
async def telegram_webhook(request: Request):
    """Webhook для получения сообщений из Telegram"""
    try:
        data = await request.json()
        
        # Обрабатываем сообщение
        if "message" in data:
            message = data["message"]
            chat_id = str(message["chat"]["id"])
            text = message.get("text", "")
            user_id = str(message["from"]["id"])
            
            # Сохраняем сообщение в БД
            await db.chat_messages.insert_one({
                "id": f"tg_{message['message_id']}",
                "sender_id": user_id,
                "recipient_id": chat_id,
                "chat_type": "telegram",
                "content": text,
                "created_at": datetime.utcnow()
            })
            
            # Обрабатываем команды
            if text.startswith("/start"):
                # Проверяем, есть ли пользователь в системе
                employee = await db.employees.find_one({"telegram_id": user_id})
                
                if employee:
                    keyboards = await telegram_service.create_employee_keyboards()
                    role = employee.get("role", "employee")
                    
                    welcome_text = f"👋 Добро пожаловать, {employee['full_name']}!\n\n🤖 Ваш AI-ассистент готов к работе."
                    
                    if role in ["director", "general_director"]:
                        keyboard = keyboards["director"]
                    elif "manager" in role or "head" in role:
                        keyboard = keyboards["manager"] 
                    else:
                        keyboard = keyboards["employee"]
                    
                    await telegram_service.send_message(chat_id, welcome_text, keyboard)
                else:
                    await telegram_service.send_message(
                        chat_id, 
                        "❌ Вы не зарегистрированы в системе.\n📞 Обратитесь к администратору для получения доступа."
                    )
            
            elif text.startswith("/menu"):
                employee = await db.employees.find_one({"telegram_id": user_id})
                if employee:
                    keyboards = await telegram_service.create_employee_keyboards()
                    role = employee.get("role", "employee")
                    
                    if role in ["director", "general_director"]:
                        keyboard = keyboards["director"]
                    elif "manager" in role or "head" in role:
                        keyboard = keyboards["manager"]
                    else:
                        keyboard = keyboards["employee"]
                    
                    await telegram_service.send_message(chat_id, "📱 Главное меню:", keyboard)
            
            else:
                # AI обработка обычного сообщения
                ai_response = "🤖 Сообщение получено и обрабатывается системой AI..."
                await telegram_service.send_message(chat_id, ai_response)
        
        # Обрабатываем callback query (нажатия на кнопки)
        elif "callback_query" in data:
            callback = data["callback_query"]
            callback_data = callback["data"]
            user_id = str(callback["from"]["id"])
            message_id = str(callback["message"]["message_id"])
            
            await telegram_service.handle_callback_query(callback_data, user_id, message_id)
        
        return {"status": "ok"}
        
    except Exception as e:
        logger.error(f"Telegram webhook error: {str(e)}")
        return {"status": "error", "message": str(e)}

@app.get("/telegram/set-webhook")
async def set_telegram_webhook():
    """Установка webhook для Telegram бота"""
    try:
        result = await telegram_service.set_webhook()
        return result
    except Exception as e:
        return {"error": str(e)}

# ====== SYSTEM LOGS ======

@api_router.get("/logs")
async def get_system_logs(limit: int = 100, event_type: Optional[str] = None):
    """Получение системных логов"""
    try:
        filter_dict = {}
        if event_type:
            filter_dict["event_type"] = event_type
            
        logs = await db.system_learning.find(
            filter_dict, 
            sort=[("created_at", -1)]
        ).limit(limit).to_list(length=None)
        
        return logs
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Include API router
app.include_router(api_router)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Event handlers
@app.on_event("startup")
async def startup_event():
    """Инициализация системы при запуске"""
    global learning_task
    
    logger.info("🚀 Starting VasDom AI Business Management System...")
    
    # Создаем индексы для оптимизации
    await create_database_indexes()
    
    # Инициализируем базовых сотрудников
    await initialize_employees()
    
    # Запускаем фоновое обучение AI
    if not learning_task:
        learning_task = asyncio.create_task(continuous_learning_task(ai_service))
        logger.info("🤖 AI continuous learning task started")
    
    # Устанавливаем Telegram webhook
    try:
        await telegram_service.set_webhook()
        logger.info("📱 Telegram webhook set successfully")
    except Exception as e:
        logger.error(f"Failed to set Telegram webhook: {str(e)}")
    
    logger.info("✅ System startup completed!")

@app.on_event("shutdown")
async def shutdown_event():
    """Завершение работы системы"""
    global learning_task
    
    if learning_task:
        learning_task.cancel()
        logger.info("🤖 AI learning task stopped")
    
    client.close()
    logger.info("📊 Database connection closed")

async def create_database_indexes():
    """Создание индексов для оптимизации запросов"""
    try:
        # Индексы для сотрудников
        await db.employees.create_index("phone")
        await db.employees.create_index("telegram_id")
        await db.employees.create_index("bitrix24_id")
        
        # Индексы для задач
        await db.tasks.create_index("assignee_id")
        await db.tasks.create_index("status")
        await db.tasks.create_index("due_date")
        
        # Индексы для проектов
        await db.projects.create_index("type")
        await db.projects.create_index("status")
        await db.projects.create_index("bitrix24_deal_id")
        
        # Индексы для финансов
        await db.finance_entries.create_index("date")
        await db.finance_entries.create_index("category")
        
        # Индексы для AI обучения
        await db.system_learning.create_index("event_type")
        await db.system_learning.create_index("created_at")
        
        logger.info("📊 Database indexes created successfully")
        
    except Exception as e:
        logger.error(f"Error creating database indexes: {str(e)}")

async def initialize_employees():
    """Инициализация базовых сотрудников из задания"""
    try:
        # Базовые сотрудники из задания пользователя
        base_employees = [
            # Акционеры и руководство
            {"full_name": "Филиппов Сергей Сергеевич", "phone": "89056400212", "role": "construction_head", "department": "Строительный отдел"},
            {"full_name": "Черкасов Ярослав Артурович", "phone": "89208855883", "role": "construction_manager", "department": "Строительный отдел"},
            {"full_name": "Маслов Максим Валерьевич", "phone": "89200924550", "role": "director", "department": "Администрация"},
            {"full_name": "Маслова Валентина Михайловна", "phone": "89208701769", "role": "general_director", "department": "Администрация"},
            
            # Бухгалтерия
            {"full_name": "Колосов Дмитрий Сергеевич", "phone": "89105489113", "role": "accountant", "department": "Бухгалтерия"},
            
            # Строительный отдел
            {"full_name": "Маслова Арина Алексеевна", "phone": "89533150101", "role": "construction_manager", "department": "Строительный отдел"},
            {"full_name": "Илья Николаевич", "phone": "", "role": "foreman", "department": "Строительный отдел"},
            
            # HR отдел
            {"full_name": "Ольга Андреевна", "phone": "89106058454", "role": "hr_director", "department": "УФИЦ"},
            {"full_name": "Попов Никита Валерьевич", "phone": "89105447777", "role": "hr_manager", "department": "УФИЦ"},
            
            # Клининг
            {"full_name": "Наталья Викторовна", "phone": "89206148777", "role": "cleaning_head", "department": "Клининг"},
            {"full_name": "Ильиных Алексей Владимирович", "phone": "89206188414", "role": "cleaning_manager", "department": "Клининг"},
            
            # Маркетинг/Клиентский сервис  
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