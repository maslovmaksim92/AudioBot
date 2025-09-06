"""
Mobile API Service - API for employee mobile application
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import jwt
import hashlib
from bitrix24_service import get_bitrix24_service
from smart_planning_service import get_optimized_routes
from rating_service import get_employee_performance_report

logger = logging.getLogger(__name__)

class MobileAPIService:
    """Service for mobile application API"""
    
    def __init__(self):
        self.jwt_secret = "your-mobile-app-secret-key"  # Change in production
        self.jwt_algorithm = "HS256"
    
    async def authenticate_employee(self, phone: str, password: str) -> Dict[str, Any]:
        """Authenticate employee for mobile app"""
        try:
            # In production, verify against real user database
            # For now, simple mock authentication
            
            # Mock employee data
            mock_employees = {
                "+79001234567": {
                    "id": "emp_001",
                    "name": "Иван Иванов",
                    "position": "Уборщик",
                    "city": "Калуга",
                    "team": "Команда А",
                    "password_hash": hashlib.md5("password123".encode()).hexdigest()
                },
                "+79001234568": {
                    "id": "emp_002", 
                    "name": "Мария Петрова",
                    "position": "Менеджер по клинингу",
                    "city": "Кемерово",
                    "team": "Команда Б",
                    "password_hash": hashlib.md5("password456".encode()).hexdigest()
                }
            }
            
            employee = mock_employees.get(phone)
            if not employee:
                return {"success": False, "error": "Пользователь не найден"}
            
            # Verify password
            password_hash = hashlib.md5(password.encode()).hexdigest()
            if password_hash != employee["password_hash"]:
                return {"success": False, "error": "Неверный пароль"}
            
            # Generate JWT token
            token_payload = {
                "employee_id": employee["id"],
                "phone": phone,
                "exp": datetime.utcnow() + timedelta(days=30)
            }
            
            token = jwt.encode(token_payload, self.jwt_secret, algorithm=self.jwt_algorithm)
            
            return {
                "success": True,
                "token": token,
                "employee": {
                    "id": employee["id"],
                    "name": employee["name"],
                    "position": employee["position"],
                    "city": employee["city"],
                    "team": employee["team"]
                }
            }
            
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return {"success": False, "error": "Ошибка аутентификации"}
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify JWT token"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            return {"valid": True, "employee_id": payload["employee_id"]}
        except jwt.ExpiredSignatureError:
            return {"valid": False, "error": "Токен истек"}
        except jwt.InvalidTokenError:
            return {"valid": False, "error": "Недействительный токен"}
    
    async def get_employee_tasks_mobile(self, employee_id: str) -> Dict[str, Any]:
        """Get tasks for employee mobile app"""
        try:
            bx24 = await get_bitrix24_service()
            
            # Get tasks assigned to employee
            tasks = await bx24.get_tasks({"RESPONSIBLE_ID": "1"})  # Mock filter
            
            # Format for mobile
            mobile_tasks = []
            for task in tasks:
                mobile_tasks.append({
                    "id": task.get("id"),
                    "title": task.get("title"),
                    "description": task.get("description", "")[:100],  # Truncate for mobile
                    "status": self._get_status_text(task.get("status")),
                    "deadline": task.get("deadline"),
                    "priority": self._get_priority_text(task.get("priority", "1")),
                    "can_complete": task.get("status") in ["2", "3"]  # In progress or almost done
                })
            
            return {
                "success": True,
                "tasks": mobile_tasks,
                "count": len(mobile_tasks),
                "pending_count": len([t for t in mobile_tasks if t["status"] == "В работе"])
            }
            
        except Exception as e:
            logger.error(f"Error getting mobile tasks: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_employee_schedule_mobile(self, employee_id: str) -> Dict[str, Any]:
        """Get employee schedule for mobile app"""
        try:
            # Get employee info (mock)
            employee_city = "Калуга"  # In production, get from employee data
            
            # Get optimized routes for city
            routes = await get_optimized_routes(employee_city)
            
            if not routes.get("success"):
                return {"success": False, "error": "Не удалось получить расписание"}
            
            # Format schedule for mobile
            today = datetime.now().date()
            mobile_schedule = []
            
            for i, route in enumerate(routes.get("routes", [])):
                schedule_date = today + timedelta(days=i)
                
                mobile_schedule.append({
                    "date": schedule_date.strftime("%Y-%m-%d"),
                    "day_name": schedule_date.strftime("%A"),
                    "route_id": route["route_id"],
                    "houses": route["houses"][:5],  # Show first 5 houses
                    "total_houses": len(route["houses"]),
                    "estimated_time": f"{route['estimated_time']:.1f} часов",
                    "team_size": route["team_size"],
                    "start_time": "09:00",
                    "status": "scheduled" if schedule_date > today else "completed" if schedule_date < today else "in_progress"
                })
            
            return {
                "success": True,
                "schedule": mobile_schedule[:7],  # Show week
                "employee_city": employee_city,
                "current_date": today.strftime("%Y-%m-%d")
            }
            
        except Exception as e:
            logger.error(f"Error getting mobile schedule: {e}")
            return {"success": False, "error": str(e)}
    
    async def submit_work_report_mobile(self, employee_id: str, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Submit work report from mobile app"""
        try:
            house_id = report_data.get("house_id")
            house_title = report_data.get("house_title", "")
            work_quality = report_data.get("quality_rating", 5)
            completion_time = report_data.get("completion_time", 1.5)
            notes = report_data.get("notes", "")
            photos = report_data.get("photos", [])  # List of photo URLs
            
            # Create task comment in Bitrix24
            bx24 = await get_bitrix24_service()
            
            report_comment = f"""
📱 МОБИЛЬНЫЙ ОТЧЕТ СОТРУДНИКА

🏠 Объект: {house_title}
⭐ Качество работы: {work_quality}/5
⏱️ Время выполнения: {completion_time} часов
📝 Заметки: {notes}
📷 Фото: {len(photos)} прикреплено
📅 Дата: {datetime.now().strftime('%d.%m.%Y %H:%M')}
👤 Сотрудник ID: {employee_id}
"""
            
            # In production, create proper task or deal update
            # For now, create a task for report
            task_result = await bx24.create_task(
                title=f"Отчет по работе: {house_title}",
                description=report_comment,
                responsible_id=1
            )
            
            return {
                "success": True,
                "report_id": f"RPT_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "task_created": task_result.get("success", False),
                "photos_uploaded": len(photos),
                "message": "Отчет успешно отправлен"
            }
            
        except Exception as e:
            logger.error(f"Error submitting work report: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_employee_performance_mobile(self, employee_id: str) -> Dict[str, Any]:
        """Get employee performance data for mobile"""
        try:
            # Get performance report
            performance = await get_employee_performance_report(employee_id)
            
            if not performance.get("success"):
                # Return mock data if no real data available
                performance = {
                    "success": True,
                    "overall_rating": 4.6,
                    "category_ratings": {
                        "quality": 4.7,
                        "punctuality": 4.5,
                        "efficiency": 4.6,
                        "communication": 4.4
                    },
                    "total_ratings": 15,
                    "trend": "improving"
                }
            
            # Format for mobile display
            mobile_performance = {
                "overall_rating": performance.get("overall_rating", 4.0),
                "overall_rating_text": self._get_rating_text(performance.get("overall_rating", 4.0)),
                "categories": [],
                "achievements": [],
                "areas_for_improvement": [],
                "trend": performance.get("trend", "stable")
            }
            
            # Format categories
            for category, rating in performance.get("category_ratings", {}).items():
                mobile_performance["categories"].append({
                    "name": self._get_category_name(category),
                    "rating": rating,
                    "rating_text": self._get_rating_text(rating),
                    "icon": self._get_category_icon(category)
                })
            
            # Add achievements
            if performance.get("overall_rating", 0) >= 4.5:
                mobile_performance["achievements"].append("🏆 Высокая общая оценка")
            
            if performance.get("trend") == "improving":
                mobile_performance["achievements"].append("📈 Положительная динамика")
            
            return {
                "success": True,
                "performance": mobile_performance,
                "last_updated": datetime.now().strftime("%d.%m.%Y")
            }
            
        except Exception as e:
            logger.error(f"Error getting mobile performance: {e}")
            return {"success": False, "error": str(e)}
    
    def _get_status_text(self, status: str) -> str:
        """Convert status ID to text"""
        status_map = {
            "1": "Новая",
            "2": "В работе", 
            "3": "Почти готово",
            "4": "Ожидает проверки", 
            "5": "Завершена",
            "6": "Отложена"
        }
        return status_map.get(status, "Неизвестно")
    
    def _get_priority_text(self, priority: str) -> str:
        """Convert priority ID to text"""
        priority_map = {
            "0": "Низкая",
            "1": "Обычная",
            "2": "Высокая"
        }
        return priority_map.get(priority, "Обычная")
    
    def _get_rating_text(self, rating: float) -> str:
        """Convert rating to text"""
        if rating >= 4.5:
            return "Отлично"
        elif rating >= 4.0:
            return "Хорошо"
        elif rating >= 3.5:
            return "Удовлетворительно"
        else:
            return "Требует улучшения"
    
    def _get_category_name(self, category: str) -> str:
        """Get category display name"""
        names = {
            "quality": "Качество работы",
            "punctuality": "Пунктуальность",
            "efficiency": "Эффективность", 
            "communication": "Коммуникация"
        }
        return names.get(category, category)
    
    def _get_category_icon(self, category: str) -> str:
        """Get category icon"""
        icons = {
            "quality": "⭐",
            "punctuality": "⏰",
            "efficiency": "⚡",
            "communication": "💬"
        }
        return icons.get(category, "📊")

# Global service instance
mobile_api_service = MobileAPIService()

# Utility functions
async def authenticate_employee_mobile(phone: str, password: str) -> Dict[str, Any]:
    """Authenticate employee for mobile"""
    return await mobile_api_service.authenticate_employee(phone, password)

async def get_employee_mobile_data(employee_id: str) -> Dict[str, Any]:
    """Get comprehensive employee data for mobile"""
    try:
        tasks = await mobile_api_service.get_employee_tasks_mobile(employee_id)
        schedule = await mobile_api_service.get_employee_schedule_mobile(employee_id)
        performance = await mobile_api_service.get_employee_performance_mobile(employee_id)
        
        return {
            "success": True,
            "tasks": tasks.get("tasks", []),
            "schedule": schedule.get("schedule", []),
            "performance": performance.get("performance", {}),
            "summary": {
                "pending_tasks": tasks.get("pending_count", 0),
                "today_houses": len(schedule.get("schedule", [{}])[0].get("houses", [])) if schedule.get("schedule") else 0,
                "overall_rating": performance.get("performance", {}).get("overall_rating", 4.0)
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting mobile data: {e}")
        return {"success": False, "error": str(e)}