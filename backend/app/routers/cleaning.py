"""
Cleaning router: Bitrix listing + brigade filtering (assigned) + details
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import logging

from backend.app.config.database import get_db
from backend.app.services.bitrix24_service import bitrix24_service
from backend.app.utils.auth_deps import get_current_user_optional, CurrentUser

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/cleaning", tags=["Cleaning"])

@router.get("/houses")
async def get_cleaning_houses(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=1000),
    address: Optional[str] = None,
    brigade: Optional[str] = None,
    status: Optional[str] = None,
    management_company: Optional[str] = None,
    cleaning_date: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current: Optional[CurrentUser] = Depends(get_current_user_optional)
):
    try:
        effective_brigade = brigade
        # RBAC: если пользователь-бригада, фильтруем строго по номеру из его логина (brigadaN)
        if current and current.is_brigade() and not brigade:
            # извлечём число из brigade_number
            if current.brigade_number:
                effective_brigade = current.brigade_number
        # Если есть поиск по адресу - загружаем ВСЕ дома (без пагинации)
        if address:
            logger.info(f"[cleaning] Searching for address: {address}")
            # Загружаем больше домов для поиска
            data = await bitrix24_service.list_houses(
                brigade=effective_brigade,
                status=status,
                management_company=management_company,
                cleaning_date=cleaning_date,
                date_from=date_from,
                date_to=date_to,
                page=1,
                limit=1000,  # Загружаем много домов для поиска
            )
            # Фильтрация по адресу
            all_houses = data.get('houses', [])
            filtered_houses = [
                h for h in all_houses 
                if address.lower() in (h.get('address') or '').lower() 
                or address.lower() in (h.get('title') or '').lower()
            ]
            logger.info(f"[cleaning] Found {len(filtered_houses)} houses matching '{address}'")
            
            # Применяем пагинацию к отфильтрованным домам
            total = len(filtered_houses)
            start = (page - 1) * limit
            end = start + limit
            paginated_houses = filtered_houses[start:end]
            
            return {
                'houses': paginated_houses,
                'total': total,
                'page': page,
                'limit': limit,
                'pages': (total + limit - 1) // limit if total > 0 else 0
            }
        else:
            # Обычная загрузка с пагинацией
            data = await bitrix24_service.list_houses(
                brigade=effective_brigade,
                status=status,
                management_company=management_company,
                cleaning_date=cleaning_date,
                date_from=date_from,
                date_to=date_to,
                page=page,
                limit=limit,
            )
            return data
    except Exception as e:
        logger.error(f"Error getting houses: {e}")
        # fallback mock
        mock_houses = [
            {"id": "1", "title": "Билибина 6", "address": "Билибина 6", "management_company": "УК Комфорт", "brigade_name": "5 бригада", "assigned_by_name": "5 бригада", "apartments": 120, "entrances": 4, "floors": 9, "cleaning_dates": {"october_1": {"dates": ["2025-10-02"], "type": "Влажная уборка"}}},
        ]
        return {"houses": mock_houses, "total": len(mock_houses), "page": 1, "limit": limit, "pages": 1}

@router.get("/filters")
async def get_cleaning_filters():
    try:
        brigades = await bitrix24_service.get_brigade_options()
        statuses = [{"id": "NEW", "name": "Новая"}, {"id": "WON", "name": "Закрыта"}]
        return {"brigades": brigades, "statuses": statuses}
    except Exception as e:
        logger.error(f"Error getting filters: {e}")
        return {"brigades": [], "statuses": []}

@router.get("/house/{house_id}/details")
async def get_house_details(house_id: str):
    try:
        details = await bitrix24_service.get_deal_details(house_id)
        if details:
            return {"house": details}
        return {"error": "Дом не найден"}
    except Exception as e:
        logger.error(f"Error getting house details: {e}")
        return {"error": str(e)}

@router.post("/sync")
async def sync_houses_from_bitrix24(db: AsyncSession = Depends(get_db)):
    try:
        result = await bitrix24_service.sync_houses(db)
        return {"success": True, **result}
    except Exception as e:
        logger.error(f"Error syncing from Bitrix24: {e}")
        return {"success": False, "error": str(e)}

@router.get("/brigades")
async def get_brigades_list():
    """Получить список всех бригад для выбора"""
    try:
        brigades = await bitrix24_service.get_all_brigades()
        return {"brigades": brigades}
    except Exception as e:
        logger.error(f"Error getting brigades: {e}")
        return {"brigades": []}

@router.get("/cleaning-types")
async def get_cleaning_types():
    """Получить список типов уборки (enum)"""
    try:
        types = await bitrix24_service.get_cleaning_types()
        return {"types": types}
    except Exception as e:
        logger.error(f"Error getting cleaning types: {e}")
        return {"types": []}

@router.get("/contacts")
async def get_contacts_list():
    """Получить список всех контактов для выбора"""
    try:
        contacts = await bitrix24_service.get_all_contacts()
        return {"contacts": contacts}
    except Exception as e:
        logger.error(f"Error getting contacts: {e}")
        return {"contacts": []}

@router.get("/debug-enum/{field_code}")
async def debug_enum_field(field_code: str):
    """Отладка: получить enum значения для поля"""
    try:
        import httpx
        async with httpx.AsyncClient(timeout=httpx.Timeout(40.0)) as client:
            # Очищаем кеш для этого поля
            cache_key = f"enum:{field_code}"
            bitrix24_service.enum_cache.store.pop(cache_key, None)
            
            # Получаем заново
            enum_map = await bitrix24_service._get_enum_map(client, field_code)
            
            return {
                "field_code": field_code,
                "enum_map": enum_map,
                "count": len(enum_map)
            }
    except Exception as e:
        logger.error(f"Error getting enum: {e}")
        return {"error": str(e)}

@router.get("/clear-cache")
async def clear_bitrix_cache():
    """Очистить весь кеш Bitrix24"""
    try:
        bitrix24_service.enum_cache.store.clear()
        bitrix24_service.company_cache.store.clear()
        bitrix24_service.user_cache.store.clear()
        bitrix24_service.deals_cache.store.clear()
        return {"success": True, "message": "Кеш очищен"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.put("/house/{house_id}")
async def update_house(house_id: str, data: dict):
    """Обновить данные дома в Bitrix24"""
    try:
        result = await bitrix24_service.update_deal(house_id, data)
        if result:
            return {"success": True, "house": result}
        return {"success": False, "error": "Не удалось обновить дом"}
    except Exception as e:
        logger.error(f"Error updating house {house_id}: {e}")
        return {"success": False, "error": str(e)}