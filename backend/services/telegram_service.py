import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import aiohttp
import json
import os
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)

class TelegramService:
    """Расширенный Telegram сервис с AI интеграцией"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.webhook_url = os.getenv("TELEGRAM_WEBHOOK_URL")
        self.db = db
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}"
        
        # Контакты руководителей из задания
        self.leadership_contacts = {
            "89056400212": {"name": "Филиппов Сергей Сергеевич", "role": "Акционер"},
            "89208855883": {"name": "Черкасов Ярослав Артурович", "role": "Акционер"},
            "89200924550": {"name": "Маслов Максим Валерьевич", "role": "Директор"},
            "89208701769": {"name": "Маслова Валентина Михайловна", "role": "Генеральный директор"}
        }
        
    async def send_message(self, chat_id: str, text: str, reply_markup: Dict = None) -> Dict[str, Any]:
        """Отправляет сообщение в Telegram"""
        try:
            url = f"{self.api_url}/sendMessage"
            
            payload = {
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "HTML"
            }
            
            if reply_markup:
                payload["reply_markup"] = reply_markup
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, timeout=30) as response:
                    result = await response.json()
                    
                    if result.get("ok"):
                        return {"status": "success", "message_id": result["result"]["message_id"]}
                    else:
                        logger.error(f"Telegram API error: {result}")
                        return {"status": "error", "error": result.get("description", "Unknown error")}
                        
        except Exception as e:
            logger.error(f"Error sending Telegram message: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    async def send_notification_to_leadership(self, message: str, urgency: str = "normal") -> Dict[str, Any]:
        """Отправляет уведомление руководству"""
        results = []
        
        for phone, contact in self.leadership_contacts.items():
            # Ищем chat_id по номеру телефона в нашей БД
            employee = await self.db.employees.find_one({"phone": phone})
            
            if employee and employee.get("telegram_id"):
                icon = "🔥" if urgency == "urgent" else "📊" if urgency == "important" else "ℹ️"
                
                formatted_message = f"{icon} <b>Уведомление для {contact['name']}</b>\n\n{message}"
                
                result = await self.send_message(employee["telegram_id"], formatted_message)
                results.append({
                    "contact": contact["name"],
                    "phone": phone,
                    "status": result.get("status", "error")
                })
            else:
                results.append({
                    "contact": contact["name"],
                    "phone": phone,
                    "status": "no_telegram_id"
                })
        
        return {"results": results, "total_sent": len([r for r in results if r["status"] == "success"])}
    
    async def create_employee_keyboards(self) -> Dict[str, Any]:
        """Создает клавиатуры для разных ролей сотрудников"""
        keyboards = {
            "director": {
                "inline_keyboard": [
                    [{"text": "📊 Дашборд", "callback_data": "dashboard"}],
                    [{"text": "👥 Сотрудники", "callback_data": "employees"}, {"text": "💰 Финансы", "callback_data": "finances"}],
                    [{"text": "📋 Задачи", "callback_data": "tasks"}, {"text": "🏢 Проекты", "callback_data": "projects"}],
                    [{"text": "🤖 AI Анализ", "callback_data": "ai_analysis"}]
                ]
            },
            "manager": {
                "inline_keyboard": [
                    [{"text": "📋 Мои задачи", "callback_data": "my_tasks"}],
                    [{"text": "👥 Команда", "callback_data": "team"}, {"text": "📊 Отчеты", "callback_data": "reports"}],
                    [{"text": "🚗 Маршруты", "callback_data": "routes"}],
                    [{"text": "📞 Связаться с AI", "callback_data": "ai_help"}]
                ]
            },
            "employee": {
                "inline_keyboard": [
                    [{"text": "📋 Мои задачи", "callback_data": "my_tasks"}],
                    [{"text": "📍 Отметиться", "callback_data": "check_in"}],
                    [{"text": "📝 Отчет", "callback_data": "report"}],
                    [{"text": "❓ Помощь", "callback_data": "help"}]
                ]
            }
        }
        
        return keyboards
    
    async def handle_callback_query(self, callback_data: str, user_id: str, message_id: str) -> Dict[str, Any]:
        """Обрабатывает нажатия на инлайн кнопки"""
        try:
            # Находим сотрудника
            employee = await self.db.employees.find_one({"telegram_id": user_id})
            
            if not employee:
                await self.send_message(user_id, "❌ Вы не зарегистрированы в системе. Обратитесь к администратору.")
                return {"status": "error", "message": "Employee not found"}
            
            response_text = ""
            
            if callback_data == "dashboard":
                response_text = await self._get_dashboard_summary()
            elif callback_data == "employees":
                response_text = await self._get_employees_summary()
            elif callback_data == "finances":
                response_text = await self._get_finances_summary()
            elif callback_data == "my_tasks":
                response_text = await self._get_employee_tasks(employee["id"])
            elif callback_data == "ai_analysis":
                response_text = await self._get_ai_analysis()
            elif callback_data == "check_in":
                response_text = await self._handle_check_in(employee["id"])
            else:
                response_text = f"⚙️ Функция '{callback_data}' в разработке..."
            
            await self.send_message(user_id, response_text)
            return {"status": "success", "action": callback_data}
            
        except Exception as e:
            logger.error(f"Error handling callback query: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    async def _get_dashboard_summary(self) -> str:
        """Краткая сводка дашборда"""
        try:
            # Получаем статистику
            total_employees = await self.db.employees.count_documents({"active": True})
            active_projects = await self.db.projects.count_documents({"status": "active"})
            pending_tasks = await self.db.tasks.count_documents({"status": "pending"})
            
            # Последние AI предложения
            latest_suggestions = await self.db.improvements.find(
                {"status": "suggested"}, sort=[("created_at", -1)]
            ).limit(3).to_list(length=None)
            
            text = f"""📊 <b>ДАШБОРД КОМПАНИИ</b>
            
👥 Активных сотрудников: {total_employees}
🏢 Активных проектов: {active_projects}  
📋 Задач в ожидании: {pending_tasks}

🤖 <b>Последние AI предложения:</b>"""
            
            for suggestion in latest_suggestions:
                text += f"\n• {suggestion.get('title', 'Предложение')} (Влияние: {suggestion.get('impact_score', 0)}/10)"
            
            if not latest_suggestions:
                text += "\n• Пока нет предложений"
                
            text += f"\n\n⏰ Обновлено: {datetime.utcnow().strftime('%H:%M %d.%m.%Y')}"
            
            return text
            
        except Exception as e:
            return f"❌ Ошибка получения данных дашборда: {str(e)}"
    
    async def _get_employees_summary(self) -> str:
        """Сводка по сотрудникам"""
        try:
            employees = await self.db.employees.find({"active": True}).to_list(length=None)
            
            departments = {}
            for emp in employees:
                dept = emp.get("department", "Неопределен")
                if dept not in departments:
                    departments[dept] = []
                departments[dept].append(emp)
            
            text = "👥 <b>СОТРУДНИКИ ПО ОТДЕЛАМ</b>\n\n"
            
            for dept, emps in departments.items():
                text += f"<b>{dept}</b> ({len(emps)} чел.):\n"
                for emp in emps[:5]:  # Показываем первых 5
                    score_icon = "🟢" if emp.get("performance_score", 0) >= 7 else "🟡" if emp.get("performance_score", 0) >= 5 else "🔴"
                    text += f"  {score_icon} {emp['full_name']} ({emp.get('role', 'Не указано')})\n"
                
                if len(emps) > 5:
                    text += f"  ... и еще {len(emps) - 5} сотрудников\n"
                text += "\n"
            
            return text
            
        except Exception as e:
            return f"❌ Ошибка получения данных сотрудников: {str(e)}"
    
    async def _get_finances_summary(self) -> str:
        """Финансовая сводка"""
        try:
            # Доходы и расходы за месяц
            month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            
            pipeline = [
                {"$match": {"date": {"$gte": month_start}}},
                {"$group": {
                    "_id": "$category",
                    "total": {"$sum": "$amount"},
                    "count": {"$sum": 1}
                }}
            ]
            
            cursor = self.db.finance_entries.aggregate(pipeline)
            results = await cursor.to_list(length=None)
            
            revenue = next((r["total"] for r in results if r["_id"] == "revenue"), 0)
            expenses = next((r["total"] for r in results if r["_id"] == "expense"), 0)
            profit = revenue - expenses
            
            text = f"""💰 <b>ФИНАНСЫ ЗА МЕСЯЦ</b>

📈 Доходы: {revenue:,.0f} ₽
📉 Расходы: {expenses:,.0f} ₽
💰 Прибыль: {profit:,.0f} ₽

📊 Рентабельность: {(profit/max(revenue, 1)*100):,.1f}%"""
            
            return text
            
        except Exception as e:
            return f"❌ Ошибка получения финансовых данных: {str(e)}"
    
    async def _get_employee_tasks(self, employee_id: str) -> str:
        """Задачи конкретного сотрудника"""
        try:
            # Активные задачи
            tasks = await self.db.tasks.find({
                "assignee_id": employee_id,
                "status": {"$in": ["pending", "in_progress"]}
            }, sort=[("due_date", 1)]).to_list(length=None)
            
            if not tasks:
                return "📋 У вас нет активных задач."
            
            text = f"📋 <b>ВАШИ АКТИВНЫЕ ЗАДАЧИ ({len(tasks)})</b>\n\n"
            
            for i, task in enumerate(tasks[:10], 1):  # Показываем первые 10
                priority_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(task.get("priority", "medium"), "🟡")
                status_icon = {"pending": "⏳", "in_progress": "🔄"}.get(task.get("status", "pending"), "⏳")
                
                due_date = ""
                if task.get("due_date"):
                    due_date = f" (до {task['due_date'].strftime('%d.%m')})"
                
                text += f"{i}. {priority_icon}{status_icon} {task['title']}{due_date}\n"
            
            if len(tasks) > 10:
                text += f"\n... и еще {len(tasks) - 10} задач"
            
            return text
            
        except Exception as e:
            return f"❌ Ошибка получения задач: {str(e)}"
    
    async def _get_ai_analysis(self) -> str:
        """Последний AI анализ"""
        try:
            # Получаем последний анализ
            analysis = await self.db.system_learning.find_one(
                {"event_type": "performance_analysis"},
                sort=[("created_at", -1)]
            )
            
            if not analysis:
                return "🤖 AI анализ еще не проводился. Ожидайте первый анализ в течение 30 минут."
            
            performance = analysis.get("performance_data", {})
            health = performance.get("overall_health", "unknown")
            
            health_emoji = {
                "excellent": "🟢",
                "good": "🟡", 
                "fair": "🟠",
                "poor": "🔴"
            }.get(health, "⚪")
            
            text = f"""🤖 <b>AI АНАЛИЗ СИСТЕМЫ</b>

{health_emoji} Общее состояние: {health.upper()}

📊 Показатели:
• Выполнение задач: {performance.get('tasks', {}).get('completion_rate', 0)*100:.1f}%
• Средняя производительность: {performance.get('employees', {}).get('average_performance', 0):.1f}/10
• Ошибок за день: {performance.get('system_errors', {}).get('total_errors', 0)}

⏰ Анализ от: {analysis['created_at'].strftime('%H:%M %d.%m.%Y')}"""
            
            return text
            
        except Exception as e:
            return f"❌ Ошибка получения AI анализа: {str(e)}"
    
    async def _handle_check_in(self, employee_id: str) -> str:
        """Обработка отметки о прибытии"""
        try:
            # Создаем запись о чек-ине
            checkin = {
                "id": f"checkin_{datetime.utcnow().timestamp()}",
                "employee_id": employee_id,
                "timestamp": datetime.utcnow(),
                "type": "check_in",
                "location": "telegram",  # В будущем можно добавить GPS
                "created_at": datetime.utcnow()
            }
            
            await self.db.employee_checkins.insert_one(checkin)
            
            # Обновляем последнюю активность сотрудника
            await self.db.employees.update_one(
                {"id": employee_id},
                {"$set": {"last_activity": datetime.utcnow()}}
            )
            
            return f"✅ Отметка о прибытии зафиксирована!\n⏰ Время: {datetime.utcnow().strftime('%H:%M %d.%m.%Y')}"
            
        except Exception as e:
            return f"❌ Ошибка при отметке: {str(e)}"
    
    async def process_voice_message(self, voice_data: Dict, user_id: str) -> str:
        """Обрабатывает голосовые сообщения (будущая функция)"""
        # Заглушка для будущей интеграции с распознаванием речи
        return "🎤 Обработка голосовых сообщений будет добавлена в следующем обновлении."
    
    async def set_webhook(self) -> Dict[str, Any]:
        """Устанавливает webhook для бота"""
        try:
            url = f"{self.api_url}/setWebhook"
            payload = {"url": self.webhook_url}
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    result = await response.json()
                    return result
                    
        except Exception as e:
            return {"ok": False, "error": str(e)}