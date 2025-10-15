"""
Webhook от Bitrix24 для автоматической обработки звонков
"""
from fastapi import APIRouter, BackgroundTasks, Request
from typing import Dict, Any
import logging

from backend.app.services.bitrix_calls_service import BitrixCallsService

router = APIRouter(prefix="/bitrix-webhook", tags=["Bitrix24 Webhook"])
logger = logging.getLogger(__name__)

bitrix_calls_service = BitrixCallsService()

@router.post("/call-finished")
async def bitrix_call_finished_webhook(
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Webhook от Bitrix24 при завершении звонка
    Автоматически создаёт саммари и отправляет в Telegram
    """
    try:
        # Получаем данные от Bitrix24
        data = await request.json()
        
        logger.info(f"📞 Received call webhook from Bitrix24: {data}")
        
        # Bitrix24 отправляет данные в формате:
        # {
        #   "event": "ONVOXIMPLANTCALLEND",
        #   "data": {
        #     "CALL_ID": "...",
        #     "CALL_TYPE": "1" (1=входящий, 2=исходящий),
        #     "PHONE_NUMBER": "+7...",
        #     "CALL_DURATION": "123",
        #     "CALL_START_DATE": "...",
        #     "RECORD_FILE_ID": "123" (если есть запись)
        #   }
        # }
        
        event = data.get("event")
        call_data = data.get("data", {})
        
        # Проверяем что это событие завершения звонка
        if event != "ONVOXIMPLANTCALLEND":
            logger.info(f"⏭️ Ignoring event: {event}")
            return {"status": "ignored", "reason": "not_call_end_event"}
        
        call_id = call_data.get("CALL_ID")
        record_file_id = call_data.get("RECORD_FILE_ID")
        call_duration = int(call_data.get("CALL_DURATION", 0))
        
        # Проверяем есть ли запись и длительность больше 10 секунд
        if not record_file_id:
            logger.info(f"⏭️ No recording for call {call_id}")
            return {"status": "skipped", "reason": "no_recording"}
        
        if call_duration < 10:
            logger.info(f"⏭️ Call too short: {call_duration} seconds")
            return {"status": "skipped", "reason": "call_too_short"}
        
        # Добавляем в фоновую обработку
        background_tasks.add_task(
            process_bitrix_call,
            call_id,
            call_data
        )
        
        logger.info(f"✅ Call {call_id} queued for processing")
        
        return {
            "status": "accepted",
            "call_id": call_id,
            "message": "Call queued for processing"
        }
        
    except Exception as e:
        logger.error(f"❌ Error processing Bitrix webhook: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {"status": "error", "message": str(e)}

async def process_bitrix_call(call_id: str, call_data: Dict[str, Any]):
    """
    Фоновая обработка звонка из Bitrix24
    """
    try:
        logger.info(f"🎙️ Processing Bitrix call: {call_id}")
        
        # 1. Получаем полные детали звонка
        call_details = await bitrix_calls_service.get_call_details(call_id)
        
        if not call_details:
            logger.error(f"❌ Failed to get call details for {call_id}")
            return
        
        # 2. Получаем ссылку на запись
        recording_url = await bitrix_calls_service.get_call_recording(call_id)
        
        if not recording_url:
            logger.error(f"❌ Failed to get recording URL for {call_id}")
            return
        
        logger.info(f"✅ Got recording URL for {call_id}")
        
        # 3. Формируем данные для обработки
        from backend.app.routers.call_summary import process_call_recording
        
        webhook_data = {
            "call_id": call_id,
            "caller": call_data.get("PHONE_NUMBER", ""),
            "called": "",  # Bitrix не всегда предоставляет
            "direction": "in" if call_data.get("CALL_TYPE") == "1" else "out",
            "duration": int(call_data.get("CALL_DURATION", 0)),
            "status": "answered",
            "record_url": recording_url,
            "timestamp": call_data.get("CALL_START_DATE")
        }
        
        # 4. Обрабатываем (создаём саммари, отправляем в Telegram, сохраняем в БД)
        await process_call_recording(webhook_data, None)
        
        logger.info(f"✅ Successfully processed call {call_id}")
        
    except Exception as e:
        logger.error(f"❌ Error processing Bitrix call {call_id}: {e}")
        import traceback
        logger.error(traceback.format_exc())

@router.get("/test")
async def test_webhook():
    """
    Тестовый endpoint для проверки работы webhook
    """
    return {
        "status": "ok",
        "message": "Bitrix webhook endpoint is working",
        "webhook_url": "/api/bitrix-webhook/call-finished"
    }
