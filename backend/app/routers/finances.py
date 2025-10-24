from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel
import logging
import asyncpg
import os
import io
import csv

logger = logging.getLogger(__name__)
router = APIRouter(tags=["finances"])

# Helper function для получения DB connection
async def get_db_connection():
    """Получить прямое соединение с БД для raw SQL"""
    db_url = os.environ.get('DATABASE_URL', '')
    
    if not db_url:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    # Для asyncpg не нужно преобразовывать URL
    try:
        return await asyncpg.connect(db_url)
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")

# Pydantic модели
class CashFlowItem(BaseModel):
    date: str
    income: float
    expense: float
    balance: float
    
class ProfitLossItem(BaseModel):
    period: str
    revenue: float
    expenses: float
    profit: float
    margin: float

class BalanceSheetItem(BaseModel):
    category: str
    assets: float
    liabilities: float
    equity: float

class ExpenseCategory(BaseModel):
    category: str
    amount: float
    percentage: float

class DebtItem(BaseModel):
    id: str
    creditor: str
    amount: float
    due_date: str
    status: str

class InventoryItem(BaseModel):
    id: str
    name: str
    quantity: int
    cost: float
    value: float

# API Endpoints

@router.get("/finances/cash-flow")
async def get_cash_flow(
    period: Optional[str] = "month"
):
    """
    Получить данные движения денег
    """
    try:
        conn = await get_db_connection()
        try:
            # Получаем данные по дням
            query = """
                SELECT 
                    DATE(date) as transaction_date,
                    SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END) as income,
                    SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END) as expense
                FROM financial_transactions
                GROUP BY DATE(date)
                ORDER BY DATE(date) DESC
                LIMIT 30
            """
            rows = await conn.fetch(query)
            
            cash_flow = []
            running_balance = 0
            
            # Сортируем от старых к новым для правильного расчета баланса
            for row in reversed(rows):
                income = float(row['income'])
                expense = float(row['expense'])
                balance = income - expense
                running_balance += balance
                
                cash_flow.append({
                    "date": row['transaction_date'].strftime("%Y-%m-%d"),
                    "income": income,
                    "expense": expense,
                    "balance": running_balance
                })
            
            # Возвращаем в обратном порядке (от новых к старым)
            cash_flow.reverse()
            
            if not cash_flow:
                # Если данных нет, возвращаем пустой результат
                return {
                    "cash_flow": [],
                    "summary": {
                        "total_income": 0,
                        "total_expense": 0,
                        "net_cash_flow": 0
                    }
                }
            
            return {
                "cash_flow": cash_flow,
                "summary": {
                    "total_income": sum(item["income"] for item in cash_flow),
                    "total_expense": sum(item["expense"] for item in cash_flow),
                    "net_cash_flow": sum(item["income"] for item in cash_flow) - sum(item["expense"] for item in cash_flow)
                }
            }
        finally:
            await conn.close()
    except Exception as e:
        logger.error(f"Error fetching cash flow: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/finances/profit-loss")
async def get_profit_loss(
    period: Optional[str] = "year",
    company: Optional[str] = "ВАШ ДОМ ФАКТ"
):
    """
    Получить отчёт о прибылях и убытках
    Использует ручную выручку из monthly_revenue если она есть
    Параметры:
    - company: Фильтр по компании (по умолчанию "ВАШ ДОМ ФАКТ")
    """
    try:
        conn = await get_db_connection()
        try:
            # Если выбрана консолидация - используем специальную функцию
            if company == "ВАШ ДОМ модель":
                result = await get_consolidated_profit_loss(conn)
                return result
            # Проверяем существует ли таблица monthly_revenue
            table_exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'monthly_revenue'
                )
            """)
            
            # Получаем ручную выручку если таблица существует
            manual_revenue = {}
            if table_exists:
                manual_rows = await conn.fetch("""
                    SELECT month, revenue
                    FROM monthly_revenue
                    WHERE company = $1
                """, company)
                manual_revenue = {row['month']: float(row['revenue']) for row in manual_rows}
            
            # Группируем данные по месяцам из даты
            query = """
                SELECT 
                    TO_CHAR(date, 'Month YYYY') as period,
                    TO_CHAR(date, 'YYYY-MM') as sort_key,
                    SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END) as revenue,
                    SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END) as expenses
                FROM financial_transactions
                WHERE date IS NOT NULL AND EXTRACT(YEAR FROM date) = 2025 AND company = $1
                GROUP BY TO_CHAR(date, 'Month YYYY'), TO_CHAR(date, 'YYYY-MM')
                ORDER BY TO_CHAR(date, 'YYYY-MM')
            """
            rows = await conn.fetch(query, company)
            
            # Маппинг английских названий месяцев на русские
            month_map = {
                'January': 'Январь', 'February': 'Февраль', 'March': 'Март',
                'April': 'Апрель', 'May': 'Май', 'June': 'Июнь',
                'July': 'Июль', 'August': 'Август', 'September': 'Сентябрь',
                'October': 'Октябрь', 'November': 'Ноябрь', 'December': 'Декабрь'
            }
            
            profit_loss = []
            for row in rows:
                period_en = row['period'].strip()
                # Переводим на русский и нормализуем пробелы
                period_ru = period_en
                for eng, rus in month_map.items():
                    if eng in period_en:
                        period_ru = period_en.replace(eng, rus)
                        break
                # Убираем лишние пробелы между месяцем и годом
                period_ru = ' '.join(period_ru.split())
                
                # Используем ручную выручку если она есть, иначе из транзакций
                revenue = manual_revenue.get(period_ru, float(row['revenue']))
                expenses = float(row['expenses'])
                profit = revenue - expenses
                margin = (profit / revenue * 100) if revenue > 0 else 0
                
                profit_loss.append({
                    "period": period_ru,
                    "revenue": revenue,
                    "expenses": expenses,
                    "profit": profit,
                    "margin": round(margin, 2),
                    "manual_revenue": period_ru in manual_revenue
                })
            
            if not profit_loss:
                # Если данных нет, возвращаем пустой результат
                return {
                    "profit_loss": [],
                    "summary": {
                        "total_revenue": 0,
                        "total_expenses": 0,
                        "net_profit": 0,
                        "average_margin": 0
                    }
                }
            
            return {
                "profit_loss": profit_loss,
                "summary": {
                    "total_revenue": sum(item["revenue"] for item in profit_loss),
                    "total_expenses": sum(item["expenses"] for item in profit_loss),
                    "net_profit": sum(item["profit"] for item in profit_loss),
                    "average_margin": round(sum(item["margin"] for item in profit_loss) / len(profit_loss), 2) if profit_loss else 0
                }
            }
        finally:
            await conn.close()
    except Exception as e:
        logger.error(f"Error fetching profit/loss: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/finances/balance-sheet")
async def get_balance_sheet():
    """
    Получить балансовый отчёт
    """
    try:
        # Mock данные
        balance = {
            "assets": {
                "current": {
                    "cash": 2500000,
                    "accounts_receivable": 1800000,
                    "inventory": 3200000,
                    "total": 7500000
                },
                "non_current": {
                    "property": 15000000,
                    "equipment": 8500000,
                    "vehicles": 5000000,
                    "total": 28500000
                },
                "total": 36000000
            },
            "liabilities": {
                "current": {
                    "accounts_payable": 1200000,
                    "short_term_debt": 800000,
                    "total": 2000000
                },
                "non_current": {
                    "long_term_debt": 10000000,
                    "total": 10000000
                },
                "total": 12000000
            },
            "equity": {
                "capital": 15000000,
                "retained_earnings": 9000000,
                "total": 24000000
            }
        }
        
        return balance
    except Exception as e:
        logger.error(f"Error fetching balance sheet: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/finances/expense-analysis")
async def get_expense_analysis(month: Optional[str] = None, company: Optional[str] = "ООО ВАШ ДОМ"):
    """
    Анализ расходов по категориям
    Параметры:
    - month: Опциональный фильтр по месяцу (например, "Январь 2025")
    - company: Фильтр по компании (по умолчанию "ООО ВАШ ДОМ")
    """
    try:
        conn = await get_db_connection()
        try:
            # Консолидированный расчет
            if company == "ООО ВАШ ДОМ + УФИЦ":
                return await get_consolidated_expenses(conn, month)
            
            # Получаем реальные данные из БД
            if month:
                query = """
                    SELECT category, SUM(amount) as total_amount
                    FROM financial_transactions
                    WHERE type = 'expense' AND project = $1 AND company = $2
                    GROUP BY category
                    ORDER BY total_amount DESC
                """
                rows = await conn.fetch(query, month, company)
            else:
                query = """
                    SELECT category, SUM(amount) as total_amount
                    FROM financial_transactions
                    WHERE type = 'expense' AND company = $1
                    GROUP BY category
                    ORDER BY total_amount DESC
                """
                rows = await conn.fetch(query, company)
            
            if not rows:
                # Если данных нет, возвращаем пустой результат
                return {
                    "expenses": [],
                    "total": 0,
                    "month": month
                }
            
            # Вычисляем общую сумму
            total = sum(float(row['total_amount']) for row in rows)
            
            # Формируем результат с процентами
            expenses = []
            for row in rows:
                amount = float(row['total_amount'])
                percentage = (amount / total * 100) if total > 0 else 0
                expenses.append({
                    "category": row['category'],
                    "amount": amount,
                    "percentage": round(percentage, 2)
                })
            
            return {
                "expenses": expenses,
                "total": total,
                "month": month
            }
        finally:
            await conn.close()
    except Exception as e:
        logger.error(f"Error fetching expense analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/finances/available-months")
async def get_available_months():
    """
    Получить список доступных месяцев с данными
    """
    try:
        conn = await get_db_connection()
        try:
            query = """
                SELECT DISTINCT project as month,
                       MIN(date) as start_date
                FROM financial_transactions
                WHERE project IS NOT NULL
                GROUP BY project
                ORDER BY start_date DESC
            """
            rows = await conn.fetch(query)
            
            months = [row['month'] for row in rows if row['month']]
            
            return {
                "months": months,
                "total": len(months)
            }
        finally:
            await conn.close()
    except Exception as e:
        logger.error(f"Error fetching available months: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/finances/debts")
async def get_debts():
    """
    Получить список задолженностей из базы данных
    """
    try:
        conn = await get_db_connection()
        try:
            # Проверяем существует ли таблица debts
            table_exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'debts'
                )
            """)
            
            if not table_exists:
                # Возвращаем пустой результат если таблицы нет
                return {
                    "debts": [],
                    "summary": {
                        "total": 0,
                        "overdue": 0,
                        "active": 0,
                        "count": 0
                    }
                }
            
            # Получаем все долги
            rows = await conn.fetch("""
                SELECT 
                    id, creditor, amount, due_date, status, type, description
                FROM debts
                ORDER BY due_date
            """)
            
            debts = []
            total_debt = 0
            overdue_debt = 0
            
            for row in rows:
                amount = float(row['amount'])
                total_debt += amount
                
                if row['status'] == 'overdue':
                    overdue_debt += amount
                
                debts.append({
                    "id": str(row['id']),
                    "creditor": row['creditor'],
                    "amount": amount,
                    "due_date": row['due_date'].strftime('%Y-%m-%d') if row['due_date'] else None,
                    "status": row['status'],
                    "type": row['type'],
                    "description": row['description']
                })
            
            return {
                "debts": debts,
                "summary": {
                    "total": total_debt,
                    "overdue": overdue_debt,
                    "active": total_debt - overdue_debt,
                    "count": len(debts)
                }
            }
        finally:
            await conn.close()
    except Exception as e:
        logger.error(f"Error fetching debts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/finances/inventory")
async def get_inventory():
    """
    Получить товарные запасы
    """
    try:
        # Mock данные
        inventory = [
            {
                "id": "inv-1",
                "name": "Моющие средства",
                "category": "Химия",
                "quantity": 500,
                "unit": "шт",
                "cost": 250,
                "value": 125000,
                "location": "Склад А"
            },
            {
                "id": "inv-2",
                "name": "Перчатки резиновые",
                "category": "Расходники",
                "quantity": 1000,
                "unit": "пар",
                "cost": 50,
                "value": 50000,
                "location": "Склад А"
            },
            {
                "id": "inv-3",
                "name": "Швабры",
                "category": "Инвентарь",
                "quantity": 150,
                "unit": "шт",
                "cost": 800,
                "value": 120000,
                "location": "Склад Б"
            },
            {
                "id": "inv-4",
                "name": "Ведра",
                "category": "Инвентарь",
                "quantity": 200,
                "unit": "шт",
                "cost": 300,
                "value": 60000,
                "location": "Склад Б"
            }
        ]
        
        total_value = sum(item["value"] for item in inventory)
        total_items = sum(item["quantity"] for item in inventory)
        
        return {
            "inventory": inventory,
            "summary": {
                "total_value": total_value,
                "total_items": total_items,
                "categories": len(set(item["category"] for item in inventory))
            }
        }
    except Exception as e:
        logger.error(f"Error fetching inventory: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/finances/dashboard")
async def get_finances_dashboard():
    """
    Получить сводку по всем финансовым показателям
    """
    try:
        # Комбинируем данные из всех эндпоинтов
        cash_flow = await get_cash_flow()
        profit_loss = await get_profit_loss()
        balance = await get_balance_sheet()
        expenses = await get_expense_analysis()
        debts = await get_debts()
        inventory = await get_inventory()
        
        return {
            "cash_flow": cash_flow["summary"],
            "profit_loss": profit_loss["summary"],
            "balance": {
                "total_assets": balance["assets"]["total"],
                "total_liabilities": balance["liabilities"]["total"],
                "total_equity": balance["equity"]["total"]
            },
            "expenses": expenses["total"],
            "debts": debts["summary"],
            "inventory": inventory["summary"]
        }
    except Exception as e:
        logger.error(f"Error getting dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/finances/export-expenses")
async def export_expenses(year: int = 2025):
    """
    Экспорт расходов в CSV формат помесячно
    """
    try:
        conn = await get_db_connection()
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
            
            # Создаем CSV в памяти
            output = io.StringIO()
            writer = csv.writer(output)
            
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
            
            # Возвращаем CSV файл
            output.seek(0)
            
            return StreamingResponse(
                io.BytesIO(output.getvalue().encode('utf-8-sig')),  # utf-8-sig для правильного отображения в Excel
                media_type='text/csv',
                headers={
                    'Content-Disposition': f'attachment; filename=expenses_{year}.csv'
                }
            )
            
        finally:
            await conn.close()
    except Exception as e:
        logger.error(f"Error exporting expenses: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/finances/expense-details")
async def get_expense_details(month: str, company: Optional[str] = "ООО ВАШ ДОМ"):
    """
    Получить детальные транзакции расходов для конкретного месяца
    Параметры:
    - month: Название месяца (например, "Июль 2025")
    - company: Фильтр по компании (по умолчанию "ООО ВАШ ДОМ")
    """
    try:
        conn = await get_db_connection()
        try:
            # Получаем все транзакции расходов для указанного месяца
            query = """
                SELECT 
                    id,
                    date,
                    amount,
                    category,
                    description,
                    payment_method,
                    counterparty
                FROM financial_transactions
                WHERE type = 'expense' AND project = $1 AND company = $2
                ORDER BY date DESC, category
            """
            rows = await conn.fetch(query, month, company)
            
            if not rows:
                return {
                    "transactions": [],
                    "total": 0,
                    "month": month,
                    "count": 0
                }
            
            # Формируем список транзакций
            transactions = []
            total = 0
            
            for row in rows:
                amount = float(row['amount'])
                total += amount
                
                transactions.append({
                    "id": row['id'],
                    "date": row['date'].strftime('%d.%m.%Y') if row['date'] else "",
                    "category": row['category'],
                    "amount": amount,
                    "description": row['description'] or "",
                    "payment_method": row['payment_method'] or "",
                    "counterparty": row['counterparty'] or ""
                })
            
            return {
                "transactions": transactions,
                "total": total,
                "month": month,
                "count": len(transactions)
            }
            
        finally:
            await conn.close()
    except Exception as e:
        logger.error(f"Error fetching expense details: {e}")


@router.get("/finances/revenue-analysis")
async def get_revenue_analysis(month: Optional[str] = None, company: Optional[str] = "ООО ВАШ ДОМ"):
    """
    Анализ выручки по категориям
    Параметры:
    - month: Опциональный фильтр по месяцу (например, "Январь 2025")
    - company: Фильтр по компании (по умолчанию "ООО ВАШ ДОМ")
    """
    try:
        conn = await get_db_connection()
        try:
            # Консолидированный расчет - выручка ООО ВАШ ДОМ минус "Швеи" и "Аутсорсинг"
            if company == "ООО ВАШ ДОМ + УФИЦ":
                return await get_consolidated_revenue(conn, month)
            
            # Получаем реальные данные из БД
            if month:
                query = """
                    SELECT category, SUM(amount) as total_amount
                    FROM financial_transactions
                    WHERE type = 'income' AND project = $1 AND company = $2
                    GROUP BY category
                    ORDER BY total_amount DESC
                """
                rows = await conn.fetch(query, month, company)
            else:
                query = """
                    SELECT category, SUM(amount) as total_amount
                    FROM financial_transactions
                    WHERE type = 'income' AND company = $1
                    GROUP BY category
                    ORDER BY total_amount DESC
                """
                rows = await conn.fetch(query, company)
            
            if not rows:
                # Если данных нет, возвращаем пустой результат
                return {
                    "revenue": [],
                    "total": 0,
                    "month": month
                }
            
            # Вычисляем общую сумму
            total = sum(float(row['total_amount']) for row in rows)
            
            # Формируем результат с процентами
            revenue = []
            for row in rows:
                amount = float(row['total_amount'])
                percentage = (amount / total * 100) if total > 0 else 0
                revenue.append({
                    "category": row['category'],
                    "amount": amount,
                    "percentage": round(percentage, 2)
                })
            
            return {
                "revenue": revenue,
                "total": total,
                "month": month
            }
        finally:
            await conn.close()
    except Exception as e:
        logger.error(f"Error fetching revenue analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))



@router.get("/finances/revenue-details")
async def get_revenue_details(month: Optional[str] = None, company: Optional[str] = "ООО ВАШ ДОМ"):
    """
    Получить детальные транзакции доходов
    Параметры:
    - month: Опциональный фильтр по месяцу (например, "Январь 2025")
    - company: Фильтр по компании (по умолчанию "ООО ВАШ ДОМ")
    """
    try:
        conn = await get_db_connection()
        try:
            # Получаем все транзакции доходов
            if month:
                query = """
                    SELECT 
                        id, date, amount, category, description, counterparty
                    FROM financial_transactions
                    WHERE type = 'income' AND project = $1 AND company = $2
                    ORDER BY date DESC
                """
                rows = await conn.fetch(query, month, company)
            else:
                query = """
                    SELECT 
                        id, date, amount, category, description, counterparty
                    FROM financial_transactions
                    WHERE type = 'income' AND company = $1
                    ORDER BY date DESC
                """
                rows = await conn.fetch(query, company)
            
            if not rows:
                return {
                    "transactions": [],
                    "total": 0,
                    "month": month,
                    "count": 0
                }
            
            # Формируем список транзакций
            transactions = []
            total = 0
            
            for row in rows:
                amount = float(row['amount'])
                total += amount
                
                transactions.append({
                    "id": str(row['id']),
                    "date": row['date'].strftime('%d.%m.%Y') if row['date'] else "",
                    "counterparty": row['counterparty'] or "—",
                    "amount": amount,
                    "description": row['description'] or "",
                    "category": row['category']
                })
            
            return {
                "transactions": transactions,
                "total": total,
                "month": month,
                "count": len(transactions)
            }
            
        finally:
            await conn.close()
    except Exception as e:
        logger.error(f"Error fetching revenue details: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def get_consolidated_revenue(conn, month: Optional[str] = None):
    """
    Консолидированная выручка: ООО ВАШ ДОМ минус "Швеи" и "Аутсорсинг"
    """
    # Получаем выручку ООО ВАШ ДОМ
    if month:
        query = """
            SELECT category, SUM(amount) as total_amount
            FROM financial_transactions
            WHERE type = 'income' AND project = $1 AND company = 'ООО ВАШ ДОМ'
            GROUP BY category
        """
        rows = await conn.fetch(query, month)
    else:
        query = """
            SELECT category, SUM(amount) as total_amount
            FROM financial_transactions
            WHERE type = 'income' AND company = 'ООО ВАШ ДОМ'
            GROUP BY category
        """
        rows = await conn.fetch(query)
    
    # Вычисляем консолидированную выручку (исключаем Швеи и Аутсорсинг)
    revenue = []
    total = 0
    
    for row in rows:
        category = row['category']
        amount = float(row['total_amount'])
        
        # Пропускаем Швеи и Аутсорсинг
        if category in ['Швеи', 'Аутсорсинг']:
            continue
        
        total += amount
        revenue.append({
            "category": category,
            "amount": amount
        })
    
    # Сортируем по убыванию
    revenue.sort(key=lambda x: x['amount'], reverse=True)
    
    # Добавляем проценты
    for item in revenue:
        item['percentage'] = round((item['amount'] / total * 100), 2) if total > 0 else 0
    
    return {
        "revenue": revenue,
        "total": total,
        "month": month
    }


async def get_consolidated_profit_loss(conn):
    """
    Консолидированный расчет: ООО ВАШ ДОМ + УФИЦ
    Выручка: ООО ВАШ ДОМ минус "Швеи" и "Аутсорсинг"
    Расходы: ООО ВАШ ДОМ + УФИЦ минус "Кредиты", "Аутсорсинг персонала с Ю/ЦЛ", "Швеи"
    """
    # Получаем выручку ООО ВАШ ДОМ по месяцам и категориям
    revenue_rows = await conn.fetch("""
        SELECT 
            project as month,
            category,
            SUM(amount) as amount
        FROM financial_transactions
        WHERE type = 'income' AND company = 'ООО ВАШ ДОМ'
        GROUP BY project, category
    """)
    
    # Группируем выручку по месяцам, исключая Швеи и Аутсорсинг
    revenue_by_month = {}
    for row in revenue_rows:
        month = row['month']
        category = row['category']
        amount = float(row['amount'])
        
        # Пропускаем Швеи и Аутсорсинг
        if category in ['Швеи', 'Аутсорсинг']:
            continue
        
        if month not in revenue_by_month:
            revenue_by_month[month] = 0
        revenue_by_month[month] += amount
    
    # Получаем расходы ВАШ ДОМ по месяцам и категориям
    vasdom_expenses = await conn.fetch("""
        SELECT 
            project as month,
            category,
            SUM(amount) as amount
        FROM financial_transactions
        WHERE type = 'expense' AND company = 'ООО ВАШ ДОМ'
        GROUP BY project, category
    """)
    
    # Получаем расходы УФИЦ по месяцам и категориям
    ufic_expenses = await conn.fetch("""
        SELECT 
            project as month,
            category,
            SUM(amount) as amount
        FROM financial_transactions
        WHERE type = 'expense' AND company = 'УФИЦ'
        GROUP BY project, category
    """)
    
    # Группируем расходы по месяцам
    expenses_by_month = {}
    
    # Добавляем расходы ВАШ ДОМ (исключая категории)
    for row in vasdom_expenses:
        month = row['month']
        category = row['category']
        amount = float(row['amount'])
        
        # Пропускаем исключаемые категории
        if category in ['Кредиты', 'Аутсорсинг персонала с Ю/ЦЛ', 'Швеи']:
            continue
        
        if month not in expenses_by_month:
            expenses_by_month[month] = 0
        expenses_by_month[month] += amount
    
    # Добавляем расходы УФИЦ (исключая категории)
    for row in ufic_expenses:
        month = row['month']
        category = row['category']
        amount = float(row['amount'])
        
        # Пропускаем исключаемые категории
        if category in ['Кредиты', 'Аутсорсинг персонала с Ю/ЦЛ', 'Швеи']:
            continue
        
        if month not in expenses_by_month:
            expenses_by_month[month] = 0
        expenses_by_month[month] += amount
    
    # Получаем все уникальные месяцы
    all_months = sorted(set(list(revenue_by_month.keys()) + list(expenses_by_month.keys())))
    
    # Вычисляем консолидированные данные
    profit_loss = []
    total_revenue = 0
    total_expenses = 0
    
    for month in all_months:
        revenue = revenue_by_month.get(month, 0)
        expenses = expenses_by_month.get(month, 0)
        profit = revenue - expenses
        margin = (profit / revenue * 100) if revenue > 0 else 0
        
        profit_loss.append({
            "period": month,
            "revenue": revenue,
            "expenses": expenses,
            "profit": profit,
            "margin": round(margin, 2)
        })
        
        total_revenue += revenue
        total_expenses += expenses
    
    total_profit = total_revenue - total_expenses
    total_margin = (total_profit / total_revenue * 100) if total_revenue > 0 else 0
    
    return {
        "profit_loss": profit_loss,
        "summary": {
            "total_revenue": total_revenue,
            "total_expenses": total_expenses,
            "total_profit": total_profit,
            "margin": round(total_margin, 2)
        }
    }


async def get_consolidated_expenses(conn, month: Optional[str] = None):
    """
    Консолидированные расходы: ВАШ ДОМ + УФИЦ
    Исключаем: "Кредиты", "Аутсорсинг персонала с Ю/ЦЛ", "Швеи"
    """
    # Получаем расходы ВАШ ДОМ
    if month:
        vasdom_query = """
            SELECT category, SUM(amount) as total_amount
            FROM financial_transactions
            WHERE type = 'expense' AND project = $1 AND company = 'ООО ВАШ ДОМ'
            GROUP BY category
        """
        vasdom_rows = await conn.fetch(vasdom_query, month)
        
        ufic_query = """
            SELECT category, SUM(amount) as total_amount
            FROM financial_transactions
            WHERE type = 'expense' AND project = $1 AND company = 'УФИЦ'
            GROUP BY category
        """
        ufic_rows = await conn.fetch(ufic_query, month)
    else:
        vasdom_query = """
            SELECT category, SUM(amount) as total_amount
            FROM financial_transactions
            WHERE type = 'expense' AND company = 'ООО ВАШ ДОМ'
            GROUP BY category
        """
        vasdom_rows = await conn.fetch(vasdom_query)
        
        ufic_query = """
            SELECT category, SUM(amount) as total_amount
            FROM financial_transactions
            WHERE type = 'expense' AND company = 'УФИЦ'
            GROUP BY category
        """
        ufic_rows = await conn.fetch(ufic_query)
    
    # Группируем по категориям (ВАШ ДОМ + УФИЦ)
    expenses_dict = {}
    
    # Добавляем расходы ВАШ ДОМ
    for row in vasdom_rows:
        category = row['category']
        amount = float(row['total_amount'])
        
        # Пропускаем исключаемые категории
        if category in ['Кредиты', 'Аутсорсинг персонала с Ю/ЦЛ', 'Швеи']:
            continue
        
        if category not in expenses_dict:
            expenses_dict[category] = 0
        expenses_dict[category] += amount
    
    # Добавляем расходы УФИЦ
    for row in ufic_rows:
        category = row['category']
        amount = float(row['total_amount'])
        
        # Пропускаем исключаемые категории
        if category in ['Кредиты', 'Аутсорсинг персонала с Ю/ЦЛ', 'Швеи']:
            continue
        
        if category not in expenses_dict:
            expenses_dict[category] = 0
        expenses_dict[category] += amount
    
    # Формируем результат
    expenses = []
    total = 0
    
    for category, amount in expenses_dict.items():
        total += amount
        expenses.append({
            "category": category,
            "amount": amount
        })
    
    # Сортируем по убыванию
    expenses.sort(key=lambda x: x['amount'], reverse=True)
    
    # Добавляем проценты
    for expense in expenses:
        expense['percentage'] = round((expense['amount'] / total * 100), 2) if total > 0 else 0
    
    return {
        "expenses": expenses,
        "total": total,
        "month": month
    }

