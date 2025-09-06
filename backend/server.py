from fastapi import FastAPI, APIRouter, HTTPException, Request
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import json
import aiohttp
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import uuid
from datetime import datetime
from emergentintegrations.llm.chat import LlmChat, UserMessage

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Environment variables
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
BITRIX24_WEBHOOK_URL = os.environ.get('BITRIX24_WEBHOOK_URL', '')
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY', '')

# Create the main app without a prefix
app = FastAPI(title="Bitrix24 Telegram Bot", version="1.0.0")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# === MODELS ===
class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class StatusCheckCreate(BaseModel):
    client_name: str

class TelegramWebhookData(BaseModel):
    url: str

class BitrixRequest(BaseModel):
    method: str
    parameters: Dict[str, Any] = {}

class ChatMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    message: str
    response: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ChatRequest(BaseModel):
    message: str
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))

# === BASIC ROUTES ===
@api_router.get("/")
async def root():
    return {"message": "Bitrix24 Telegram Bot API"}

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

# === TELEGRAM BOT ROUTES ===
@api_router.get("/telegram/set-webhook")
async def set_telegram_webhook(request: Request):
    """Устанавливает webhook для Telegram бота"""
    try:
        if not TELEGRAM_BOT_TOKEN:
            raise HTTPException(status_code=400, detail="TELEGRAM_BOT_TOKEN не настроен")
        
        # Получаем базовый URL приложения
        base_url = str(request.base_url).rstrip('/')
        webhook_url = f"{base_url}/api/telegram/webhook"
        
        # Устанавливаем webhook через Telegram API
        telegram_api_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/setWebhook"
        
        async with aiohttp.ClientSession() as session:
            async with session.post(telegram_api_url, json={"url": webhook_url}) as response:
                result = await response.json()
                
                if result.get("ok"):
                    logger.info(f"Webhook установлен: {webhook_url}")
                    return {
                        "success": True,
                        "message": "Webhook успешно установлен",
                        "webhook_url": webhook_url,
                        "telegram_response": result
                    }
                else:
                    logger.error(f"Ошибка установки webhook: {result}")
                    raise HTTPException(status_code=400, detail=f"Ошибка Telegram API: {result}")
                    
    except Exception as e:
        logger.error(f"Ошибка установки webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/telegram/webhook")
async def telegram_webhook(request: Request):
    """Обрабатывает входящие сообщения от Telegram"""
    try:
        data = await request.json()
        logger.info(f"Получено сообщение: {data}")
        
        # Извлекаем данные сообщения
        message = data.get("message", {})
        chat_id = message.get("chat", {}).get("id")
        text = message.get("text", "")
        
        if not chat_id or not text:
            return {"ok": True}
        
        # Обрабатываем команды
        if text.startswith("/"):
            response_text = await handle_telegram_command(text, chat_id)
        else:
            # Обычное сообщение - используем AI для ответа
            response_text = await generate_ai_response(text, str(chat_id))
        
        # Отправляем ответ пользователю
        await send_telegram_message(chat_id, response_text)
        
        return {"ok": True}
        
    except Exception as e:
        logger.error(f"Ошибка обработки webhook: {str(e)}")
        return {"ok": False, "error": str(e)}

async def handle_telegram_command(command: str, chat_id: int) -> str:
    """Обрабатывает команды Telegram"""
    if command.startswith("/start"):
        return "Привет! Я бот для работы с Bitrix24. Отправьте мне сообщение или используйте команды."
    elif command.startswith("/help"):
        return """
Доступные команды:
/start - Начать работу
/help - Показать справку
/bitrix - Работа с Bitrix24
        """
    elif command.startswith("/bitrix"):
        if not BITRIX24_WEBHOOK_URL:
            return "Bitrix24 не настроен. Обратитесь к администратору."
        return "Bitrix24 подключен. Какую операцию выполнить?"
    else:
        return "Неизвестная команда. Используйте /help для справки."

async def generate_ai_response(message: str, session_id: str) -> str:
    """Генерирует ответ с помощью AI"""
    try:
        if not EMERGENT_LLM_KEY:
            return "AI не настроен"
        
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=session_id,
            system_message="Ты помощник для работы с Bitrix24. Отвечай кратко и по делу на русском языке."
        ).with_model("openai", "gpt-4o-mini")
        
        user_message = UserMessage(text=message)
        response = await chat.send_message(user_message)
        
        # Сохраняем в базу данных
        chat_record = ChatMessage(
            session_id=session_id,
            message=message,
            response=response
        )
        await db.chat_messages.insert_one(chat_record.dict())
        
        return response
        
    except Exception as e:
        logger.error(f"Ошибка AI ответа: {str(e)}")
        return "Извините, произошла ошибка при обработке сообщения."

async def send_telegram_message(chat_id: int, text: str):
    """Отправляет сообщение в Telegram"""
    try:
        if not TELEGRAM_BOT_TOKEN:
            return
            
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                result = await response.json()
                if not result.get("ok"):
                    logger.error(f"Ошибка отправки сообщения: {result}")
                    
    except Exception as e:
        logger.error(f"Ошибка отправки сообщения: {str(e)}")

# === BITRIX24 ROUTES ===
@api_router.post("/bitrix/request")
async def bitrix_request(request: BitrixRequest):
    """Выполняет запрос к Bitrix24 API"""
    try:
        if not BITRIX24_WEBHOOK_URL:
            raise HTTPException(status_code=400, detail="BITRIX24_WEBHOOK_URL не настроен")
        
        # Формируем URL для запроса
        url = f"{BITRIX24_WEBHOOK_URL}{request.method}/"
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=request.parameters) as response:
                result = await response.json()
                
                if "error" in result:
                    raise HTTPException(status_code=400, detail=result["error"])
                
                return {
                    "success": True,
                    "method": request.method,
                    "data": result
                }
                
    except aiohttp.ClientError as e:
        logger.error(f"Ошибка запроса к Bitrix24: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка соединения с Bitrix24: {str(e)}")
    except Exception as e:
        logger.error(f"Ошибка Bitrix24 запроса: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/bitrix/methods")
async def get_bitrix_methods():
    """Возвращает список доступных методов Bitrix24"""
    return {
        "crm": [
            "crm.deal.list",
            "crm.deal.get",
            "crm.deal.add",
            "crm.deal.update",
            "crm.contact.list",
            "crm.contact.get",
            "crm.contact.add",
            "crm.contact.update",
            "crm.company.list",
            "crm.company.get",
            "crm.company.add",
            "crm.company.update"
        ],
        "task": [
            "tasks.task.list",
            "tasks.task.get",
            "tasks.task.add",
            "tasks.task.update",
            "tasks.task.complete"
        ],
        "user": [
            "user.get",
            "user.current",
            "user.search"
        ]
    }

# === AI CHAT ROUTES ===
@api_router.post("/chat")
async def chat_with_ai(request: ChatRequest):
    """Чат с AI ассистентом"""
    try:
        if not EMERGENT_LLM_KEY:
            raise HTTPException(status_code=400, detail="EMERGENT_LLM_KEY не настроен")
        
        response = await generate_ai_response(request.message, request.session_id)
        
        return {
            "success": True,
            "response": response,
            "session_id": request.session_id
        }
        
    except Exception as e:
        logger.error(f"Ошибка AI чата: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/chat/history/{session_id}")
async def get_chat_history(session_id: str):
    """Получает историю чата"""
    try:
        messages = await db.chat_messages.find(
            {"session_id": session_id}
        ).sort("timestamp", 1).to_list(100)
        
        return {
            "success": True,
            "session_id": session_id,
            "messages": [ChatMessage(**msg) for msg in messages]
        }
        
    except Exception as e:
        logger.error(f"Ошибка получения истории: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)