"""
API для управления товарными запасами
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import asyncpg
import os
import logging
from uuid import uuid4

logger = logging.getLogger(__name__)
router = APIRouter(tags=["inventory"])


class InventoryBase(BaseModel):
    name: str
    category: str
    quantity: int
    unit: str
    cost: float
    location: Optional[str] = None


class InventoryCreate(InventoryBase):
    pass


class InventoryUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    quantity: Optional[int] = None
    unit: Optional[str] = None
    cost: Optional[float] = None
    location: Optional[str] = None


class InventoryResponse(BaseModel):
    id: str
    name: str
    category: str
    quantity: int
    unit: str
    cost: float
    value: float
    location: Optional[str] = None
    created_at: Optional[datetime] = None
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


@router.get("/inventory")
async def get_all_inventory():
    """
    Получить все товарные запасы
    """
    try:
        conn = await get_db_connection()
        try:
            # Проверяем существование таблицы
            table_exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' AND table_name = 'inventory'
                )
            """)
            
            if not table_exists:
                # Возвращаем mock данные
                return {
                    "inventory": [
                        {
                            "id": "inv-1",
                            "name": "Моющие средства",
                            "category": "Химия",
                            "quantity": 500,
                            "unit": "шт",
                            "cost": 250,
                            "value": 125000,
                            "location": "Склад А"
                        },
                        {
                            "id": "inv-2",
                            "name": "Перчатки резиновые",
                            "category": "Расходники",
                            "quantity": 1000,
                            "unit": "пар",
                            "cost": 50,
                            "value": 50000,
                            "location": "Склад А"
                        },
                        {
                            "id": "inv-3",
                            "name": "Швабры",
                            "category": "Инвентарь",
                            "quantity": 150,
                            "unit": "шт",
                            "cost": 800,
                            "value": 120000,
                            "location": "Склад Б"
                        }
                    ],
                    "summary": {
                        "total_value": 295000,
                        "total_items": 1650,
                        "categories": 3
                    }
                }
            
            # Получаем данные из БД
            query = """
                SELECT id, name, category, quantity, unit, cost, value, location, created_at, updated_at
                FROM inventory
                ORDER BY category, name
            """
            rows = await conn.fetch(query)
            
            inventory = []
            for row in rows:
                inventory.append({
                    "id": row['id'],
                    "name": row['name'],
                    "category": row['category'],
                    "quantity": row['quantity'],
                    "unit": row['unit'],
                    "cost": float(row['cost']),
                    "value": float(row['value']),
                    "location": row['location'],
                    "created_at": row['created_at'].isoformat() if row['created_at'] else None,
                    "updated_at": row['updated_at'].isoformat() if row['updated_at'] else None
                })
            
            # Вычисляем summary
            total_value = sum(item['value'] for item in inventory)
            total_items = sum(item['quantity'] for item in inventory)
            categories = len(set(item['category'] for item in inventory))
            
            return {
                "inventory": inventory,
                "summary": {
                    "total_value": total_value,
                    "total_items": total_items,
                    "categories": categories
                }
            }
        finally:
            await conn.close()
    except Exception as e:
        logger.error(f"Error fetching inventory: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/inventory", response_model=InventoryResponse)
async def create_inventory_item(item: InventoryCreate):
    """
    Создать новую позицию в запасах
    """
    try:
        conn = await get_db_connection()
        try:
            item_id = str(uuid4())
            value = item.quantity * item.cost
            
            query = """
                INSERT INTO inventory (id, name, category, quantity, unit, cost, value, location, created_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, CURRENT_TIMESTAMP)
                RETURNING id, name, category, quantity, unit, cost, value, location, created_at, updated_at
            """
            
            row = await conn.fetchrow(
                query,
                item_id,
                item.name,
                item.category,
                item.quantity,
                item.unit,
                item.cost,
                value,
                item.location
            )
            
            return {
                "id": row['id'],
                "name": row['name'],
                "category": row['category'],
                "quantity": row['quantity'],
                "unit": row['unit'],
                "cost": float(row['cost']),
                "value": float(row['value']),
                "location": row['location'],
                "created_at": row['created_at'],
                "updated_at": row['updated_at']
            }
        finally:
            await conn.close()
    except Exception as e:
        logger.error(f"Error creating inventory item: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/inventory/{item_id}", response_model=InventoryResponse)
async def update_inventory_item(item_id: str, item: InventoryUpdate):
    """
    Обновить позицию в запасах
    """
    try:
        conn = await get_db_connection()
        try:
            # Получаем текущие данные для расчета value
            current = await conn.fetchrow("SELECT quantity, cost FROM inventory WHERE id = $1", item_id)
            if not current:
                raise HTTPException(status_code=404, detail="Inventory item not found")
            
            quantity = item.quantity if item.quantity is not None else current['quantity']
            cost = item.cost if item.cost is not None else float(current['cost'])
            value = quantity * cost
            
            # Формируем динамический запрос
            updates = []
            values = []
            param_count = 1
            
            if item.name is not None:
                updates.append(f"name = ${param_count}")
                values.append(item.name)
                param_count += 1
            
            if item.category is not None:
                updates.append(f"category = ${param_count}")
                values.append(item.category)
                param_count += 1
            
            if item.quantity is not None:
                updates.append(f"quantity = ${param_count}")
                values.append(item.quantity)
                param_count += 1
            
            if item.unit is not None:
                updates.append(f"unit = ${param_count}")
                values.append(item.unit)
                param_count += 1
            
            if item.cost is not None:
                updates.append(f"cost = ${param_count}")
                values.append(item.cost)
                param_count += 1
            
            if item.location is not None:
                updates.append(f"location = ${param_count}")
                values.append(item.location)
                param_count += 1
            
            if not updates:
                raise HTTPException(status_code=400, detail="No fields to update")
            
            updates.append(f"value = ${param_count}")
            values.append(value)
            param_count += 1
            
            updates.append(f"updated_at = CURRENT_TIMESTAMP")
            values.append(item_id)
            
            query = f"""
                UPDATE inventory
                SET {', '.join(updates)}
                WHERE id = ${param_count}
                RETURNING id, name, category, quantity, unit, cost, value, location, created_at, updated_at
            """
            
            row = await conn.fetchrow(query, *values)
            
            return {
                "id": row['id'],
                "name": row['name'],
                "category": row['category'],
                "quantity": row['quantity'],
                "unit": row['unit'],
                "cost": float(row['cost']),
                "value": float(row['value']),
                "location": row['location'],
                "created_at": row['created_at'],
                "updated_at": row['updated_at']
            }
        finally:
            await conn.close()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating inventory item: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/inventory/{item_id}")
async def delete_inventory_item(item_id: str):
    """
    Удалить позицию из запасов
    """
    try:
        conn = await get_db_connection()
        try:
            query = "DELETE FROM inventory WHERE id = $1 RETURNING id"
            row = await conn.fetchrow(query, item_id)
            
            if not row:
                raise HTTPException(status_code=404, detail="Inventory item not found")
            
            return {"success": True, "message": "Inventory item deleted successfully"}
        finally:
            await conn.close()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting inventory item: {e}")
        raise HTTPException(status_code=500, detail=str(e))
