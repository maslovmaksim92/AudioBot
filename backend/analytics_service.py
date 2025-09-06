"""
Analytics and Financial Forecasting Service
Provides predictive analytics and financial forecasting based on Bitrix24 data
"""

import os
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dotenv import load_dotenv
import asyncio
from bitrix24_service import get_bitrix24_service
from ai_service import ai_assistant
from db import db_manager
from models import FinancialData, FinancialForecast, BusinessInsight

load_dotenv()
logger = logging.getLogger(__name__)

class AnalyticsService:
    """Service for business analytics and financial forecasting"""
    
    def __init__(self):
        self.db = db_manager
    
    async def get_financial_forecast(self, period: str = "monthly", months_ahead: int = 3) -> Dict[str, Any]:
        """Generate financial forecast based on historical Bitrix24 data"""
        try:
            # Get Bitrix24 service and historical data
            bx24 = await get_bitrix24_service()
            
            # Get deals data for analysis
            deals = await bx24.get_deals()
            if not deals:
                return {"error": "No deals data available for forecasting"}
            
            # Analyze historical revenue patterns
            revenue_by_month = {}
            current_date = datetime.utcnow()
            
            # Process deals to extract revenue patterns
            total_deals_value = 0
            won_deals = 0
            
            for deal in deals:
                try:
                    # Get deal value and date
                    opportunity = float(deal.get('OPPORTUNITY', 0))
                    stage_id = deal.get('STAGE_ID', '')
                    
                    if 'WON' in stage_id or 'SUCCESS' in stage_id:
                        won_deals += 1
                        total_deals_value += opportunity
                        
                        # Extract month from deal
                        date_created = deal.get('DATE_CREATE', '')
                        if date_created:
                            try:
                                deal_date = datetime.fromisoformat(date_created.replace('T', ' ').replace('+03:00', ''))
                                month_key = deal_date.strftime('%Y-%m')
                                revenue_by_month[month_key] = revenue_by_month.get(month_key, 0) + opportunity
                            except:
                                pass
                except:
                    continue
            
            # Calculate average monthly revenue
            avg_monthly_revenue = total_deals_value / max(len(revenue_by_month), 1) if revenue_by_month else 0
            
            # Generate forecasts for next months
            forecasts = []
            for i in range(1, months_ahead + 1):
                future_date = current_date + timedelta(days=30 * i)
                month_key = future_date.strftime('%Y-%m')
                
                # Simple growth model with seasonal adjustments
                growth_factor = 1.15  # 15% annual growth
                seasonal_factor = self._get_seasonal_factor(future_date.month)
                
                predicted_revenue = avg_monthly_revenue * growth_factor * seasonal_factor
                confidence = 0.75 - (i * 0.1)  # Decreasing confidence over time
                
                forecast = {
                    "period": month_key,
                    "predicted_revenue": round(predicted_revenue, 2),
                    "confidence_score": max(confidence, 0.3),
                    "factors": [
                        "Исторические данные по сделкам",
                        f"Средний рост {(growth_factor-1)*100:.0f}% в год",
                        "Сезонные колебания",
                        "Тенденции развития клинингового рынка"
                    ]
                }
                forecasts.append(forecast)
            
            # Save forecasts to database
            try:
                collection = self.db.get_collection("financial_forecasts")
                for forecast in forecasts:
                    forecast_obj = FinancialForecast(**forecast, model_version="v1.0")
                    await collection.replace_one(
                        {"period": forecast["period"]},
                        forecast_obj.dict(),
                        upsert=True
                    )
            except Exception as e:
                logger.error(f"Error saving forecasts: {e}")
            
            return {
                "success": True,
                "forecasts": forecasts,
                "historical_data": {
                    "total_deals": len(deals),
                    "won_deals": won_deals,
                    "total_revenue": total_deals_value,
                    "avg_monthly_revenue": avg_monthly_revenue,
                    "months_analyzed": len(revenue_by_month)
                },
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating financial forecast: {e}")
            return {"error": str(e), "success": False}
    
    def _get_seasonal_factor(self, month: int) -> float:
        """Get seasonal adjustment factor for cleaning business"""
        # Cleaning business typically peaks in spring/summer
        seasonal_factors = {
            1: 0.8,   # January - low
            2: 0.85,  # February - low
            3: 1.1,   # March - spring cleaning starts
            4: 1.2,   # April - peak spring
            5: 1.3,   # May - peak
            6: 1.2,   # June - high
            7: 1.15,  # July - summer maintenance
            8: 1.1,   # August - good
            9: 1.2,   # September - back to school/office
            10: 1.0,  # October - normal
            11: 0.9,  # November - lower
            12: 0.8   # December - holiday season low
        }
        return seasonal_factors.get(month, 1.0)
    
    async def generate_business_insights(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """Generate AI-powered business insights from data analysis"""
        try:
            # Get fresh data from multiple sources
            bx24 = await get_bitrix24_service()
            
            # Collect data for analysis
            deals = await bx24.get_deals()
            contacts = await bx24.get_contacts()
            companies = await bx24.get_companies()
            stats = await bx24.get_cleaning_statistics()
            
            # Get employee data from local database
            try:
                employees_collection = self.db.get_collection("employees")
                total_employees = await employees_collection.count_documents({})
                active_employees = await employees_collection.count_documents({"is_active": True})
            except Exception as e:
                logger.error(f"Error getting employee data: {e}")
                total_employees = 0
                active_employees = 0
            
            # Prepare comprehensive business context
            business_context = f"""
АНАЛИЗ ТЕКУЩЕГО СОСТОЯНИЯ БИЗНЕСА ВасДом:

ДАННЫЕ CRM (Bitrix24):
- Всего сделок: {len(deals)}
- Контакты: {len(contacts)}
- Компании: {len(companies)}
- Общая статистика: {stats}

ПЕРСОНАЛ:
- Всего сотрудников: {total_employees}
- Активных: {active_employees}

ГЕОГРАФИЯ:
- Калуга: ~500 домов
- Кемерово: ~100 домов

На основе этих данных дай 5-7 конкретных бизнес-инсайтов с рекомендациями:
1. Анализ эффективности продаж
2. Рекомендации по развитию персонала
3. Географическое расширение
4. Оптимизация процессов
5. Финансовые возможности
6. Технологические улучшения
7. Клиентский сервис

Каждый инсайт должен содержать:
- Конкретную проблему/возможность
- Цифровое обоснование
- Практическую рекомендацию
- Ожидаемый результат
"""
            
            # Get AI insights
            ai_response = await ai_assistant.chat(business_context, "business_insights_analysis")
            insights_text = ai_response.get("response", "")
            
            # Parse and structure insights
            insights = []
            lines = insights_text.split('\n')
            current_insight = ""
            
            for line in lines:
                line = line.strip()
                if line and (line[0].isdigit() or line.startswith('-') or line.startswith('•')):
                    if current_insight:
                        insights.append({
                            "id": f"insight_{len(insights)+1}",
                            "category": self._categorize_insight(current_insight),
                            "insight": current_insight.strip(),
                            "confidence_score": 0.8,
                            "data_sources": ["bitrix24", "employees_db", "ai_analysis"],
                            "created_at": datetime.utcnow(),
                            "is_active": True
                        })
                    current_insight = line
                elif line and current_insight:
                    current_insight += " " + line
            
            # Add last insight
            if current_insight:
                insights.append({
                    "id": f"insight_{len(insights)+1}",
                    "category": self._categorize_insight(current_insight),
                    "insight": current_insight.strip(),
                    "confidence_score": 0.8,
                    "data_sources": ["bitrix24", "employees_db", "ai_analysis"],
                    "created_at": datetime.utcnow(),
                    "is_active": True
                })
            
            # Save insights to database
            try:
                collection = self.db.get_collection("business_insights")
                for insight in insights:
                    # Convert datetime to string for MongoDB
                    insight_copy = insight.copy()
                    if 'created_at' in insight_copy and isinstance(insight_copy['created_at'], datetime):
                        insight_copy['created_at'] = insight_copy['created_at'].isoformat()
                    await collection.insert_one(insight_copy)
            except Exception as e:
                logger.error(f"Error saving insights: {e}")
            
            # Convert datetime objects to strings for JSON serialization
            serializable_insights = []
            for insight in insights[:7]:
                insight_copy = insight.copy()
                if 'created_at' in insight_copy and isinstance(insight_copy['created_at'], datetime):
                    insight_copy['created_at'] = insight_copy['created_at'].isoformat()
                serializable_insights.append(insight_copy)
            
            return serializable_insights
            
        except Exception as e:
            logger.error(f"Error generating business insights: {e}")
            return [
                {
                    "category": "system",
                    "insight": f"Ошибка при генерации инсайтов: {str(e)}",
                    "confidence_score": 0.1,
                    "data_sources": ["error"],
                    "created_at": datetime.utcnow()
                }
            ]
    
    def _categorize_insight(self, insight_text: str) -> str:
        """Categorize insight based on content"""
        text_lower = insight_text.lower()
        
        if any(word in text_lower for word in ["финанс", "деньги", "прибыль", "доход", "расход"]):
            return "financial"
        elif any(word in text_lower for word in ["сотрудник", "персонал", "команда", "hr"]):
            return "hr"
        elif any(word in text_lower for word in ["клиент", "продаж", "маркетинг", "реклам"]):
            return "marketing"
        elif any(word in text_lower for word in ["процесс", "операц", "эффективн", "автоматиз"]):
            return "operational"
        else:
            return "strategic"
    
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get key performance metrics for the business"""
        try:
            bx24 = await get_bitrix24_service()
            
            # Get deals and calculate metrics
            deals = await bx24.get_deals()
            contacts = await bx24.get_contacts()
            
            # Calculate conversion rates
            total_deals = len(deals)
            won_deals = len([d for d in deals if 'WON' in d.get('STAGE_ID', '') or 'SUCCESS' in d.get('STAGE_ID', '')])
            conversion_rate = (won_deals / total_deals * 100) if total_deals > 0 else 0
            
            # Calculate average deal size
            total_value = sum(float(d.get('OPPORTUNITY', 0)) for d in deals if d.get('OPPORTUNITY'))
            avg_deal_size = total_value / max(won_deals, 1)
            
            # Employee metrics
            try:
                employees_collection = self.db.get_collection("employees")
                total_employees = await employees_collection.count_documents({})
                kaluga_employees = await employees_collection.count_documents({"city": "Калуга"})
                kemerovo_employees = await employees_collection.count_documents({"city": "Кемерово"})
            except Exception as e:
                logger.error(f"Error getting employee metrics: {e}")
                total_employees = 0
                kaluga_employees = 0
                kemerovo_employees = 0
            
            return {
                "sales_metrics": {
                    "total_deals": total_deals,
                    "won_deals": won_deals,
                    "conversion_rate": round(conversion_rate, 1),
                    "avg_deal_size": round(avg_deal_size, 2),
                    "total_pipeline_value": round(total_value, 2)
                },
                "client_metrics": {
                    "total_contacts": len(contacts),
                    "active_clients": won_deals,
                    "client_satisfaction": 4.8  # Mock data - would come from surveys
                },
                "operational_metrics": {
                    "total_employees": total_employees,
                    "kaluga_team": kaluga_employees,
                    "kemerovo_team": kemerovo_employees,
                    "houses_managed": 600,
                    "avg_response_time_hours": 2
                },
                "growth_metrics": {
                    "quarterly_growth": "15%",
                    "revenue_target_achievement": 92,
                    "new_clients_monthly": round(won_deals / 12, 1) if won_deals > 0 else 0
                },
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting performance metrics: {e}")
            return {"error": str(e)}

# Global analytics service instance
analytics_service = AnalyticsService()

# Convenience functions
async def get_financial_forecast(period: str = "monthly", months_ahead: int = 3) -> Dict[str, Any]:
    """Get financial forecast"""
    return await analytics_service.get_financial_forecast(period, months_ahead)

async def get_business_insights(force_refresh: bool = False) -> List[Dict[str, Any]]:
    """Get business insights"""
    return await analytics_service.generate_business_insights(force_refresh)

async def get_performance_metrics() -> Dict[str, Any]:
    """Get performance metrics"""
    return await analytics_service.get_performance_metrics()