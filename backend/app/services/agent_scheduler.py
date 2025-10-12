"""
Сервис планирования агентов - интеграция с APScheduler
"""
import logging
import asyncio
from typing import Dict, Any, List
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)

class AgentScheduler:
    """Планировщик для автоматического запуска агентов"""
    
    def __init__(self, scheduler: AsyncIOScheduler):
        self.scheduler = scheduler
        self.registered_agents = {}  # agent_id -> job_id
    
    async def register_agent(self, agent: Dict[str, Any], executor_func):
        """
        Зарегистрировать агента в планировщике
        
        Args:
            agent: Данные агента
            executor_func: Функция для выполнения агента
        """
        agent_id = agent['id']
        agent_name = agent['name']
        
        # Удаляем старую задачу если она есть
        if agent_id in self.registered_agents:
            await self.unregister_agent(agent_id)
        
        # Ищем cron triggers
        for trigger in agent.get('triggers', []):
            if trigger.get('type') == 'cron':
                cron_config = trigger.get('config', {})
                cron_expr = cron_config.get('cron')
                
                if not cron_expr:
                    logger.warning(f"⚠️ Agent {agent_name} has cron trigger without cron expression")
                    continue
                
                try:
                    # Парсим cron выражение: "25 8 * * 1-5"
                    parts = cron_expr.split()
                    if len(parts) == 5:
                        minute, hour, day, month, day_of_week = parts
                        
                        # Создаём CronTrigger
                        cron_trigger = CronTrigger(
                            minute=minute,
                            hour=hour,
                            day=day,
                            month=month,
                            day_of_week=day_of_week
                        )
                        
                        # Добавляем задачу в планировщик
                        job = self.scheduler.add_job(
                            executor_func,
                            trigger=cron_trigger,
                            args=[agent],
                            id=f"agent_{agent_id}",
                            name=f"Agent: {agent_name}",
                            replace_existing=True
                        )
                        
                        self.registered_agents[agent_id] = job.id
                        
                        logger.info(f"✅ Agent '{agent_name}' registered with cron: {cron_expr}")
                        logger.info(f"   Next run: {job.next_run_time}")
                    
                    else:
                        logger.error(f"❌ Invalid cron expression for agent {agent_name}: {cron_expr}")
                
                except Exception as e:
                    logger.error(f"❌ Error registering agent {agent_name}: {e}")
    
    async def unregister_agent(self, agent_id: str):
        """
        Удалить агента из планировщика
        
        Args:
            agent_id: ID агента
        """
        if agent_id in self.registered_agents:
            job_id = self.registered_agents[agent_id]
            try:
                self.scheduler.remove_job(job_id)
                del self.registered_agents[agent_id]
                logger.info(f"✅ Agent {agent_id} unregistered from scheduler")
            except Exception as e:
                logger.error(f"❌ Error unregistering agent {agent_id}: {e}")
    
    async def reload_all_agents(self, agents: List[Dict[str, Any]], executor_func):
        """
        Перезагрузить всех агентов в планировщике
        
        Args:
            agents: Список всех агентов
            executor_func: Функция для выполнения агента
        """
        logger.info("🔄 Reloading all agents in scheduler...")
        
        # Удаляем все текущие задачи агентов
        for agent_id in list(self.registered_agents.keys()):
            await self.unregister_agent(agent_id)
        
        # Регистрируем активных агентов с cron triggers
        active_count = 0
        for agent in agents:
            if agent.get('status') == 'active':
                has_cron = any(t.get('type') == 'cron' for t in agent.get('triggers', []))
                if has_cron:
                    await self.register_agent(agent, executor_func)
                    active_count += 1
        
        logger.info(f"✅ Loaded {active_count} active agents with cron triggers")
    
    def get_registered_agents(self) -> Dict[str, str]:
        """Получить список зарегистрированных агентов"""
        return self.registered_agents.copy()
    
    def get_agent_next_run(self, agent_id: str):
        """Получить время следующего запуска агента"""
        if agent_id in self.registered_agents:
            job_id = self.registered_agents[agent_id]
            try:
                job = self.scheduler.get_job(job_id)
                if job:
                    return job.next_run_time
            except Exception as e:
                logger.error(f"❌ Error getting next run time for agent {agent_id}: {e}")
        return None


# Глобальный экземпляр (будет инициализирован в server.py)
agent_scheduler = None


def init_agent_scheduler(scheduler: AsyncIOScheduler) -> AgentScheduler:
    """Инициализировать планировщик агентов"""
    global agent_scheduler
    agent_scheduler = AgentScheduler(scheduler)
    return agent_scheduler
