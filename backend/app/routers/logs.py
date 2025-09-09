import logging
from datetime import datetime
from fastapi import APIRouter
from ..config.database import database

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["logs"])

@router.get("/logs")
async def get_logs():
    """Системные логи"""
    try:
        if database:
            query = "SELECT * FROM voice_logs ORDER BY timestamp DESC LIMIT 50"
            logs = await database.fetch_all(query)
            logs_list = [dict(log) for log in logs]
            logger.info(f"📋 Retrieved {len(logs_list)} logs")
        else:
            logs_list = []
        
        return {
            "status": "success",
            "voice_logs": logs_list,
            "total": len(logs_list),
            "database": "PostgreSQL" if database else "disabled"
        }
    except Exception as e:
        logger.error(f"❌ Logs error: {e}")
        return {"status": "success", "voice_logs": [], "total": 0}

@router.get("/logs/ai")
async def get_ai_logs():
    """AI логи для самообучения"""
    try:
        if database:
            query = """
            SELECT user_message, ai_response, context, timestamp 
            FROM voice_logs 
            WHERE context LIKE 'AI_%' 
            ORDER BY timestamp DESC 
            LIMIT 20
            """
            logs = await database.fetch_all(query)
            logs_list = [dict(log) for log in logs]
            logger.info(f"🤖 Retrieved {len(logs_list)} AI logs")
        else:
            logs_list = []
        
        return {
            "status": "success",
            "ai_logs": logs_list,
            "total": len(logs_list),
            "purpose": "self_learning_analysis"
        }
    except Exception as e:
        logger.error(f"❌ AI logs error: {e}")
        return {"status": "success", "ai_logs": [], "total": 0}

@router.get("/logs/telegram")
async def get_telegram_logs():
    """Telegram логи"""
    try:
        if database:
            query = """
            SELECT user_message, ai_response, context, timestamp 
            FROM voice_logs 
            WHERE context LIKE 'telegram_%' 
            ORDER BY timestamp DESC 
            LIMIT 20
            """
            logs = await database.fetch_all(query)
            logs_list = [dict(log) for log in logs]
            logger.info(f"📱 Retrieved {len(logs_list)} Telegram logs")
        else:
            logs_list = []
        
        return {
            "status": "success",
            "telegram_logs": logs_list,
            "total": len(logs_list)
        }
    except Exception as e:
        logger.error(f"❌ Telegram logs error: {e}")
        return {"status": "success", "telegram_logs": [], "total": 0}