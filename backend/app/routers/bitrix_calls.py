"""
API роутер для работы со звонками из Bitrix24
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Dict, Any, Optional
import logging

from backend.app.services.bitrix_calls_service import BitrixCallsService

router = APIRouter(prefix="/bitrix-calls", tags=["Bitrix24 Calls"])
logger = logging.getLogger(__name__)

bitrix_calls_service = BitrixCallsService()

@router.get("/recent")
async def get_recent_calls(limit: int = 50):
    """
    Получить последние звонки из Bitrix24
    """
    try:
        calls = await bitrix_calls_service.get_recent_calls(limit)
        
        # Форматируем для фронтенда
        formatted_calls = [
            bitrix_calls_service.format_call_info(call)
            for call in calls
        ]
        
        return {
            "total": len(formatted_calls),
            "calls": formatted_calls
        }
        
    except Exception as e:
        logger.error(f"Error getting recent calls: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/call/{call_id}")
async def get_call_details(call_id: str):
    """
    Получить детали конкретного звонка
    """
    try:
        call = await bitrix_calls_service.get_call_details(call_id)
        
        if not call:
            raise HTTPException(status_code=404, detail="Call not found")
        
        return bitrix_calls_service.format_call_info(call)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting call details: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/call/{call_id}/recording")
async def get_call_recording_url(call_id: str):
    """
    Получить ссылку на запись звонка
    """
    try:
        recording_url = await bitrix_calls_service.get_call_recording(call_id)
        
        if not recording_url:
            raise HTTPException(status_code=404, detail="Recording not found")
        
        return {
            "call_id": call_id,
            "recording_url": recording_url
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting recording URL: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search")
async def search_calls(phone: str):
    """
    Поиск звонков по номеру телефона
    """
    try:
        calls = await bitrix_calls_service.search_calls_by_phone(phone)
        
        formatted_calls = [
            bitrix_calls_service.format_call_info(call)
            for call in calls
        ]
        
        return {
            "phone": phone,
            "total": len(formatted_calls),
            "calls": formatted_calls
        }
        
    except Exception as e:
        logger.error(f"Error searching calls: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/process/{call_id}")
async def process_call_from_bitrix(
    call_id: str,
    background_tasks: BackgroundTasks
):
    """
    Создать саммари для звонка из Bitrix24
    """
    try:
        # Получаем детали звонка
        call = await bitrix_calls_service.get_call_details(call_id)
        
        if not call:
            raise HTTPException(status_code=404, detail="Call not found")
        
        # Получаем запись
        recording_url = await bitrix_calls_service.get_call_recording(call_id)
        
        if not recording_url:
            raise HTTPException(status_code=404, detail="Recording not found")
        
        # Формируем webhook данные для обработки
        from backend.app.routers.call_summary import process_call_recording
        
        webhook_data = {
            "call_id": call.get("CALL_ID", call_id),
            "caller": call.get("PHONE_NUMBER", ""),
            "called": "",  # TODO: получить из Bitrix24
            "direction": "in" if call.get("CALL_TYPE") == "1" else "out",
            "duration": int(call.get("CALL_DURATION", 0)),
            "status": "answered",
            "record_url": recording_url
        }
        
        # Добавляем в фоновую обработку
        background_tasks.add_task(
            process_call_recording,
            webhook_data,
            None  # db session
        )
        
        return {
            "status": "processing",
            "call_id": call_id,
            "message": "Саммари создаётся в фоновом режиме"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing call: {e}")
        raise HTTPException(status_code=500, detail=str(e))
