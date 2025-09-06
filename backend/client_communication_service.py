"""
Client Communication Service - Smart notifications and communication
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import asyncio
import json
from bitrix24_service import get_bitrix24_service
from ai_service import ai_assistant

logger = logging.getLogger(__name__)

class ClientCommunicationService:
    """Service for intelligent client communication"""
    
    def __init__(self):
        self.sms_api_key = None  # Will be configured later
        self.email_api_key = None
    
    async def send_cleaning_notification(self, house_id: str, notification_type: str) -> Dict[str, Any]:
        """Send cleaning notifications to clients"""
        try:
            bx24 = await get_bitrix24_service()
            
            # Get house/deal information
            deals = await bx24.get_deals({"ID": house_id})
            if not deals:
                return {"success": False, "error": "House not found"}
            
            house = deals[0]
            house_title = house.get("TITLE", "")
            
            # Get contact information
            contact_id = house.get("CONTACT_ID")
            if contact_id:
                contacts = await bx24.get_contacts({"ID": contact_id})
                contact = contacts[0] if contacts else {}
            else:
                contact = {}
            
            # Generate notification message
            message = await self._generate_notification_message(house_title, notification_type, contact)
            
            # Send notification (mock implementation)
            results = {
                "sms_sent": False,
                "email_sent": False,
                "telegram_sent": False
            }
            
            # Mock SMS sending
            if contact.get("PHONE"):
                results["sms_sent"] = await self._send_sms(contact["PHONE"], message["sms"])
            
            # Mock Email sending  
            if contact.get("EMAIL"):
                results["email_sent"] = await self._send_email(contact["EMAIL"], message["email"])
            
            return {
                "success": True,
                "house_id": house_id,
                "house_title": house_title,
                "notification_type": notification_type,
                "results": results,
                "message": message
            }
            
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
            return {"success": False, "error": str(e)}
    
    async def _generate_notification_message(self, house_title: str, notification_type: str, contact: Dict) -> Dict[str, str]:
        """Generate personalized notification messages"""
        try:
            contact_name = contact.get("NAME", "Уважаемый клиент")
            
            templates = {
                "cleaning_scheduled": {
                    "sms": f"Добрый день, {contact_name}! Уборка в {house_title} запланирована на завтра. Время: 10:00-12:00. ВасДом",
                    "email": f"""
                    Уважаемый {contact_name}!
                    
                    Информируем Вас о предстоящей уборке:
                    Объект: {house_title}
                    Дата: {(datetime.now() + timedelta(days=1)).strftime('%d.%m.%Y')}
                    Время: 10:00-12:00
                    
                    Наша команда выполнит полный комплекс работ по уборке подъезда.
                    
                    С уважением,
                    Команда ВасДом
                    """
                },
                "cleaning_completed": {
                    "sms": f"{contact_name}, уборка в {house_title} завершена! Фото отчет отправлен на email. Спасибо за доверие! ВасДом",
                    "email": f"""
                    Уважаемый {contact_name}!
                    
                    Уборка успешно завершена:
                    Объект: {house_title}
                    Дата выполнения: {datetime.now().strftime('%d.%m.%Y')}
                    
                    Выполненные работы:
                    ✓ Влажная уборка всех поверхностей
                    ✓ Мойка окон и зеркал  
                    ✓ Уборка лестничных площадок
                    ✓ Вынос мусора
                    
                    Фото-отчет во вложении.
                    
                    Оцените качество наших услуг: [ссылка на оценку]
                    
                    С уважением,
                    Команда ВасДом
                    """
                },
                "quality_check": {
                    "sms": f"{contact_name}, как качество уборки в {house_title}? Ваше мнение важно для нас! Ответьте на 3 вопроса: [ссылка]",
                    "email": f"""
                    Уважаемый {contact_name}!
                    
                    Помогите нам стать лучше!
                    
                    Оцените качество уборки в {house_title}:
                    - Общее качество работ (1-5)
                    - Пунктуальность команды (1-5) 
                    - Готовы ли рекомендовать нас? (Да/Нет)
                    
                    [Кнопка: Оценить качество]
                    
                    Ваше мнение поможет нам улучшить сервис!
                    
                    С уважением,
                    Команда ВасДом
                    """
                }
            }
            
            return templates.get(notification_type, {
                "sms": f"Уведомление от ВасДом по объекту {house_title}",
                "email": f"Уведомление по объекту {house_title}"
            })
            
        except Exception as e:
            logger.error(f"Error generating message: {e}")
            return {"sms": "Уведомление от ВасДом", "email": "Уведомление от ВасДом"}
    
    async def _send_sms(self, phone: str, message: str) -> bool:
        """Send SMS notification (mock implementation)"""
        try:
            # Mock SMS sending - replace with real SMS service
            logger.info(f"SMS sent to {phone}: {message[:50]}...")
            return True
        except Exception as e:
            logger.error(f"Error sending SMS: {e}")
            return False
    
    async def _send_email(self, email: str, message: str) -> bool:
        """Send email notification (mock implementation)"""
        try:
            # Mock email sending - replace with real email service
            logger.info(f"Email sent to {email}: {len(message)} characters")
            return True
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return False
    
    async def generate_client_satisfaction_report(self) -> Dict[str, Any]:
        """Generate client satisfaction analytics"""
        try:
            # Mock satisfaction data - in production, get from surveys/feedback
            satisfaction_data = {
                "total_surveys": 87,
                "response_rate": 0.73,
                "average_rating": 4.6,
                "categories": {
                    "quality": 4.7,
                    "punctuality": 4.5,
                    "communication": 4.4,
                    "value_for_money": 4.8
                },
                "nps_score": 67,  # Net Promoter Score
                "recent_feedback": [
                    {"rating": 5, "comment": "Отличная работа, все очень чисто!", "date": "2024-01-15"},
                    {"rating": 4, "comment": "Хорошо, но хотелось бы больше внимания к деталям", "date": "2024-01-14"},
                    {"rating": 5, "comment": "Команда очень вежливая и профессиональная", "date": "2024-01-13"}
                ]
            }
            
            # Generate insights using AI
            insights_prompt = f"""
            Проанализируй данные удовлетворенности клиентов:
            - Средняя оценка: {satisfaction_data['average_rating']}
            - NPS: {satisfaction_data['nps_score']}
            - Качество: {satisfaction_data['categories']['quality']}
            - Пунктуальность: {satisfaction_data['categories']['punctuality']}
            
            Дай 3 конкретные рекомендации по улучшению сервиса.
            """
            
            ai_response = await ai_assistant.chat(insights_prompt, "satisfaction_analysis")
            insights = ai_response.get("response", "Анализ временно недоступен")
            
            return {
                "success": True,
                "satisfaction_data": satisfaction_data,
                "ai_insights": insights,
                "recommendations": [
                    "Усилить контроль качества на объектах с оценкой ниже 4.5",
                    "Провести дополнительное обучение по коммуникации с клиентами",
                    "Внедрить систему премирования за высокие оценки клиентов"
                ]
            }
            
        except Exception as e:
            logger.error(f"Error generating satisfaction report: {e}")
            return {"success": False, "error": str(e)}
    
    async def schedule_automatic_notifications(self) -> Dict[str, Any]:
        """Schedule automatic client notifications"""
        try:
            bx24 = await get_bitrix24_service()
            houses = await bx24.get_cleaning_houses_deals()
            
            scheduled_notifications = []
            
            for house in houses:
                house_id = house.get("ID")
                house_title = house.get("TITLE", "")
                stage_id = house.get("STAGE_ID", "")
                
                # Schedule notifications based on deal stage
                if "NEW" in stage_id:
                    # Schedule "cleaning_scheduled" notification
                    scheduled_notifications.append({
                        "house_id": house_id,
                        "house_title": house_title,
                        "notification_type": "cleaning_scheduled",
                        "scheduled_date": (datetime.now() + timedelta(days=1)).isoformat(),
                        "status": "scheduled"
                    })
                elif "WORK" in stage_id:
                    # Schedule "cleaning_completed" notification
                    scheduled_notifications.append({
                        "house_id": house_id,
                        "house_title": house_title,
                        "notification_type": "cleaning_completed",
                        "scheduled_date": (datetime.now() + timedelta(hours=2)).isoformat(),
                        "status": "scheduled"
                    })
                elif "WON" in stage_id:
                    # Schedule "quality_check" notification
                    scheduled_notifications.append({
                        "house_id": house_id,
                        "house_title": house_title,
                        "notification_type": "quality_check",
                        "scheduled_date": (datetime.now() + timedelta(days=1)).isoformat(),
                        "status": "scheduled"
                    })
            
            return {
                "success": True,
                "scheduled_count": len(scheduled_notifications),
                "notifications": scheduled_notifications[:10],  # Show first 10
                "next_run": (datetime.now() + timedelta(hours=1)).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error scheduling notifications: {e}")
            return {"success": False, "error": str(e)}
    
    async def handle_client_complaint(self, complaint_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle and route client complaints"""
        try:
            house_title = complaint_data.get("house_title", "")
            complaint_text = complaint_data.get("complaint", "")
            client_contact = complaint_data.get("client_contact", "")
            priority = complaint_data.get("priority", "medium")
            
            # Analyze complaint using AI
            analysis_prompt = f"""
            Проанализируй жалобу клиента:
            Объект: {house_title}
            Жалоба: {complaint_text}
            
            Определи:
            1. Категорию проблемы (качество, сроки, персонал, оборудование)
            2. Уровень серьезности (1-5)
            3. Рекомендуемые действия
            4. Ответственное лицо для решения
            """
            
            ai_response = await ai_assistant.chat(analysis_prompt, "complaint_analysis")
            analysis = ai_response.get("response", "Анализ временно недоступен")
            
            # Create task in Bitrix24 for complaint resolution
            bx24 = await get_bitrix24_service()
            task_result = await bx24.create_task(
                title=f"ЖАЛОБА: {house_title}",
                description=f"""
                ЖАЛОБА КЛИЕНТА:
                {complaint_text}
                
                КОНТАКТ КЛИЕНТА: {client_contact}
                ПРИОРИТЕТ: {priority}
                
                AI-АНАЛИЗ:
                {analysis}
                
                ТРЕБУЕТСЯ: Немедленное реагирование и устранение проблемы
                """,
                responsible_id=1,
                deadline=(datetime.now() + timedelta(hours=4)).strftime('%Y-%m-%d %H:%M:%S')
            )
            
            return {
                "success": True,
                "complaint_id": f"COMPLAINT_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "task_created": task_result.get("success", False),
                "task_id": task_result.get("task_id"),
                "ai_analysis": analysis,
                "priority": priority,
                "estimated_resolution_time": "4 часа"
            }
            
        except Exception as e:
            logger.error(f"Error handling complaint: {e}")
            return {"success": False, "error": str(e)}

# Global service instance
client_communication_service = ClientCommunicationService()

# Utility functions
async def send_client_notification(house_id: str, notification_type: str) -> Dict[str, Any]:
    """Send notification to client"""
    return await client_communication_service.send_cleaning_notification(house_id, notification_type)

async def get_client_satisfaction_report() -> Dict[str, Any]:
    """Get client satisfaction analytics"""
    return await client_communication_service.generate_client_satisfaction_report()

async def handle_complaint(complaint_data: Dict[str, Any]) -> Dict[str, Any]:
    """Handle client complaint"""
    return await client_communication_service.handle_client_complaint(complaint_data)