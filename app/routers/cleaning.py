import logging
from datetime import datetime
from typing import Optional
from fastapi import APIRouter
from ..models.schemas import House
from ..services.bitrix_service import BitrixService
from ..config.settings import BITRIX24_WEBHOOK_URL

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["cleaning"])

@router.get("/cleaning/houses", response_model=dict)
async def get_cleaning_houses(limit: Optional[int] = None):
    """Все дома из Bitrix24 (старая категория - 348 домов)"""
    try:
        logger.info("🏠 Loading houses from CRM (old category)...")
        
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
            "source": "🔥 Bitrix24 CRM (Category 34)",
            "sync_timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Houses error: {e}")
        return {"status": "error", "message": str(e)}

@router.get("/cleaning/houses-490", response_model=dict)
async def get_cleaning_houses_490():
    """Новый endpoint - 490 домов из правильной категории Bitrix24"""
    try:
        logger.info("🏠 Loading 490 houses from CRM (Category 34)...")
        
        bitrix = BitrixService(BITRIX24_WEBHOOK_URL)
        deals = await bitrix.get_deals(limit=500)  # Загружаем все 490+ домов
        
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
        
        logger.info(f"✅ Houses-490 data prepared: {len(houses)} houses")
        
        return {
            "status": "success",
            "houses": houses,
            "total": len(houses),
            "source": "🔥 Bitrix24 CRM - 490 Houses (Category 34)",
            "category_id": "34",
            "sync_timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Houses-490 error: {e}")
        return {"status": "error", "message": str(e)}

@router.get("/force-houses-490")
async def force_houses_490():
    """Принудительная загрузка 490 домов"""
    try:
        logger.info("🔄 FORCE loading 490 houses...")
        
        # Сначала проверяем подключение к Bitrix24
        bitrix = BitrixService(BITRIX24_WEBHOOK_URL)
        test_deals = await bitrix.get_deals(limit=1)
        
        if not test_deals:
            return {
                "status": "error", 
                "message": "❌ Нет подключения к Bitrix24",
                "webhook_url": BITRIX24_WEBHOOK_URL[:50] + "..."
            }
        
        # Принудительно загружаем все дома
        all_deals = await bitrix.get_deals(limit=600)
        
        logger.info(f"🔥 FORCE loaded {len(all_deals)} houses from Bitrix24")
        
        return {
            "status": "success",
            "message": f"✅ Принудительно загружено {len(all_deals)} домов",
            "houses_count": len(all_deals),
            "category_id": "34",
            "source": "Bitrix24 CRM",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Force houses error: {e}")
        return {"status": "error", "message": str(e)}

@router.get("/debug-houses")
async def debug_houses():
    """Отладочный endpoint для диагностики"""
    try:
        logger.info("🔧 Debug houses endpoint called...")
        
        debug_info = {
            "status": "success",
            "bitrix24_webhook": BITRIX24_WEBHOOK_URL[:50] + "..." if BITRIX24_WEBHOOK_URL else "❌ Not configured",
            "category_info": {
                "old_category": "2 (348 домов)",
                "new_category": "34 (490 домов) ✅ ИСПОЛЬЗУЕТСЯ",
                "current_filter": "CATEGORY_ID=34"
            },
            "endpoints": {
                "/api/cleaning/houses": "Старый endpoint (348 домов)",
                "/api/cleaning/houses-490": "✅ Новый endpoint (490 домов)",
                "/api/force-houses-490": "✅ Принудительная загрузка",
                "/api/debug-houses": "✅ Этот отладочный endpoint"
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Проверяем подключение к Bitrix24
        if BITRIX24_WEBHOOK_URL:
            try:
                bitrix = BitrixService(BITRIX24_WEBHOOK_URL)
                test_deals = await bitrix.get_deals(limit=1)
                
                debug_info["bitrix_connection"] = {
                    "status": "✅ Connected" if test_deals else "⚠️ Connected but no data",
                    "test_deals_count": len(test_deals) if test_deals else 0,
                    "sample_deal": test_deals[0] if test_deals else None
                }
            except Exception as conn_error:
                debug_info["bitrix_connection"] = {
                    "status": "❌ Connection failed",
                    "error": str(conn_error)
                }
        
        return debug_info
        
    except Exception as e:
        logger.error(f"❌ Debug houses error: {e}")
        return {"status": "error", "message": str(e)}

@router.get("/version-check")
async def version_check():
    """Проверка версии кода"""
    return {
        "status": "success",
        "version": "3.0.0",
        "app_name": "VasDom AudioBot API",
        "category_fix": "✅ Fixed CATEGORY_ID=34 (490 houses)",
        "endpoints_added": [
            "/api/cleaning/houses-490",
            "/api/force-houses-490", 
            "/api/debug-houses",
            "/api/version-check"
        ],
        "timestamp": datetime.utcnow().isoformat()
    }

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