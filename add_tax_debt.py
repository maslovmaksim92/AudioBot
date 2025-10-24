#!/usr/bin/env python3
"""
Добавление долга по налогам
"""
import asyncpg
import os
import asyncio
from datetime import datetime
from uuid import uuid4

async def add_tax_debt():
    db_url = os.environ.get('DATABASE_URL')
    conn = await asyncpg.connect(db_url)
    
    try:
        debt_id = str(uuid4())
        await conn.execute("""
            INSERT INTO debts (id, creditor, amount, due_date, type, status, description, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """, 
            debt_id,
            'Налоги',
            2150000,
            datetime(2025, 12, 31),
            'tax',
            'active',
            'Задолженность по налогам'
        )
        print(f"✅ Добавлен долг: Налоги 2,150,000 ₽")
        
    finally:
        await conn.close()

if __name__ == '__main__':
    asyncio.run(add_tax_debt())
