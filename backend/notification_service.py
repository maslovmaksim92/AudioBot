"""
Smart Notification Service for Telegram
Provides daily summaries and smart alerts for business owner
"""

import os
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta, time
from dotenv import load_dotenv
import asyncio
from aiogram import Bot
from analytics_service import analytics_service, get_performance_metrics, get_business_insights
from bitrix24_service import get_bitrix24_service
from ai_service import ai_assistant
from db import db_manager
from models import NotificationTemplate, NotificationLog

load_dotenv()
logger = logging.getLogger(__name__)

class NotificationService:
    """Smart notification service for business alerts and summaries"""
    
    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.bot = Bot(token=self.bot_token) if self.bot_token else None
        self.db = db_manager
        self.owner_chat_id = None  # Will be set when owner starts bot
        
    async def send_daily_summary(self, chat_id: int) -> bool:
        """Send comprehensive daily business summary"""
        try:
            if not self.bot:
                logger.error("Telegram bot not configured")
                return False
            
            # Gather all business data
            summary_data = await self._gather_daily_data()
            
            # Generate AI summary
            summary_prompt = f"""
Создай краткую ежедневную сводку для генерального директора ВасДом на основе данных:

ФИНАНСОВЫЕ ПОКАЗАТЕЛИ:
{summary_data.get('financial', {})}

ОПЕРАЦИОННЫЕ МЕТРИКИ:
{summary_data.get('operational', {})}

СДЕЛКИ И КЛИЕНТЫ:
{summary_data.get('sales', {})}

КОМАНДА:
{summary_data.get('team', {})}

Сводка должна быть:
- Краткой (до 300 слов)
- Фокусироваться на ключевых цифрах
- Содержать 2-3 основные рекомендации
- Быть в деловом тоне с эмодзи для структуры
"""
            
            ai_response = await ai_assistant.chat(summary_prompt, "daily_summary")
            summary_text = ai_response.get("response", "Ошибка генерации сводки")
            
            # Format message
            message = f"""🌅 **ЕЖЕДНЕВНАЯ СВОДКА ВасДом**
📅 {datetime.utcnow().strftime('%d.%m.%Y')}

{summary_text}

📊 **БЫСТРЫЕ ЦИФРЫ:**
• Активные сделки: {summary_data.get('sales', {}).get('active_deals', 0)}
• Команда: {summary_data.get('team', {}).get('total', 0)} чел
• Объекты: {summary_data.get('operational', {}).get('houses', 600)}

💡 Подробная аналитика: /dashboard
🤖 Задать вопрос AI: просто напишите сообщение"""

            # Send message
            await self.bot.send_message(chat_id, message, parse_mode="Markdown")
            
            # Log notification
            await self._log_notification("daily_summary", str(chat_id), message, "sent")
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending daily summary: {e}")
            await self._log_notification("daily_summary", str(chat_id), "", "failed", str(e))
            return False
    
    async def send_alert(self, chat_id: int, alert_type: str, data: Dict[str, Any]) -> bool:
        """Send smart business alert"""
        try:
            if not self.bot:
                return False
            
            alert_messages = {
                "low_conversion": f"🔻 **ВНИМАНИЕ**: Конверсия сделок упала до {data.get('rate', 0)}%",
                "high_activity": f"📈 **РОСТ**: Активность выросла на {data.get('increase', 0)}%",
                "new_large_deal": f"💰 **КРУПНАЯ СДЕЛКА**: {data.get('amount', 0)} руб - {data.get('title', 'Новая сделка')}",
                "team_milestone": f"🏆 **КОМАНДА**: {data.get('message', 'Достижение команды')}",
                "system_error": f"⚠️ **ОШИБКА СИСТЕМЫ**: {data.get('error', 'Неизвестная ошибка')}",
                "financial_target": f"🎯 **ЦЕЛЬ**: {data.get('message', 'Финансовая цель достигнута')}"
            }
            
            message = alert_messages.get(alert_type, f"📢 Уведомление: {data}")
            message += f"\n\n⏰ {datetime.utcnow().strftime('%H:%M %d.%m.%Y')}"
            
            await self.bot.send_message(chat_id, message, parse_mode="Markdown")
            await self._log_notification(alert_type, str(chat_id), message, "sent")
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending alert: {e}")
            await self._log_notification(alert_type, str(chat_id), "", "failed", str(e))
            return False
    
    async def send_weekly_report(self, chat_id: int) -> bool:
        """Send comprehensive weekly business report"""
        try:
            if not self.bot:
                return False
            
            # Get weekly insights and metrics
            insights = await get_business_insights(force_refresh=True)
            metrics = await get_performance_metrics()
            
            # Generate weekly report with AI
            report_prompt = f"""
Создай еженедельный отчет для руководства ВасДом:

КЛЮЧЕВЫЕ МЕТРИКИ НЕДЕЛИ:
{metrics}

БИЗНЕС-ИНСАЙТЫ:
{insights[:3]}

Отчет должен включать:
1. Основные достижения недели
2. Проблемные зоны
3. Планы на следующую неделю
4. 3 ключевые рекомендации

Формат: деловой, структурированный, до 500 слов.
"""
            
            ai_response = await ai_assistant.chat(report_prompt, "weekly_report")
            report_text = ai_response.get("response", "Ошибка генерации отчета")
            
            message = f"""📊 **ЕЖЕНЕДЕЛЬНЫЙ ОТЧЕТ ВасДом**
📅 Неделя {datetime.utcnow().strftime('%W, %Y')}

{report_text}

📈 **МЕТРИКИ НЕДЕЛИ:**
• Конверсия: {metrics.get('sales_metrics', {}).get('conversion_rate', 0)}%
• Средняя сделка: {metrics.get('sales_metrics', {}).get('avg_deal_size', 0):,.0f} руб
• Активных клиентов: {metrics.get('client_metrics', {}).get('active_clients', 0)}

🎯 Следующая неделя: больше фокуса на конверсии и качестве сервиса
"""
            
            await self.bot.send_message(chat_id, message, parse_mode="Markdown")
            await self._log_notification("weekly_report", str(chat_id), message, "sent")
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending weekly report: {e}")
            return False
    
    async def schedule_notifications(self):
        """Schedule periodic notifications"""
        try:
            while True:
                current_time = datetime.utcnow()
                
                # Daily summary at 8:00 AM Moscow time (5:00 UTC)
                if current_time.hour == 5 and current_time.minute == 0:
                    await self._send_to_all_owners("daily_summary")
                
                # Weekly report on Monday at 9:00 AM Moscow time (6:00 UTC)
                elif current_time.weekday() == 0 and current_time.hour == 6 and current_time.minute == 0:
                    await self._send_to_all_owners("weekly_report")
                
                # Check for business alerts every hour
                elif current_time.minute == 0:
                    await self._check_and_send_alerts()
                
                # Wait 1 minute before next check
                await asyncio.sleep(60)
                
        except Exception as e:
            logger.error(f"Error in notification scheduler: {e}")
    
    async def _gather_daily_data(self) -> Dict[str, Any]:
        """Gather all daily business data"""
        try:
            bx24 = await get_bitrix24_service()
            
            # Get various data sources
            deals = await bx24.get_deals()
            contacts = await bx24.get_contacts()
            stats = await bx24.get_cleaning_statistics()
            
            # Employee data
            try:
                employees_collection = self.db.get_collection("employees")
                total_employees = await employees_collection.count_documents({})
            except Exception as e:
                logger.error(f"Error getting employee data: {e}")
                total_employees = 0
            
            return {
                "financial": {
                    "total_pipeline": sum(float(d.get('OPPORTUNITY', 0)) for d in deals),
                    "won_deals_value": sum(float(d.get('OPPORTUNITY', 0)) for d in deals if 'WON' in d.get('STAGE_ID', ''))
                },
                "sales": {
                    "total_deals": len(deals),
                    "active_deals": len([d for d in deals if 'WON' not in d.get('STAGE_ID', '') and 'LOSE' not in d.get('STAGE_ID', '')]),
                    "total_contacts": len(contacts)
                },
                "team": {
                    "total": total_employees,
                    "active": total_employees  # Assuming all are active
                },
                "operational": {
                    "houses": 600,
                    "cities": 2,
                    "bitrix_stats": stats
                }
            }
            
        except Exception as e:
            logger.error(f"Error gathering daily data: {e}")
            return {}
    
    async def _send_to_all_owners(self, notification_type: str):
        """Send notification to all business owners"""
        try:
            # Get owner chat IDs from database or configuration
            owner_ids = [self.owner_chat_id] if self.owner_chat_id else []
            
            # You can expand this to get multiple owners from database
            # owner_profiles = await self.db.get_collection("user_profiles").find({"role": "owner"})
            
            for chat_id in owner_ids:
                if chat_id:
                    if notification_type == "daily_summary":
                        await self.send_daily_summary(int(chat_id))
                    elif notification_type == "weekly_report":
                        await self.send_weekly_report(int(chat_id))
                    
                    # Small delay between messages
                    await asyncio.sleep(1)
                    
        except Exception as e:
            logger.error(f"Error sending to owners: {e}")
    
    async def _check_and_send_alerts(self):
        """Check business metrics and send alerts if needed"""
        try:
            metrics = await get_performance_metrics()
            
            # Check conversion rate
            conversion_rate = metrics.get('sales_metrics', {}).get('conversion_rate', 0)
            if conversion_rate < 15:  # Alert if conversion below 15%
                await self._send_to_all_owners_alert("low_conversion", {"rate": conversion_rate})
            
            # Check for large deals
            bx24 = await get_bitrix24_service()
            deals = await bx24.get_deals()
            
            for deal in deals:
                value = float(deal.get('OPPORTUNITY', 0))
                if value > 100000:  # Alert for deals over 100k rubles
                    await self._send_to_all_owners_alert("new_large_deal", {
                        "amount": value,
                        "title": deal.get('TITLE', 'Новая сделка')
                    })
            
        except Exception as e:
            logger.error(f"Error checking alerts: {e}")
    
    async def _send_to_all_owners_alert(self, alert_type: str, data: Dict[str, Any]):
        """Send alert to all owners"""
        owner_ids = [self.owner_chat_id] if self.owner_chat_id else []
        
        for chat_id in owner_ids:
            if chat_id:
                await self.send_alert(int(chat_id), alert_type, data)
    
    async def _log_notification(self, template_id: str, recipient: str, message: str, 
                               status: str, error_message: Optional[str] = None):
        """Log notification to database"""
        try:
            collection = self.db.get_collection("notification_logs")
            
            log_data = NotificationLog(
                template_id=template_id,
                recipient=recipient,
                message=message,
                status=status,
                sent_at=datetime.utcnow() if status == "sent" else None,
                error_message=error_message
            )
            
            await collection.insert_one(log_data.dict())
            
        except Exception as e:
            logger.error(f"Error logging notification: {e}")
    
    def set_owner_chat_id(self, chat_id: int):
        """Set the main owner's chat ID for notifications"""
        self.owner_chat_id = chat_id
        logger.info(f"Owner chat ID set to: {chat_id}")

# Global notification service instance
notification_service = NotificationService()

# Convenience functions
async def send_daily_summary(chat_id: int) -> bool:
    """Send daily summary"""
    return await notification_service.send_daily_summary(chat_id)

async def send_business_alert(chat_id: int, alert_type: str, data: Dict[str, Any]) -> bool:
    """Send business alert"""
    return await notification_service.send_alert(chat_id, alert_type, data)

async def start_notification_scheduler():
    """Start the notification scheduler"""
    asyncio.create_task(notification_service.schedule_notifications())

def set_owner_chat_id(chat_id: int):
    """Set owner chat ID"""
    notification_service.set_owner_chat_id(chat_id)