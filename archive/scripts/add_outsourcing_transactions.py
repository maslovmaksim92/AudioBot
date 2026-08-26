#!/usr/bin/env python3
"""
Скрипт для добавления транзакций "Аутсорсинг персонала" для ВАШ ДОМ модель
"""

import asyncio
import asyncpg
import os
import uuid
from datetime import datetime
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv('/app/backend/.env')

# Данные Аутсорсинга персонала (уборщицы УФИЦ)
OUTSOURCING_DATA = {
    'Январь 2025': 1400700,
    'Февраль 2025': 2070600,
    'Март 2025': 2801400,
    'Апрель 2025': 2984100,
    'Май 2025': 3105900,
    'Июнь 2025': 2923200,
    'Июль 2025': 2862300,
    'Август 2025': 2801400,
    'Сентябрь 2025': 2862300
}

async def add_outsourcing():
    """Добавить транзакции Аутсорсинга персонала"""
    db_url = os.environ.get('DATABASE_URL')
    
    if not db_url:
        print("❌ DATABASE_URL не найден")
        return
    
    print(f"🔗 Подключение к базе данных...")
    conn = await asyncpg.connect(db_url)
    
    try:
        print("\n📊 Добавление транзакций 'Аутсорсинг персонала' для 'ВАШ ДОМ модель'...")
        
        # Удаляем старые транзакции Аутсорсинга персонала для ВАШ ДОМ модель
        await conn.execute("""
            DELETE FROM financial_transactions 
            WHERE company = 'ВАШ ДОМ модель' 
              AND category = 'Аутсорсинг персонала'
        """)
        print("✅ Старые транзакции удалены")
        
        # Добавляем новые транзакции с UUID
        total = 0
        for month, amount in OUTSOURCING_DATA.items():
            transaction_id = str(uuid.uuid4())
            await conn.execute("""
                INSERT INTO financial_transactions 
                (id, date, type, category, amount, description, counterparty, project, company, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            """, 
                transaction_id,
                datetime.now(),
                'expense',
                'Аутсорсинг персонала',
                amount,
                f'Уборщицы УФИЦ - {month}',
                'УФИЦ',
                month,
                'ВАШ ДОМ модель',
                datetime.now(),
                datetime.now()
            )
            total += amount
            print(f"   ✅ {month}: {amount:,.0f} ₽")
        
        print(f"\n✅ Добавлено {len(OUTSOURCING_DATA)} транзакций")
        print(f"💰 Общая сумма: {total:,.0f} ₽")
        
        # Проверяем результат
        print("\n📋 Проверка транзакций 'Аутсорсинг персонала':")
        rows = await conn.fetch("""
            SELECT project as month, amount
            FROM financial_transactions
            WHERE company = 'ВАШ ДОМ модель' 
              AND category = 'Аутсорсинг персонала'
            ORDER BY project
        """)
        
        for row in rows:
            print(f"   {row['month']}: {row['amount']:,.0f} ₽")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(add_outsourcing())
