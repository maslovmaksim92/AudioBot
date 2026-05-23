#!/usr/bin/env python3
"""Скрипт для получения расходов УФИЦ за 2025 год"""

import asyncio
import asyncpg
import os

async def get_ufic_expenses():
    db_url = os.environ.get('DATABASE_URL', '')
    conn = await asyncpg.connect(db_url)
    
    try:
        # Получаем расходы УФИЦ за 2025
        expenses_query = """
            SELECT SUM(amount) as total_expenses
            FROM financial_transactions
            WHERE type = 'expense' AND company = 'УФИЦ модель'
        """
        expenses_result = await conn.fetchrow(expenses_query)
        total_expenses = float(expenses_result['total_expenses']) if expenses_result['total_expenses'] else 0
        
        print(f"УФИЦ факт 2025 - Расходы: {total_expenses:,.2f} ₽")
        return total_expenses
        
    finally:
        await conn.close()

if __name__ == "__main__":
    expenses = asyncio.run(get_ufic_expenses())
