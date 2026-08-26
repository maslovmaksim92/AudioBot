#!/usr/bin/env python3
"""
Скрипт для переименования компаний в базе данных
ООО ВАШ ДОМ -> ВАШ ДОМ ФАКТ
УФИЦ -> УФИЦ модель
"""

import asyncio
import asyncpg
import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv('/app/backend/.env')

async def rename_companies():
    """Переименовать компании в базе данных"""
    db_url = os.environ.get('DATABASE_URL')
    
    if not db_url:
        print("❌ DATABASE_URL не найден")
        return
    
    print(f"🔗 Подключение к базе данных...")
    conn = await asyncpg.connect(db_url)
    
    try:
        # Переименовываем в таблице financial_transactions
        print("\n📊 Обновление таблицы financial_transactions...")
        
        # ООО ВАШ ДОМ -> ВАШ ДОМ ФАКТ
        result1 = await conn.execute("""
            UPDATE financial_transactions 
            SET company = 'ВАШ ДОМ ФАКТ' 
            WHERE company = 'ООО ВАШ ДОМ'
        """)
        print(f"✅ Обновлено 'ООО ВАШ ДОМ' -> 'ВАШ ДОМ ФАКТ': {result1}")
        
        # УФИЦ -> УФИЦ модель
        result2 = await conn.execute("""
            UPDATE financial_transactions 
            SET company = 'УФИЦ модель' 
            WHERE company = 'УФИЦ'
        """)
        print(f"✅ Обновлено 'УФИЦ' -> 'УФИЦ модель': {result2}")
        
        # Проверяем результат
        print("\n📋 Проверка обновлений...")
        companies = await conn.fetch("""
            SELECT company, COUNT(*) as count 
            FROM financial_transactions 
            GROUP BY company
        """)
        
        for row in companies:
            print(f"   {row['company']}: {row['count']} записей")
        
        # Обновляем таблицу monthly_revenue если существует
        print("\n📊 Обновление таблицы monthly_revenue...")
        table_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'monthly_revenue'
            )
        """)
        
        if table_exists:
            result3 = await conn.execute("""
                UPDATE monthly_revenue 
                SET company = 'ВАШ ДОМ ФАКТ' 
                WHERE company = 'ООО ВАШ ДОМ'
            """)
            print(f"✅ Обновлено 'ООО ВАШ ДОМ' -> 'ВАШ ДОМ ФАКТ': {result3}")
            
            result4 = await conn.execute("""
                UPDATE monthly_revenue 
                SET company = 'УФИЦ модель' 
                WHERE company = 'УФИЦ'
            """)
            print(f"✅ Обновлено 'УФИЦ' -> 'УФИЦ модель': {result4}")
        else:
            print("⚠️  Таблица monthly_revenue не существует")
        
        print("\n✅ Все компании успешно переименованы!")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(rename_companies())
