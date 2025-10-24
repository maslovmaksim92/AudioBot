#!/usr/bin/env python3
"""
Импорт реальных данных по долгам
"""
import asyncpg
import os
import asyncio
from datetime import datetime
from uuid import uuid4

DEBTS_DATA = [
    {
        'creditor': 'Кредит Сбербанк 1',
        'amount': 532089,
        'due_date': datetime(2027, 2, 5),
        'type': 'loan',
        'status': 'active',
        'description': 'Остаток кредита Сбербанк 1'
    },
    {
        'creditor': 'Кредит Сбербанк 2',
        'amount': 3888888,
        'due_date': datetime(2028, 9, 12),
        'type': 'loan',
        'status': 'active',
        'description': 'Остаток кредита Сбербанк 2'
    },
    {
        'creditor': 'Лизинг ВТБ погрузчик',
        'amount': 1189000,
        'due_date': datetime(2026, 12, 12),
        'type': 'lease',
        'status': 'active',
        'description': 'Остаток лизинга ВТБ на погрузчик'
    }
]

async def import_debts():
    db_url = os.environ.get('DATABASE_URL')
    conn = await asyncpg.connect(db_url)
    
    try:
        # Проверяем существует ли таблица debts
        table_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'debts'
            )
        """)
        
        if not table_exists:
            print("⚠️  Таблица debts не существует. Создаем...")
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS debts (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    creditor VARCHAR(255) NOT NULL,
                    amount DECIMAL(15, 2) NOT NULL,
                    due_date DATE,
                    type VARCHAR(50),
                    status VARCHAR(50) DEFAULT 'active',
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("✅ Таблица debts создана")
        
        # Удаляем все существующие долги
        await conn.execute("DELETE FROM debts")
        print("🗑️  Старые записи удалены")
        
        # Вставляем новые данные
        imported = 0
        for debt in DEBTS_DATA:
            debt_id = str(uuid4())
            await conn.execute("""
                INSERT INTO debts (id, creditor, amount, due_date, type, status, description, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """, 
                debt_id,
                debt['creditor'],
                debt['amount'],
                debt['due_date'],
                debt['type'],
                debt['status'],
                debt['description']
            )
            imported += 1
            print(f"✅ {debt['creditor']}: {debt['amount']:,.0f} ₽ (до {debt['due_date'].strftime('%d.%m.%Y')})")
        
        print(f"\n=== ИТОГО ===")
        print(f"✅ Импортировано долгов: {imported}")
        
        # Проверяем итоговую сумму
        total = await conn.fetchval("SELECT SUM(amount) FROM debts WHERE status = 'active'")
        print(f"💰 Общая сумма долгов: {float(total):,.0f} ₽")
        
    finally:
        await conn.close()

if __name__ == '__main__':
    asyncio.run(import_debts())
