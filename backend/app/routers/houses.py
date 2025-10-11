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
