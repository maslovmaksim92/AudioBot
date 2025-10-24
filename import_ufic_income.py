#!/usr/bin/env python3
"""
Импорт доходов УФИЦ из Excel файла
"""
import pandas as pd
import asyncpg
import os
import asyncio
from datetime import datetime
from uuid import uuid4

# Маппинг месяцев
MONTH_MAP = {
    'Январь': ('Январь 2025', 1),
    'Февраль': ('Февраль 2025', 2),
    'Март': ('Март 2025', 3),
    'Апрель': ('Апрель 2025', 4),
    'Май': ('Май 2025', 5),
    'Июнь': ('Июнь 2025', 6),
    'Июль': ('Июль 2025', 7),
    'Август': ('Август 2025', 8),
    'Сентябрь': ('Сентябрь 2025', 9),
    'Октябрь': ('Октябрь 2025', 10)
}

async def import_income():
    # Читаем Excel файл
    df = pd.read_excel('/tmp/income_ufic.xlsx', header=None)
    
    print(f"Загружено {len(df)} строк")
    
    # Подключаемся к базе данных
    db_url = os.environ.get('DATABASE_URL')
    conn = await asyncpg.connect(db_url)
    
    try:
        imported = 0
        
        # Обрабатываем строки с 5 по 14 (месяцы)
        for index in range(5, 14):
            row = df.iloc[index]
            
            month_name = str(row[2]).strip()  # Название месяца в колонке 2
            
            if month_name not in MONTH_MAP:
                continue
            
            month_ru, month_num = MONTH_MAP[month_name]
            
            # Создаем дату (15-е число месяца)
            date = datetime(2025, month_num, 15)
            
            # Колонка 4: Уборщицы - Ставки
            cleaning_amount = row[4]
            if pd.notna(cleaning_amount):
                try:
                    amount = float(cleaning_amount)
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
                            'Уборщицы',
                            'income',
                            f'Доход Уборщицы УФИЦ - {month_ru}',
                            month_ru,
                            'УФИЦ'
                        )
                        imported += 1
                        print(f"✅ {month_ru}: Уборщицы {amount:,.2f} ₽")
                except (ValueError, TypeError):
                    pass
            
            # Колонка 9: Другая категория доходов (если есть)
            other_amount = row[9]
            if pd.notna(other_amount):
                try:
                    amount = float(other_amount)
                    if amount > 0:
                        transaction_id = str(uuid4())
                        await conn.execute(
                            query,
                            transaction_id,
                            date,
                            amount,
                            'Другие доходы',
                            'income',
                            f'Другие доходы УФИЦ - {month_ru}',
                            month_ru,
                            'УФИЦ'
                        )
                        imported += 1
                        print(f"✅ {month_ru}: Другие доходы {amount:,.2f} ₽")
                except (ValueError, TypeError):
                    pass
            
            # Колонка 13: Аутсорсинг - Ставки
            outsource_amount = row[13]
            if pd.notna(outsource_amount):
                try:
                    amount = float(outsource_amount)
                    if amount > 0:
                        transaction_id = str(uuid4())
                        await conn.execute(
                            query,
                            transaction_id,
                            date,
                            amount,
                            'Аутсорсинг',
                            'income',
                            f'Доход Аутсорсинг УФИЦ - {month_ru}',
                            month_ru,
                            'УФИЦ'
                        )
                        imported += 1
                        print(f"✅ {month_ru}: Аутсорсинг {amount:,.2f} ₽")
                except (ValueError, TypeError):
                    pass
        
        print(f"\n=== ИТОГО ===")
        print(f"✅ Импортировано доходов: {imported}")
        
    finally:
        await conn.close()

if __name__ == '__main__':
    asyncio.run(import_income())
