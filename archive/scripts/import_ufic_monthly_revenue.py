#!/usr/bin/env python3
"""
Импорт ручной выручки УФИЦ в таблицу monthly_revenue
"""
import asyncpg
import os
import asyncio

# Данные из файла
UFIC_REVENUE = {
    'Январь 2025': 1400700,
    'Февраль 2025': 2070600,
    'Март 2025': 2801400,
    'Апрель 2025': 3166125,
    'Май 2025': 3557300,
    'Июнь 2025': 3591200,
    'Июль 2025': 3429700,
    'Август 2025': 3438600,
    'Сентябрь 2025': 3648900,
    'Октябрь 2025': 220500
}

async def import_revenue():
    db_url = os.environ.get('DATABASE_URL')
    conn = await asyncpg.connect(db_url)
    
    try:
        # Сначала удаляем все записи УФИЦ
        await conn.execute("""
            DELETE FROM monthly_revenue WHERE company = 'УФИЦ'
        """)
        print("🗑️  Удалены старые записи УФИЦ")
        
        imported = 0
        from uuid import uuid4
        
        for month, revenue in UFIC_REVENUE.items():
            # Вставляем новую запись с UUID
            record_id = str(uuid4())
            await conn.execute("""
                INSERT INTO monthly_revenue (id, month, revenue, company)
                VALUES ($1, $2, $3, $4)
            """, record_id, month, revenue, 'УФИЦ')
            print(f"✅ Добавлено: {month} = {revenue:,.0f} ₽")
            
            imported += 1
        
        print(f"\n=== ИТОГО ===")
        print(f"✅ Обработано записей: {imported}")
        
    finally:
        await conn.close()

if __name__ == '__main__':
    asyncio.run(import_revenue())
