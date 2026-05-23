#!/usr/bin/env python3
"""
Добавление поля company и пометка текущих данных как "ООО ВАШ ДОМ"
"""
import asyncpg
import os
import asyncio

async def add_company_field():
    db_url = os.environ.get('DATABASE_URL')
    conn = await asyncpg.connect(db_url)
    
    try:
        # Добавляем колонку company
        print("Добавление колонки company...")
        query1 = """
            ALTER TABLE financial_transactions 
            ADD COLUMN IF NOT EXISTS company VARCHAR(100) DEFAULT 'ООО ВАШ ДОМ'
        """
        await conn.execute(query1)
        print("✅ Колонка company добавлена")
        
        # Помечаем все существующие записи как "ООО ВАШ ДОМ"
        print("\nПометка существующих записей как 'ООО ВАШ ДОМ'...")
        query2 = """
            UPDATE financial_transactions
            SET company = 'ООО ВАШ ДОМ'
            WHERE company IS NULL
        """
        result = await conn.execute(query2)
        print(f"✅ Обновлено записей: {result.split()[-1]}")
        
        # Создаем индекс для быстрого поиска
        print("\nСоздание индекса...")
        query3 = """
            CREATE INDEX IF NOT EXISTS idx_transactions_company 
            ON financial_transactions(company)
        """
        await conn.execute(query3)
        print("✅ Индекс создан")
        
    finally:
        await conn.close()

if __name__ == '__main__':
    asyncio.run(add_company_field())
