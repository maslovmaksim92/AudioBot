"""
API роутер для тестирования уведомлений и звонков
"""
from fastapi import APIRouter, HTTPException
from typing import Optional
import logging

from backend.app.tasks.scheduler import task_scheduler

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/notifications", tags=["Notifications"])

@router.post("/test/plannerka")
async def test_plannerka_notification():
    """
    Тестовая отправка уведомления о планерке
    """
    try:
        await task_scheduler.send_plannerka_reminder()
        return {
            "success": True,
            "message": "Notification sent successfully"
        }
    except Exception as e:
        logger.error(f"Error sending test notification: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/test/ai-call")
async def test_ai_call_report():
    """
    Тестовый AI звонок для сбора отчётности
    """
    try:
        await task_scheduler.ai_call_employees()
        return {
            "success": True,
            "message": "AI call initiated successfully"
        }
    except Exception as e:
        logger.error(f"Error initiating test AI call: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/schedule")
async def get_schedule():
    """
    Получить расписание всех запланированных задач
    """
    try:
        jobs = task_scheduler.scheduler.get_jobs()
        schedule = []
        
        for job in jobs:
            schedule.append({
                "id": job.id,
                "name": job.name,
                "next_run": str(job.next_run_time) if job.next_run_time else None,
                "trigger": str(job.trigger)
            })
        
        return {
            "success": True,
            "total_jobs": len(schedule),
            "schedule": schedule
        }
    except Exception as e:
        logger.error(f"Error getting schedule: {e}")
        raise HTTPException(status_code=500, detail=str(e))
