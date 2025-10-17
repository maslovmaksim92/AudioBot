"""
API для управления выручкой по месяцам
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import asyncpg
import os
import logging
from datetime import datetime
from uuid import uuid4

logger = logging.getLogger(__name__)
router = APIRouter(tags=["revenue"])


class MonthlyRevenue(BaseModel):
    month: str  # например "Январь 2025"
    revenue: float
    notes: Optional[str] = None


class UpdateRevenueRequest(BaseModel):
    revenues: List[MonthlyRevenue]


async def get_db_connection():
    """Получить прямое соединение с БД"""
    db_url = os.environ.get('DATABASE_URL', '')
    
    if not db_url:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    try:
        return await asyncpg.connect(db_url)
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")


@router.get("/finances/revenue/monthly")
async def get_monthly_revenue():
    """
    Получить выручку по месяцам (ручной ввод)
    """
    try:
        conn = await get_db_connection()
        try:
            # Проверяем существует ли таблица
            table_exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'monthly_revenue'
                )
            """)
            
            if not table_exists:
                # Создаем таблицу если её нет
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS monthly_revenue (
                        id VARCHAR(255) PRIMARY KEY,
                        month VARCHAR(50) UNIQUE NOT NULL,
                        revenue DECIMAL(15, 2) NOT NULL,
                        notes TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                logger.info("Таблица monthly_revenue создана")
                
                return {
                    "revenues": [],
                    "message": "Таблица создана, данных пока нет"
                }
            
            # Получаем данные о выручке
            rows = await conn.fetch("""
                SELECT month, revenue, notes, updated_at
                FROM monthly_revenue
                ORDER BY 
                    CASE 
                        WHEN month LIKE '%Январь%' THEN 1
                        WHEN month LIKE '%Февраль%' THEN 2
                        WHEN month LIKE '%Март%' THEN 3
                        WHEN month LIKE '%Апрель%' THEN 4
                        WHEN month LIKE '%Май%' THEN 5
                        WHEN month LIKE '%Июнь%' THEN 6
                        WHEN month LIKE '%Июль%' THEN 7
                        WHEN month LIKE '%Август%' THEN 8
                        WHEN month LIKE '%Сентябрь%' THEN 9
                        WHEN month LIKE '%Октябрь%' THEN 10
                        WHEN month LIKE '%Ноябрь%' THEN 11
                        WHEN month LIKE '%Декабрь%' THEN 12
                        ELSE 13
                    END DESC
            """)
            
            revenues = []
            for row in rows:
                revenues.append({
                    "month": row['month'],
                    "revenue": float(row['revenue']),
                    "notes": row['notes'],
                    "updated_at": row['updated_at'].isoformat() if row['updated_at'] else None
                })
            
            return {
                "revenues": revenues,
                "total": len(revenues)
            }
        finally:
            await conn.close()
    except Exception as e:
        logger.error(f"Error fetching monthly revenue: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/finances/revenue/monthly")
async def update_monthly_revenue(request: UpdateRevenueRequest):
    """
    Обновить выручку по месяцам (создать или обновить)
    """
    try:
        conn = await get_db_connection()
        try:
            # Проверяем существует ли таблица
            table_exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'monthly_revenue'
                )
            """)
            
            if not table_exists:
                # Создаем таблицу
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS monthly_revenue (
                        id VARCHAR(255) PRIMARY KEY,
                        month VARCHAR(50) UNIQUE NOT NULL,
                        revenue DECIMAL(15, 2) NOT NULL,
                        notes TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
            
            updated_count = 0
            created_count = 0
            
            for revenue_data in request.revenues:
                # Проверяем существует ли запись
                exists = await conn.fetchval("""
                    SELECT EXISTS(SELECT 1 FROM monthly_revenue WHERE month = $1)
                """, revenue_data.month)
                
                now = datetime.now()
                
                if exists:
                    # Обновляем
                    await conn.execute("""
                        UPDATE monthly_revenue
                        SET revenue = $1, notes = $2, updated_at = $3
                        WHERE month = $4
                    """, revenue_data.revenue, revenue_data.notes, now, revenue_data.month)
                    updated_count += 1
                else:
                    # Создаем новую запись
                    record_id = str(uuid4())
                    await conn.execute("""
                        INSERT INTO monthly_revenue (id, month, revenue, notes, created_at, updated_at)
                        VALUES ($1, $2, $3, $4, $5, $6)
                    """, record_id, revenue_data.month, revenue_data.revenue, revenue_data.notes, now, now)
                    created_count += 1
            
            return {
                "success": True,
                "created": created_count,
                "updated": updated_count,
                "message": f"Создано: {created_count}, обновлено: {updated_count}"
            }
        finally:
            await conn.close()
    except Exception as e:
        logger.error(f"Error updating monthly revenue: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/finances/revenue/monthly/{month}")
async def delete_monthly_revenue(month: str):
    """
    Удалить выручку за конкретный месяц
    """
    try:
        conn = await get_db_connection()
        try:
            result = await conn.execute("""
                DELETE FROM monthly_revenue
                WHERE month = $1
            """, month)
            
            if result == "DELETE 0":
                raise HTTPException(status_code=404, detail="Месяц не найден")
            
            return {
                "success": True,
                "message": f"Выручка за {month} удалена"
            }
        finally:
            await conn.close()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting monthly revenue: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/finances/revenue/sync-to-transactions")
async def sync_revenue_to_transactions():
    """
    Синхронизировать выручку из monthly_revenue в financial_transactions
    Создает или обновляет транзакции типа income для каждого месяца
    """
    try:
        conn = await get_db_connection()
        try:
            # Проверяем существует ли таблица monthly_revenue
            table_exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'monthly_revenue'
                )
            """)
            
            if not table_exists:
                return {
                    "success": False,
                    "message": "Таблица monthly_revenue не существует"
                }
            
            # Получаем все записи выручки
            revenue_rows = await conn.fetch("""
                SELECT month, revenue, notes
                FROM monthly_revenue
                ORDER BY month
            """)
            
            if not revenue_rows:
                return {
                    "success": False,
                    "message": "Нет данных для синхронизации"
                }
            
            created_count = 0
            updated_count = 0
            
            for row in revenue_rows:
                month = row['month']
                revenue = float(row['revenue'])
                notes = row['notes'] or 'Выручка за месяц'
                
                # Определяем дату для транзакции (последний день месяца)
                month_mapping = {
                    'Январь': (1, 31), 'Февраль': (2, 28), 'Март': (3, 31),
                    'Апрель': (4, 30), 'Май': (5, 31), 'Июнь': (6, 30),
                    'Июль': (7, 31), 'Август': (8, 31), 'Сентябрь': (9, 30),
                    'Октябрь': (10, 31), 'Ноябрь': (11, 30), 'Декабрь': (12, 31)
                }
                
                month_name = month.split()[0]
                year = int(month.split()[1]) if len(month.split()) > 1 else 2025
                
                if month_name in month_mapping:
                    month_num, last_day = month_mapping[month_name]
                    trans_date = datetime(year, month_num, last_day)
                else:
                    # Fallback к текущей дате
                    trans_date = datetime.now()
                
                # Проверяем существует ли уже транзакция выручки для этого месяца
                existing = await conn.fetchval("""
                    SELECT id FROM financial_transactions
                    WHERE project = $1 
                    AND type = 'income'
                    AND description LIKE '%Выручка за месяц%'
                    LIMIT 1
                """, month)
                
                now = datetime.now()
                
                if existing:
                    # Обновляем существующую транзакцию
                    await conn.execute("""
                        UPDATE financial_transactions
                        SET amount = $1, 
                            date = $2,
                            description = $3,
                            category = 'Поступление от покупателей'
                        WHERE id = $4
                    """, revenue, trans_date, notes, existing)
                    updated_count += 1
                else:
                    # Создаем новую транзакцию
                    transaction_id = str(uuid4())
                    await conn.execute("""
                        INSERT INTO financial_transactions 
                        (id, date, amount, category, type, description, 
                         project, created_at)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    """, 
                        transaction_id,
                        trans_date,
                        revenue,
                        'Поступление от покупателей',
                        'income',
                        notes,
                        month,
                        now
                    )
                    created_count += 1
            
            return {
                "success": True,
                "created": created_count,
                "updated": updated_count,
                "message": f"Создано: {created_count}, обновлено: {updated_count} транзакций"
            }
        finally:
            await conn.close()
    except Exception as e:
        logger.error(f"Error syncing revenue to transactions: {e}")
        raise HTTPException(status_code=500, detail=str(e))
