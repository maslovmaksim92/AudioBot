"""
Планировщик задач - автоматические задачи по расписанию
- Синхронизация Bitrix24 каждые 15 минут
- Напоминания о планерках
- AI звонки сотрудникам
"""
import asyncio
import logging
from datetime import datetime, timezone
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
import pytz

from backend.app.services.bitrix24_service import bitrix24_service
from backend.app.services.telegram_service import telegram_service
from backend.app.config.database import AsyncSessionLocal
from backend.app.tasks.call_summary_agent import run_call_summary_agent

logger = logging.getLogger(__name__)

class TaskScheduler:
    """Планировщик автоматических задач"""
    
    def __init__(self):
        # Создаём планировщик с московским часовым поясом
        moscow_tz = pytz.timezone('Europe/Moscow')
        self.scheduler = AsyncIOScheduler(timezone=moscow_tz)
        self.running = False
    
    def start(self):
        """Запуск планировщика"""
        if self.running:
            logger.warning("Scheduler already running")
            return
        
        # Синхронизация Bitrix24 каждые 30 минут (оптимально для нагрузки)
        self.scheduler.add_job(
            self.sync_bitrix24_houses,
            trigger=IntervalTrigger(minutes=30),
            id='sync_bitrix24',
            name='Синхронизация домов из Bitrix24',
            replace_existing=True
        )
        
        # Напоминание о планерке каждый день в 8:25
        self.scheduler.add_job(
            self.send_plannerka_reminder,
            trigger=CronTrigger(hour=8, minute=25),
            id='plannerka_reminder',
            name='Напоминание о планерке',
            replace_existing=True
        )
        
        # Автоматическая обработка звонков каждые 5 минут
        self.scheduler.add_job(
            run_call_summary_agent,
            trigger=IntervalTrigger(minutes=5),
            id='call_summary_agent',
            name='Агент саммари звонков',
            replace_existing=True
        )
        
        # AI звонки сотрудникам каждый день в 16:55
        self.scheduler.add_job(
            self.ai_call_employees,
            trigger=CronTrigger(hour=16, minute=55),
            id='ai_calls_daily',
            name='AI звонки сотрудникам',
            replace_existing=True
        )
        
        self.scheduler.start()
        self.running = True
        
        logger.info("=" * 70)
        logger.info("🚀 Task Scheduler started!")
        logger.info("=" * 70)
        logger.info("📅 Scheduled tasks (Moscow Time - MSK):")
        moscow_tz = pytz.timezone('Europe/Moscow')
        for job in self.scheduler.get_jobs():
            next_run_msk = job.next_run_time.astimezone(moscow_tz) if job.next_run_time else None
            logger.info(f"   - {job.name} (ID: {job.id})")
            if next_run_msk:
                logger.info(f"     Next run: {next_run_msk.strftime('%Y-%m-%d %H:%M:%S MSK')}")
        logger.info("=" * 70)
    
    def stop(self):
        """Остановка планировщика"""
        if not self.running:
            return
        
        self.scheduler.shutdown()
        self.running = False
        logger.info("🛑 Task Scheduler stopped")
    
    async def sync_bitrix24_houses(self):
        """Задача: Синхронизация домов из Bitrix24"""
        logger.info("🔄 Starting Bitrix24 sync...")
        
        try:
            async with AsyncSessionLocal() as db:
                # Загрузка всех сделок
                deals = await bitrix24_service.get_all_deals()
                
                if not deals:
                    logger.warning("No deals loaded from Bitrix24")
                    return
                
                synced = 0
                created = 0
                updated = 0
                
                from backend.app.models.house import House
                from sqlalchemy import select
                
                for deal in deals:
                    house_data = bitrix24_service.parse_deal_to_house(deal)
                    
                    if not house_data.get("address"):
                        continue
                    
                    # Проверка существования
                    result = await db.execute(
                        select(House).where(House.bitrix_id == house_data["bitrix_id"])
                    )
                    existing = result.scalar_one_or_none()
                    
                    if existing:
                        # Обновление
                        for key, value in house_data.items():
                            if key != "id":
                                setattr(existing, key, value)
                        updated += 1
                    else:
                        # Создание
                        new_house = House(**house_data)
                        db.add(new_house)
                        created += 1
                    
                    synced += 1
                
                await db.commit()
                
                logger.info(f"✅ Bitrix24 sync complete: {synced} total, {created} created, {updated} updated")
                
                # Логирование в БД
                from backend.app.models.log import Log, LogLevel, LogCategory
                from uuid import uuid4
                log = Log(
                    id=str(uuid4()),
                    level=LogLevel.INFO,
                    category=LogCategory.INTEGRATION,
                    message=f"Автосинхронизация Bitrix24 завершена: {synced} домов ({created} создано, {updated} обновлено)",
                    extra_data={"synced": synced, "created": created, "updated": updated}
                )
                db.add(log)
                await db.commit()
                
        except Exception as e:
            logger.error(f"❌ Bitrix24 sync error: {e}")
            # Логирование ошибки в БД
            try:
                async with AsyncSessionLocal() as db:
                    from backend.app.models.log import Log, LogLevel, LogCategory
                    from uuid import uuid4
                    log = Log(
                        id=str(uuid4()),
                        level=LogLevel.ERROR,
                        category=LogCategory.INTEGRATION,
                        message=f"Ошибка автосинхронизации Bitrix24: {str(e)}",
                        extra_data={"error": str(e)}
                    )
                    db.add(log)
                    await db.commit()
            except:
                pass
    
    async def send_plannerka_reminder(self):
        """Задача: Напоминание о планерке в 8:25"""
        logger.info("🔔 Sending plannerka reminders...")
        
        try:
            import os
            
            # Получаем chat_id директора из переменной окружения
            director_chat_id = os.getenv('CHAT_ID_DIRECTOR')
            
            if not director_chat_id:
                logger.error("❌ CHAT_ID_DIRECTOR не настроен! Добавьте переменную на Render")
                return
            
            message = "🔔 <b>в 8:30 планерка, сбор</b>"
            
            success = await telegram_service.send_message(
                chat_id=director_chat_id,
                text=message
            )
            
            if success:
                logger.info(f"✅ Plannerka reminder sent to director (chat_id: {director_chat_id})")
            else:
                logger.warning(f"⚠️ Failed to send to director (chat_id: {director_chat_id})")
                
        except Exception as e:
            logger.error(f"❌ Plannerka reminder error: {e}")
    
    async def ai_call_employees(self):
        """Задача: AI звонки сотрудникам в 16:55"""
        logger.info("📞 Starting AI call to collect daily report...")
        
        try:
            import httpx
            import os
            
            # Владелец (ММВ)
            owner_phone = "+79200924550"
            
            # Промпт для сбора отчётности
            reporting_prompt = """Вы - AI помощник компании VasDom, звоните директору для сбора ежедневной отчётности.

Ваша задача:
1. Поздороваться и представиться: "Добрый вечер! Я AI помощник VasDom. Звоню по расписанию для сбора отчётности."
2. Спросить про выполненные задачи за день
3. Узнать о проблемах или рекламациях
4. Спросить про планы на завтра
5. Узнать, нужна ли какая-то помощь или поддержка
6. Вежливо попрощаться

Будьте вежливы, профессиональны и внимательны. Активно слушайте и задавайте уточняющие вопросы."""
            
            # Используем внешний URL (как фронтенд)
            backend_url = os.getenv('REACT_APP_BACKEND_URL') or os.getenv('BACKEND_URL') or 'http://localhost:8001'
            voice_api_url = f"{backend_url}/api/voice/ai-call"
            
            # Отправка запроса через httpx
            async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
                payload = {
                    "phone_number": owner_phone,
                    "prompt": reporting_prompt
                }
                
                logger.info(f"📞 Calling voice API: {voice_api_url}")
                response = await client.post(voice_api_url, json=payload)
                
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"✅ AI call initiated to {owner_phone} for daily report")
                    logger.info(f"📞 Call details: {data}")
                else:
                    logger.error(f"❌ Failed to initiate AI call: {response.status_code} - {response.text}")
            
        except Exception as e:
            logger.error(f"❌ AI call error: {e}")
            import traceback
            logger.error(traceback.format_exc())

# Singleton instance
task_scheduler = TaskScheduler()
