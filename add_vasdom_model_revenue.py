#!/usr/bin/env python3
"""
Скрипт для добавления ручной выручки для "ВАШ ДОМ модель"
Используем данные из скриншота пользователя
"""

import asyncio
import asyncpg
import os
import uuid
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv('/app/backend/.env')

# Данные выручки для консолидированной модели (из скриншота)
REVENUE_DATA = {
    'Январь 2025': 4712459,
    'Февраль 2025': 4425900,
    'Март 2025': 4402000,
    'Апрель 2025': 5245890,
    'Май 2025': 5127353,
    'Июнь 2025': 4418148,
    'Июль 2025': 4597926,
    'Август 2025': 5899305,
    'Сентябрь 2025': 5325049
}

async def add_revenue():
    """Добавить выручку для ВАШ ДОМ модель"""
    db_url = os.environ.get('DATABASE_URL')
    
    if not db_url:
        print("❌ DATABASE_URL не найден")
        return
    
    print(f"🔗 Подключение к базе данных...")
    conn = await asyncpg.connect(db_url)
    
    try:
        # Проверяем существование таблицы monthly_revenue
        table_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'monthly_revenue'
            )
        """)
        
        if not table_exists:
            print("❌ Таблица monthly_revenue не существует")
            return
        
        print("\n📊 Добавление выручки для 'ВАШ ДОМ модель'...")
        
        # Удаляем старые записи для консолидированной модели
        await conn.execute("""
            DELETE FROM monthly_revenue 
            WHERE company = 'ВАШ ДОМ модель'
        """)
        print("✅ Старые записи удалены")
        
        # Добавляем новые записи с UUID
        for month, revenue in REVENUE_DATA.items():
            record_id = str(uuid.uuid4())
            await conn.execute("""
                INSERT INTO monthly_revenue (id, month, revenue, company)
                VALUES ($1, $2, $3, $4)
            """, record_id, month, revenue, 'ВАШ ДОМ модель')
            print(f"   ✅ {month}: {revenue:,.0f} ₽")
        
        print(f"\n✅ Добавлено {len(REVENUE_DATA)} записей выручки")
        
        # Проверяем результат
        print("\n📋 Проверка выручки по компаниям:")
        companies = await conn.fetch("""
            SELECT company, COUNT(*) as count, SUM(revenue) as total
            FROM monthly_revenue 
            GROUP BY company
            ORDER BY company
        """)
        
        for row in companies:
            print(f"   {row['company']}: {row['count']} месяцев, итого {row['total']:,.0f} ₽")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(add_revenue())
