"""
API роутер для мониторинга статуса автоматической обработки звонков Novofon
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import Dict, Any
import logging

from backend.app.config.database import get_db
from backend.app.services.scheduler import get_scheduler_status

router = APIRouter(prefix="/novofon-status", tags=["Novofon Status"])
logger = logging.getLogger(__name__)


@router.get("/scheduler")
async def get_scheduler_info():
    """
    Получить статус scheduler (планировщика задач)
    """
    try:
        status = get_scheduler_status()
        return {
            "success": True,
            "scheduler": status
        }
    except Exception as e:
        logger.error(f"Error getting scheduler status: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/stats")
async def get_processing_stats(db: AsyncSession = Depends(get_db)):
    """
    Получить статистику обработанных звонков
    """
    try:
        # Общая статистика
        result = await db.execute(text("""
            SELECT 
                COUNT(*) as total_calls,
                COUNT(*) FILTER (WHERE success = TRUE) as successful,
                COUNT(*) FILTER (WHERE success = FALSE) as failed
            FROM processed_calls
        """))
        stats = result.fetchone()
        
        # Последние обработанные звонки
        result = await db.execute(text("""
            SELECT call_id, processed_at, success
            FROM processed_calls
            ORDER BY processed_at DESC
            LIMIT 10
        """))
        recent_calls = result.fetchall()
        
        return {
            "success": True,
            "stats": {
                "total_calls": stats[0] if stats else 0,
                "successful": stats[1] if stats else 0,
                "failed": stats[2] if stats else 0
            },
            "recent_calls": [
                {
                    "call_id": row[0],
                    "processed_at": row[1].isoformat() if row[1] else None,
                    "success": row[2]
                }
                for row in recent_calls
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return {
            "success": False,
            "error": str(e),
            "stats": {
                "total_calls": 0,
                "successful": 0,
                "failed": 0
            },
            "recent_calls": []
        }


@router.get("/nedvigka-calls")
async def get_nedvigka_calls(
    limit: int = 20,
    db: AsyncSession = Depends(get_db)
):
    """
    Получить историю звонков по недвижимости
    """
    try:
        result = await db.execute(
            text("""
                SELECT 
                    id, call_id, caller, called, direction, duration,
                    agency_name, lead_category, interest_rating, priority,
                    created_at
                FROM nedvigka_calls
                ORDER BY created_at DESC
                LIMIT :limit
            """),
            {"limit": limit}
        )
        
        calls = result.fetchall()
        
        calls_list = []
        for row in calls:
            calls_list.append({
                "id": row[0],
                "call_id": row[1],
                "caller": row[2],
                "called": row[3],
                "direction": row[4],
                "duration": row[5],
                "agency_name": row[6],
                "lead_category": row[7],
                "interest_rating": row[8],
                "priority": row[9],
                "created_at": row[10].isoformat() if row[10] else None
            })
        
        return {
            "success": True,
            "total": len(calls_list),
            "calls": calls_list
        }
        
    except Exception as e:
        logger.error(f"Error getting nedvigka calls: {e}")
        return {
            "success": False,
            "error": str(e),
            "total": 0,
            "calls": []
        }


@router.get("/call-detail/{call_id}")
async def get_call_detail(call_id: str, db: AsyncSession = Depends(get_db)):
    """
    Получить полную информацию о звонке
    """
    try:
        result = await db.execute(
            text("""
                SELECT 
                    id, call_id, caller, called, direction, duration,
                    transcription, analysis, agency_name, lead_category,
                    interest_rating, priority, created_at
                FROM nedvigka_calls
                WHERE call_id = :call_id
            """),
            {"call_id": call_id}
        )
        
        row = result.fetchone()
        
        if not row:
            return {
                "success": False,
                "error": "Call not found"
            }
        
        import json
        
        return {
            "success": True,
            "call": {
                "id": row[0],
                "call_id": row[1],
                "caller": row[2],
                "called": row[3],
                "direction": row[4],
                "duration": row[5],
                "transcription": row[6],
                "analysis": json.loads(row[7]) if row[7] else {},
                "agency_name": row[8],
                "lead_category": row[9],
                "interest_rating": row[10],
                "priority": row[11],
                "created_at": row[12].isoformat() if row[12] else None
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting call detail: {e}")
        return {
            "success": False,
            "error": str(e)
        }
