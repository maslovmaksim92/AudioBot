#!/usr/bin/env python3
"""
Удаление импортированных транзакций из Excel
"""
import asyncpg
import os
import asyncio

async def delete_imported():
    db_url = os.environ.get('DATABASE_URL')
    conn = await asyncpg.connect(db_url)
    
    try:
        # Удаляем все транзакции, которые были импортированы из Excel
        query = """
            DELETE FROM financial_transactions
            WHERE description LIKE 'Импорт из Excel%'
        """
        
        result = await conn.execute(query)
        print(f"✅ Удалено транзакций: {result.split()[-1]}")
        
    finally:
        await conn.close()

if __name__ == '__main__':
    asyncio.run(delete_imported())
