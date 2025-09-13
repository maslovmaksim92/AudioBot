import logging
import uuid
from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from ..config.mongodb import get_mongo_db, Collections

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/ai", tags=["ai-chat"])

class ChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
    timestamp: str

@router.post("/chat", response_model=ChatResponse)
async def chat_with_ai(chat_message: ChatMessage):
    """Основной endpoint для AI чата"""
    try:
        # Генерируем session_id если не передан
        session_id = chat_message.session_id or str(uuid.uuid4())
        
        # Получаем MongoDB
        db = await get_mongo_db()
        
        if db is not None:
            # Сохраняем сообщение пользователя
            await db[Collections.CHAT_SESSIONS].insert_one({
                "session_id": session_id,
                "type": "user",
                "message": chat_message.message,
                "timestamp": datetime.utcnow()
            })
        
        # Простой AI ответ (заглушка для демонстрации)
        user_msg = chat_message.message.lower()
        
        if "дом" in user_msg or "квартир" in user_msg:
            ai_response = f"У нас в управлении 490 домов и 50,960 квартир. Могу предоставить детальную информацию по любому объекту. Что именно вас интересует?"
        elif "сотрудник" in user_msg or "бригад" in user_msg:
            ai_response = f"В VasDom работает 82 сотрудника в 6 бригадах по районам: Центральный, Никитинский, Желетово, Северный, Пригород и Окраины. Нужна информация по конкретной бригаде?"
        elif "планерк" in user_msg:
            ai_response = f"Система записи планерок готова к работе. Можете начать запись через раздел 'Планерки'. Автоматически создается транскрипт и AI-анализ."
        elif "привет" in user_msg or "здравствуй" in user_msg:
            ai_response = f"Привет! Я VasDom AI, ваш помощник по управлению клининговой компанией. У меня есть актуальная информация по 490 домам, 82 сотрудникам и всем процессам. Чем помочь?"
        elif "стат" in user_msg or "показат" in user_msg:
            ai_response = f"📊 Текущая статистика VasDom:\n• 490 домов в управлении\n• 50,960 квартир\n• 1,592 подъезда\n• 4,165 этажей\n• 82 сотрудника в 6 бригадах\n\nВсе данные синхронизированы с Bitrix24 CRM."
        else:
            ai_response = f"Спасибо за вопрос! Я VasDom AI и помогаю с управлением нашей клининговой компанией. У нас 490 домов, 82 сотрудника в 6 бригадах. Могу рассказать о домах, сотрудниках, планерках или помочь с другими вопросами. Что вас интересует?"
        
        # Сохраняем ответ AI
        if db is not None:
            await db[Collections.CHAT_SESSIONS].insert_one({
                "session_id": session_id,
                "type": "ai",
                "message": ai_response,
                "timestamp": datetime.utcnow()
            })
        
        return ChatResponse(
            response=ai_response,
            session_id=session_id,
            timestamp=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        logger.error(f"AI Chat error: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при обработке сообщения")

@router.get("/chat/history/{session_id}")
async def get_chat_history(session_id: str):
    """Получить историю чата"""
    try:
        db = await get_mongo_db()
        
        if db is None:
            return {"messages": [], "error": "Database unavailable"}
        
        # Получаем историю сообщений
        cursor = db[Collections.CHAT_SESSIONS].find({
            "session_id": session_id
        }).sort("timestamp", 1)
        
        messages = []
        async for doc in cursor:
            messages.append({
                "type": doc["type"],
                "message": doc["message"],
                "timestamp": doc["timestamp"].isoformat()
            })
        
        return {"messages": messages}
        
    except Exception as e:
        logger.error(f"Chat history error: {e}")
        return {"messages": [], "error": str(e)}

@router.post("/analyze-meeting")
async def analyze_meeting(data: dict):
    """Анализ планерки (для MeetingRecorder)"""
    try:
        transcript = data.get("transcript", "")
        
        if not transcript.strip():
            raise HTTPException(status_code=400, detail="Пустой транскрипт")
        
        # Простой анализ текста
        words = transcript.split()
        word_count = len(words)
        
        # Определяем ключевые темы
        themes = []
        if any(word in transcript.lower() for word in ["дом", "квартир", "подъезд"]):
            themes.append("Управление домами")
        if any(word in transcript.lower() for word in ["сотрудник", "бригад", "работник"]):
            themes.append("Кадровые вопросы")
        if any(word in transcript.lower() for word in ["план", "задач", "цель"]):
            themes.append("Планирование")
        if any(word in transcript.lower() for word in ["проблем", "ошибк", "сбой"]):
            themes.append("Проблемы")
        
        # Создаем summary
        summary = f"""🎤 АНАЛИЗ ПЛАНЕРКИ

📊 Статистика:
• Длительность транскрипта: {word_count} слов
• Примерное время: {word_count // 150} минут

🎯 Основные темы:
{chr(10).join([f"• {theme}" for theme in themes]) if themes else "• Общие вопросы"}

📝 Краткое содержание:
{transcript[:200]}{'...' if len(transcript) > 200 else ''}

✅ Рекомендации:
• Зафиксировать обсуждённые вопросы в системе
• Назначить ответственных за выполнение задач
• Запланировать следующую планёрку"""

        # Сохраняем в БД
        db = await get_mongo_db()
        if db is not None:
            await db[Collections.MEETINGS].insert_one({
                "transcript": transcript,
                "analysis": summary,
                "themes": themes,
                "word_count": word_count,
                "timestamp": datetime.utcnow()
            })
        
        return {
            "summary": summary,
            "themes": themes,
            "word_count": word_count,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Meeting analysis error: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при анализе планерки")