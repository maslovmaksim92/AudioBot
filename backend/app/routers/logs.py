"""
API роутер для журнала событий (логов)
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List, Optional
from datetime import datetime, timezone

from backend.app.config.database import get_db
from backend.app.models.log import Log
from backend.app.schemas.log import LogCreate, LogResponse

router = APIRouter(prefix="/logs", tags=["Logs"])

@router.get("", response_model=List[LogResponse])
async def get_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    level: Optional[str] = Query(None, description="Уровень лога: INFO, WARNING, ERROR"),
    service: Optional[str] = Query(None, description="Имя сервиса"),
    db: AsyncSession = Depends(get_db)
):
    """
    Получение логов системы с фильтрацией
    
    Поддерживает:
    - Пагинацию (skip, limit)
    - Фильтрацию по уровню (level)
    - Фильтрацию по сервису (service)
    """
    query = select(Log).order_by(desc(Log.created_at))
    
    # Фильтры
    if level:
        query = query.where(Log.level == level.upper())
    if service:
        query = query.where(Log.service == service)
    
    # Пагинация
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    logs = result.scalars().all()
    
    return logs

@router.post("", response_model=LogResponse, status_code=201)
async def create_log(
    log_data: LogCreate,
    db: AsyncSession = Depends(get_db)
):
    """Создание нового лога"""
    new_log = Log(
        level=log_data.level,
        service=log_data.service,
        message=log_data.message,
        metadata=log_data.metadata,
        created_at=datetime.now(timezone.utc)
    )
    
    db.add(new_log)
    await db.commit()
    await db.refresh(new_log)
    
    return new_log

@router.delete("/{log_id}")
async def delete_log(log_id: int, db: AsyncSession = Depends(get_db)):
    """Удаление лога по ID"""
    result = await db.execute(select(Log).where(Log.id == log_id))
    log = result.scalar_one_or_none()
    
    if not log:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Лог не найден")
    
    await db.delete(log)
    await db.commit()
    
    return {"ok": True, "message": f"Лог {log_id} удален"}

@router.get("/stats")
async def get_logs_stats(db: AsyncSession = Depends(get_db)):
    """Статистика по логам (количество по уровням)"""
    from sqlalchemy import func
    
    result = await db.execute(
        select(
            Log.level,
            func.count(Log.id).label('count')
        ).group_by(Log.level)
    )
    
    stats = {row[0]: row[1] for row in result.fetchall()}
    
    return {
        "total": sum(stats.values()),
        "by_level": stats
    }