"""
API роутер для AI ассистента
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging

from backend.app.services.ai_assistant import ai_assistant

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai-assistant", tags=["AI Assistant"])

class ChatRequest(BaseModel):
    """Запрос к AI ассистенту"""
    message: str
    conversation_history: Optional[List[Dict[str, str]]] = None
    voice_mode: bool = False

class AnalysisRequest(BaseModel):
    """Запрос на анализ данных"""
    analysis_type: str  # financial, performance, predictions

@router.post("/chat")
async def chat_with_assistant(request: ChatRequest):
    """
    Чат с AI ассистентом
    
    Ассистент знает о:
    - Домах и их статусах
    - Сотрудниках
    - Финансах
    - Агентах автоматизации
    """
    try:
        result = await ai_assistant.chat(
            user_query=request.message,
            conversation_history=request.conversation_history,
            voice_mode=request.voice_mode
        )
        
        return result
    
    except Exception as e:
        logger.error(f"❌ Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze")
async def analyze_data(request: AnalysisRequest):
    """
    Автоматический анализ данных
    
    Типы анализа:
    - financial: Финансовый анализ (прибыль, ROI, соотношения)
    - performance: Анализ производительности (дома, агенты)
    - predictions: Прогнозы и рекомендации
    """
    try:
        result = await ai_assistant.analyze_data(request.analysis_type)
        return result
    
    except Exception as e:
        logger.error(f"❌ Analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/context")
async def get_context():
    """
    Получить текущий контекст системы
    
    Возвращает данные о домах, сотрудниках, финансах, агентах
    """
    try:
        context = await ai_assistant.get_context("")
        return {
            'success': True,
            'context': context
        }
    
    except Exception as e:
        logger.error(f"❌ Context error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
