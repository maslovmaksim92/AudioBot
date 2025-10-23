#!/usr/bin/env python3
"""
Импорт расходов из Excel файла в базу данных PostgreSQL
"""
import pandas as pd
import asyncpg
import os
import asyncio
from datetime import datetime
from uuid import uuid4

# Маппинг английских месяцев на русские
MONTH_MAP = {
    'January': 'Январь 2025',
    'February': 'Февраль 2025',
    'March': 'Март 2025',
    'April': 'Апрель 2025',
    'May': 'Май 2025',
    'June': 'Июнь 2025',
    'July': 'Июль 2025',
    'August': 'Август 2025',
    'September': 'Сентябрь 2025'
}

async def import_expenses():
    # Читаем Excel файл
    df = pd.read_excel('/tmp/expenses.xlsx')
    
    print(f"Загружено {len(df)} строк")
    print(f"Колонки: {df.columns.tolist()}")
    print("\nПервые 5 строк:")
    print(df.head())
    
    # Подключаемся к базе данных
    db_url = os.environ.get('DATABASE_URL')
    conn = await asyncpg.connect(db_url)
    
    try:
        imported = 0
        skipped = 0
        
        for index, row in df.iterrows():
            try:
                month_eng = str(row.iloc[0]).strip()  # Первая колонка - месяц
                category = str(row.iloc[1]).strip()   # Вторая колонка - категория
                amount = float(row.iloc[2])            # Третья колонка - сумма
                
                # Пропускаем пустые строки или итоговые
                if pd.isna(amount) or amount == 0 or month_eng == 'nan':
                    skipped += 1
                    continue
                
                # Конвертируем месяц
                month_ru = MONTH_MAP.get(month_eng)
                if not month_ru:
                    print(f"⚠️  Неизвестный месяц: {month_eng}, пропуск")
                    skipped += 1
                    continue
                
                # Создаем транзакцию
                transaction_id = str(uuid4())
                
                # Генерируем дату внутри месяца (15-е число)
                month_num = list(MONTH_MAP.keys()).index(month_eng) + 1
                transaction_date = datetime(2025, month_num, 15)
                
                # Вставляем в БД
                query = """
                    INSERT INTO financial_transactions 
                    (id, date, amount, category, type, description, project, created_at, updated_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """
                
                await conn.execute(
                    query,
                    transaction_id,
                    transaction_date,
                    amount,
                    category,
                    'expense',
                    f'Импорт из Excel - {category}',
                    month_ru
                )
                
                imported += 1
                
                if imported % 50 == 0:
                    print(f"✅ Импортировано {imported} транзакций...")
                    
            except Exception as e:
                print(f"❌ Ошибка в строке {index}: {e}")
                skipped += 1
                continue
        
        print(f"\n=== ИТОГО ===")
        print(f"✅ Импортировано: {imported}")
        print(f"⏭️  Пропущено: {skipped}")
        
    finally:
        await conn.close()

if __name__ == '__main__':
    asyncio.run(import_expenses())
