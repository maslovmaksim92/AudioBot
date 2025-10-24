#!/usr/bin/env python3
"""
Добавление ФОТ управляющего персонала для УФИЦ
"""
import asyncpg
import os
import asyncio
from datetime import datetime
from uuid import uuid4

MONTH_MAP = {
    1: 'Январь 2025',
    2: 'Февраль 2025',
    3: 'Март 2025',
    4: 'Апрель 2025',
    5: 'Май 2025',
    6: 'Июнь 2025',
    7: 'Июль 2025',
    8: 'Август 2025',
    9: 'Сентябрь 2025'
}

async def add_management_fot():
    db_url = os.environ.get('DATABASE_URL')
    conn = await asyncpg.connect(db_url)
    
    try:
        imported = 0
        
        for month_num, month_ru in MONTH_MAP.items():
            date = datetime(2025, month_num, 15)
            transaction_id = str(uuid4())
            
            query = """
                INSERT INTO financial_transactions 
                (id, date, amount, category, type, description, project, company, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """
            await conn.execute(
                query,
                transaction_id,
                date,
                312000,
                'ФОТ управляющие персонал',
                'expense',
                f'ФОТ управляющего персонала УФИЦ - {month_ru}',
                month_ru,
                'УФИЦ'
            )
            imported += 1
            print(f"✅ {month_ru}: ФОТ управляющие персонал 312,000 ₽")
        
        print(f"\n=== ИТОГО ===")
        print(f"✅ Добавлено расходов: {imported}")
        
    finally:
        await conn.close()

if __name__ == '__main__':
    asyncio.run(add_management_fot())
