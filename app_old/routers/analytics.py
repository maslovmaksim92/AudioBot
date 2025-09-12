import logging
from datetime import datetime
from fastapi import APIRouter
from ..services.bitrix_service import BitrixService
from ..config.settings import BITRIX24_WEBHOOK_URL

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["analytics"])

@router.get("/analytics")
async def get_analytics():
    """Расширенная аналитика для Фазы 4"""
    try:
        logger.info("📊 Loading analytics data...")
        
        bitrix = BitrixService(BITRIX24_WEBHOOK_URL)
        deals = await bitrix.get_deals(limit=500)
        
        if not deals:
            return {
                "status": "error",
                "message": "No deals data available"
            }
        
        # Аналитика по бригадам
        brigade_stats = {}
        company_stats = {}
        schedule_stats = {
            "scheduled": 0,
            "not_scheduled": 0,
            "total_cleaning_events": 0
        }
        
        for deal in deals:
            # Статистика по бригадам
            brigade = deal.get('brigade', 'Не назначена')
            if brigade not in brigade_stats:
                brigade_stats[brigade] = {
                    "houses": 0,
                    "apartments": 0,
                    "entrances": 0,
                    "floors": 0,
                    "scheduled_houses": 0,
                    "problem_houses": 0
                }
            
            brigade_stats[brigade]["houses"] += 1
            brigade_stats[brigade]["apartments"] += deal.get('apartments_count', 0)
            brigade_stats[brigade]["entrances"] += deal.get('entrances_count', 0)
            brigade_stats[brigade]["floors"] += deal.get('floors_count', 0)
            
            # Проверяем график
            if deal.get('september_schedule', {}).get('has_schedule'):
                brigade_stats[brigade]["scheduled_houses"] += 1
                schedule_stats["scheduled"] += 1
                
                # Подсчет событий уборки
                cleaning_dates_1 = deal.get('september_schedule', {}).get('cleaning_date_1', [])
                cleaning_dates_2 = deal.get('september_schedule', {}).get('cleaning_date_2', [])
                schedule_stats["total_cleaning_events"] += len(cleaning_dates_1) + len(cleaning_dates_2)
            else:
                schedule_stats["not_scheduled"] += 1
            
            # Проблемные дома (по статусу)
            if deal.get('status_color') in ['red', 'yellow']:
                brigade_stats[brigade]["problem_houses"] += 1
            
            # Статистика по УК
            company = deal.get('management_company', 'Не указана')
            if company not in company_stats:
                company_stats[company] = {
                    "houses": 0,
                    "apartments": 0,
                    "avg_apartments": 0
                }
            
            company_stats[company]["houses"] += 1
            company_stats[company]["apartments"] += deal.get('apartments_count', 0)
        
        # Вычисляем средние значения
        for company in company_stats:
            if company_stats[company]["houses"] > 0:
                company_stats[company]["avg_apartments"] = round(
                    company_stats[company]["apartments"] / company_stats[company]["houses"], 1
                )
        
        # KPI расчеты
        total_houses = len(deals)
        coverage_rate = round((schedule_stats["scheduled"] / total_houses * 100), 1) if total_houses > 0 else 0
        
        # Эффективность бригад
        brigade_efficiency = {}
        for brigade, stats in brigade_stats.items():
            if stats["houses"] > 0:
                efficiency = round((stats["scheduled_houses"] / stats["houses"] * 100), 1)
                brigade_efficiency[brigade] = {
                    "coverage": efficiency,
                    "houses_per_brigade": stats["houses"],
                    "avg_apartments": round(stats["apartments"] / stats["houses"], 1) if stats["houses"] > 0 else 0,
                    "problem_rate": round((stats["problem_houses"] / stats["houses"] * 100), 1) if stats["houses"] > 0 else 0
                }
        
        return {
            "status": "success",
            "data": {
                "overview": {
                    "total_houses": total_houses,
                    "coverage_rate": coverage_rate,
                    "total_cleaning_events": schedule_stats["total_cleaning_events"],
                    "avg_events_per_house": round(schedule_stats["total_cleaning_events"] / total_houses, 1) if total_houses > 0 else 0
                },
                "brigade_stats": brigade_stats,
                "brigade_efficiency": brigade_efficiency,
                "company_stats": dict(sorted(company_stats.items(), key=lambda x: x[1]["houses"], reverse=True)[:15]),
                "schedule_distribution": schedule_stats,
                "generated_at": datetime.utcnow().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Analytics error: {e}")
        return {
            "status": "error",
            "message": f"Analytics error: {str(e)}"
        }

@router.get("/calendar")
async def get_cleaning_calendar():
    """Календарь уборок для Фазы 4"""
    try:
        logger.info("📅 Loading cleaning calendar...")
        
        bitrix = BitrixService(BITRIX24_WEBHOOK_URL)
        deals = await bitrix.get_deals(limit=500)
        
        if not deals:
            return {
                "status": "error",
                "message": "No calendar data available"
            }
        
        calendar_events = []
        monthly_summary = {}
        brigade_calendar = {}
        
        for deal in deals:
            address = deal.get('address', 'Неизвестный адрес')
            brigade = deal.get('brigade', 'Не назначена')
            deal_id = deal.get('deal_id', '')
            
            # Инициализация календаря бригады
            if brigade not in brigade_calendar:
                brigade_calendar[brigade] = {
                    "september": [],
                    "october": [],
                    "november": [], 
                    "december": []
                }
            
            # Обрабатываем сентябрь 2025
            september = deal.get('september_schedule', {})
            if september.get('has_schedule'):
                cleaning_dates_1 = september.get('cleaning_date_1', [])
                cleaning_type_1 = september.get('cleaning_type_1', '')
                
                for date_str in cleaning_dates_1:
                    try:
                        date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                        
                        event = {
                            "id": f"{deal_id}_{date_obj.strftime('%Y%m%d')}_1",
                            "title": f"Уборка: {address}",
                            "date": date_obj.strftime('%Y-%m-%d'),
                            "time": date_obj.strftime('%H:%M'),
                            "type": cleaning_type_1,
                            "address": address,
                            "brigade": brigade,
                            "deal_id": deal_id,
                            "month": "september",
                            "status": "scheduled"
                        }
                        
                        calendar_events.append(event)
                        brigade_calendar[brigade]["september"].append(event)
                        
                        # Суммарная статистика по месяцам
                        month_key = date_obj.strftime('%Y-%m')
                        if month_key not in monthly_summary:
                            monthly_summary[month_key] = {
                                "total_events": 0,
                                "brigades": {},
                                "types": {}
                            }
                        
                        monthly_summary[month_key]["total_events"] += 1
                        
                        if brigade not in monthly_summary[month_key]["brigades"]:
                            monthly_summary[month_key]["brigades"][brigade] = 0
                        monthly_summary[month_key]["brigades"][brigade] += 1
                        
                        if cleaning_type_1 not in monthly_summary[month_key]["types"]:
                            monthly_summary[month_key]["types"][cleaning_type_1] = 0
                        monthly_summary[month_key]["types"][cleaning_type_1] += 1
                        
                    except Exception as date_error:
                        logger.warning(f"Date parsing error: {date_error}")
                
                # Вторая уборка в сентябре
                cleaning_dates_2 = september.get('cleaning_date_2', [])
                cleaning_type_2 = september.get('cleaning_type_2', '')
                
                for date_str in cleaning_dates_2:
                    try:
                        date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                        
                        event = {
                            "id": f"{deal_id}_{date_obj.strftime('%Y%m%d')}_2",
                            "title": f"Уборка: {address}",
                            "date": date_obj.strftime('%Y-%m-%d'),
                            "time": date_obj.strftime('%H:%M'),
                            "type": cleaning_type_2,
                            "address": address,
                            "brigade": brigade,
                            "deal_id": deal_id,
                            "month": "september",
                            "status": "scheduled"
                        }
                        
                        calendar_events.append(event)
                        brigade_calendar[brigade]["september"].append(event)
                        
                    except Exception as date_error:
                        logger.warning(f"Date parsing error for second cleaning: {date_error}")
        
        # Сортируем события по дате
        calendar_events.sort(key=lambda x: x['date'])
        
        # Статистика календаря
        calendar_stats = {
            "total_events": len(calendar_events),
            "houses_with_schedule": len([d for d in deals if d.get('september_schedule', {}).get('has_schedule')]),
            "brigades_involved": len([b for b in brigade_calendar if brigade_calendar[b]["september"]]),
            "date_range": {
                "start": calendar_events[0]['date'] if calendar_events else None,
                "end": calendar_events[-1]['date'] if calendar_events else None
            }
        }
        
        return {
            "status": "success",
            "data": {
                "events": calendar_events,
                "monthly_summary": monthly_summary,
                "brigade_calendar": brigade_calendar,
                "statistics": calendar_stats,
                "generated_at": datetime.utcnow().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Calendar error: {e}")
        return {
            "status": "error",
            "message": f"Calendar error: {str(e)}"
        }