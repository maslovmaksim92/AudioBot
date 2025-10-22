#!/usr/bin/env python3
"""
Скрипт для экспорта расходов в CSV формат
"""
import asyncpg
import asyncio
import csv

async def export_expenses(year=2025, output_file='expenses_2025.csv'):
    """Экспортировать расходы в CSV"""
    conn = await asyncpg.connect(
        'postgresql://vasdom_user:Vasdom40!@rc1a-gls4njl0umfqv554.mdb.yandexcloud.net:6432/vasdom_audiobot?sslmode=require'
    )
    
    try:
        # Получаем расходы по месяцам с детализацией по категориям
        query = """
            SELECT 
                TO_CHAR(date, 'YYYY-MM') as month,
                TO_CHAR(date, 'Month YYYY') as month_name,
                category,
                SUM(amount) as total_amount,
                COUNT(*) as transactions_count
            FROM financial_transactions
            WHERE type = 'expense' AND EXTRACT(YEAR FROM date) = $1
            GROUP BY TO_CHAR(date, 'YYYY-MM'), TO_CHAR(date, 'Month YYYY'), category
            ORDER BY month, category
        """
        rows = await conn.fetch(query, year)
        
        # Записываем в CSV
        with open(output_file, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f)
            
            # Заголовки
            writer.writerow(['Месяц', 'Категория', 'Сумма расходов (₽)', 'Количество транзакций'])
            
            # Данные
            for row in rows:
                writer.writerow([
                    row['month_name'].strip(),
                    row['category'],
                    float(row['total_amount']),
                    row['transactions_count']
                ])
            
            # Добавляем итоги по месяцам
            writer.writerow([])
            writer.writerow(['ИТОГО ПО МЕСЯЦАМ:'])
            writer.writerow(['Месяц', 'Всего расходов (₽)'])
            
            monthly_query = """
                SELECT 
                    TO_CHAR(date, 'Month YYYY') as month_name,
                    SUM(amount) as total_amount
                FROM financial_transactions
                WHERE type = 'expense' AND EXTRACT(YEAR FROM date) = $1
                GROUP BY TO_CHAR(date, 'YYYY-MM'), TO_CHAR(date, 'Month YYYY')
                ORDER BY TO_CHAR(date, 'YYYY-MM')
            """
            monthly_rows = await conn.fetch(monthly_query, year)
            
            for row in monthly_rows:
                writer.writerow([
                    row['month_name'].strip(),
                    float(row['total_amount'])
                ])
        
        print(f"✅ Расходы экспортированы в файл: {output_file}")
        print(f"   Всего записей: {len(rows)}")
        print(f"   Месяцев: {len(monthly_rows)}")
        
    finally:
        await conn.close()

if __name__ == '__main__':
    asyncio.run(export_expenses())
