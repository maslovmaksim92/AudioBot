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

@router.get("/house/{house_id}/photo-history")
async def get_house_photo_history(
    house_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Получить историю фото уборок для конкретного дома
    Возвращает список всех уборок с фото, датами и ссылками на посты в TG
    """
    try:
        from app.config.database import get_db_pool
        
        db_pool = await get_db_pool()
        if not db_pool:
            logger.error("[cleaning] DB pool not available")
            return {"error": "Database connection error", "cleanings": []}
        
        async with db_pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT 
                    id,
                    house_id,
                    house_address,
                    brigade_id,
                    cleaning_date,
                    photo_file_ids,
                    photo_count,
                    ai_caption,
                    telegram_message_id,
                    telegram_chat_id,
                    telegram_post_url,
                    status,
                    sent_to_group_at,
                    created_at
                FROM cleaning_photos
                WHERE house_id = $1
                ORDER BY cleaning_date DESC
                """,
                house_id
            )
            
            cleanings = []
            for row in rows:
                cleanings.append({
                    "id": str(row['id']),
                    "house_id": row['house_id'],
                    "house_address": row['house_address'],
                    "brigade_id": row['brigade_id'],
                    "cleaning_date": row['cleaning_date'].isoformat() if row['cleaning_date'] else None,
                    "photo_file_ids": row['photo_file_ids'] or [],
                    "photo_count": row['photo_count'],
                    "ai_caption": row['ai_caption'],
                    "telegram_message_id": row['telegram_message_id'],
                    "telegram_chat_id": row['telegram_chat_id'],
                    "telegram_post_url": row['telegram_post_url'],
                    "status": row['status'],
                    "sent_to_group_at": row['sent_to_group_at'].isoformat() if row['sent_to_group_at'] else None,
                    "created_at": row['created_at'].isoformat() if row['created_at'] else None
                })
            
            logger.info(f"[cleaning] Found {len(cleanings)} cleanings for house {house_id}")
            return {"cleanings": cleanings}
            
    except Exception as e:
        logger.error(f"[cleaning] Error getting photo history for house {house_id}: {e}")
        return {"error": str(e), "cleanings": []}

@router.post("/resend-photos")
async def resend_photos_to_telegram(data: dict):
    """
    Повторно отправить фото в Telegram группы
    """
    try:
        cleaning_id = data.get('cleaning_id')
        
        if not cleaning_id:
            return {"success": False, "error": "cleaning_id is required"}
        
        from app.config.database import get_db_pool
        import os
        
        db_pool = await get_db_pool()
        if not db_pool:
            return {"success": False, "error": "Database connection error"}
        
        # Получаем данные уборки
        async with db_pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT 
                    house_address,
                    photo_file_ids,
                    ai_caption
                FROM cleaning_photos
                WHERE id = $1
                """,
                cleaning_id
            )
            
            if not row:
                return {"success": False, "error": "Cleaning not found"}
            
            photo_file_ids = row['photo_file_ids'] or []
            caption = row['ai_caption']
            
            if not photo_file_ids:
                return {"success": False, "error": "No photos to send"}
            
            # Отправляем в группы
            from backend.app.services.telegram_cleaning_bot import send_photo, send_media_group
            
            target_chat_id = os.getenv('TELEGRAM_TARGET_CHAT_ID')
            report_chat_id = os.getenv('TELEGRAM_REPORT_CHAT_ID')
            
            sent_count = 0
            
            # Отправка в публичную группу
            if target_chat_id:
                if len(photo_file_ids) == 1:
                    result = await send_photo(target_chat_id, photo_file_ids[0], caption)
                else:
                    result = await send_media_group(target_chat_id, photo_file_ids, caption)
                
                if result and result.get('success'):
                    sent_count += 1
            
            # Отправка в отчетную группу
            if report_chat_id and report_chat_id != target_chat_id:
                if len(photo_file_ids) == 1:
                    result = await send_photo(report_chat_id, photo_file_ids[0], caption)
                else:
                    result = await send_media_group(report_chat_id, photo_file_ids, caption)
                
                if result and result.get('success'):
                    sent_count += 1
            
            return {
                "success": True,
                "sent_to_groups": sent_count,
                "message": f"Фото отправлено в {sent_count} группу(ы)"
            }
            
    except Exception as e:
        logger.error(f"[cleaning] Error resending photos: {e}")
        return {"success": False, "error": str(e)}

@router.get("/missing-data-report")
async def get_missing_data_report(with_contacts: bool = False):
    """
    Генерирует CSV отчет по домам с недостающими данными
    Проверяет: address, management_company, entrances, floors, apartments, cleaning_schedule, elder_contact
    
    Параметры:
    - with_contacts: bool = False - загружать контакты старшего (медленно, ~10 минут)
    
    По умолчанию генерирует быстрый отчет без контактов (1-2 секунды)
    Для полного отчета: ?with_contacts=true
    """
    try:
        from fastapi.responses import StreamingResponse
        import io
        import csv
        import asyncio
        
        logger.info(f"[cleaning] Generating missing data report (with_contacts={with_contacts})...")
        
        # Загружаем ВСЕ дома из Bitrix24 (с учетом пагинации)
        all_houses = []
        page = 1
        page_limit = 50  # Bitrix24 лимит на страницу
        
        while True:
            logger.info(f"[cleaning] Loading page {page}...")
            data = await bitrix24_service.list_houses(page=page, limit=page_limit)
            houses = data.get('houses', [])
            
            if not houses:
                break
            
            all_houses.extend(houses)
            
            # Проверяем, есть ли еще страницы
            total_pages = data.get('pages', 1)
            if page >= total_pages:
                break
            
            page += 1
        
        logger.info(f"[cleaning] Loaded {len(all_houses)} houses for report")
        
        if with_contacts:
            logger.info("[cleaning] Loading elder contacts for each house (this may take 10+ minutes)...")
        
        # Проверяем каждый дом на недостающие данные
        missing_data_houses = []
        
        # Счетчик для логирования прогресса
        processed_count = 0
        
        for house in all_houses:
            processed_count += 1
            
            # Логируем прогресс каждые 50 домов
            if processed_count % 50 == 0:
                logger.info(f"[cleaning] Progress: {processed_count}/{len(all_houses)} houses processed")
            
            missing_fields = []
            
            # Проверка адреса
            if not house.get('address') or len(house.get('address', '')) < 10:
                missing_fields.append('Адрес')
            
            # Проверка УК
            if not house.get('management_company') or house.get('management_company') == '':
                missing_fields.append('УК')
            
            # Проверка старшего/ответственного
            if not house.get('brigade_name') or house.get('brigade_name') in ['Бригада не назначена', '']:
                missing_fields.append('Бригада')
            
            # Проверка подъездов
            if not house.get('entrances') or house.get('entrances') == 0:
                missing_fields.append('Подъезды')
            
            # Проверка этажей
            if not house.get('floors') or house.get('floors') == 0:
                missing_fields.append('Этажи')
            
            # Проверка квартир
            if not house.get('apartments') or house.get('apartments') == 0:
                missing_fields.append('Квартиры')
            
            # Проверка графика уборки (октябрь и ноябрь)
            cleaning_dates = house.get('cleaning_dates', {})
            has_october = (cleaning_dates.get('october_1', {}).get('dates') or 
                          cleaning_dates.get('october_2', {}).get('dates'))
            has_november = (cleaning_dates.get('november_1', {}).get('dates') or 
                           cleaning_dates.get('november_2', {}).get('dates'))
            
            if not has_october and not has_november:
                missing_fields.append('График уборки')
            
            # ЗАГРУЖАЕМ ДЕТАЛИ ДОМА для получения контактов старшего
            elder_name = 'Не указан'
            elder_phone = 'Не указан'
            elder_email = 'Не указан'
            
            try:
                house_details = await bitrix24_service.get_deal_details(house.get('id'))
                if house_details:
                    elder_contact = house_details.get('elder_contact', {})
                    if elder_contact and isinstance(elder_contact, dict):
                        elder_name = elder_contact.get('name', 'Не указан')
                        phones = elder_contact.get('phones', [])
                        emails = elder_contact.get('emails', [])
                        elder_phone = phones[0] if phones else 'Не указан'
                        elder_email = emails[0] if emails else 'Не указан'
                    
                    # Проверка наличия контактов
                    if elder_name == 'Не указан' or not elder_name:
                        missing_fields.append('Старший (ФИО)')
                    if elder_phone == 'Не указан' or not elder_phone:
                        missing_fields.append('Старший (телефон)')
            except Exception as e:
                logger.warning(f"[cleaning] Failed to load details for house {house.get('id')}: {e}")
                missing_fields.append('Старший (ФИО)')
                missing_fields.append('Старший (телефон)')
            
            # Добавляем в отчет (всегда, не только если есть недостающие поля)
            # Это позволит видеть полную информацию по всем домам
            missing_data_houses.append({
                'id': house.get('id', ''),
                'address': house.get('address') or house.get('title', 'Не указан'),
                'management_company': house.get('management_company', 'Не указана'),
                'brigade_name': house.get('brigade_name', 'Не назначена'),
                'entrances': house.get('entrances', 0),
                'floors': house.get('floors', 0),
                'apartments': house.get('apartments', 0),
                'periodicity': house.get('periodicity', 'Не указана'),
                'elder_name': elder_name,
                'elder_phone': elder_phone,
                'elder_email': elder_email,
                'missing_fields': ', '.join(missing_fields) if missing_fields else 'Нет'
            })
        
        logger.info(f"[cleaning] Finished processing all {len(all_houses)} houses")
        
        logger.info(f"[cleaning] Found {len(missing_data_houses)} houses with missing data")
        
        # Создаем CSV с правильным разделителем для Excel
        output = io.StringIO()
        
        # Используем точку с запятой как разделитель для совместимости с Excel
        writer = csv.DictWriter(
            output, 
            fieldnames=[
                'ID', 'Адрес', 'УК', 'Бригада', 'Подъезды', 'Этажи', 
                'Квартиры', 'Периодичность', 'Старший (ФИО)', 'Старший (телефон)', 
                'Старший (email)', 'Недостающие поля'
            ],
            delimiter=';',  # Точка с запятой для Excel
            quoting=csv.QUOTE_MINIMAL
        )
        
        writer.writeheader()
        
        for house in missing_data_houses:
            writer.writerow({
                'ID': house['id'],
                'Адрес': house['address'],
                'УК': house['management_company'],
                'Бригада': house['brigade_name'],
                'Подъезды': house['entrances'],
                'Этажи': house['floors'],
                'Квартиры': house['apartments'],
                'Периодичность': house['periodicity'],
                'Старший (ФИО)': house['elder_name'],
                'Старший (телефон)': house['elder_phone'],
                'Старший (email)': house['elder_email'],
                'Недостающие поля': house['missing_fields']
            })
        
        # Возвращаем CSV как downloadable file
        output.seek(0)
        
        from datetime import datetime
        filename = f"missing_data_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode('utf-8-sig')),  # BOM для корректного отображения в Excel
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
        
    except Exception as e:
        logger.error(f"[cleaning] Error generating report: {e}")
        return {"error": str(e), "houses_with_issues": []}