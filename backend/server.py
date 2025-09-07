from fastapi import FastAPI, APIRouter, UploadFile, File, HTTPException
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
import asyncio
from emergentintegrations.llm.chat import LlmChat, UserMessage


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

# Новые модели для диктофона планерок
class Meeting(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    date: datetime = Field(default_factory=datetime.utcnow)
    transcript: Optional[str] = None
    summary: Optional[str] = None
    participants: List[str] = []
    status: str = "recording"  # recording, completed, processing

class MeetingCreate(BaseModel):
    title: str
    participants: List[str] = []

# Новые модели для живого разговора
class VoiceSession(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = "default_user"
    start_time: datetime = Field(default_factory=datetime.utcnow)
    status: str = "active"  # active, ended
    messages: List[dict] = []

class VoiceMessage(BaseModel):
    session_id: str
    user_message: str
    ai_response: Optional[str] = None
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

# =====================================
# ДИКТОФОН ПЛАНЕРОК - API ENDPOINTS
# =====================================

@api_router.post("/meetings/create", response_model=Meeting)
async def create_meeting(meeting_data: MeetingCreate):
    """Создать новую планерку для записи"""
    meeting = Meeting(**meeting_data.dict())
    await db.meetings.insert_one(meeting.dict())
    return meeting

@api_router.get("/meetings", response_model=List[Meeting])
async def get_meetings():
    """Получить все планерки"""
    meetings = await db.meetings.find().to_list(1000)
    return [Meeting(**meeting) for meeting in meetings]

@api_router.get("/meetings/{meeting_id}", response_model=Meeting)
async def get_meeting(meeting_id: str):
    """Получить конкретную планерку"""
    meeting = await db.meetings.find_one({"id": meeting_id})
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return Meeting(**meeting)

@api_router.post("/meetings/{meeting_id}/transcribe")
async def transcribe_meeting(meeting_id: str, audio_text: dict):
    """Транскрибировать планерку с помощью ИИ"""
    meeting = await db.meetings.find_one({"id": meeting_id})
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    # Инициализация ИИ для транскрипции и анализа
    chat = LlmChat(
        api_key=os.environ['EMERGENT_LLM_KEY'],
        session_id=f"meeting_{meeting_id}",
        system_message="Ты профессиональный помощник для анализа планерок. Анализируй транскрипты встреч и создавай краткое саммари с ключевыми решениями и задачами."
    ).with_model("openai", "gpt-4o-mini")
    
    transcript_text = audio_text.get("transcript", "")
    
    # Генерация саммари планерки
    summary_prompt = UserMessage(
        text=f"Проанализируй этот транскрипт планерки и создай краткое саммари с ключевыми решениями и задачами:\n\n{transcript_text}"
    )
    
    summary_response = await chat.send_message(summary_prompt)
    
    # Обновление планерки в базе
    update_data = {
        "transcript": transcript_text,
        "summary": summary_response,
        "status": "completed"
    }
    
    await db.meetings.update_one(
        {"id": meeting_id},
        {"$set": update_data}
    )
    
    return {"message": "Meeting transcribed and analyzed", "summary": summary_response}

@api_router.post("/meetings/{meeting_id}/complete")
async def complete_meeting(meeting_id: str):
    """Завершить планерку"""
    await db.meetings.update_one(
        {"id": meeting_id},
        {"$set": {"status": "completed"}}
    )
    return {"message": "Meeting completed"}

# =====================================
# ЖИВОЙ РАЗГОВОР - API ENDPOINTS  
# =====================================

@api_router.post("/voice/start-session", response_model=VoiceSession)
async def start_voice_session():
    """Начать новую голосовую сессию"""
    session = VoiceSession()
    await db.voice_sessions.insert_one(session.dict())
    return session

@api_router.get("/voice/sessions", response_model=List[VoiceSession])
async def get_voice_sessions():
    """Получить все голосовые сессии"""
    sessions = await db.voice_sessions.find().to_list(1000)
    return [VoiceSession(**session) for session in sessions]

@api_router.post("/voice/{session_id}/chat")
async def voice_chat(session_id: str, message_data: dict):
    """Отправить сообщение в голосовой чат и получить ответ от ИИ"""
    session = await db.voice_sessions.find_one({"id": session_id})
    if not session:
        raise HTTPException(status_code=404, detail="Voice session not found")
    
    user_message = message_data.get("message", "")
    
    # Инициализация ИИ для голосового чата
    chat = LlmChat(
        api_key=os.environ['EMERGENT_LLM_KEY'],
        session_id=session_id,
        system_message="Ты дружелюбный голосовой ИИ-помощник. Отвечай кратко и по делу, как в живом разговоре. Будь полезным и отзывчивым."
    ).with_model("openai", "gpt-4o-mini")
    
    # Получение ответа от ИИ
    ai_prompt = UserMessage(text=user_message)
    ai_response = await chat.send_message(ai_prompt)
    
    # Создание записи сообщения
    voice_message = VoiceMessage(
        session_id=session_id,
        user_message=user_message,
        ai_response=ai_response
    )
    
    # Сохранение сообщения в базе
    await db.voice_messages.insert_one(voice_message.dict())
    
    # Обновление сессии
    session_messages = session.get("messages", [])
    session_messages.append({
        "user": user_message,
        "ai": ai_response,
        "timestamp": datetime.utcnow().isoformat()
    })
    
    await db.voice_sessions.update_one(
        {"id": session_id},
        {"$set": {"messages": session_messages}}
    )
    
    return {
        "user_message": user_message,
        "ai_response": ai_response,
        "session_id": session_id
    }

@api_router.get("/voice/{session_id}/history")
async def get_voice_history(session_id: str):
    """Получить историю голосового чата"""
    session = await db.voice_sessions.find_one({"id": session_id})
    if not session:
        raise HTTPException(status_code=404, detail="Voice session not found")
    
    messages = await db.voice_messages.find({"session_id": session_id}).to_list(1000)
    return {
        "session_id": session_id,
        "messages": [VoiceMessage(**msg) for msg in messages]
    }

@api_router.post("/voice/{session_id}/end")
async def end_voice_session(session_id: str):
    """Завершить голосовую сессию"""
    await db.voice_sessions.update_one(
        {"id": session_id},
        {"$set": {"status": "ended"}}
    )
    return {"message": "Voice session ended"}

# Include the router in the main app
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
