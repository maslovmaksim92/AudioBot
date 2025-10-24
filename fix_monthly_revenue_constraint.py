#!/usr/bin/env python3
"""
Изменение constraint в таблице monthly_revenue
"""
import asyncpg
import os
import asyncio

async def fix_constraint():
    db_url = os.environ.get('DATABASE_URL')
    conn = await asyncpg.connect(db_url)
    
    try:
        # Удаляем старый constraint
        print("Удаление старого constraint...")
        await conn.execute("""
            ALTER TABLE monthly_revenue 
            DROP CONSTRAINT IF EXISTS monthly_revenue_month_key
        """)
        print("✅ Старый constraint удален")
        
        # Создаем новый constraint на пару (month, company)
        print("\nСоздание нового constraint...")
        await conn.execute("""
            ALTER TABLE monthly_revenue 
            ADD CONSTRAINT monthly_revenue_month_company_key 
            UNIQUE (month, company)
        """)
        print("✅ Новый constraint создан: UNIQUE(month, company)")
        
    finally:
        await conn.close()

if __name__ == '__main__':
    asyncio.run(fix_constraint())
