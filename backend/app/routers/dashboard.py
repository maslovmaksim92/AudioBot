"""
API роутер для Dashboard - статистика и аналитика
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Dict, Any
from datetime import datetime, timezone, timedelta

from backend.app.config.database import get_db
from backend.app.models.house import House
from backend.app.models.task import Task, TaskStatus
from backend.app.models.user import User
from backend.app.models.log import Log

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/stats")
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)):
    """
    Получение основной статистики для дашборда
    Real-time данные из БД
    """
    
    try:
        # Статистика по домам
        houses_result = await db.execute(select(func.count(House.id)))
        total_houses = houses_result.scalar() or 0
        
        # Сумма квартир
        apts_result = await db.execute(select(func.sum(House.apartments_count)))
        total_apartments = apts_result.scalar() or 0
        
        # Сумма подъездов
        entr_result = await db.execute(select(func.sum(House.entrances_count)))
        total_entrances = entr_result.scalar() or 0
        
        # Сумма этажей
        floors_result = await db.execute(select(func.sum(House.floors_count)))
        total_floors = floors_result.scalar() or 0
        
        # Активные бригады (уникальные brigade_number)
        brigades_result = await db.execute(
            select(func.count(func.distinct(House.brigade_number)))
            .where(House.brigade_number.isnot(None))
        )
        active_brigades = brigades_result.scalar() or 0
        
        # Статистика по задачам
        tasks_result = await db.execute(select(func.count(Task.id)))
        total_tasks = tasks_result.scalar() or 0
        
        # Активные задачи (не завершенные)
        active_tasks_result = await db.execute(
            select(func.count(Task.id))
            .where(Task.status.in_([TaskStatus.TODO, TaskStatus.IN_PROGRESS]))
        )
        active_tasks = active_tasks_result.scalar() or 0
        
        # Завершенные задачи
        completed_tasks = total_tasks - active_tasks
        
        # Статистика по сотрудникам
        employees_result = await db.execute(select(func.count(User.id)))
        total_employees = employees_result.scalar() or 0
        
        # Логи за последние 24 часа
        yesterday = datetime.now(timezone.utc) - timedelta(days=1)
        # Убираем timezone для PostgreSQL без timezone
        yesterday_naive = yesterday.replace(tzinfo=None)
        logs_result = await db.execute(
            select(func.count(Log.id))
            .where(Log.created_at >= yesterday_naive)
        )
        recent_logs = logs_result.scalar() or 0
        
        # УК (уникальные)
        companies_result = await db.execute(
            select(func.count(func.distinct(House.company_title)))
            .where(House.company_title.isnot(None))
        )
        total_companies = companies_result.scalar() or 0
        
        return {
            "total_houses": total_houses,
            "total_apartments": total_apartments or 0,
            "total_entrances": total_entrances or 0,
            "total_floors": total_floors or 0,
            "active_brigades": active_brigades,
            "total_tasks": total_tasks,
            "active_tasks": active_tasks,
            "completed_tasks": completed_tasks,
            "employees": total_employees,
            "recent_logs": recent_logs,
            "total_companies": total_companies,
            "last_sync": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        # Fallback если БД не готова
        return {
            "total_houses": 490,
            "total_apartments": 12500,
            "total_entrances": 1850,
            "total_floors": 45000,
            "active_brigades": 7,
            "total_tasks": 0,
            "active_tasks": 0,
            "completed_tasks": 0,
            "employees": 18,
            "recent_logs": 0,
            "total_companies": 45,
            "last_sync": datetime.now(timezone.utc).isoformat(),
            "error": str(e)
        }

@router.get("/recent-activity")
async def get_recent_activity(limit: int = 20, db: AsyncSession = Depends(get_db)):
    """Последние события в системе"""
    
    try:
        result = await db.execute(
            select(Log)
            .order_by(Log.created_at.desc())
            .limit(limit)
        )
        logs = result.scalars().all()
        
        return [{
            "id": log.id,
            "level": log.level.value,
            "category": log.category.value,
            "message": log.message,
            "user_email": log.user_email,
            "created_at": log.created_at.isoformat()
        } for log in logs]
        
    except Exception:
        return []

@router.get("/brigade-stats")
async def get_brigade_stats(db: AsyncSession = Depends(get_db)):
    """Статистика по бригадам"""
    
    try:
        result = await db.execute(
            select(
                House.brigade_number,
                func.count(House.id).label('house_count')
            )
            .where(House.brigade_number.isnot(None))
            .group_by(House.brigade_number)
            .order_by(House.brigade_number)
        )
        
        brigade_stats = []
        for row in result:
            brigade_stats.append({
                "brigade": f"Бригада {row.brigade_number}",
                "houses": row.house_count
            })
        
        return brigade_stats
        
    except Exception:
        return []

@router.get("/tasks-by-status")
async def get_tasks_by_status(db: AsyncSession = Depends(get_db)):
    """Статистика задач по статусам"""
    
    try:
        result = await db.execute(
            select(
                Task.status,
                func.count(Task.id).label('count')
            )
            .group_by(Task.status)
        )
        
        stats = {}
        for row in result:
            stats[row.status.value] = row.count
        
        return stats
        
    except Exception:
        return {
            "todo": 0,
            "in_progress": 0,
            "done": 0,
            "cancelled": 0
        }

@router.get("/houses-by-brigade")
async def get_houses_by_brigade(db: AsyncSession = Depends(get_db)):
    """Распределение домов по бригадам для круговой диаграммы"""
    
    try:
        # Сначала пробуем по brigade_number
        result = await db.execute(
            select(
                House.brigade_number,
                func.count(House.id).label('count')
            )
            .where(House.brigade_number.isnot(None))
            .group_by(House.brigade_number)
            .order_by(House.brigade_number)
        )
        
        data = []
        colors = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899', '#14B8A6']
        
        rows = result.all()
        
        if rows and len(rows) > 0:
            for idx, row in enumerate(rows):
                data.append({
                    "label": f"Бригада {row.brigade_number}",
                    "value": row.count,
                    "color": colors[idx % len(colors)]
                })
        else:
            # Fallback: группируем по assigned_by_id
            result2 = await db.execute(
                select(
                    House.assigned_by_id,
                    func.count(House.id).label('count')
                )
                .where(House.assigned_by_id.isnot(None))
                .group_by(House.assigned_by_id)
                .order_by(func.count(House.id).desc())
                .limit(7)
            )
            
            for idx, row in enumerate(result2):
                data.append({
                    "label": f"Бригада {idx + 1}",
                    "value": row.count,
                    "color": colors[idx % len(colors)]
                })
        
        return {"data": data}
        
    except Exception as e:
        logger.error(f"Error in houses-by-brigade: {e}")
        return {"data": []}

@router.get("/cleaning-stats-monthly")
async def get_cleaning_stats_monthly(db: AsyncSession = Depends(get_db)):
    """Статистика уборок по месяцам для графика"""
    
    # Пока возвращаем mock данные, позже можно будет считать из cleaning_dates
    return {
        "months": ["Сентябрь", "Октябрь", "Ноябрь", "Декабрь"],
        "planned": [450, 490, 485, 480],
        "completed": [430, 465, 0, 0]
    }

@router.get("/sync-status")
async def get_sync_status(db: AsyncSession = Depends(get_db)):
    """Статус последней синхронизации с Bitrix24"""
    
    try:
        # Последний лог синхронизации
        result = await db.execute(
            select(Log)
            .where(Log.category == 'integration')
            .where(Log.message.like('%Bitrix24%'))
            .order_by(Log.created_at.desc())
            .limit(1)
        )
        last_sync = result.scalar_one_or_none()
        
        if last_sync:
            return {
                "last_sync": last_sync.created_at.isoformat() if last_sync.created_at else None,
                "status": "success" if last_sync.level.value == "info" else "error",
                "message": last_sync.message,
                "details": last_sync.extra_data
            }
        
        return {
            "last_sync": None,
            "status": "unknown",
            "message": "Синхронизация еще не выполнялась"
        }
        
    except Exception as e:
        return {
            "last_sync": None,
            "status": "error",
            "message": f"Ошибка получения статуса: {str(e)}"
        }