from fastapi import APIRouter, HTTPException, File, UploadFile
from typing import List, Optional, Literal
from datetime import datetime, timedelta
from pydantic import BaseModel
import logging
import asyncpg
import csv
import io
from uuid import uuid4
import os

logger = logging.getLogger(__name__)
router = APIRouter(tags=["finance-transactions"])

# Pydantic модели (определены здесь, чтобы избежать конфликтов импорта)
class TransactionBase(BaseModel):
    date: datetime
    amount: float
    category: str
    type: Literal["income", "expense"]
    description: Optional[str] = None
    payment_method: Optional[str] = None
    counterparty: Optional[str] = None
    project: Optional[str] = None
    tags: Optional[list[str]] = []

class TransactionCreate(TransactionBase):
    pass

class TransactionUpdate(BaseModel):
    date: Optional[datetime] = None
    amount: Optional[float] = None
    category: Optional[str] = None
    type: Optional[Literal["income", "expense"]] = None
    description: Optional[str] = None
    payment_method: Optional[str] = None
    counterparty: Optional[str] = None
    project: Optional[str] = None
    tags: Optional[list[str]] = None

class TransactionResponse(TransactionBase):
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

DEFAULT_INCOME_CATEGORIES = [
    "Поступление от покупателей", "Оплата услуг", "Продажа товаров", "Аренда", "Инвестиции", "Прочие доходы"
]

DEFAULT_EXPENSE_CATEGORIES = [
    "Зарплата", 
    "Филиал Ленинск-Кузнецкий",
    "Материалы", 
    "Аренда", 
    "Коммунальные услуги", 
    "Транспорт",
    "Реклама и маркетинг", 
    "Налоги", 
    "Страхование", 
    "Оборудование",
    "Покупка авто",
    "Канцтовары",
    "Юридические услуги",
    "Аутсорсинг",
    "Лизинг",
    "Кредиты",
    "Мобильная связь",
    "Продукты питания",
    "Цифровая техника",
    "Прочие расходы"
]

# Helper function для получения DB connection
async def get_db_connection():
    """Получить прямое соединение с БД для raw SQL"""
    db_url = os.environ.get('DATABASE_URL', '')
    
    if not db_url:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    # Преобразуем asyncpg URL
    db_url = db_url.replace('postgresql+asyncpg://', 'postgresql://')
    
    try:
        return await asyncpg.connect(db_url)
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")

# CRUD операции

@router.post("/transactions", response_model=TransactionResponse)
async def create_transaction(transaction: TransactionCreate):
    """
    Создать новую финансовую транзакцию
    """
    try:
        conn = await get_db_connection()
        try:
            transaction_id = str(uuid4())
            now = datetime.now()
            
            await conn.execute("""
                INSERT INTO financial_transactions 
                (id, date, amount, category, type, description, payment_method, 
                 counterparty, project, tags, created_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            """, transaction_id, transaction.date, transaction.amount, 
                transaction.category, transaction.type, transaction.description,
                transaction.payment_method, transaction.counterparty, 
                transaction.project, transaction.tags or [], now)
            
            # Получить созданную транзакцию
            row = await conn.fetchrow(
                "SELECT * FROM financial_transactions WHERE id = $1", 
                transaction_id
            )
            
            return TransactionResponse(
                id=row['id'],
                date=row['date'],
                amount=float(row['amount']),
                category=row['category'],
                type=row['type'],
                description=row['description'],
                payment_method=row['payment_method'],
                counterparty=row['counterparty'],
                project=row['project'],
                tags=row['tags'] or [],
                created_at=row['created_at'],
                updated_at=row['updated_at']
            )
        finally:
            await conn.close()
    except Exception as e:
        logger.error(f"Error creating transaction: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/transactions", response_model=List[TransactionResponse])
async def get_transactions(
    type: Optional[str] = None,
    category: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
):
    """
    Получить список транзакций с фильтрами
    """
    try:
        conn = await get_db_connection()
        try:
            query = "SELECT * FROM financial_transactions WHERE 1=1"
            params = []
            param_count = 0
            
            if type:
                param_count += 1
                query += f" AND type = ${param_count}"
                params.append(type)
            
            if category:
                param_count += 1
                query += f" AND category = ${param_count}"
                params.append(category)
            
            if date_from:
                param_count += 1
                query += f" AND date >= ${param_count}"
                params.append(datetime.fromisoformat(date_from))
            
            if date_to:
                param_count += 1
                query += f" AND date <= ${param_count}"
                params.append(datetime.fromisoformat(date_to))
            
            query += " ORDER BY date DESC"
            
            param_count += 1
            query += f" LIMIT ${param_count}"
            params.append(limit)
            
            param_count += 1
            query += f" OFFSET ${param_count}"
            params.append(offset)
            
            rows = await conn.fetch(query, *params)
            
            return [
                TransactionResponse(
                    id=row['id'],
                    date=row['date'],
                    amount=float(row['amount']),
                    category=row['category'],
                    type=row['type'],
                    description=row['description'],
                    payment_method=row['payment_method'],
                    counterparty=row['counterparty'],
                    project=row['project'],
                    tags=row['tags'] or [],
                    created_at=row['created_at'],
                    updated_at=row['updated_at']
                )
                for row in rows
            ]
        finally:
            await conn.close()
    except Exception as e:
        logger.error(f"Error fetching transactions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/transactions/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(transaction_id: str):
    """
    Получить конкретную транзакцию по ID
    """
    try:
        conn = await get_db_connection()
        try:
            row = await conn.fetchrow(
                "SELECT * FROM financial_transactions WHERE id = $1",
                transaction_id
            )
            
            if not row:
                raise HTTPException(status_code=404, detail="Transaction not found")
            
            return TransactionResponse(
                id=row['id'],
                date=row['date'],
                amount=float(row['amount']),
                category=row['category'],
                type=row['type'],
                description=row['description'],
                payment_method=row['payment_method'],
                counterparty=row['counterparty'],
                project=row['project'],
                tags=row['tags'] or [],
                created_at=row['created_at'],
                updated_at=row['updated_at']
            )
        finally:
            await conn.close()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching transaction: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/transactions/{transaction_id}", response_model=TransactionResponse)
async def update_transaction(transaction_id: str, transaction: TransactionUpdate):
    """
    Обновить транзакцию
    """
    try:
        conn = await get_db_connection()
        try:
            # Проверить существование
            existing = await conn.fetchrow(
                "SELECT id FROM financial_transactions WHERE id = $1",
                transaction_id
            )
            if not existing:
                raise HTTPException(status_code=404, detail="Transaction not found")
            
            # Построить UPDATE запрос
            update_fields = []
            params = []
            param_count = 0
            
            if transaction.date is not None:
                param_count += 1
                update_fields.append(f"date = ${param_count}")
                params.append(transaction.date)
            
            if transaction.amount is not None:
                param_count += 1
                update_fields.append(f"amount = ${param_count}")
                params.append(transaction.amount)
            
            if transaction.category is not None:
                param_count += 1
                update_fields.append(f"category = ${param_count}")
                params.append(transaction.category)
            
            if transaction.type is not None:
                param_count += 1
                update_fields.append(f"type = ${param_count}")
                params.append(transaction.type)
            
            if transaction.description is not None:
                param_count += 1
                update_fields.append(f"description = ${param_count}")
                params.append(transaction.description)
            
            if transaction.payment_method is not None:
                param_count += 1
                update_fields.append(f"payment_method = ${param_count}")
                params.append(transaction.payment_method)
            
            if transaction.counterparty is not None:
                param_count += 1
                update_fields.append(f"counterparty = ${param_count}")
                params.append(transaction.counterparty)
            
            if transaction.project is not None:
                param_count += 1
                update_fields.append(f"project = ${param_count}")
                params.append(transaction.project)
            
            if transaction.tags is not None:
                param_count += 1
                update_fields.append(f"tags = ${param_count}")
                params.append(transaction.tags)
            
            # updated_at
            param_count += 1
            update_fields.append(f"updated_at = ${param_count}")
            params.append(datetime.now())
            
            if not update_fields:
                raise HTTPException(status_code=400, detail="No fields to update")
            
            param_count += 1
            params.append(transaction_id)
            
            query = f"""
                UPDATE financial_transactions 
                SET {', '.join(update_fields)}
                WHERE id = ${param_count}
            """
            
            await conn.execute(query, *params)
            
            # Вернуть обновлённую транзакцию
            return await get_transaction(transaction_id)
        finally:
            await conn.close()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating transaction: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/transactions/{transaction_id}")
async def delete_transaction(transaction_id: str):
    """
    Удалить транзакцию
    """
    try:
        conn = await get_db_connection()
        try:
            result = await conn.execute(
                "DELETE FROM financial_transactions WHERE id = $1",
                transaction_id
            )
            
            if result == "DELETE 0":
                raise HTTPException(status_code=404, detail="Transaction not found")
            
            return {"success": True, "message": "Transaction deleted"}
        finally:
            await conn.close()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting transaction: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Дополнительные endpoints

@router.get("/categories")
async def get_categories():
    """
    Получить список категорий доходов и расходов
    """
    return {
        "income": DEFAULT_INCOME_CATEGORIES,
        "expense": DEFAULT_EXPENSE_CATEGORIES
    }

@router.post("/transactions/import-csv")
async def import_csv(file: UploadFile = File(...)):
    """
    Импортировать транзакции из CSV файла
    
    Формат CSV: date,amount,category,type,description,payment_method,counterparty
    """
    try:
        content = await file.read()
        csv_text = content.decode('utf-8')
        csv_reader = csv.DictReader(io.StringIO(csv_text))
        
        conn = await get_db_connection()
        try:
            imported_count = 0
            errors = []
            
            for row_num, row in enumerate(csv_reader, start=2):
                try:
                    transaction_id = str(uuid4())
                    now = datetime.now()
                    
                    # Парсинг даты
                    date = datetime.fromisoformat(row['date'].strip())
                    amount = float(row['amount'].strip())
                    category = row['category'].strip()
                    trans_type = row['type'].strip().lower()
                    
                    if trans_type not in ['income', 'expense']:
                        raise ValueError(f"Invalid type: {trans_type}")
                    
                    await conn.execute("""
                        INSERT INTO financial_transactions 
                        (id, date, amount, category, type, description, payment_method, 
                         counterparty, project, tags, created_at)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                    """, transaction_id, date, amount, category, trans_type,
                        row.get('description', '').strip(),
                        row.get('payment_method', '').strip(),
                        row.get('counterparty', '').strip(),
                        row.get('project', '').strip(),
                        [], now)
                    
                    imported_count += 1
                except Exception as e:
                    errors.append(f"Строка {row_num}: {str(e)}")
            
            return {
                "success": True,
                "imported": imported_count,
                "errors": errors if errors else None
            }
        finally:
            await conn.close()
    except Exception as e:
        logger.error(f"Error importing CSV: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/init-database")
async def init_database():
    """
    Инициализировать таблицу финансовых транзакций
    """
    CREATE_TABLE_SQL = """
    CREATE TABLE IF NOT EXISTS financial_transactions (
        id VARCHAR(36) PRIMARY KEY,
        date TIMESTAMP WITH TIME ZONE NOT NULL,
        amount DECIMAL(15, 2) NOT NULL,
        category VARCHAR(100) NOT NULL,
        type VARCHAR(10) NOT NULL CHECK (type IN ('income', 'expense')),
        description TEXT,
        payment_method VARCHAR(50),
        counterparty VARCHAR(200),
        project VARCHAR(100),
        tags TEXT[],
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE
    );

    CREATE INDEX IF NOT EXISTS idx_transactions_date ON financial_transactions(date);
    CREATE INDEX IF NOT EXISTS idx_transactions_type ON financial_transactions(type);
    CREATE INDEX IF NOT EXISTS idx_transactions_category ON financial_transactions(category);
    """
    
    try:
        conn = await get_db_connection()
        try:
            await conn.execute(CREATE_TABLE_SQL)
            return {"success": True, "message": "Database table created successfully"}
        finally:
            await conn.close()
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise HTTPException(status_code=500, detail=str(e))
