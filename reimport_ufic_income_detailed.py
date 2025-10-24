#!/usr/bin/env python3
"""
Переимпорт доходов УФИЦ с детализацией по категориям
"""
import asyncpg
import os
import asyncio
from datetime import datetime
from uuid import uuid4

# Данные из файлов
INCOME_DATA = {
    'Январь 2025': {
        'Уборщицы': 1400700,
        'Швеи': 0,
        'Аутсорсинг': 0
    },
    'Февраль 2025': {
        'Уборщицы': 2070600,
        'Швеи': 0,
        'Аутсорсинг': 0
    },
    'Март 2025': {
        'Уборщицы': 2801400,
        'Швеи': 0,
        'Аутсорсинг': 0
    },
    'Апрель 2025': {
        'Уборщицы': 2984100,
        'Швеи': 182025,
        'Аутсорсинг': 0
    },
    'Май 2025': {
        'Уборщицы': 3105900,
        'Швеи': 451400,
        'Аутсорсинг': 0
    },
    'Июнь 2025': {
        'Уборщицы': 2923200,
        'Швеи': 668000,
        'Аутсорсинг': 0
    },
    'Июль 2025': {
        'Уборщицы': 2862300,
        'Швеи': 567400,
        'Аутсорсинг': 0
    },
    'Август 2025': {
        'Уборщицы': 2801400,
        'Швеи': 637200,
        'Аутсорсинг': 0
    },
    'Сентябрь 2025': {
        'Уборщицы': 2862300,
        'Швеи': 713100,
        'Аутсорсинг': 73500
    }
}

MONTH_NUM = {
    'Январь 2025': 1,
    'Февраль 2025': 2,
    'Март 2025': 3,
    'Апрель 2025': 4,
    'Май 2025': 5,
    'Июнь 2025': 6,
    'Июль 2025': 7,
    'Август 2025': 8,
    'Сентябрь 2025': 9
}

async def reimport_income():
    db_url = os.environ.get('DATABASE_URL')
    conn = await asyncpg.connect(db_url)
    
    try:
        # Удаляем все доходы УФИЦ
        print("🗑️  Удаление старых доходов УФИЦ...")
        await conn.execute("""
            DELETE FROM financial_transactions
            WHERE company = 'УФИЦ' AND type = 'income'
        """)
        print("✅ Старые доходы удалены")
        
        imported = 0
        
        for month, categories in INCOME_DATA.items():
            month_num = MONTH_NUM[month]
            date = datetime(2025, month_num, 15)
            
            for category, amount in categories.items():
                if amount > 0:
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
                        amount,
                        category,
                        'income',
                        f'{category} УФИЦ - {month}',
                        month,
                        'УФИЦ'
                    )
                    imported += 1
                    print(f"✅ {month}: {category} {amount:,.0f} ₽")
        
        print(f"\n=== ИТОГО ===")
        print(f"✅ Импортировано доходов: {imported}")
        
    finally:
        await conn.close()

if __name__ == '__main__':
    asyncio.run(reimport_income())
