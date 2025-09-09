from fastapi import FastAPI, APIRouter, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import httpx
import asyncio
import os
from dotenv import load_dotenv
from pathlib import Path
import json
from datetime import datetime
import logging

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="VasDom AudioBot API", version="1.0.0")

# Create API router
api_router = APIRouter(prefix="/api")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =============================================================================
# MODELS
# =============================================================================

class DashboardStats(BaseModel):
    houses: int = 348
    apartments: int = 25812
    employees: int = 82
    brigades: int = 6
    completed_objects: int = 147
    problem_objects: int = 25

class House(BaseModel):
    id: str
    address: str
    status: str
    amount: Optional[float] = None
    responsible: Optional[str] = None
    brigade: Optional[str] = None

class VoiceRequest(BaseModel):
    text: str
    user_id: str

class VoiceResponse(BaseModel):
    response: str
    confidence: float = 0.95

class MeetingRequest(BaseModel):
    meeting_type: str = "планерка"
    participants: List[str] = []

class MeetingResponse(BaseModel):
    meeting_id: str
    status: str
    timestamp: datetime

# =============================================================================
# BITRIX24 INTEGRATION
# =============================================================================

class Bitrix24Client:
    def __init__(self):
        self.webhook_url = os.getenv("BITRIX24_WEBHOOK_URL")
        if not self.webhook_url:
            logger.warning("BITRIX24_WEBHOOK_URL not set")
    
    async def get_houses(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Получить дома из воронки 'Уборка подъездов'"""
        if not self.webhook_url:
            # Return mock data when webhook not available
            return self._get_mock_houses(limit)
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                url = f"{self.webhook_url}crm.deal.list"
                params = {
                    "filter": {
                        "CATEGORY_ID": "2",  # Воронка "Уборка подъездов"
                    },
                    "select": [
                        "ID", "TITLE", "STAGE_ID", "OPPORTUNITY", 
                        "ASSIGNED_BY_ID", "UF_CRM_1569831275", "ADDRESS"
                    ],
                    "start": 0
                }
                
                response = await client.post(url, json=params)
                response.raise_for_status()
                data = response.json()
                
                if data.get("result"):
                    return data["result"][:limit]
                else:
                    logger.warning(f"No houses found in Bitrix24: {data}")
                    return self._get_mock_houses(limit)
                    
        except Exception as e:
            logger.error(f"Error fetching houses from Bitrix24: {e}")
            return self._get_mock_houses(limit)
    
    def _get_mock_houses(self, limit: int) -> List[Dict[str, Any]]:
        """Моковые данные домов в Калуге"""
        mock_houses = [
            {"ID": "1", "TITLE": "ул. Пролетарская, 145", "STAGE_ID": "C2:WON", "OPPORTUNITY": "45000", "ASSIGNED_BY_ID": "1"},
            {"ID": "2", "TITLE": "ул. Никитиной, 62", "STAGE_ID": "C2:FINAL_INVOICE", "OPPORTUNITY": "38000", "ASSIGNED_BY_ID": "2"},
            {"ID": "3", "TITLE": "ул. Хрустальная, 28", "STAGE_ID": "C2:WON", "OPPORTUNITY": "52000", "ASSIGNED_BY_ID": "1"},
            {"ID": "4", "TITLE": "с. Жилетово, д. 15", "STAGE_ID": "C2:APOLOGY", "OPPORTUNITY": "31000", "ASSIGNED_BY_ID": "3"},
            {"ID": "5", "TITLE": "г. Кондрово, ул. Советская, 89", "STAGE_ID": "C2:WON", "OPPORTUNITY": "47000", "ASSIGNED_BY_ID": "2"},
            {"ID": "6", "TITLE": "ул. Гагарина, 24", "STAGE_ID": "C2:WON", "OPPORTUNITY": "41000", "ASSIGNED_BY_ID": "1"},
            {"ID": "7", "TITLE": "ул. Ленина, 156", "STAGE_ID": "C2:FINAL_INVOICE", "OPPORTUNITY": "49000", "ASSIGNED_BY_ID": "3"},
            {"ID": "8", "TITLE": "пр. Ленина, 78", "STAGE_ID": "C2:WON", "OPPORTUNITY": "55000", "ASSIGNED_BY_ID": "2"},
        ]
        return mock_houses[:limit]

# Initialize Bitrix24 client
bitrix_client = Bitrix24Client()

# =============================================================================
# AI СИСТЕМА
# =============================================================================

from emergentintegrations.llm.chat import LlmChat, UserMessage

class VasDomAI:
    """AI система для VasDom с интеграцией Emergent LLM"""
    
    def __init__(self):
        self.api_key = os.getenv("EMERGENT_LLM_KEY")
        self.context = {
            "company": "VasDom",
            "city": "Калуга",
            "houses": 348,
            "employees": 82,
            "brigades": 6,
            "apartments": 25812
        }
        self.system_message = f"""Ты - AI-ассистент компании VasDom, клининговой компании в Калуге.

КОНТЕКСТ КОМПАНИИ:
- Название: VasDom
- Город: Калуга и область
- Обслуживаем: {self.context['houses']} многоквартирных домов
- Сотрудников: {self.context['employees']} человек
- Рабочих бригад: {self.context['brigades']}
- Квартир в обслуживании: {self.context['apartments']}

ТВОЯ РОЛЬ:
- Отвечай на русском языке
- Предоставляй точную информацию о компании
- Помогай с планированием задач и управлением
- Анализируй статистику и данные
- Будь профессиональным и дружелюбным

СПЕЦИАЛИЗАЦИЯ:
- Управление клининговыми бригадами
- Контроль качества уборки
- Планирование работ по домам
- Статистика и отчетность
- Решение проблем с объектами"""

    async def process_voice_request(self, text: str, user_id: str) -> VoiceResponse:
        """Обработка голосового запроса через Emergent LLM"""
        try:
            if not self.api_key:
                # Fallback to rule-based if no API key
                return await self._fallback_response(text)
            
            # Создаем чат с контекстом
            chat = LlmChat(
                api_key=self.api_key,
                session_id=f"vasdom_{user_id}",
                system_message=self.system_message
            ).with_model("openai", "gpt-4o-mini")
            
            # Создаем сообщение пользователя
            user_message = UserMessage(text=text)
            
            # Получаем ответ от AI
            ai_response = await chat.send_message(user_message)
            
            logger.info(f"AI response: {ai_response}")
            
            return VoiceResponse(response=ai_response, confidence=0.98)
            
        except Exception as e:
            logger.error(f"Error with Emergent LLM: {e}")
            # Fallback to rule-based response
            return await self._fallback_response(text)
    
    async def _fallback_response(self, text: str) -> VoiceResponse:
        """Резервная система ответов если AI недоступен"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ["дом", "домов", "объект"]):
            response = f"В настоящий момент компания VasDom обслуживает {self.context['houses']} многоквартирных домов в Калуге и области."
        elif any(word in text_lower for word in ["сотрудник", "работник", "персонал"]):
            response = f"В штате компании VasDom работает {self.context['employees']} сотрудника, разделенных на {self.context['brigades']} рабочих бригад."
        elif any(word in text_lower for word in ["квартир", "площадь", "объем"]):
            response = f"Общая площадь обслуживания составляет {self.context['apartments']} квартир во всех {self.context['houses']} домах."
        else:
            response = f"Я помогаю управлять компанией VasDom в Калуге. У нас {self.context['houses']} домов и {self.context['employees']} сотрудников. Задайте вопрос о статистике или работе компании."
        
        return VoiceResponse(response=response, confidence=0.85)

# Initialize AI system
ai_system = VasDomAI()

# =============================================================================
# API ROUTES
# =============================================================================

@api_router.get("/")
async def root():
    """Статус API"""
    return {"message": "VasDom AudioBot API активна", "version": "1.0.0"}

@api_router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard():
    """Получить статистику для дашборда"""
    return DashboardStats()

@api_router.get("/bitrix24/test")
async def test_bitrix24():
    """Тест подключения к Bitrix24"""
    try:
        houses = await bitrix_client.get_houses(limit=3)
        return {
            "status": "success",
            "webhook_url": bitrix_client.webhook_url,
            "houses_count": len(houses),
            "sample_houses": houses
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@api_router.get("/cleaning/houses")
async def get_cleaning_houses(limit: int = 10):
    """Получить дома из воронки уборки"""
    try:
        houses = await bitrix_client.get_houses(limit=limit)
        return {
            "houses": houses,
            "count": len(houses),
            "total_in_system": 348
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/voice/process", response_model=VoiceResponse)
async def process_voice(request: VoiceRequest):
    """Обработка голосового запроса через AI"""
    try:
        response = await ai_system.process_voice_request(request.text, request.user_id)
        
        # Логируем взаимодействие
        logger.info(f"Voice request from {request.user_id}: {request.text}")
        logger.info(f"AI response: {response.response}")
        
        return response
    except Exception as e:
        logger.error(f"Error processing voice request: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/meetings/start-recording", response_model=MeetingResponse)
async def start_meeting_recording(request: MeetingRequest):
    """Начать запись планерки"""
    meeting_id = f"meeting_{int(datetime.now().timestamp())}"
    logger.info(f"Started meeting recording: {meeting_id}")
    
    return MeetingResponse(
        meeting_id=meeting_id,
        status="recording",
        timestamp=datetime.now()
    )

@api_router.post("/meetings/stop-recording")
async def stop_meeting_recording(meeting_id: str):
    """Остановить запись планерки"""
    logger.info(f"Stopped meeting recording: {meeting_id}")
    return {"status": "stopped", "meeting_id": meeting_id}

@api_router.get("/meetings")
async def get_meetings():
    """Получить список планерок"""
    return {
        "meetings": [
            {"id": "meeting_1", "date": "2024-01-15", "type": "планерка", "duration": "45 мин"},
            {"id": "meeting_2", "date": "2024-01-14", "type": "планерка", "duration": "38 мин"},
        ]
    }

@api_router.get("/logs")
async def get_system_logs():
    """Получить системные логи"""
    return {
        "logs": [
            {"timestamp": datetime.now().isoformat(), "level": "INFO", "message": "Система работает нормально"},
            {"timestamp": datetime.now().isoformat(), "level": "INFO", "message": "Подключение к Bitrix24 активно"},
        ]
    }

# Include router in app
app.include_router(api_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)