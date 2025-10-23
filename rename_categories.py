#!/usr/bin/env python3
"""
Переименование категорий расходов
"""
import asyncpg
import os
import asyncio

async def rename_categories():
    db_url = os.environ.get('DATABASE_URL')
    conn = await asyncpg.connect(db_url)
    
    try:
        # Переименовываем "Коммунальные услуги" в "Текущий ремонт"
        query1 = """
            UPDATE financial_transactions
            SET category = 'Текущий ремонт'
            WHERE category = 'Коммунальные услуги' AND type = 'expense'
        """
        result1 = await conn.execute(query1)
        print(f"✅ Переименовано 'Коммунальные услуги' → 'Текущий ремонт': {result1.split()[-1]} записей")
        
        # Переименовываем "Прочие расходы" в "Налоги"
        query2 = """
            UPDATE financial_transactions
            SET category = 'Налоги'
            WHERE category = 'Прочие расходы' AND type = 'expense'
        """
        result2 = await conn.execute(query2)
        print(f"✅ Переименовано 'Прочие расходы' → 'Налоги': {result2.split()[-1]} записей")
        
    finally:
        await conn.close()

if __name__ == '__main__':
    asyncio.run(rename_categories())
