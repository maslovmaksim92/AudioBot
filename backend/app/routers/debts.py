"""
API для управления задолженностями
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Literal
from datetime import datetime
import asyncpg
import os
import logging
from uuid import uuid4

logger = logging.getLogger(__name__)
router = APIRouter(tags=["debts"])


class DebtBase(BaseModel):
    creditor: str
    amount: float
    due_date: str  # YYYY-MM-DD
    status: Literal["active", "overdue", "paid"]
    type: Literal["loan", "credit_line", "accounts_payable", "lease", "other"]
    description: Optional[str] = None


class DebtCreate(DebtBase):
    pass


class DebtUpdate(BaseModel):
    creditor: Optional[str] = None
    amount: Optional[float] = None
    due_date: Optional[str] = None
    status: Optional[Literal["active", "overdue", "paid"]] = None
    type: Optional[Literal["loan", "credit_line", "accounts_payable", "lease", "other"]] = None
    description: Optional[str] = None


class DebtResponse(DebtBase):
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None


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


@router.get("/debts")
async def get_all_debts():
    """
    Получить все задолженности
    """
    try:
        conn = await get_db_connection()
        try:
            # Проверяем существование таблицы
            table_exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' AND table_name = 'debts'
                )
            """)
            
            if not table_exists:
                # Возвращаем mock данные если таблицы нет
                return {
                    "debts": [
                        {
                            "id": "debt-1",
                            "creditor": "Банк ВТБ",
                            "amount": 5000000,
                            "due_date": "2025-12-31",
                            "status": "active",
                            "type": "loan",
                            "description": "Кредит на развитие бизнеса"
                        },
                        {
                            "id": "debt-2",
                            "creditor": "Сбербанк",
                            "amount": 3000000,
                            "due_date": "2026-06-30",
                            "status": "active",
                            "type": "credit_line",
                            "description": "Кредитная линия"
                        },
                        {
                            "id": "debt-3",
                            "creditor": "Поставщик ООО Стройматериалы",
                            "amount": 800000,
                            "due_date": "2025-11-15",
                            "status": "overdue",
                            "type": "accounts_payable",
                            "description": "Задолженность за материалы"
                        },
                        {
                            "id": "debt-4",
                            "creditor": "Лизинговая компания",
                            "amount": 2000000,
                            "due_date": "2027-03-20",
                            "status": "active",
                            "type": "lease",
                            "description": "Лизинг оборудования"
                        }
                    ],
                    "summary": {
                        "total": 10800000,
                        "overdue": 800000,
                        "active": 10000000,
                        "count": 4
                    }
                }
            
            # Получаем данные из БД
            query = """
                SELECT id, creditor, amount, due_date, status, type, description, created_at, updated_at
                FROM debts
                ORDER BY due_date ASC
            """
            rows = await conn.fetch(query)
            
            debts = []
            for row in rows:
                debts.append({
                    "id": row['id'],
                    "creditor": row['creditor'],
                    "amount": float(row['amount']),
                    "due_date": row['due_date'].strftime("%Y-%m-%d"),
                    "status": row['status'],
                    "type": row['type'],
                    "description": row['description'],
                    "created_at": row['created_at'].isoformat() if row['created_at'] else None,
                    "updated_at": row['updated_at'].isoformat() if row['updated_at'] else None
                })
            
            # Вычисляем summary
            total = sum(d['amount'] for d in debts)
            overdue = sum(d['amount'] for d in debts if d['status'] == 'overdue')
            active = sum(d['amount'] for d in debts if d['status'] == 'active')
            
            return {
                "debts": debts,
                "summary": {
                    "total": total,
                    "overdue": overdue,
                    "active": active,
                    "count": len(debts)
                }
            }
        finally:
            await conn.close()
    except Exception as e:
        logger.error(f"Error fetching debts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/debts", response_model=DebtResponse)
async def create_debt(debt: DebtCreate):
    """
    Создать новую задолженность
    """
    try:
        conn = await get_db_connection()
        try:
            debt_id = str(uuid4())
            
            query = """
                INSERT INTO debts (id, creditor, amount, due_date, status, type, description, created_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, CURRENT_TIMESTAMP)
                RETURNING id, creditor, amount, due_date, status, type, description, created_at, updated_at
            """
            
            row = await conn.fetchrow(
                query,
                debt_id,
                debt.creditor,
                debt.amount,
                debt.due_date,
                debt.status,
                debt.type,
                debt.description
            )
            
            return {
                "id": row['id'],
                "creditor": row['creditor'],
                "amount": float(row['amount']),
                "due_date": row['due_date'].strftime("%Y-%m-%d"),
                "status": row['status'],
                "type": row['type'],
                "description": row['description'],
                "created_at": row['created_at'],
                "updated_at": row['updated_at']
            }
        finally:
            await conn.close()
    except Exception as e:
        logger.error(f"Error creating debt: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/debts/{debt_id}", response_model=DebtResponse)
async def update_debt(debt_id: str, debt: DebtUpdate):
    """
    Обновить задолженность
    """
    try:
        conn = await get_db_connection()
        try:
            # Формируем динамический запрос только для переданных полей
            updates = []
            values = []
            param_count = 1
            
            if debt.creditor is not None:
                updates.append(f"creditor = ${param_count}")
                values.append(debt.creditor)
                param_count += 1
            
            if debt.amount is not None:
                updates.append(f"amount = ${param_count}")
                values.append(debt.amount)
                param_count += 1
            
            if debt.due_date is not None:
                updates.append(f"due_date = ${param_count}")
                values.append(debt.due_date)
                param_count += 1
            
            if debt.status is not None:
                updates.append(f"status = ${param_count}")
                values.append(debt.status)
                param_count += 1
            
            if debt.type is not None:
                updates.append(f"type = ${param_count}")
                values.append(debt.type)
                param_count += 1
            
            if debt.description is not None:
                updates.append(f"description = ${param_count}")
                values.append(debt.description)
                param_count += 1
            
            if not updates:
                raise HTTPException(status_code=400, detail="No fields to update")
            
            updates.append(f"updated_at = CURRENT_TIMESTAMP")
            values.append(debt_id)
            
            query = f"""
                UPDATE debts
                SET {', '.join(updates)}
                WHERE id = ${param_count}
                RETURNING id, creditor, amount, due_date, status, type, description, created_at, updated_at
            """
            
            row = await conn.fetchrow(query, *values)
            
            if not row:
                raise HTTPException(status_code=404, detail="Debt not found")
            
            return {
                "id": row['id'],
                "creditor": row['creditor'],
                "amount": float(row['amount']),
                "due_date": row['due_date'].strftime("%Y-%m-%d"),
                "status": row['status'],
                "type": row['type'],
                "description": row['description'],
                "created_at": row['created_at'],
                "updated_at": row['updated_at']
            }
        finally:
            await conn.close()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating debt: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/debts/{debt_id}")
async def delete_debt(debt_id: str):
    """
    Удалить задолженность
    """
    try:
        conn = await get_db_connection()
        try:
            query = "DELETE FROM debts WHERE id = $1 RETURNING id"
            row = await conn.fetchrow(query, debt_id)
            
            if not row:
                raise HTTPException(status_code=404, detail="Debt not found")
            
            return {"success": True, "message": "Debt deleted successfully"}
        finally:
            await conn.close()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting debt: {e}")
        raise HTTPException(status_code=500, detail=str(e))
