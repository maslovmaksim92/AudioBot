from fastapi import FastAPI, APIRouter, HTTPException, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import os
import uuid
import logging
import asyncio
import aiohttp
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'audiobot')]

# FastAPI app
app = FastAPI(title="VasDom AudioBot API", version="2.0.0")
api_router = APIRouter(prefix="/api")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic Models
class Employee(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    role: str
    telegram_id: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Meeting(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    audio_url: Optional[str] = None
    transcription: Optional[str] = None
    summary: Optional[str] = None
    tasks_created: List[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)

class AITask(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    scheduled_time: datetime
    recurring: bool = False
    status: str = "pending"
    chat_messages: List[Dict] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)

class House(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    address: str
    bitrix24_deal_id: str
    stage: str
    brigade: Optional[str] = None
    cleaning_schedule: Optional[Dict] = None
    last_cleaning: Optional[datetime] = None

class VoiceMessage(BaseModel):
    text: str
    user_id: str = "user"

class ChatResponse(BaseModel):
    response: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# Bitrix24 Integration
class BitrixIntegration:
    def __init__(self):
        self.webhook_url = os.environ.get('BITRIX24_WEBHOOK_URL', '')
        
    async def get_deals(self, funnel_id: str = None, limit: int = 50):
        """Получить сделки из Bitrix24"""
        try:
            params = {
                'start': 0,
                'select': ['*', 'UF_*']
            }
            if limit:
                params['filter'] = {'CATEGORY_ID': '2'}  # Уборка подъездов
                
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.webhook_url}crm.deal.list",
                    json=params
                ) as response:
                    data = await response.json()
                    if data.get('result'):
                        return data['result'][:limit] if limit else data['result']
                    return []
        except Exception as e:
            logging.error(f"Bitrix24 error: {e}")
            return []
    
    async def test_connection(self):
        """Тест подключения к Bitrix24"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.webhook_url}app.info") as response:
                    return await response.json()
        except Exception as e:
            logging.error(f"Bitrix24 connection error: {e}")
            return {"error": str(e)}

bitrix = BitrixIntegration()

# AI Integration with Emergent LLM
class AIService:
    def __init__(self):
        self.llm_key = os.environ.get('EMERGENT_LLM_KEY', '')
        
    async def process_voice_message(self, text: str) -> str:
        """Обработка голосового сообщения через AI"""
        try:
            # Используем emergentintegrations для GPT-4 mini
            import emergentintegrations
            
            response = await emergentintegrations.chat_completion(
                model="gpt-4-mini",
                messages=[
                    {"role": "system", "content": "Ты VasDom AI - помощник для управления клининговой компанией. Отвечай на русском языке кратко и по делу."},
                    {"role": "user", "content": text}
                ],
                api_key=self.llm_key
            )
            
            return response.choices[0].message.content
        except Exception as e:
            logging.error(f"AI processing error: {e}")
            return "Извините, не могу обработать ваш запрос прямо сейчас."
    
    async def transcribe_audio(self, audio_file: bytes) -> str:
        """Транскрипция аудио через Whisper"""
        try:
            # Здесь должна быть интеграция с Whisper API
            return "Функция транскрипции будет реализована"
        except Exception as e:
            logging.error(f"Transcription error: {e}")
            return ""

ai_service = AIService()

# API Routes
@api_router.get("/")
async def root():
    return {
        "message": "VasDom AudioBot API",
        "version": "2.0.0",
        "status": "🚀 Интеграции активны"
    }

@api_router.get("/dashboard")
async def get_dashboard_stats():
    """Получить статистику для дашборда"""
    try:
        # Получение данных из Bitrix24
        houses = await bitrix.get_deals(limit=None)
        
        # Подсчет сотрудников (мокаем пока)
        employees_count = 82
        
        # Подсчет встреч
        meetings = await db.meetings.find().to_list(100)
        
        # Подсчет задач AI
        ai_tasks = await db.ai_tasks.find().to_list(100)
        
        return {
            "status": "success",
            "stats": {
                "employees": employees_count,
                "houses": len(houses),
                "entrances": sum(1 for house in houses if house.get('UF_CRM_1234567890123')), # Примерное поле
                "apartments": sum(int(house.get('UF_CRM_APARTMENTS', 0) or 0) for house in houses),
                "floors": sum(int(house.get('UF_CRM_FLOORS', 0) or 0) for house in houses),
                "meetings": len(meetings),
                "ai_tasks": len(ai_tasks)
            }
        }
    except Exception as e:
        logging.error(f"Dashboard stats error: {e}")
        return {"status": "error", "message": str(e)}

@api_router.get("/bitrix24/test")
async def test_bitrix24():
    """Тест подключения к Bitrix24"""
    result = await bitrix.test_connection()
    return {"status": "success", "bitrix_info": result}

@api_router.get("/cleaning/houses")
async def get_cleaning_houses(limit: int = 50):
    """Получить дома для уборки из Bitrix24"""
    try:
        deals = await bitrix.get_deals(limit=limit)
        
        houses = []
        for deal in deals:
            houses.append({
                "address": deal.get('TITLE', 'Без названия'),
                "bitrix24_deal_id": deal.get('ID'),
                "stage": deal.get('STAGE_ID'),
                "created_date": deal.get('DATE_CREATE'),
                "responsible": deal.get('ASSIGNED_BY_ID')
            })
        
        return {
            "status": "success", 
            "houses": houses,
            "total": len(houses)
        }
    except Exception as e:
        logging.error(f"Houses fetch error: {e}")
        return {"status": "error", "message": str(e)}

@api_router.post("/voice/process")
async def process_voice_message(message: VoiceMessage):
    """Обработка голосового сообщения"""
    try:
        ai_response = await ai_service.process_voice_message(message.text)
        
        # Сохранение в логи
        await db.voice_logs.insert_one({
            "user_message": message.text,
            "ai_response": ai_response,
            "timestamp": datetime.utcnow(),
            "user_id": message.user_id
        })
        
        return ChatResponse(response=ai_response)
    except Exception as e:
        logging.error(f"Voice processing error: {e}")
        return ChatResponse(response="Извините, произошла ошибка при обработке сообщения")

@api_router.post("/meetings/start-recording")
async def start_meeting_recording():
    """Начать запись планерки"""
    meeting_id = str(uuid.uuid4())
    
    meeting = Meeting(
        id=meeting_id,
        title=f"Планерка {datetime.now().strftime('%d.%m.%Y %H:%M')}",
        transcription="Запись начата..."
    )
    
    await db.meetings.insert_one(meeting.dict())
    
    return {"status": "success", "meeting_id": meeting_id}

@api_router.post("/meetings/stop-recording")
async def stop_meeting_recording(meeting_id: str):
    """Остановить запись планерки"""
    try:
        # Здесь будет логика остановки записи и обработки аудио
        await db.meetings.update_one(
            {"id": meeting_id},
            {"$set": {"transcription": "Запись завершена"}}
        )
        
        return {"status": "success", "message": "Запись завершена"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@api_router.get("/meetings")
async def get_meetings():
    """Получить список встреч"""
    meetings = await db.meetings.find().to_list(100)
    return {"status": "success", "meetings": meetings}

@api_router.post("/ai-tasks")
async def create_ai_task(title: str = Form(...), description: str = Form(...), scheduled_time: str = Form(...)):
    """Создать задачу для AI"""
    try:
        scheduled_dt = datetime.fromisoformat(scheduled_time.replace('Z', '+00:00'))
        
        task = AITask(
            title=title,
            description=description,
            scheduled_time=scheduled_dt
        )
        
        await db.ai_tasks.insert_one(task.dict())
        
        return {"status": "success", "task_id": task.id}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@api_router.get("/ai-tasks")
async def get_ai_tasks():
    """Получить список AI задач"""
    tasks = await db.ai_tasks.find().to_list(100)
    return {"status": "success", "tasks": tasks}

@api_router.post("/ai-tasks/{task_id}/chat")
async def chat_with_ai_about_task(task_id: str, message: str = Form(...)):
    """Чат с AI по конкретной задаче"""
    try:
        ai_response = await ai_service.process_voice_message(f"Задача: {message}")
        
        # Добавляем сообщение в историю чата задачи
        await db.ai_tasks.update_one(
            {"id": task_id},
            {"$push": {"chat_messages": {
                "user": message,
                "ai": ai_response,
                "timestamp": datetime.utcnow()
            }}}
        )
        
        return {"status": "success", "response": ai_response}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@api_router.get("/employees")
async def get_employees():
    """Получить список сотрудников"""
    employees = await db.employees.find().to_list(100)
    if not employees:
        # Мокаем данные сотрудников
        mock_employees = [
            {"name": "Анна Иванова", "role": "Бригадир", "phone": "+79001234567"},
            {"name": "Петр Петров", "role": "Уборщик", "phone": "+79001234568"},
            {"name": "Мария Сидорова", "role": "Уборщик", "phone": "+79001234569"}
        ]
        return {"status": "success", "employees": mock_employees, "total": 82}
    
    return {"status": "success", "employees": employees, "total": len(employees)}

@api_router.get("/logs")
async def get_system_logs():
    """Получить системные логи"""
    voice_logs = await db.voice_logs.find().sort("timestamp", -1).to_list(50)
    return {"status": "success", "logs": voice_logs}

# Include router
app.include_router(api_router)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

@app.on_event("shutdown")
async def shutdown_event():
    client.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)