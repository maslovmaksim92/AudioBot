"""
Тестовый endpoint для запуска агента вручную
"""
from fastapi import APIRouter
import logging

router = APIRouter(prefix="/test-agent", tags=["Test Agent"])
logger = logging.getLogger(__name__)

@router.post("/run-call-agent")
async def run_call_agent_now():
    """
    Запустить агент обработки звонков прямо сейчас (для тестирования)
    """
    try:
        from backend.app.tasks.call_summary_agent import run_call_summary_agent
        
        logger.info("🚀 Manually triggering call summary agent...")
        
        # Запускаем агента
        await run_call_summary_agent()
        
        return {
            "status": "success",
            "message": "Agent executed successfully. Check logs for details."
        }
        
    except Exception as e:
        logger.error(f"Error running agent: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            "status": "error",
            "message": str(e)
        }
