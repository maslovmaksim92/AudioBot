"""
API роутер для домов - интеграция с Bitrix24
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import List, Optional
from datetime import datetime, timezone

from backend.app.config.database import get_db
from backend.app.models.house import House
from backend.app.schemas.house import HouseResponse, HouseCreate, HouseUpdate
from backend.app.services.bitrix24_service import bitrix24_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/houses", tags=["Houses"])

@router.get("/", response_model=List[HouseResponse])
async def get_houses(
    skip: int = 0,
    limit: int = 100,
    brigade_number: Optional[str] = None,
    company_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Получение списка домов с фильтрацией"""
    
    query = select(House)
    
    # Фильтр по бригаде (для RBAC)
    if brigade_number:
        query = query.where(House.brigade_number == brigade_number)
    
    # Фильтр по УК
    if company_id:
        query = query.where(House.company_id == company_id)
    
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    houses = result.scalars().all()
    
    # Вычисляем periodicity для каждого дома
    houses_with_periodicity = []
    for house in houses:
        house_dict = {
            "id": house.id,
            "bitrix_id": house.bitrix_id,
            "address": house.address,
            "apartments_count": house.apartments_count,
            "entrances_count": house.entrances_count,
            "floors_count": house.floors_count,
            "company_id": house.company_id,
            "company_title": house.company_title,
            "assigned_by_id": house.assigned_by_id,
            "assigned_by_name": house.assigned_by_name,
            "brigade_number": house.brigade_number,
            "tariff": house.tariff,
            "elder_contact": house.elder_contact,
            "notes": house.notes,
            "cleaning_schedule": house.cleaning_schedule,
            "complaints": house.complaints,
            "act_signed": house.act_signed,
            "last_cleaning": house.last_cleaning,
            "created_at": house.created_at,
            "updated_at": house.updated_at,
            "synced_at": house.synced_at,
            # Вычисляем periodicity
            "periodicity": bitrix24_service._compute_periodicity(house.cleaning_schedule or {})
        }
        houses_with_periodicity.append(house_dict)
    
    return houses_with_periodicity

@router.get("/{house_id}", response_model=HouseResponse)
async def get_house(house_id: str, db: AsyncSession = Depends(get_db)):
    """Получение дома по ID"""
    
    result = await db.execute(select(House).where(House.id == house_id))
    house = result.scalar_one_or_none()
    
    if not house:
        raise HTTPException(status_code=404, detail="Дом не найден")
    
    # Преобразуем в dict с periodicity
    house_dict = {
        "id": house.id,
        "bitrix_id": house.bitrix_id,
        "address": house.address,
        "apartments_count": house.apartments_count,
        "entrances_count": house.entrances_count,
        "floors_count": house.floors_count,
        "company_id": house.company_id,
        "company_title": house.company_title,
        "assigned_by_id": house.assigned_by_id,
        "assigned_by_name": house.assigned_by_name,
        "brigade_number": house.brigade_number,
        "tariff": house.tariff,
        "elder_contact": house.elder_contact,
        "notes": house.notes,
        "cleaning_schedule": house.cleaning_schedule,
        "complaints": house.complaints,
        "act_signed": house.act_signed,
        "last_cleaning": house.last_cleaning,
        "created_at": house.created_at,
        "updated_at": house.updated_at,
        "synced_at": house.synced_at,
        "periodicity": bitrix24_service._compute_periodicity(house.cleaning_schedule or {})
    }
    
    return house_dict

@router.post("/", response_model=HouseResponse, status_code=201)
async def create_house(house_data: HouseCreate, db: AsyncSession = Depends(get_db)):
    """Создание нового дома"""
    
    from uuid import uuid4
    
    new_house = House(
        id=str(uuid4()),
        **house_data.dict()
    )
    
    db.add(new_house)
    await db.commit()
    await db.refresh(new_house)
    
    return new_house

@router.patch("/{house_id}", response_model=HouseResponse)
async def update_house(
    house_id: str,
    house_data: HouseUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Обновление дома"""
    
    result = await db.execute(select(House).where(House.id == house_id))
    house = result.scalar_one_or_none()
    
    if not house:
        raise HTTPException(status_code=404, detail="Дом не найден")
    
    # Обновление полей
    update_data = house_data.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(house, key, value)
    
    house.updated_at = datetime.now(timezone.utc)
    
    await db.commit()
    await db.refresh(house)
    
    return house

@router.delete("/{house_id}")
async def delete_house(house_id: str, db: AsyncSession = Depends(get_db)):
    """Удаление дома"""
    
    result = await db.execute(select(House).where(House.id == house_id))
    house = result.scalar_one_or_none()
    
    if not house:
        raise HTTPException(status_code=404, detail="Дом не найден")
    
    await db.delete(house)
    await db.commit()
    
    return {"message": "Дом удален"}

@router.post("/sync-bitrix24")
async def sync_bitrix24(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Синхронизация домов из Bitrix24
    Загружает все сделки и обновляет/создает дома в БД
    """
    
    logger.info("🔄 Начало синхронизации домов из Bitrix24...")
    
    # Запускаем синхронизацию в фоне
    background_tasks.add_task(sync_houses_from_bitrix24, db)
    
    return {
        "message": "Синхронизация запущена в фоновом режиме",
        "status": "processing"
    }

async def sync_houses_from_bitrix24(db: AsyncSession):
    """Фоновая задача синхронизации"""
    
    try:
        # Загрузка всех сделок из Bitrix24
        deals = await bitrix24_service.get_all_deals()
        
        logger.info(f"Загружено {len(deals)} сделок из Bitrix24")
        
        synced_count = 0
        created_count = 0
        updated_count = 0
        
        for deal in deals:
            # Парсинг сделки в формат дома
            house_data = bitrix24_service.parse_deal_to_house(deal)
            
            if not house_data.get("address"):
                continue
            
            # Проверка существования дома по bitrix_id
            result = await db.execute(
                select(House).where(House.bitrix_id == house_data["bitrix_id"])
            )
            existing_house = result.scalar_one_or_none()
            
            if existing_house:
                # Обновление существующего дома
                for key, value in house_data.items():
                    if key != "id":  # Не обновляем ID
                        setattr(existing_house, key, value)
                
                updated_count += 1
            else:
                # Создание нового дома
                new_house = House(**house_data)
                db.add(new_house)
                created_count += 1
            
            synced_count += 1
        
        await db.commit()
        
        logger.info(f"✅ Синхронизация завершена: {synced_count} домов, создано: {created_count}, обновлено: {updated_count}")
        
    except Exception as e:
        logger.error(f"❌ Ошибка синхронизации: {e}")
        await db.rollback()

@router.get("/stats/summary")
async def get_houses_stats(db: AsyncSession = Depends(get_db)):
    """Статистика по домам"""
    
    result = await db.execute(select(House))
    houses = result.scalars().all()
    
    stats = {
        "total": len(houses),
        "by_brigade": {},
        "by_company": {},
        "last_sync": None
    }
    
    for house in houses:
        # Статистика по бригадам
        brigade = house.brigade_number or "Не назначено"
        stats["by_brigade"][brigade] = stats["by_brigade"].get(brigade, 0) + 1
        
        # Статистика по УК
        company = house.company_title or "Не указано"
        stats["by_company"][company] = stats["by_company"].get(company, 0) + 1
        
        # Последняя синхронизация
        if house.synced_at:
            if not stats["last_sync"] or house.synced_at > stats["last_sync"]:
                stats["last_sync"] = house.synced_at
    
    return stats



# ==================== АКТЫ ====================

from pydantic import BaseModel

class ActSignRequest(BaseModel):
    """Запрос на подписание акта"""
    house_id: str
    house_address: str
    act_month: str  # YYYY-MM
    signed_date: str  # YYYY-MM-DD
    signed_by: Optional[str] = None
    brigade_id: Optional[str] = None
    notes: Optional[str] = None


class ActResponse(BaseModel):
    """Ответ с информацией об акте"""
    id: str
    house_id: str
    house_address: str
    act_month: str
    act_signed_date: str
    signed_by: Optional[str]
    cleaning_count: int
    created_at: datetime


class ActsStatsResponse(BaseModel):
    """Статистика по актам за месяц"""
    month: str  # YYYY-MM
    total_houses: int
    signed_acts: int
    unsigned_acts: int
    signed_percentage: float
    acts_by_date: dict  # {date: count}


@router.post("/acts/sign")
async def sign_act(request: ActSignRequest):
    """
    Пометить акт как подписанный
    
    Ключевой показатель для компании
    """
    try:
        from app.config.database import get_db_pool
        
        db_pool = await get_db_pool()
        if not db_pool:
            raise HTTPException(status_code=503, detail="Database not available")
        
        # Получаем количество уборок за месяц для этого дома
        async with db_pool.acquire() as conn:
            cleaning_count = await conn.fetchval(
                """
                SELECT COUNT(*) FROM cleaning_photos 
                WHERE house_id = $1 
                AND TO_CHAR(cleaning_date, 'YYYY-MM') = $2
                """,
                request.house_id,
                request.act_month
            )
            
            # Вставляем или обновляем акт
            result = await conn.fetchrow(
                """
                INSERT INTO house_acts (
                    house_id, house_address, act_month, act_signed_date,
                    signed_by, brigade_id, cleaning_count, notes
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                ON CONFLICT (house_id, act_month) 
                DO UPDATE SET
                    act_signed_date = EXCLUDED.act_signed_date,
                    signed_by = EXCLUDED.signed_by,
                    cleaning_count = EXCLUDED.cleaning_count,
                    notes = EXCLUDED.notes,
                    updated_at = NOW()
                RETURNING id, created_at
                """,
                request.house_id,
                request.house_address,
                request.act_month,
                request.signed_date,
                request.signed_by,
                request.brigade_id,
                cleaning_count or 0,
                request.notes
            )
        
        logger.info(f"[houses/acts] ✅ Act signed: {request.house_id} for {request.act_month}")
        
        return {
            "success": True,
            "message": "Акт помечен как подписанный",
            "act_id": str(result['id']),
            "cleaning_count": cleaning_count or 0
        }
        
    except Exception as e:
        logger.error(f"[houses/acts] Error signing act: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/acts/stats")
async def get_acts_stats(month: str):
    """
    Статистика по подписанным актам за месяц
    
    Args:
        month: Месяц в формате YYYY-MM (например, "2025-10")
    
    Returns:
        Статистика: всего домов, подписано, не подписано, процент
    """
    try:
        from app.config.database import get_db_pool
        
        db_pool = await get_db_pool()
        if not db_pool:
            raise HTTPException(status_code=503, detail="Database not available")
        
        async with db_pool.acquire() as conn:
            # Подписанные акты
            signed_acts = await conn.fetch(
                """
                SELECT 
                    house_id, 
                    house_address, 
                    act_signed_date,
                    cleaning_count,
                    signed_by
                FROM house_acts 
                WHERE act_month = $1
                ORDER BY act_signed_date DESC
                """,
                month
            )
            
            # Всего домов (из cleaning_photos за этот месяц)
            total_houses = await conn.fetchval(
                """
                SELECT COUNT(DISTINCT house_id) 
                FROM cleaning_photos 
                WHERE TO_CHAR(cleaning_date, 'YYYY-MM') = $1
                """,
                month
            ) or 0
            
            # Подписанные по датам
            acts_by_date = {}
            for act in signed_acts:
                date_str = act['act_signed_date'].strftime('%Y-%m-%d')
                acts_by_date[date_str] = acts_by_date.get(date_str, 0) + 1
        
        signed_count = len(signed_acts)
        unsigned_count = total_houses - signed_count
        signed_percentage = (signed_count / total_houses * 100) if total_houses > 0 else 0
        
        return {
            "month": month,
            "total_houses": total_houses,
            "signed_acts": signed_count,
            "unsigned_acts": unsigned_count,
            "signed_percentage": round(signed_percentage, 1),
            "acts_by_date": acts_by_date,
            "acts": [
                {
                    "house_id": act['house_id'],
                    "house_address": act['house_address'],
                    "signed_date": act['act_signed_date'].strftime('%Y-%m-%d'),
                    "cleaning_count": act['cleaning_count'],
                    "signed_by": act['signed_by']
                }
                for act in signed_acts
            ]
        }
        
    except Exception as e:
        logger.error(f"[houses/acts] Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/acts/{house_id}/{month}")
async def delete_act(house_id: str, month: str):
    """
    Удалить подпись акта (отменить подписание)
    
    Args:
        house_id: ID дома
        month: Месяц в формате YYYY-MM
    """
    try:
        from app.config.database import get_db_pool
        
        db_pool = await get_db_pool()
        if not db_pool:
            raise HTTPException(status_code=503, detail="Database not available")
        
        async with db_pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM house_acts WHERE house_id = $1 AND act_month = $2",
                house_id,
                month
            )
        
        logger.info(f"[houses/acts] ✅ Act deleted: {house_id} for {month}")
        
        return {
            "success": True,
            "message": "Подпись акта отменена"
        }
        
    except Exception as e:
        logger.error(f"[houses/acts] Error deleting act: {e}")
        raise HTTPException(status_code=500, detail=str(e))

