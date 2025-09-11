import logging
import json
import os
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from emergentintegrations.llm.openai import OpenAIChatRealtime
from ..services.bitrix_service import BitrixService
from ..config.settings import EMERGENT_LLM_KEY, BITRIX24_WEBHOOK_URL

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["realtime-voice"])

# Initialize services
chat_realtime = OpenAIChatRealtime(api_key=EMERGENT_LLM_KEY)
bitrix_service = BitrixService(BITRIX24_WEBHOOK_URL) if BITRIX24_WEBHOOK_URL else None

# Register GPT-4o Realtime router
OpenAIChatRealtime.register_openai_realtime_router(router, chat_realtime)

class VasDomRealtimeAssistant:
    def __init__(self):
        self.bitrix_service = bitrix_service
        self.context = {
            "company": "VasDom",
            "location": "Калуга", 
            "role": "Персональный помощник Алиса",
            "houses_count": 348,
            "employees_count": 82,
            "brigades_count": 6
        }
    
    async def get_company_data(self, query: str) -> str:
        """Получить данные из Bitrix24 по запросу"""
        if not self.bitrix_service:
            return "Извините, данные Bitrix24 временно недоступны"
            
        try:
            query_lower = query.lower()
            
            if any(word in query_lower for word in ['дом', 'дома', 'адрес', 'подъезд']):
                # Запрос по домам
                deals = await self.bitrix_service.get_deals()
                houses_info = []
                
                for deal in deals[:10]:  # Первые 10 домов
                    title = deal.get('TITLE', 'Без названия')
                    status_info, _ = self.bitrix_service.get_status_info(deal.get('STAGE_ID', ''))
                    brigade = self.bitrix_service.analyze_house_brigade(title)
                    
                    houses_info.append(f"📍 {title} - {status_info} ({brigade})")
                
                return f"Вот информация по нашим домам:\n" + "\n".join(houses_info[:5])
                
            elif any(word in query_lower for word in ['бригад', 'команд', 'сотрудник']):
                # Информация о бригадах
                users = await self.bitrix_service.get_users()
                return f"У нас работает {len(users)} сотрудников в 6 бригадах:\n" \
                       f"1️⃣ Центральный район\n2️⃣ Никитинский район\n3️⃣ Жилетово\n" \
                       f"4️⃣ Северный район\n5️⃣ Пригород\n6️⃣ Окраины"
                       
            elif any(word in query_lower for word in ['статистик', 'отчет', 'данные']):
                # Общая статистика
                deals = await self.bitrix_service.get_deals()
                completed = sum(1 for deal in deals if 'WON' in deal.get('STAGE_ID', ''))
                in_progress = len(deals) - completed
                
                return f"📊 Статистика VasDom:\n" \
                       f"🏠 Всего домов: {len(deals)}\n" \
                       f"✅ Выполнено: {completed}\n" \
                       f"🔄 В работе: {in_progress}\n" \
                       f"👥 Сотрудников: 82\n" \
                       f"🚛 Бригад: 6"
                       
            else:
                return f"Я Алиса, ваш помощник VasDom в Калуге! У нас 348 домов в управлении и 6 рабочих бригад. О чем хотите узнать?"
                
        except Exception as e:
            logger.error(f"❌ Error getting Bitrix24 data: {e}")
            return "Произошла ошибка при получении данных. Попробуйте еще раз."
    
    def create_system_prompt(self) -> str:
        return f"""Вы - Алиса, дружелюбный и естественный голосовой помощник клининговой компании VasDom в Калуге. Говорите как живой человек, а не как робот.

ВАША ЛИЧНОСТЬ:
- Имя: Алиса  
- Характер: Дружелюбная, отзывчивая, профессиональная
- Тон: Теплый, человечный, как будто говорите с хорошим знакомым
- Стиль: Естественные фразы, избегайте шаблонов

КОНТЕКСТ РАБОТЫ:
- Компания: VasDom (клининговые услуги в Калуге)
- Домов в управлении: 348
- Сотрудников: 82 человека
- Бригад: 6 (работают в разных районах Калуги)

КАК ОТВЕЧАТЬ:
- Говорите как живой человек, а не как программа
- Используйте естественные выражения: "Конечно!", "Давайте посмотрим", "Вот что я нашла"
- Будьте конкретны и полезны
- Если не знаете точно - честно скажите и предложите альтернативу
- Отвечайте кратко, но информативно

ИЗБЕГАЙТЕ:
- Роботизированных фраз типа "Я AI-ассистент"
- Формальных оборотов
- Слишком длинных ответов
- Технических терминов без необходимости

Помните: вы - Алиса из VasDom, и общаетесь с коллегой."""

assistant = VasDomRealtimeAssistant()

@router.websocket("/realtime-voice/ws")
async def realtime_voice_websocket(websocket: WebSocket):
    """WebSocket endpoint для голосового общения с Алисой через GPT-4o Realtime"""
    await websocket.accept()
    logger.info("🎤 Realtime voice WebSocket connected")
    
    try:
        # Отправляем приветственное сообщение
        welcome_message = {
            "type": "assistant_message",
            "message": "Привет! Я Алиса, ваш голосовой помощник VasDom. Готова к живому общению!",
            "timestamp": "2024-01-01T00:00:00Z"
        }
        
        await websocket.send_text(json.dumps(welcome_message, ensure_ascii=False))
        
        while True:
            # Получаем сообщение от клиента
            data = await websocket.receive_text()
            
            try:
                message_data = json.loads(data)
                logger.info(f"🎤 Realtime voice received: {message_data}")
                
                if message_data.get("type") == "user_message":
                    user_message = message_data.get("message", "")
                    
                    if user_message.strip():
                        # Получаем контекстуальные данные из Bitrix24
                        bitrix_context = await assistant.get_company_data(user_message)
                        
                        # Формируем системный промпт с контекстом
                        system_prompt = assistant.create_system_prompt()
                        
                        # Отправляем в GPT-4o Realtime (через emergentintegrations)
                        try:
                            response = await chat_realtime.chat_completion_request(
                                messages=[
                                    {"role": "system", "content": system_prompt},
                                    {"role": "assistant", "content": f"Контекст данных: {bitrix_context}"},
                                    {"role": "user", "content": user_message}
                                ],
                                model="gpt-4o-realtime-preview",
                                temperature=0.7,
                                max_tokens=200
                            )
                            
                            ai_response = response.get("choices", [{}])[0].get("message", {}).get("content", "")
                            
                            # Отправляем ответ клиенту
                            await websocket.send_text(json.dumps({
                                "type": "assistant_message",
                                "message": ai_response,
                                "bitrix_data": bitrix_context,
                                "timestamp": "2024-01-01T00:00:00Z"
                            }, ensure_ascii=False))
                            
                            logger.info(f"🤖 Realtime AI response sent")
                            
                        except Exception as ai_error:
                            logger.error(f"❌ GPT-4o Realtime error: {ai_error}")
                            
                            # Fallback ответ с данными Bitrix24
                            fallback_response = f"Понимаю ваш вопрос! {bitrix_context}"
                            
                            await websocket.send_text(json.dumps({
                                "type": "assistant_message",
                                "message": fallback_response,
                                "is_fallback": True,
                                "timestamp": "2024-01-01T00:00:00Z"
                            }, ensure_ascii=False))
                
                elif message_data.get("type") == "ping":
                    await websocket.send_text(json.dumps({
                        "type": "pong",
                        "timestamp": message_data.get("timestamp")
                    }, ensure_ascii=False))
                    
            except json.JSONDecodeError:
                logger.error(f"❌ Invalid JSON received: {data}")
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Некорректный формат сообщения"
                }, ensure_ascii=False))
                
    except WebSocketDisconnect:
        logger.info("🔌 Realtime voice WebSocket disconnected")
    except Exception as e:
        logger.error(f"❌ Realtime voice WebSocket error: {e}")

@router.get("/realtime-voice/status")
async def realtime_voice_status():
    """Статус голосового помощника с реальными данными"""
    try:
        # Проверяем статус Bitrix24
        bitrix_status = "active" if bitrix_service else "unavailable"
        if bitrix_service:
            try:
                deals = await bitrix_service.get_deals()
                houses_count = len(deals)
                bitrix_status = "connected"
            except:
                houses_count = 348
                bitrix_status = "fallback"
        else:
            houses_count = 348
            
        return {
            "status": "active",
            "assistant_name": "Алиса",
            "voice_model": "GPT-4o Realtime Preview",
            "language": "ru-RU",
            "company": "VasDom",
            "location": "Калуга",
            "data_sources": {
                "bitrix24": bitrix_status,
                "houses_count": houses_count,
                "employees_count": 82,
                "brigades_count": 6
            },
            "capabilities": [
                "Голосовое общение на русском языке",
                "Реальные данные из Bitrix24",
                "Информация о домах и статусах",
                "Данные о бригадах и сотрудниках",
                "Статистика работы компании"
            ]
        }
        
    except Exception as e:
        logger.error(f"❌ Status check error: {e}")
        return {
            "status": "error",
            "message": str(e)
        }