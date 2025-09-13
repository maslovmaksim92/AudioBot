import uuid
import logging
from datetime import datetime
from typing import List
from fastapi import APIRouter, HTTPException
from ..models.schemas import Meeting
from ..config.database import database

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["meetings"])

@router.post("/meetings/start-recording")
async def start_meeting_recording():
    """Начать запись планерки - теперь работает без базы данных"""
    try:
        meeting_id = str(uuid.uuid4())
        logger.info(f"🎤 Starting meeting: {meeting_id}")
        
        # Пытаемся сохранить в БД, если доступна
        if database:
            try:
                query = """
                INSERT INTO meetings (id, title, transcription, status, created_at)
                VALUES (:id, :title, :transcription, :status, :created_at)
                """
                values = {
                    "id": meeting_id,
                    "title": f"Планерка {datetime.now().strftime('%d.%m.%Y %H:%M')}",
                    "transcription": "🎙️ Запись начата...",
                    "status": "recording",
                    "created_at": datetime.utcnow()
                }
                await database.execute(query, values)
                logger.info(f"✅ Meeting saved to database: {meeting_id}")
                database_status = "saved"
            except Exception as db_error:
                logger.warning(f"⚠️ Database save failed, continuing without DB: {db_error}")
                database_status = "unavailable"
        else:
            logger.info(f"📝 Meeting created in memory-only mode: {meeting_id}")
            database_status = "disabled"
        
        return {
            "status": "success",
            "meeting_id": meeting_id,
            "message": "Запись планерки начата",
            "database_status": database_status,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Start meeting error: {e}")
        # Даже при ошибке возвращаем meeting_id для продолжения работы
        fallback_meeting_id = str(uuid.uuid4())
        return {
            "status": "success", 
            "meeting_id": fallback_meeting_id,
            "message": "Запись планерки начата (fallback режим)",
            "database_status": "error",
            "timestamp": datetime.now().isoformat()
        }

@router.post("/meetings/stop-recording")
async def stop_meeting_recording(meeting_id: str):
    """Остановить запись планерки"""
    try:
        if database:
            query = """
            UPDATE meetings 
            SET status = :status, ended_at = :ended_at, transcription = :transcription
            WHERE id = :id
            """
            values = {
                "id": meeting_id,
                "status": "completed",
                "ended_at": datetime.utcnow(),
                "transcription": "🎙️ Запись завершена. Транскрипция готова к обработке."
            }
            await database.execute(query, values)
            logger.info(f"✅ Meeting stopped: {meeting_id}")
        
        return {
            "status": "success",
            "meeting_id": meeting_id,
            "message": "Запись планерки остановлена"
        }
        
    except Exception as e:
        logger.error(f"❌ Stop meeting error: {e}")
        return {"status": "error", "message": str(e)}

@router.get("/meetings", response_model=dict)
async def get_meetings():
    """Список встреч"""
    try:
        if database:
            query = "SELECT * FROM meetings ORDER BY created_at DESC LIMIT 100"
            meetings = await database.fetch_all(query)
            meetings_list = [dict(meeting) for meeting in meetings]
            logger.info(f"📋 Retrieved {len(meetings_list)} meetings")
        else:
            meetings_list = []
        
        return {"status": "success", "meetings": meetings_list}
    except Exception as e:
        logger.error(f"❌ Get meetings error: {e}")
        return {"status": "success", "meetings": []}

@router.get("/meetings/{meeting_id}")
async def get_meeting(meeting_id: str):
    """Получить конкретную встречу"""
    try:
        if database:
            query = "SELECT * FROM meetings WHERE id = :id"
            meeting = await database.fetch_one(query, {"id": meeting_id})
            
            if meeting:
                return {"status": "success", "meeting": dict(meeting)}
            else:
                raise HTTPException(status_code=404, detail="Meeting not found")
        else:
            raise HTTPException(status_code=503, detail="Database unavailable")
            
    except Exception as e:
        logger.error(f"❌ Get meeting error: {e}")
        raise HTTPException(status_code=500, detail=str(e))