#!/usr/bin/env python3
"""
Импорт данных УФИЦ из Excel файла
"""
import pandas as pd
import asyncpg
import os
import asyncio
from datetime import datetime
from uuid import uuid4

# Маппинг месяцев
MONTH_MAP = {
    1: 'Январь 2025',
    2: 'Февраль 2025',
    3: 'Март 2025',
    4: 'Апрель 2025',
    5: 'Май 2025',
    6: 'Июнь 2025',
    7: 'Июль 2025',
    8: 'Август 2025',
    9: 'Сентябрь 2025',
    10: 'Октябрь 2025',
    11: 'Ноябрь 2025',
    12: 'Декабрь 2025'
}

async def import_ufic():
    # Читаем Excel файл
    df = pd.read_excel('/tmp/ufic.xlsx', header=None)
    
    print(f"Загружено {len(df)} строк")
    
    # Подключаемся к базе данных
    db_url = os.environ.get('DATABASE_URL')
    conn = await asyncpg.connect(db_url)
    
    try:
        imported = 0
        
        # Обрабатываем строки со 2 по 10 (индексы 2-10, месяцы с января по сентябрь)
        for index in range(2, 11):
            row = df.iloc[index]
            
            date = row[1]  # Дата
            fot = row[2]   # ФОТ (Зарплата)
            taxes = row[3] # Налоги
            
            if pd.isna(date) or pd.isna(fot):
                continue
            
            # Получаем месяц
            month_num = date.month
            month_ru = MONTH_MAP.get(month_num)
            
            if not month_ru:
                continue
            
            # Преобразуем в float
            fot_amount = float(fot) if not pd.isna(fot) else 0
            taxes_amount = float(taxes) if not pd.isna(taxes) else 0
            
            # Преобразуем дату в Python datetime
            python_date = date.to_pydatetime()
            
            # Создаем транзакцию для ФОТ (Зарплата)
            if fot_amount > 0:
                transaction_id = str(uuid4())
                query = """
                    INSERT INTO financial_transactions 
                    (id, date, amount, category, type, description, project, company, created_at, updated_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """
                await conn.execute(
                    query,
                    transaction_id,
                    python_date,
                    fot_amount,
                    'Зарплата',
                    'expense',
                    f'ФОТ УФИЦ - {month_ru}',
                    month_ru,
                    'УФИЦ'
                )
                imported += 1
                print(f"✅ {month_ru}: ФОТ {fot_amount:,.2f} ₽")
            
            # Создаем транзакцию для Налогов
            if taxes_amount > 0:
                transaction_id = str(uuid4())
                await conn.execute(
                    query,
                    transaction_id,
                    python_date,
                    taxes_amount,
                    'Налоги',
                    'expense',
                    f'Налоги УФИЦ - {month_ru}',
                    month_ru,
                    'УФИЦ'
                )
                imported += 1
                print(f"✅ {month_ru}: Налоги {taxes_amount:,.2f} ₽")
        
        print(f"\n=== ИТОГО ===")
        print(f"✅ Импортировано транзакций: {imported}")
        
    finally:
        await conn.close()

if __name__ == '__main__':
    asyncio.run(import_ufic())
