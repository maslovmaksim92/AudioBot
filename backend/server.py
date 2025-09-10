from fastapi import FastAPI, APIRouter, HTTPException, Depends, WebSocket, WebSocketDisconnect
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
import websockets
import asyncio

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
        chat = LlmChat(
            api_key=openai_key,
            session_id="chat_session",
            system_message=system_message
        )
        chat.with_model("openai", "gpt-4o-mini")
        
        user_message = UserMessage(text=request.message)
        chat_response = await chat.send_message(user_message)
        
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

# OpenAI Realtime API endpoints - SIMPLIFIED APPROACH
@api_router.post("/realtime/token", response_model=RealtimeTokenResponse)
async def get_realtime_token():
    """Get session info for OpenAI Realtime API - Direct WebSocket approach"""
    try:
        openai_key = os.environ.get('EMERGENT_LLM_KEY') or os.environ.get('OPENAI_API_KEY') or os.environ.get('OPENAI_KEY')
        if not openai_key:
            raise HTTPException(status_code=500, detail="OpenAI API key not configured")
        
        # For Realtime API, we just return the key info for direct WebSocket connection
        # The actual session is created via WebSocket, not HTTP
        import time
        expires_at = int(time.time()) + 3600  # 1 hour from now
        
        return RealtimeTokenResponse(
            token=openai_key,  # Return the API key for WebSocket auth
            expires_at=expires_at
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
        chat = LlmChat(
            api_key=openai_key,
            session_id="voice_session",
            system_message=system_message
        )
        chat.with_model("openai", "gpt-4o-mini")
        
        user_message = UserMessage(text=request.text)
        chat_response = await chat.send_message(user_message)
        
        return {"response": chat_response}
        
    except Exception as e:
        logging.error(f"Voice processing error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Voice processing error: {str(e)}")

# WebSocket endpoint for Realtime Voice Chat
@app.websocket("/ws/realtime")
async def websocket_realtime(websocket: WebSocket):
    """WebSocket proxy to OpenAI Realtime API"""
    await websocket.accept()
    
    try:
        openai_key = os.environ.get('EMERGENT_LLM_KEY') or os.environ.get('OPENAI_API_KEY') or os.environ.get('OPENAI_KEY')
        if not openai_key:
            await websocket.close(code=1008, reason="OpenAI API key not configured")
            return
        
        # Connect to OpenAI Realtime API
        openai_ws_uri = "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-12-17"
        headers = {
            "Authorization": f"Bearer {openai_key}",
            "OpenAI-Beta": "realtime=v1"
        }
        
        async with websockets.connect(openai_ws_uri, extra_headers=headers) as openai_ws:
            # Send initial session configuration
            session_config = {
                "type": "session.update",
                "session": {
                    "modalities": ["text", "audio"],
                    "instructions": "Ты - голосовой AI помощник VasDom AudioBot. Говори живым человеческим голосом на русском языке. Отвечай дружелюбно и естественно.",
                    "voice": "verse",
                    "input_audio_format": "pcm16",
                    "output_audio_format": "pcm16",
                    "input_audio_transcription": {
                        "model": "whisper-1"
                    }
                }
            }
            await openai_ws.send(json.dumps(session_config))
            
            # Create bidirectional proxy
            async def client_to_openai():
                """Forward messages from client to OpenAI"""
                try:
                    async for message in websocket.iter_text():
                        await openai_ws.send(message)
                except WebSocketDisconnect:
                    pass
                except Exception as e:
                    logging.error(f"Client to OpenAI error: {e}")
            
            async def openai_to_client():
                """Forward messages from OpenAI to client"""
                try:
                    async for message in openai_ws:
                        await websocket.send_text(message)
                except websockets.exceptions.ConnectionClosed:
                    pass
                except Exception as e:
                    logging.error(f"OpenAI to client error: {e}")
            
            # Run both directions concurrently
            await asyncio.gather(
                client_to_openai(),
                openai_to_client(),
                return_exceptions=True
            )
            
    except Exception as e:
        logging.error(f"WebSocket realtime error: {e}")
        await websocket.close(code=1011, reason=f"Internal error: {str(e)}")

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