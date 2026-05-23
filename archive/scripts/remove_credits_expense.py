#!/usr/bin/env python3
"""
Удаление расходов по статье "Кредиты" из ООО ВАШ ДОМ
"""
import asyncpg
import os
import asyncio

async def remove_credits():
    db_url = os.environ.get('DATABASE_URL')
    conn = await asyncpg.connect(db_url)
    
    try:
        # Проверяем сколько есть
        count = await conn.fetchval("""
            SELECT COUNT(*) FROM financial_transactions
            WHERE company = 'ООО ВАШ ДОМ' AND type = 'expense' 
            AND (category LIKE '%кредит%' OR category LIKE '%Кредит%')
        """)
        
        total = await conn.fetchval("""
            SELECT SUM(amount) FROM financial_transactions
            WHERE company = 'ООО ВАШ ДОМ' AND type = 'expense' 
            AND (category LIKE '%кредит%' OR category LIKE '%Кредит%')
        """)
        
        print(f"Найдено транзакций: {count}")
        print(f"Общая сумма: {float(total) if total else 0:,.2f} ₽")
        
        # Удаляем
        result = await conn.execute("""
            DELETE FROM financial_transactions
            WHERE company = 'ООО ВАШ ДОМ' AND type = 'expense' 
            AND (category LIKE '%кредит%' OR category LIKE '%Кредит%')
        """)
        
        print(f"✅ Удалено: {result.split()[-1]} транзакций")
        
    finally:
        await conn.close()

if __name__ == '__main__':
    asyncio.run(remove_credits())
