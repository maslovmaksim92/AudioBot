import asyncio
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import aiohttp
import os
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)

class AIReflectionService:
    """AI система саморефлексии и самообучения"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.emergent_key = os.getenv("EMERGENT_LLM_KEY")
        self.openrouter_key = os.getenv("OPENROUTER_API_KEY")
        self.learning_threshold = 0.7
        
    async def analyze_system_performance(self) -> Dict[str, Any]:
        """Анализирует общую производительность системы"""
        try:
            # Собираем данные за последние 24 часа
            yesterday = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            
            # Статистика по задачам
            tasks_stats = await self._analyze_tasks_performance(yesterday)
            
            # Статистика по сотрудникам
            employee_stats = await self._analyze_employee_performance()
            
            # Финансовая статистика
            finance_stats = await self._analyze_financial_performance(yesterday)
            
            # Системные ошибки
            system_errors = await self._analyze_system_errors(yesterday)
            
            performance_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "tasks": tasks_stats,
                "employees": employee_stats,
                "finances": finance_stats,
                "system_errors": system_errors,
                "overall_health": self._calculate_health_score(tasks_stats, employee_stats, system_errors)
            }
            
            # AI анализ и предложения
            suggestions = await self._generate_improvement_suggestions(performance_data)
            
            # Сохраняем результат анализа
            await self._save_analysis_result(performance_data, suggestions)
            
            return {
                "performance": performance_data,
                "suggestions": suggestions,
                "learning_status": "active"
            }
            
        except Exception as e:
            logger.error(f"Error in system performance analysis: {str(e)}")
            return {"error": str(e), "learning_status": "error"}
    
    async def _analyze_tasks_performance(self, since: datetime) -> Dict[str, Any]:
        """Анализ производительности задач"""
        pipeline = [
            {"$match": {"created_at": {"$gte": since}}},
            {"$group": {
                "_id": "$status",
                "count": {"$sum": 1},
                "avg_completion_time": {"$avg": {
                    "$cond": {
                        "if": {"$eq": ["$status", "completed"]},
                        "then": {"$subtract": ["$completed_at", "$created_at"]},
                        "else": 0
                    }
                }}
            }}
        ]
        
        cursor = self.db.tasks.aggregate(pipeline)
        results = await cursor.to_list(length=None)
        
        return {
            "total_created": sum(r["count"] for r in results),
            "completion_rate": next((r["count"] for r in results if r["_id"] == "completed"), 0) / max(sum(r["count"] for r in results), 1),
            "average_completion_time": next((r["avg_completion_time"] for r in results if r["_id"] == "completed"), 0),
            "status_breakdown": {r["_id"]: r["count"] for r in results}
        }
    
    async def _analyze_employee_performance(self) -> Dict[str, Any]:
        """Анализ производительности сотрудников"""
        # Получаем активных сотрудников
        employees = await self.db.employees.find({"active": True}).to_list(length=None)
        
        performance_data = []
        
        for employee in employees:
            # Подсчитываем задачи сотрудника за неделю
            week_ago = datetime.utcnow().timestamp() - 7 * 24 * 3600
            
            completed_tasks = await self.db.tasks.count_documents({
                "assignee_id": employee["id"],
                "status": "completed",
                "completed_at": {"$gte": datetime.fromtimestamp(week_ago)}
            })
            
            overdue_tasks = await self.db.tasks.count_documents({
                "assignee_id": employee["id"],
                "status": {"$in": ["pending", "in_progress"]},
                "due_date": {"$lt": datetime.utcnow()}
            })
            
            performance_score = max(0, completed_tasks - overdue_tasks * 0.5)
            
            performance_data.append({
                "employee_id": employee["id"],
                "name": employee["full_name"],
                "completed_tasks": completed_tasks,
                "overdue_tasks": overdue_tasks,
                "performance_score": performance_score,
                "role": employee["role"]
            })
        
        return {
            "total_employees": len(employees),
            "average_performance": sum(p["performance_score"] for p in performance_data) / max(len(performance_data), 1),
            "top_performers": sorted(performance_data, key=lambda x: x["performance_score"], reverse=True)[:5],
            "underperformers": [p for p in performance_data if p["performance_score"] < 3 and p["overdue_tasks"] > 0]
        }
    
    async def _analyze_financial_performance(self, since: datetime) -> Dict[str, Any]:
        """Анализ финансовой производительности"""
        pipeline = [
            {"$match": {"date": {"$gte": since}}},
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
        
        return {
            "daily_revenue": revenue,
            "daily_expenses": expenses,
            "profit": revenue - expenses,
            "profit_margin": (revenue - expenses) / max(revenue, 1) * 100,
            "breakdown": {r["_id"]: r["total"] for r in results}
        }
    
    async def _analyze_system_errors(self, since: datetime) -> Dict[str, Any]:
        """Анализ системных ошибок"""
        errors = await self.db.system_learning.find({
            "event_type": "error",
            "created_at": {"$gte": since}
        }).to_list(length=None)
        
        error_patterns = {}
        for error in errors:
            pattern = error.get("pattern_detected", "unknown")
            error_patterns[pattern] = error_patterns.get(pattern, 0) + 1
        
        return {
            "total_errors": len(errors),
            "error_patterns": error_patterns,
            "critical_errors": [e for e in errors if e.get("confidence_score", 0) > 0.8]
        }
    
    def _calculate_health_score(self, tasks: Dict, employees: Dict, errors: Dict) -> str:
        """Вычисляет общий показатель здоровья системы"""
        score = 100
        
        # Штрафы за плохую производительность
        if tasks.get("completion_rate", 0) < 0.8:
            score -= 20
        
        if employees.get("average_performance", 0) < 5:
            score -= 15
            
        if len(errors.get("critical_errors", [])) > 0:
            score -= 25
            
        if errors.get("total_errors", 0) > 10:
            score -= 10
        
        if score >= 90:
            return "excellent"
        elif score >= 75:
            return "good"
        elif score >= 60:
            return "fair"
        else:
            return "poor"
    
    async def _generate_improvement_suggestions(self, performance_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Генерирует предложения по улучшению с помощью AI"""
        try:
            prompt = f"""
            Analyze the following business performance data and provide specific improvement suggestions:

            System Performance Data:
            {json.dumps(performance_data, indent=2)}

            Please provide 3-5 specific, actionable improvement suggestions in JSON format:
            [
                {{
                    "title": "Suggestion title",
                    "description": "Detailed description",
                    "category": "process|technology|training|management",
                    "impact_score": 8.5,
                    "effort_score": 6.0,
                    "implementation_steps": ["step1", "step2", "step3"]
                }}
            ]

            Focus on:
            1. Task completion efficiency
            2. Employee performance optimization  
            3. Cost reduction opportunities
            4. Process automation possibilities
            5. System reliability improvements
            """
            
            suggestions = await self._call_ai_service(prompt)
            
            # Сохраняем каждое предложение в БД
            for suggestion in suggestions:
                await self.db.improvements.insert_one({
                    "id": str(datetime.utcnow().timestamp()),
                    "title": suggestion.get("title", "AI Suggestion"),
                    "description": suggestion.get("description", ""),
                    "category": suggestion.get("category", "process"),
                    "suggested_by": "AI",
                    "impact_score": suggestion.get("impact_score", 5.0),
                    "effort_score": suggestion.get("effort_score", 5.0),
                    "status": "suggested",
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                })
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Error generating AI suggestions: {str(e)}")
            return [{"title": "System Analysis", "description": "Basic system monitoring active", "category": "system", "impact_score": 3.0, "effort_score": 1.0}]
    
    async def _call_ai_service(self, prompt: str) -> List[Dict[str, Any]]:
        """Вызывает AI сервис для анализа"""
        try:
            url = "https://emergentmethods.ai/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.emergent_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": "You are a business intelligence AI assistant that provides actionable improvement suggestions based on performance data. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 1500
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=data, timeout=30) as response:
                    if response.status == 200:
                        result = await response.json()
                        content = result["choices"][0]["message"]["content"]
                        
                        # Парсим JSON из ответа
                        try:
                            suggestions = json.loads(content)
                            return suggestions if isinstance(suggestions, list) else [suggestions]
                        except json.JSONDecodeError:
                            # Fallback если не удалось распарсить JSON
                            return [{"title": "AI Analysis", "description": content, "category": "general", "impact_score": 5.0, "effort_score": 3.0}]
                    else:
                        logger.error(f"AI API error: {response.status}")
                        return []
                        
        except Exception as e:
            logger.error(f"Error calling AI service: {str(e)}")
            return []
    
    async def _save_analysis_result(self, performance_data: Dict, suggestions: List[Dict]):
        """Сохраняет результат анализа в БД"""
        analysis_result = {
            "id": str(datetime.utcnow().timestamp()),
            "timestamp": datetime.utcnow(),
            "performance_data": performance_data,
            "suggestions_count": len(suggestions),
            "system_health": performance_data.get("overall_health", "unknown"),
            "created_at": datetime.utcnow()
        }
        
        await self.db.system_learning.insert_one({
            **analysis_result,
            "event_type": "performance_analysis",
            "confidence_score": 0.9
        })
    
    async def learn_from_feedback(self, feedback_data: Dict[str, Any]) -> Dict[str, Any]:
        """Учится на основе обратной связи пользователей"""
        try:
            learning_entry = {
                "id": str(datetime.utcnow().timestamp()),
                "event_type": "user_feedback",
                "data": feedback_data,
                "confidence_score": feedback_data.get("rating", 3) / 5.0,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            # Анализируем паттерны в обратной связи
            if feedback_data.get("rating", 0) < 3:
                learning_entry["pattern_detected"] = "low_satisfaction"
                learning_entry["action_taken"] = "schedule_improvement_analysis"
            
            await self.db.system_learning.insert_one(learning_entry)
            
            return {"status": "learned", "confidence": learning_entry["confidence_score"]}
            
        except Exception as e:
            logger.error(f"Error learning from feedback: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    async def get_ai_insights(self) -> Dict[str, Any]:
        """Возвращает текущие AI инсайты и предложения"""
        # Последние предложения по улучшению
        recent_suggestions = await self.db.improvements.find(
            {"status": {"$in": ["suggested", "approved"]}},
            sort=[("created_at", -1)]
        ).limit(5).to_list(length=None)
        
        # Последние паттерны обучения
        learning_patterns = await self.db.system_learning.find(
            {"pattern_detected": {"$exists": True}},
            sort=[("created_at", -1)]
        ).limit(10).to_list(length=None)
        
        return {
            "active_suggestions": len([s for s in recent_suggestions if s["status"] == "suggested"]),
            "implemented_improvements": len([s for s in recent_suggestions if s["status"] == "completed"]),
            "recent_suggestions": recent_suggestions,
            "learning_patterns": learning_patterns,
            "ai_status": "active_learning"
        }

# Background task для непрерывного обучения
async def continuous_learning_task(ai_service: AIReflectionService):
    """Фоновая задача для непрерывного обучения системы"""
    while True:
        try:
            logger.info("Starting continuous learning cycle...")
            
            # Анализируем систему каждые 30 минут
            analysis = await ai_service.analyze_system_performance()
            logger.info(f"System analysis completed: {analysis.get('learning_status', 'unknown')}")
            
            # Ждем 30 минут до следующего анализа
            await asyncio.sleep(1800)  # 30 minutes
            
        except Exception as e:
            logger.error(f"Error in continuous learning: {str(e)}")
            await asyncio.sleep(300)  # Wait 5 minutes on error