import logging
import json
import os
import tempfile
import base64
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import Response
from emergentintegrations.llm.chat import LlmChat, UserMessage
from openai import OpenAI
from ..services.bitrix_service import BitrixService
from ..config.settings import EMERGENT_LLM_KEY, BITRIX24_WEBHOOK_URL

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["realistic-voice"])

# Initialize services
openai_client = OpenAI(api_key=EMERGENT_LLM_KEY)
llm_chat = LlmChat(
    api_key=EMERGENT_LLM_KEY,
    session_id="vasdom_realistic_voice",
    system_message="Вы - Алиса, естественный голосовой помощник VasDom. Говорите как живой человек."
).with_model("openai", "gpt-4o-mini")

bitrix_service = BitrixService(BITRIX24_WEBHOOK_URL) if BITRIX24_WEBHOOK_URL else None

class VasDomRealisticVoice:
    def __init__(self):
        self.bitrix_service = bitrix_service
        self.context = {
            "company": "VasDom",
            "location": "Калуга", 
            "role": "Алиса - живой голосовой помощник",
            "houses_count": 50,  # Реальные данные из Bitrix24
            "employees_count": 82,
            "brigades_count": 6
        }
    
    async def get_company_data(self, query: str) -> str:
        """Получить данные из Bitrix24 по запросу"""
        if not self.bitrix_service:
            return "Я знаю основную информацию о VasDom"
            
        try:
            query_lower = query.lower()
            
            if any(word in query_lower for word in ['дом', 'дома', 'адрес', 'подъезд']):
                deals = await self.bitrix_service.get_deals()
                houses_info = []
                
                for deal in deals[:5]:  # Первые 5 домов
                    title = deal.get('TITLE', 'Без названия')
                    status_info, _ = self.bitrix_service.get_status_info(deal.get('STAGE_ID', ''))
                    brigade = self.bitrix_service.analyze_house_brigade(title)
                    houses_info.append(f"{title} - {status_info}")
                
                return f"Конечно! Вот что у нас есть: " + ". ".join(houses_info[:3])
                
            elif any(word in query_lower for word in ['бригад', 'команд', 'сотрудник']):
                return f"У нас работает 82 замечательных сотрудника в 6 бригадах по всей Калуге"
                       
            elif any(word in query_lower for word in ['статистик', 'отчет', 'данные']):
                deals = await self.bitrix_service.get_deals()
                return f"Давайте посмотрим статистику: у нас {len(deals)} домов в работе, 82 сотрудника в 6 бригадах"
                       
            else:
                return f"Я Алиса из VasDom! У нас 50 домов в управлении в Калуге"
                
        except Exception as e:
            logger.error(f"❌ Error getting Bitrix24 data: {e}")
            return "Давайте я расскажу что знаю о VasDom"
    
    def create_human_prompt(self) -> str:
        return """Вы - Алиса, живой и естественный помощник клининговой компании VasDom в Калуге.

ВАЖНО - ГОВОРИТЕ КАК НАСТОЯЩИЙ ЧЕЛОВЕК:
- Используйте живые выражения: "Конечно!", "Давайте посмотрим", "О, отличный вопрос!"
- Будьте эмоциональной и дружелюбной
- Никаких роботизированных фраз
- Говорите как будто вы реальный сотрудник VasDom

О КОМПАНИИ:
- VasDom - клининговая компания в Калуге
- 50 домов в управлении (реальные данные)
- 82 сотрудника в 6 бригадах
- Вы работаете здесь и знаете все процессы

СТИЛЬ ОБЩЕНИЯ:
- Теплый, человечный, как с хорошим знакомым
- Короткие, живые ответы
- Используйте "Ну", "Да", "Конечно", "Слушайте"
- Будьте искренней и отзывчивой"""

realistic_assistant = VasDomRealisticVoice()

@router.websocket("/realistic-voice/ws")
async def realistic_voice_websocket(websocket: WebSocket):
    """WebSocket для реального человеческого голоса"""
    await websocket.accept()
    logger.info("🎤 Realistic Voice WebSocket connected")
    
    try:
        # Приветственное сообщение
        welcome_text = "Привет! Я Алиса из VasDom. Рада с вами пообщаться!"
        
        # Генерируем реальный человеческий голос
        audio_response = await generate_realistic_voice(welcome_text, "nova")
        
        await websocket.send_text(json.dumps({
            "type": "voice_message",
            "text": welcome_text,
            "audio_data": audio_response,
            "voice_type": "human_realistic",
            "timestamp": "2024-01-01T00:00:00Z"
        }, ensure_ascii=False))
        
        while True:
            data = await websocket.receive_text()
            
            try:
                message_data = json.loads(data)
                logger.info(f"🎤 Realistic voice received: {message_data}")
                
                if message_data.get("type") == "user_message":
                    user_message = message_data.get("message", "")
                    
                    if user_message.strip():
                        # Получаем контекст из Bitrix24
                        bitrix_context = await realistic_assistant.get_company_data(user_message)
                        
                        # Генерируем ответ через AI
                        try:
                            system_prompt = realistic_assistant.create_human_prompt()
                            full_context = f"{system_prompt}\n\nКонтекст: {bitrix_context}\n\nВопрос пользователя: {user_message}"
                            
                            user_msg = UserMessage(text=full_context)
                            ai_response = await llm_chat.send_message(user_msg)
                            
                            # Генерируем реальный человеческий голос
                            audio_data = await generate_realistic_voice(ai_response, "nova")
                            
                            await websocket.send_text(json.dumps({
                                "type": "voice_message",
                                "text": ai_response,
                                "audio_data": audio_data,
                                "bitrix_context": bitrix_context,
                                "voice_type": "human_realistic",
                                "model": "OpenAI TTS + GPT-4o mini",
                                "timestamp": "2024-01-01T00:00:00Z"
                            }, ensure_ascii=False))
                            
                            logger.info(f"🗣️ Realistic voice response sent: {ai_response[:50]}...")
                            
                        except Exception as ai_error:
                            logger.error(f"❌ AI error: {ai_error}")
                            
                            fallback_text = f"Понимаю! {bitrix_context}"
                            audio_data = await generate_realistic_voice(fallback_text, "nova")
                            
                            await websocket.send_text(json.dumps({
                                "type": "voice_message",
                                "text": fallback_text,
                                "audio_data": audio_data,
                                "is_fallback": True,
                                "voice_type": "human_realistic",
                                "timestamp": "2024-01-01T00:00:00Z"
                            }, ensure_ascii=False))
                
                elif message_data.get("type") == "ping":
                    await websocket.send_text(json.dumps({
                        "type": "pong",
                        "timestamp": message_data.get("timestamp")
                    }, ensure_ascii=False))
                    
            except json.JSONDecodeError:
                logger.error(f"❌ Invalid JSON received: {data}")
                
    except WebSocketDisconnect:
        logger.info("🔌 Realistic Voice WebSocket disconnected")
    except Exception as e:
        logger.error(f"❌ Realistic Voice WebSocket error: {e}")

async def generate_realistic_voice(text: str, voice: str = "nova") -> str:
    """Генерирует реальный человеческий голос через OpenAI TTS API"""
    try:
        import httpx
        
        # Оптимизируем текст для русского языка
        optimized_text = optimize_russian_text(text)
        
        # Используем emergent LLM key для OpenAI TTS через HTTP API
        headers = {
            "Authorization": f"Bearer {EMERGENT_LLM_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "tts-1-hd",
            "voice": voice,
            "input": optimized_text,
            "response_format": "mp3"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.openai.com/v1/audio/speech",
                headers=headers,
                json=payload,
                timeout=30.0
            )
            
            if response.status_code == 200:
                # Конвертируем в base64 для передачи через WebSocket
                audio_base64 = base64.b64encode(response.content).decode('utf-8')
                logger.info(f"🎤 Generated realistic voice: {len(response.content)} bytes")
                return audio_base64
            else:
                logger.error(f"❌ OpenAI TTS API error: {response.status_code} - {response.text}")
                return ""
        
    except Exception as e:
        logger.error(f"❌ Voice generation error: {e}")
        return ""

def optimize_russian_text(text: str) -> str:
    """Оптимизирует русский текст для лучшего произношения"""
    # Замены для более естественного произношения
    replacements = {
        'что': 'што',
        'конечно': 'конешно', 
        'скучно': 'скушно',
        'нарочно': 'нарошно'
    }
    
    optimized = text
    for original, replacement in replacements.items():
        optimized = optimized.replace(original, replacement)
    
    # Добавляем паузы для естественности
    if not optimized.strip().endswith(('.', '!', '?')):
        optimized += '.'
    
    return optimized

@router.get("/realistic-voice/status")
async def realistic_voice_status():
    """Статус системы реального голоса"""
    try:
        # Проверяем доступность OpenAI TTS
        test_response = openai_client.audio.speech.create(
            model="tts-1",
            voice="nova",
            input="тест",
            response_format="mp3"
        )
        
        openai_status = "active" if len(test_response.content) > 0 else "error"
        
        # Проверяем Bitrix24
        bitrix_status = "connected" if bitrix_service else "unavailable"
        if bitrix_service:
            try:
                deals = await bitrix_service.get_deals()
                houses_count = len(deals)
                bitrix_status = "connected"
            except:
                houses_count = 50
                bitrix_status = "fallback"
        else:
            houses_count = 50
            
        return {
            "status": "active",
            "assistant_name": "Алиса",
            "voice_technology": "OpenAI TTS HD",
            "voice_model": "tts-1-hd",
            "voice_type": "nova (женский, естественный)",
            "language": "ru-RU",
            "company": "VasDom",
            "location": "Калуга",
            "data_sources": {
                "openai_tts": openai_status,
                "bitrix24": bitrix_status,
                "houses_count": houses_count,
                "employees_count": 82,
                "brigades_count": 6
            },
            "capabilities": [
                "Реальный человеческий голос OpenAI TTS",
                "Неотличимый от живого человека",
                "Актуальные данные из Bitrix24",
                "Естественное русское произношение",
                "Эмоциональная речь и интонации"
            ]
        }
        
    except Exception as e:
        logger.error(f"❌ Status check error: {e}")
        return {
            "status": "error",
            "message": str(e)
        }

@router.post("/realistic-voice/test")
async def test_realistic_voice(text: str = "Привет! Это тест реального голоса Алисы из VasDom."):
    """Тестирование реального голоса"""
    try:
        audio_data = await generate_realistic_voice(text, "nova")
        
        if audio_data:
            return {
                "success": True,
                "text": text,
                "audio_base64": audio_data,
                "voice_type": "human_realistic",
                "technology": "OpenAI TTS HD"
            }
        else:
            return {
                "success": False,
                "error": "Failed to generate voice"
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))