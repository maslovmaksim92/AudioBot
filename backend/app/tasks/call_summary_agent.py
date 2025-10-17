"""
Агент для автоматической обработки звонков из Novofon и Bitrix24
Проверяет новые звонки каждые 5 минут и создаёт саммари
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Set

from backend.app.services.bitrix_calls_service import BitrixCallsService
from backend.app.services.novofon_service import novofon_service
from backend.app.routers.call_summary import process_call_recording

logger = logging.getLogger(__name__)

# Храним ID обработанных звонков, чтобы не обрабатывать дважды
processed_calls: Set[str] = set()

class CallSummaryAgent:
    def __init__(self):
        self.bitrix_service = BitrixCallsService()
        self.novofon_service = novofon_service
        self.is_running = False
    
    async def check_and_process_calls(self):
        """
        Проверяет новые звонки из Novofon и Bitrix24 и создаёт саммари
        """
        try:
            if self.is_running:
                logger.info("⏭️ Previous task still running, skipping...")
                return
            
            self.is_running = True
            logger.info("🔍 Checking for new calls to process...")
            
            processed_count = 0
            
            # 1. Обработка звонков из Novofon (приоритет)
            try:
                novofon_calls = await self.novofon_service.get_calls(
                    start_date=datetime.now() - timedelta(hours=2),
                    limit=50,
                    is_recorded=True
                )
                
                if novofon_calls:
                    logger.info(f"📞 Found {len(novofon_calls)} calls from Novofon")
                    for call in novofon_calls:
                        call_id = f"novofon_{call.get('id', call.get('call_id'))}"
                        
                        if call_id in processed_calls:
                            continue
                        
                        try:
                            await self.process_novofon_call(call)
                            processed_calls.add(call_id)
                            processed_count += 1
                            await asyncio.sleep(2)
                        except Exception as e:
                            logger.error(f"❌ Failed to process Novofon call {call_id}: {e}")
            except Exception as e:
                logger.error(f"❌ Error fetching Novofon calls: {e}")
            
            # 2. Обработка звонков из Bitrix24 (резервный источник)
            try:
                bitrix_calls = await self.bitrix_service.get_recent_calls(limit=20)
                
                if bitrix_calls:
                    logger.info(f"📞 Found {len(bitrix_calls)} calls from Bitrix24")
                    for call in bitrix_calls:
                        call_id = f"bitrix_{call.get('CALL_ID')}"
                        
                        if call_id in processed_calls:
                            continue
                        
                        has_record = bool(call.get("RECORD_FILE_ID"))
                        duration = int(call.get("CALL_DURATION", 0))
                        call_status = call.get("CALL_STATUS")
                        
                        if not has_record or duration < 10 or call_status != "200":
                            processed_calls.add(call_id)
                            continue
                        
                        try:
                            await self.process_single_call(call)
                            processed_calls.add(call_id)
                            processed_count += 1
                            await asyncio.sleep(2)
                        except Exception as e:
                            logger.error(f"❌ Failed to process Bitrix call {call_id}: {e}")
            except Exception as e:
                logger.error(f"❌ Error fetching Bitrix24 calls: {e}")
            
            if processed_count > 0:
                logger.info(f"✅ Processed {processed_count} calls total")
            else:
                logger.info("📭 No new calls to process")
            
            # Очищаем старые ID из памяти
            if len(processed_calls) > 1000:
                logger.info("🧹 Cleaning old call IDs from memory...")
                processed_calls.clear()
            
        except Exception as e:
            logger.error(f"❌ Error in call summary agent: {e}")
            import traceback
            logger.error(traceback.format_exc())
        finally:
            self.is_running = False
    
    async def process_single_call(self, call: dict):
        """
        Обработать один звонок из Bitrix24
        """
        call_id = call.get("CALL_ID")
        
        # Получаем ссылку на запись
        recording_url = await self.bitrix_service.get_call_recording(call_id)
        
        if not recording_url:
            raise Exception(f"Failed to get recording URL for call {call_id}")
        
        # Формируем данные для обработки
        webhook_data = {
            "call_id": call_id,
            "caller": call.get("PHONE_NUMBER", ""),
            "called": "",  # Не всегда доступно в Bitrix24
            "direction": "in" if call.get("CALL_TYPE") == "1" else "out",
            "duration": int(call.get("CALL_DURATION", 0)),
            "status": "answered",
            "record_url": recording_url,
            "timestamp": call.get("CALL_START_DATE")
        }
        
        # Обрабатываем (транскрипция + саммари + отправка)
        await process_call_recording(webhook_data, None)
    
    async def process_novofon_call(self, call: dict):
        """
        Обработать один звонок из Novofon
        """
        call_id = call.get("id") or call.get("call_id")
        
        logger.info(f"🎙️ Processing Novofon call {call_id}")
        
        # Проверяем условия
        duration = int(call.get("duration", 0))
        status = call.get("status", "")
        
        if duration < 10:
            logger.debug(f"⏭️ Call {call_id}: too short ({duration}s)")
            return
        
        # Получаем URL записи
        recording_url = call.get("recording_url") or await self.novofon_service.get_call_recording_url(call_id)
        
        if not recording_url:
            logger.warning(f"⚠️ No recording URL for call {call_id}")
            return
        
        # Формируем данные для обработки
        webhook_data = {
            "call_id": f"novofon_{call_id}",
            "caller": call.get("caller", call.get("from", "")),
            "called": call.get("called", call.get("to", "")),
            "direction": call.get("direction", "in"),
            "duration": duration,
            "status": status,
            "record_url": recording_url,
            "timestamp": call.get("start_time", call.get("timestamp", datetime.now().isoformat()))
        }
        
        # Обрабатываем (транскрипция + саммари + отправка)
        await process_call_recording(webhook_data, None)
        logger.info(f"✅ Successfully processed Novofon call {call_id}")

# Глобальный экземпляр агента
call_summary_agent = CallSummaryAgent()

async def run_call_summary_agent():
    """
    Функция для запуска агента (вызывается из scheduler)
    """
    await call_summary_agent.check_and_process_calls()
