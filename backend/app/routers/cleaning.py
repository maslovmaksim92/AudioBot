import logging
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException
from ..models.schemas import House
from ..services.bitrix_service import BitrixService
from ..config.settings import BITRIX24_WEBHOOK_URL

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["cleaning"])

@router.get("/cleaning/houses", response_model=dict)
async def get_cleaning_houses(
    limit: Optional[int] = None,
    brigade: Optional[str] = None,
    cleaning_day: Optional[str] = None
):
    """Все дома из Bitrix24 с фильтрацией по бригадам и дням уборки"""
    try:
        logger.info(f"🏠 Loading houses from CRM with filters: brigade={brigade}, cleaning_day={cleaning_day}")
        
        bitrix = BitrixService(BITRIX24_WEBHOOK_URL)
        deals = await bitrix.get_deals(limit=limit)
        
        houses = []
        for deal in deals:
            address = deal.get('TITLE', 'Без названия')
            deal_id = deal.get('ID', '')
            stage_id = deal.get('STAGE_ID', '')
            
            # Определяем бригаду и статус
            brigade_info = bitrix.analyze_house_brigade(address)
            status_text, status_color = bitrix.get_status_info(stage_id)
            
            # Извлекаем расширенные данные из Bitrix24
            apartments_count = _parse_int(deal.get('UF_CRM_1726148184'))
            floors_count = _parse_int(deal.get('UF_CRM_1726148203'))
            entrances_count = _parse_int(deal.get('UF_CRM_1726148223'))
            tariff = deal.get('UF_CRM_1726148242', '')
            
            # Парсим график уборки
            cleaning_date_1_str = deal.get('UF_CRM_1726148261', '')
            cleaning_type_1 = deal.get('UF_CRM_1726148280', '')
            cleaning_date_2_str = deal.get('UF_CRM_1726148299', '')
            cleaning_type_2 = deal.get('UF_CRM_1726148318', '')
            
            # Преобразуем даты в список
            cleaning_date_1 = _parse_dates(cleaning_date_1_str)
            cleaning_date_2 = _parse_dates(cleaning_date_2_str)
            
            # Определяем дни недели для фильтрации
            cleaning_days = _extract_weekdays(cleaning_date_1 + cleaning_date_2)
            
            from ..models.schemas import House, CleaningSchedule
            
            house_data = House(
                address=address,
                deal_id=deal_id,
                stage=stage_id,
                brigade=brigade_info,
                status_text=status_text,
                status_color=status_color,
                created_date=deal.get('DATE_CREATE'),
                opportunity=deal.get('OPPORTUNITY'),
                last_sync=datetime.utcnow().isoformat(),
                
                # Расширенные данные
                apartments_count=apartments_count,
                floors_count=floors_count,
                entrances_count=entrances_count,
                tariff=tariff,
                
                # График уборки
                september_schedule=CleaningSchedule(
                    cleaning_date_1=cleaning_date_1,
                    cleaning_type_1=cleaning_type_1,
                    cleaning_date_2=cleaning_date_2,
                    cleaning_type_2=cleaning_type_2,
                    frequency=tariff
                ),
                
                cleaning_days=cleaning_days
            )
            
            # Применяем фильтры
            if brigade and brigade.lower() not in brigade_info.lower():
                continue
                
            if cleaning_day and cleaning_day.lower() not in [day.lower() for day in cleaning_days]:
                continue
            
            houses.append(house_data.dict())
        
        logger.info(f"✅ Houses data prepared: {len(houses)} houses (filtered)")
        
        return {
            "status": "success",
            "houses": houses,
            "total": len(houses),
            "filters": {
                "brigade": brigade,
                "cleaning_day": cleaning_day
            },
            "source": "🔥 Bitrix24 CRM с расширенными данными",
            "sync_timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Houses error: {e}")
        return {"status": "error", "message": str(e)}

def _parse_int(value) -> Optional[int]:
    """Парсинг целого числа из строки"""
    if not value:
        return None
    try:
        return int(str(value).strip())
    except (ValueError, TypeError):
        return None

def _parse_dates(date_str: str) -> List[str]:
    """Парсинг дат из строки формата '04.09.2025, 18.09.2025'"""
    if not date_str:
        return []
    
    dates = []
    for date_part in str(date_str).split(','):
        date_part = date_part.strip()
        if date_part and len(date_part) >= 8:  # Минимум для даты
            dates.append(date_part)
    return dates

def _extract_weekdays(dates: List[str]) -> List[str]:
    """Извлечение дней недели из дат"""
    weekdays = set()
    weekday_names = {
        0: 'Понедельник',
        1: 'Вторник', 
        2: 'Среда',
        3: 'Четверг',
        4: 'Пятница',
        5: 'Суббота',
        6: 'Воскресенье'
    }
    
    for date_str in dates:
        try:
            # Парсим дату в формате DD.MM.YYYY
            day, month, year = date_str.split('.')
            from datetime import date
            date_obj = date(int(year), int(month), int(day))
            weekday_name = weekday_names[date_obj.weekday()]
            weekdays.add(weekday_name)
        except (ValueError, IndexError):
            continue
    
    return list(weekdays)

@router.get("/cleaning/filters")
async def get_cleaning_filters():
    """Получить доступные фильтры для домов"""
    try:
        bitrix = BitrixService(BITRIX24_WEBHOOK_URL)
        deals = await bitrix.get_deals(limit=None)
        
        brigades = set()
        cleaning_days = set()
        
        for deal in deals:
            address = deal.get('TITLE', '')
            brigade_info = bitrix.analyze_house_brigade(address)
            brigades.add(brigade_info)
            
            # Извлекаем дни уборки
            cleaning_date_1_str = deal.get('UF_CRM_1726148261', '')
            cleaning_date_2_str = deal.get('UF_CRM_1726148299', '')
            
            dates = _parse_dates(cleaning_date_1_str) + _parse_dates(cleaning_date_2_str)
            weekdays = _extract_weekdays(dates)
            cleaning_days.update(weekdays)
        
        return {
            "status": "success",
            "brigades": sorted(list(brigades)),
            "cleaning_days": sorted(list(cleaning_days)),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Filters error: {e}")
        return {"status": "error", "message": str(e)}

@router.get("/cleaning/brigades")
async def get_brigades():
    """Информация о бригадах"""
    return {
        "status": "success",
        "brigades": [
            {"id": 1, "name": "1 бригада - Центральный район", "employees": 14, "areas": ["Пролетарская", "Баррикад", "Ленина"]},
            {"id": 2, "name": "2 бригада - Никитинский район", "employees": 13, "areas": ["Чижевского", "Никитина", "Телевизионная"]},
            {"id": 3, "name": "3 бригада - Жилетово", "employees": 12, "areas": ["Молодежная", "Широкая"]},
            {"id": 4, "name": "4 бригада - Северный район", "employees": 15, "areas": ["Жукова", "Хрустальная", "Гвардейская"]},
            {"id": 5, "name": "5 бригада - Пригород", "employees": 14, "areas": ["Кондрово", "Пушкина", "Тульская"]},
            {"id": 6, "name": "6 бригада - Окраины", "employees": 14, "areas": ["Остальные районы"]}
        ],
        "total_employees": 82,
        "total_brigades": 6
    }

@router.get("/cleaning/stats")
async def get_cleaning_stats():
    """Статистика по уборке"""
    try:
        bitrix = BitrixService(BITRIX24_WEBHOOK_URL)
        houses_data = await bitrix.get_deals()
        
        # Подсчет статистики по статусам
        stats = {
            "total_houses": len(houses_data),
            "completed": 0,
            "in_progress": 0,
            "problematic": 0,
            "invoiced": 0
        }
        
        for house in houses_data:
            stage = house.get('STAGE_ID', '')
            if stage == 'C2:WON':
                stats["completed"] += 1
            elif 'APOLOGY' in stage or 'LOSE' in stage:
                stats["problematic"] += 1
            elif 'FINAL_INVOICE' in stage:
                stats["invoiced"] += 1
            else:
                stats["in_progress"] += 1
        
        return {
            "status": "success",
            "stats": stats,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Cleaning stats error: {e}")
        return {"status": "error", "message": str(e)}

@router.get("/bitrix24/categories")
async def get_bitrix24_categories():
    """Исследование всех категорий сделок в Bitrix24"""
    try:
        logger.info("🔍 Investigating Bitrix24 categories...")
        
        bitrix = BitrixService(BITRIX24_WEBHOOK_URL)
        
        # Загружаем первые 100 сделок без фильтра по категории
        params = {
            'select[0]': 'ID',
            'select[1]': 'TITLE', 
            'select[2]': 'CATEGORY_ID',
            'select[3]': 'STAGE_ID',
            'order[DATE_CREATE]': 'DESC',
            'start': '0'
        }
        
        import urllib.parse
        query_string = urllib.parse.urlencode(params)
        url = f"{bitrix.webhook_url}crm.deal.list.json?{query_string}"
        
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                deals = data.get('result', [])
                
                # Группируем по категориям
                categories = {}
                for deal in deals:
                    cat_id = deal.get('CATEGORY_ID', 'no_category')
                    stage_id = deal.get('STAGE_ID', 'no_stage')
                    
                    if cat_id not in categories:
                        categories[cat_id] = {
                            'count': 0,
                            'stages': set(),
                            'sample_titles': []
                        }
                    
                    categories[cat_id]['count'] += 1
                    categories[cat_id]['stages'].add(stage_id)
                    
                    if len(categories[cat_id]['sample_titles']) < 3:
                        categories[cat_id]['sample_titles'].append(deal.get('TITLE', ''))
                
                # Преобразуем sets в lists для JSON
                for cat_data in categories.values():
                    cat_data['stages'] = list(cat_data['stages'])
                
                logger.info(f"✅ Found categories: {list(categories.keys())}")
                return {
                    "status": "success",
                    "categories": categories,
                    "total_deals_analyzed": len(deals),
                    "timestamp": datetime.utcnow().isoformat()
                }
            else:
                return {
                    "status": "error",
                    "message": f"Bitrix24 API error: {response.status_code}",
                    "timestamp": datetime.utcnow().isoformat()
                }
                
    except Exception as e:
        logger.error(f"❌ Categories investigation error: {e}")
        return {
            "status": "error",
            "message": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

@router.get("/bitrix24/test")
async def test_bitrix24_integration():
    """Тест интеграции с Bitrix24"""
    try:
        logger.info("🔧 Testing Bitrix24 integration...")
        
        bitrix = BitrixService(BITRIX24_WEBHOOK_URL)  
        deals = await bitrix.get_deals(limit=3)  # Тестируем на 3 домах
        
        if deals and len(deals) > 0:
            test_results = {
                "status": "success",
                "webhook_url": BITRIX24_WEBHOOK_URL[:50] + "..." if len(BITRIX24_WEBHOOK_URL) > 50 else BITRIX24_WEBHOOK_URL,
                "connection": "✅ Connected",
                "sample_deals": len(deals),
                "sample_data": [
                    {
                        "id": deal.get('ID'),
                        "title": deal.get('TITLE', ''),
                        "stage": deal.get('STAGE_ID', ''),
                        "created": deal.get('DATE_CREATE', '')
                    } for deal in deals[:2]  # Показываем только первые 2
                ],
                "timestamp": datetime.utcnow().isoformat()
            }
            
            logger.info(f"✅ Bitrix24 test successful: {len(deals)} deals loaded")
            return test_results
            
        else:
            return {
                "status": "error",
                "webhook_url": "configured" if BITRIX24_WEBHOOK_URL else "not_configured",
                "connection": "❌ No data received",
                "message": "Bitrix24 вернул пустой результат",
                "timestamp": datetime.utcnow().isoformat()
            }
            
    except Exception as e:
        logger.error(f"❌ Bitrix24 test error: {e}")
        return {
            "status": "error",
            "webhook_url": "error" if BITRIX24_WEBHOOK_URL else "not_configured", 
            "connection": "❌ Connection failed",
            "message": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }