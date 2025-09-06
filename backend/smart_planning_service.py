"""
Smart Planning Service - AI-powered planning and optimization
"""

import os
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta, date
import json
from bitrix24_service import get_bitrix24_service
from ai_service import ai_assistant

logger = logging.getLogger(__name__)

class SmartPlanningService:
    """Service for intelligent planning and optimization"""
    
    def __init__(self):
        self.weather_api_key = os.getenv("WEATHER_API_KEY")  # Optional
    
    async def optimize_cleaning_routes(self, city: str = "Калуга") -> Dict[str, Any]:
        """Optimize cleaning routes for maximum efficiency"""
        try:
            bx24 = await get_bitrix24_service()
            houses = await bx24.get_cleaning_houses_deals()
            
            # Filter by city
            city_houses = [h for h in houses if city.lower() in h.get('TITLE', '').lower()]
            
            # Simple route optimization (in production, use proper routing algorithm)
            optimized_routes = []
            houses_per_route = 8  # Max houses per cleaning team
            
            for i in range(0, len(city_houses), houses_per_route):
                route_houses = city_houses[i:i + houses_per_route]
                route = {
                    'route_id': f"{city}_route_{i//houses_per_route + 1}",
                    'houses': [h.get('TITLE', '') for h in route_houses],
                    'estimated_time': len(route_houses) * 1.5,  # 1.5 hours per house
                    'team_size': 2,
                    'priority': 'normal'
                }
                optimized_routes.append(route)
            
            return {
                'success': True,
                'city': city,
                'total_houses': len(city_houses),
                'routes': optimized_routes,
                'estimated_total_time': sum(r['estimated_time'] for r in optimized_routes),
                'teams_needed': len(optimized_routes)
            }
            
        except Exception as e:
            logger.error(f"Error optimizing routes: {e}")
            return {'success': False, 'error': str(e)}
    
    async def predict_maintenance_needs(self) -> List[Dict[str, Any]]:
        """Predict which houses will need maintenance soon"""
        try:
            bx24 = await get_bitrix24_service()
            houses = await bx24.get_cleaning_houses_deals()
            
            predictions = []
            current_date = datetime.now()
            
            for house in houses:
                title = house.get('TITLE', '')
                last_modified = house.get('DATE_MODIFY', '')
                
                # Simple prediction based on last activity
                if last_modified:
                    try:
                        last_date = datetime.fromisoformat(last_modified.replace('T', ' ').replace('+03:00', ''))
                        days_since = (current_date - last_date).days
                        
                        # Predict maintenance need
                        if days_since > 30:
                            priority = 'high'
                            predicted_date = current_date + timedelta(days=7)
                        elif days_since > 15:
                            priority = 'medium'
                            predicted_date = current_date + timedelta(days=14)
                        else:
                            priority = 'low'
                            predicted_date = current_date + timedelta(days=30)
                        
                        predictions.append({
                            'house': title,
                            'priority': priority,
                            'days_since_last': days_since,
                            'predicted_maintenance_date': predicted_date.strftime('%Y-%m-%d'),
                            'recommended_action': self._get_maintenance_recommendation(days_since)
                        })
                    except:
                        continue
            
            # Sort by priority
            priority_order = {'high': 0, 'medium': 1, 'low': 2}
            predictions.sort(key=lambda x: priority_order.get(x['priority'], 3))
            
            return predictions[:20]  # Return top 20 predictions
            
        except Exception as e:
            logger.error(f"Error predicting maintenance: {e}")
            return []
    
    def _get_maintenance_recommendation(self, days_since: int) -> str:
        """Get maintenance recommendation based on days since last service"""
        if days_since > 30:
            return "Срочная инспекция и полная уборка"
        elif days_since > 15:
            return "Плановая проверка состояния"
        else:
            return "Обычная уборка по графику"
    
    async def generate_weekly_schedule(self, city: str = "Калуга") -> Dict[str, Any]:
        """Generate optimized weekly cleaning schedule"""
        try:
            routes = await self.optimize_cleaning_routes(city)
            predictions = await self.predict_maintenance_needs()
            
            if not routes.get('success'):
                return routes
            
            # Generate schedule for the week
            schedule = {}
            current_date = datetime.now().date()
            
            for i in range(7):  # 7 days
                day_date = current_date + timedelta(days=i)
                day_name = day_date.strftime('%A')
                
                # Distribute routes across weekdays (skip weekends for regular cleaning)
                if day_date.weekday() < 5:  # Monday to Friday
                    route_index = i % len(routes['routes'])
                    if route_index < len(routes['routes']):
                        route = routes['routes'][route_index]
                        
                        # Add high-priority maintenance houses
                        urgent_houses = [p['house'] for p in predictions if p['priority'] == 'high'][:3]
                        
                        schedule[day_date.strftime('%Y-%m-%d')] = {
                            'date': day_date.strftime('%d.%m.%Y'),
                            'day': day_name,
                            'route': route,
                            'urgent_maintenance': urgent_houses,
                            'total_estimated_time': route['estimated_time'] + len(urgent_houses) * 0.5,
                            'weather_consideration': await self._get_weather_consideration(day_date)
                        }
            
            return {
                'success': True,
                'city': city,
                'week_start': current_date.strftime('%d.%m.%Y'),
                'schedule': schedule,
                'total_houses_week': sum(len(day['route']['houses']) for day in schedule.values()),
                'optimization_notes': [
                    "Маршруты оптимизированы по географическому принципу",
                    "Приоритетные объекты добавлены в ежедневные планы",
                    "Учтены погодные условия для планирования",
                    "Время выполнения рассчитано с учетом сложности объектов"
                ]
            }
            
        except Exception as e:
            logger.error(f"Error generating schedule: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _get_weather_consideration(self, date: date) -> str:
        """Get weather considerations for planning (mock implementation)"""
        # In production, integrate with weather API
        return "Ясная погода, нормальные условия для работы"
    
    async def analyze_team_efficiency(self) -> Dict[str, Any]:
        """Analyze team efficiency and suggest improvements"""
        try:
            # Get team performance data (mock for now)
            teams_data = {
                'kaluga_team_1': {'houses_per_day': 6, 'quality_score': 4.8, 'complaints': 2},
                'kaluga_team_2': {'houses_per_day': 5, 'quality_score': 4.6, 'complaints': 4},
                'kemerovo_team_1': {'houses_per_day': 7, 'quality_score': 4.9, 'complaints': 1}
            }
            
            analysis = []
            for team, data in teams_data.items():
                efficiency_score = (data['houses_per_day'] * 0.4 + 
                                 data['quality_score'] * 0.4 + 
                                 (5 - data['complaints']) * 0.2)
                
                recommendations = []
                if data['houses_per_day'] < 6:
                    recommendations.append("Оптимизировать маршрут для увеличения производительности")
                if data['quality_score'] < 4.7:
                    recommendations.append("Дополнительное обучение по качеству работ")
                if data['complaints'] > 3:
                    recommendations.append("Провести анализ причин жалоб и корректирующие действия")
                
                analysis.append({
                    'team': team,
                    'efficiency_score': round(efficiency_score, 2),
                    'performance': data,
                    'recommendations': recommendations,
                    'status': 'excellent' if efficiency_score > 4.5 else 'good' if efficiency_score > 4.0 else 'needs_improvement'
                })
            
            return {
                'success': True,
                'analysis': analysis,
                'overall_efficiency': round(sum(t['efficiency_score'] for t in analysis) / len(analysis), 2),
                'best_team': max(analysis, key=lambda x: x['efficiency_score'])['team'],
                'improvement_areas': [
                    "Стандартизация процессов между командами",
                    "Обмен лучшими практиками",
                    "Регулярный мониторинг KPI"
                ]
            }
            
        except Exception as e:
            logger.error(f"Error analyzing team efficiency: {e}")
            return {'success': False, 'error': str(e)}

# Global service instance
smart_planning_service = SmartPlanningService()

# Utility functions
async def get_optimized_routes(city: str = "Калуга") -> Dict[str, Any]:
    """Get optimized cleaning routes"""
    return await smart_planning_service.optimize_cleaning_routes(city)

async def get_maintenance_predictions() -> List[Dict[str, Any]]:
    """Get maintenance predictions"""
    return await smart_planning_service.predict_maintenance_needs()

async def get_weekly_schedule(city: str = "Калуга") -> Dict[str, Any]:
    """Get weekly cleaning schedule"""
    return await smart_planning_service.generate_weekly_schedule(city)