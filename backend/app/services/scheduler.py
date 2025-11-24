"""
Планировщик задач (Scheduler) для фоновых процессов
Используется APScheduler для периодических задач
"""
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime

logger = logging.getLogger(__name__)

# Глобальный scheduler
scheduler = AsyncIOScheduler()


def start_scheduler():
    """Запускает scheduler с настроенными задачами"""
    try:
        # Импортируем процессор звонков
        from backend.app.services.novofon_auto_processor import novofon_auto_processor
        
        # Добавляем задачу: проверка новых звонков каждую минуту
        scheduler.add_job(
            novofon_auto_processor.process_new_calls,
            trigger=IntervalTrigger(minutes=1),
            id='novofon_calls_check',
            name='Проверка новых звонков Novofon',
            replace_existing=True,
            max_instances=1  # Только один экземпляр одновременно
        )
        
        # Запускаем scheduler
        scheduler.start()
        logger.info("✅ Scheduler started successfully!")
        logger.info("📞 Novofon auto-processor: checking every 1 minute")
        
    except Exception as e:
        logger.error(f"❌ Failed to start scheduler: {e}")
        import traceback
        logger.error(traceback.format_exc())


def stop_scheduler():
    """Останавливает scheduler"""
    try:
        if scheduler.running:
            scheduler.shutdown()
            logger.info("✅ Scheduler stopped")
    except Exception as e:
        logger.error(f"Error stopping scheduler: {e}")


def get_scheduler_status():
    """Возвращает статус scheduler и список задач"""
    if not scheduler.running:
        return {
            "running": False,
            "jobs": []
        }
    
    jobs = []
    for job in scheduler.get_jobs():
        next_run = job.next_run_time
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run": next_run.isoformat() if next_run else None,
            "trigger": str(job.trigger)
        })
    
    return {
        "running": True,
        "jobs": jobs
    }
