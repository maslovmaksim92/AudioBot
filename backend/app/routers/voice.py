import logging
from fastapi import APIRouter, HTTPException, Depends
from ..models.schemas import VoiceMessage, ChatResponse
from ..services.ai_service import AIService
from ..security import optional_auth

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["voice"])

# Initialize AI service
ai_service = AIService()

@router.post("/voice/process", response_model=ChatResponse)
async def process_voice_message(
    message: VoiceMessage,
    authenticated: bool = Depends(optional_auth)
):
    """Голосовое взаимодействие с AI с опциональной аутентификацией"""
    try:
        logger.info(f"🎤 Voice: '{message.text[:50]}...' (auth: {authenticated})")
        
        response = await ai_service.process_message(message.text, message.user_id)
        
        return ChatResponse(response=response)
        
    except Exception as e:
        logger.error(f"❌ Voice error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Извините, произошла ошибка при обработке голосового сообщения"
        )

@router.get("/self-learning/status")
async def get_self_learning_status():
    """Статус системы самообучения"""
    try:
        from ..services.ai_service import EMERGENT_AVAILABLE
        from ..config.settings import EMERGENT_LLM_KEY
        from ..config.database import database
        
        emergent_status = "available" if EMERGENT_AVAILABLE else "fallback"
        emergent_key_present = bool(EMERGENT_LLM_KEY)
        
        if database:
            try:
                query = "SELECT COUNT(*) as count FROM voice_logs WHERE context LIKE 'AI_%'"
                logs_result = await database.fetch_one(query)
                ai_interactions = logs_result['count'] if logs_result else 0
            except:
                ai_interactions = 0
            
            return {
                "status": "active",
                "emergent_llm": {
                    "package_available": EMERGENT_AVAILABLE,
                    "key_present": emergent_key_present,
                    "mode": "GPT-4 mini" if EMERGENT_AVAILABLE and emergent_key_present else "Advanced Fallback"
                },
                "ai_interactions": ai_interactions,
                "database": "connected",
                "crm_integration": "centralized"  # Новое поле
            }
        else:
            return {
                "status": "database_disabled",
                "emergent_llm": {
                    "package_available": EMERGENT_AVAILABLE,
                    "key_present": emergent_key_present,
                    "mode": "Fallback AI (no database)"
                },
                "message": "База данных отключена, самообучение недоступно"
            }
    except Exception as e:
        logger.error(f"❌ Self-learning status error: {e}")
        return {
            "status": "error",
            "message": str(e)
        }

@router.post("/self-learning/test")
async def test_self_learning():
    """Тест системы самообучения"""
    try:
        # Отправляем тестовое сообщение через AI
        test_message = "Тест системы самообучения VasDom AudioBot"
        ai_response = await ai_service.process_message(test_message, "self_learning_test")
        
        return {
            "status": "success",
            "test_message": test_message,
            "ai_response": ai_response,
            "message": "✅ Тест самообучения выполнен. Проверьте /api/logs для подтверждения сохранения."
        }
    except Exception as e:
        logger.error(f"❌ Self-learning test error: {e}")
        return {
            "status": "error",
            "message": str(e)
        }