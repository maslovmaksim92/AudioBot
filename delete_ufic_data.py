#!/usr/bin/env python3
"""
Удаление всех данных УФИЦ
"""
import asyncpg
import os
import asyncio

async def delete_ufic():
    db_url = os.environ.get('DATABASE_URL')
    conn = await asyncpg.connect(db_url)
    
    try:
        query = """
            DELETE FROM financial_transactions
            WHERE company = 'УФИЦ'
        """
        result = await conn.execute(query)
        print(f"✅ Удалено транзакций УФИЦ: {result.split()[-1]}")
        
    finally:
        await conn.close()

if __name__ == '__main__':
    asyncio.run(delete_ufic())
