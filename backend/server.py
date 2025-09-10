from fastapi import FastAPI, APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer
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
from emergentintegrations.llm.chat import LlmChat, UserMessage
import json
import httpx
import httpx

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI(title="VasDom AudioBot API", version="1.0.0")
security = HTTPBearer()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Models
class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class StatusCheckCreate(BaseModel):
    client_name: str

class ChatMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    message: str
    response: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ChatRequest(BaseModel):
    message: str

class RealtimeTokenResponse(BaseModel):
    token: str
    expires_at: int

class VoiceRequest(BaseModel):
    text: str

# Basic routes
@api_router.get("/")
async def root():
    return {"message": "VasDom AudioBot API v1.0", "status": "running"}

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.dict()
    status_obj = StatusCheck(**status_dict)
    await db.status_checks.insert_one(status_obj.dict())
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find().to_list(1000)
    return [StatusCheck(**status_check) for status_check in status_checks]

# AI Chat endpoints
@api_router.post("/chat/message")
async def send_chat_message(request: ChatRequest):
    """Send message to AI and get response"""
    try:
        openai_key = os.environ.get('EMERGENT_LLM_KEY') or os.environ.get('OPENAI_API_KEY') or os.environ.get('OPENAI_KEY')
        if not openai_key:
            raise HTTPException(status_code=500, detail="OpenAI API key not configured")
        
        # Use LlmChat for OpenAI communication
        system_message = "Ты - AI помощник VasDom AudioBot. Отвечай дружелюбно и помогай пользователям. Отвечай на русском языке."
        llm_chat = LlmChat(
            api_key=openai_key,
            session_id="chat_session",  # Unique session ID
            system_message=system_message
        )
        # Pass message directly as string
        chat_response = await llm_chat.achat(
            messages=[request.message],
            model="gpt-4o-mini",
            max_tokens=1000,
            temperature=0.7
        )
        
        # Save to database
        chat_message = ChatMessage(
            message=request.message,
            response=chat_response
        )
        await db.chat_messages.insert_one(chat_message.dict())
        
        return {"response": chat_response, "message_id": chat_message.id}
        
    except Exception as e:
        logging.error(f"Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")

@api_router.get("/chat/messages")
async def get_chat_messages():
    """Get chat history"""
    try:
        messages = await db.chat_messages.find().sort("timestamp", -1).limit(50).to_list(50)
        return [ChatMessage(**msg) for msg in messages]
    except Exception as e:
        logging.error(f"Error fetching messages: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching messages: {str(e)}")

# OpenAI Realtime API endpoints
@api_router.post("/realtime/token", response_model=RealtimeTokenResponse)
async def get_realtime_token():
    """Get ephemeral token for OpenAI Realtime API"""
    try:
        openai_key = os.environ.get('EMERGENT_LLM_KEY') or os.environ.get('OPENAI_API_KEY') or os.environ.get('OPENAI_KEY')
        if not openai_key:
            raise HTTPException(status_code=500, detail="OpenAI API key not configured")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.openai.com/v1/realtime/sessions",
                headers={
                    "Authorization": f"Bearer {openai_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-4o-realtime-preview-2024-12-17",
                    "voice": "verse"
                }
            )
        
        if response.status_code != 200:
            logging.error(f"OpenAI Realtime error: {response.text}")
            raise HTTPException(status_code=500, detail="Error creating realtime session")
        
        session_data = response.json()
        return RealtimeTokenResponse(
            token=session_data["client_secret"]["value"],
            expires_at=session_data["expires_at"]
        )
        
    except Exception as e:
        logging.error(f"Realtime token error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Realtime token error: {str(e)}")

# Voice processing endpoint
@api_router.post("/voice/process")
async def process_voice(request: VoiceRequest):
    """Process voice text using OpenAI"""
    try:
        openai_key = os.environ.get('EMERGENT_LLM_KEY') or os.environ.get('OPENAI_API_KEY') or os.environ.get('OPENAI_KEY')
        if not openai_key:
            raise HTTPException(status_code=500, detail="OpenAI API key not configured")
        
        # Use LlmChat for OpenAI communication
        system_message = "Ты - голосовой AI помощник VasDom AudioBot. Отвечай кратко и по делу. Используй разговорный стиль. Отвечай на русском языке."
        llm_chat = LlmChat(
            api_key=openai_key,
            session_id="voice_session",  # Unique session ID
            system_message=system_message
        )
        # Pass message directly as string
        chat_response = await llm_chat.achat(
            messages=[request.text],
            model="gpt-4o-mini",
            max_tokens=500,
            temperature=0.8
        )
        
        return {"response": chat_response}
        
    except Exception as e:
        logging.error(f"Voice processing error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Voice processing error: {str(e)}")

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