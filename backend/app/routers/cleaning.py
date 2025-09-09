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
async def get_cleaning_houses(limit: Optional[int] = None):
    """Все дома из Bitrix24"""
    try:
        logger.info(f"🏠 Loading houses from CRM...")
        
        bitrix = BitrixService(BITRIX24_WEBHOOK_URL)
        deals = await bitrix.get_deals(limit=limit)
        
        houses = []
        for deal in deals:
            address = deal.get('TITLE', 'Без названия')
            deal_id = deal.get('ID', '')
            stage_id = deal.get('STAGE_ID', '')
            
            # Определяем бригаду и статус
            brigade = bitrix.analyze_house_brigade(address)
            status_text, status_color = bitrix.get_status_info(stage_id)
            
            house_data = House(
                address=address,
                deal_id=deal_id,
                stage=stage_id,
                brigade=brigade,
                status_text=status_text,
                status_color=status_color,
                created_date=deal.get('DATE_CREATE'),
                opportunity=deal.get('OPPORTUNITY'),
                last_sync=datetime.utcnow().isoformat()
            )
            
            houses.append(house_data.dict())
        
        logger.info(f"✅ Houses data prepared: {len(houses)} houses")
        
        return {
            "status": "success",
            "houses": houses,
            "total": len(houses),
            "source": "🔥 Bitrix24 CRM",
            "sync_timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Houses error: {e}")
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