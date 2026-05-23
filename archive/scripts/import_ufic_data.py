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
        
        # Определяем категории и их колонки
        categories = {
            2: 'Зарплата',
            3: 'Налоги',
            4: 'НДФЛ',
            6: 'Прикамский институт',
            7: 'ВДПО КО',
            8: 'КРЭО',
            9: 'Водоканал',
            10: 'ГАЗПРОМ',
            11: 'Первый газовый'
        }
        
        # Обрабатываем строки со 2 по 10 (индексы 2-10, месяцы с января по сентябрь)
        for index in range(2, 11):
            row = df.iloc[index]
            
            date = row[1]  # Дата
            
            if pd.isna(date):
                continue
            
            # Получаем месяц
            month_num = date.month
            month_ru = MONTH_MAP.get(month_num)
            
            if not month_ru:
                continue
            
            # Преобразуем дату в Python datetime
            python_date = date.to_pydatetime()
            
            query = """
                INSERT INTO financial_transactions 
                (id, date, amount, category, type, description, project, company, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """
            
            # Обрабатываем все категории
            for col_idx, category_name in categories.items():
                value = row[col_idx]
                
                if pd.notna(value):
                    try:
                        amount = float(value)
                        if amount > 0:
                            transaction_id = str(uuid4())
                            await conn.execute(
                                query,
                                transaction_id,
                                python_date,
                                amount,
                                category_name,
                                'expense',
                                f'{category_name} УФИЦ - {month_ru}',
                                month_ru,
                                'УФИЦ'
                            )
                            imported += 1
                            print(f"✅ {month_ru}: {category_name} {amount:,.2f} ₽")
                    except (ValueError, TypeError):
                        continue
        
        print(f"\n=== ИТОГО ===")
        print(f"✅ Импортировано транзакций: {imported}")
        
    finally:
        await conn.close()

if __name__ == '__main__':
    asyncio.run(import_ufic())
