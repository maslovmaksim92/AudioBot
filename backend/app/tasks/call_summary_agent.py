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
        self.is_running = False
    
    async def check_and_process_calls(self):
        """
        Проверяет новые звонки и создаёт саммари
        """
        try:
            if self.is_running:
                logger.info("⏭️ Previous task still running, skipping...")
                return
            
            self.is_running = True
            logger.info("🔍 Checking for new calls to process...")
            
            # Получаем последние звонки за последние 2 часа
            calls = await self.bitrix_service.get_recent_calls(limit=20)
            
            if not calls:
                logger.info("📭 No calls found")
                self.is_running = False
                return
            
            processed_count = 0
            
            for call in calls:
                call_id = call.get("CALL_ID")
                
                # Пропускаем уже обработанные
                if call_id in processed_calls:
                    continue
                
                # Проверяем условия
                has_record = bool(call.get("RECORD_FILE_ID"))
                duration = int(call.get("CALL_DURATION", 0))
                call_status = call.get("CALL_STATUS")
                
                # Только звонки с записью, длительностью > 10 сек и отвеченные
                if not has_record:
                    logger.debug(f"⏭️ Call {call_id}: no recording")
                    processed_calls.add(call_id)  # Помечаем чтобы больше не проверять
                    continue
                
                if duration < 10:
                    logger.debug(f"⏭️ Call {call_id}: too short ({duration}s)")
                    processed_calls.add(call_id)
                    continue
                
                if call_status != "200":  # 200 = answered
                    logger.debug(f"⏭️ Call {call_id}: not answered (status: {call_status})")
                    processed_calls.add(call_id)
                    continue
                
                # Обрабатываем звонок
                logger.info(f"🎙️ Processing call {call_id} ({duration}s)")
                
                try:
                    await self.process_single_call(call)
                    processed_calls.add(call_id)
                    processed_count += 1
                    logger.info(f"✅ Successfully processed call {call_id}")
                    
                    # Небольшая пауза между обработкой
                    await asyncio.sleep(2)
                    
                except Exception as e:
                    logger.error(f"❌ Failed to process call {call_id}: {e}")
                    import traceback
                    logger.error(traceback.format_exc())
            
            if processed_count > 0:
                logger.info(f"✅ Processed {processed_count} calls")
            else:
                logger.info("📭 No new calls to process")
            
            # Очищаем старые ID из памяти (старше 24 часов)
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
        Обработать один звонок
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

# Глобальный экземпляр агента
call_summary_agent = CallSummaryAgent()

async def run_call_summary_agent():
    """
    Функция для запуска агента (вызывается из scheduler)
    """
    await call_summary_agent.check_and_process_calls()
