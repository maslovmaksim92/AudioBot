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
async def get_expense_analysis(month: Optional[str] = None, company: Optional[str] = "ВАШ ДОМ ФАКТ"):
    """
    Анализ расходов по категориям
    Параметры:
    - month: Опциональный фильтр по месяцу (например, "Январь 2025")
    - company: Фильтр по компании (по умолчанию "ВАШ ДОМ ФАКТ")
    """
    try:
        conn = await get_db_connection()
        try:
            # Консолидированный расчет
            if company == "ВАШ ДОМ модель":
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
async def get_revenue_analysis(month: Optional[str] = None, company: Optional[str] = "ВАШ ДОМ ФАКТ"):
    """
    Анализ выручки по категориям
    Параметры:
    - month: Опциональный фильтр по месяцу (например, "Январь 2025")
    - company: Фильтр по компании (по умолчанию "ВАШ ДОМ ФАКТ")
    """
    try:
        conn = await get_db_connection()
        try:
            # Консолидированный расчет - выручка ООО ВАШ ДОМ минус "Швеи" и "Аутсорсинг"
            if company == "ВАШ ДОМ модель":
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
async def get_revenue_details(month: Optional[str] = None, company: Optional[str] = "ВАШ ДОМ ФАКТ"):
    """
    Получить детальные транзакции доходов
    Параметры:
    - month: Опциональный фильтр по месяцу (например, "Январь 2025")
    - company: Фильтр по компании (по умолчанию "ВАШ ДОМ ФАКТ")
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
    Консолидированная выручка для "ВАШ ДОМ модель"
    Используется ручная выручка из monthly_revenue
    """
    # Для консолидированной модели используем ручную выручку из monthly_revenue
    if month:
        query = """
            SELECT month, revenue
            FROM monthly_revenue
            WHERE company = 'ВАШ ДОМ модель' AND month = $1
        """
        rows = await conn.fetch(query, month)
    else:
        query = """
            SELECT month, revenue
            FROM monthly_revenue
            WHERE company = 'ВАШ ДОМ модель'
            ORDER BY month
        """
        rows = await conn.fetch(query)
    
    if not rows:
        return {
            "revenue": [],
            "total": 0,
            "month": month
        }
    
    # Вычисляем общую сумму
    total = sum(float(row['revenue']) for row in rows)
    
    # Формируем результат
    revenue = [{
        "category": "Консолидированная выручка",
        "amount": total,
        "percentage": 100.0
    }]
    
    return {
        "revenue": revenue,
        "total": total,
        "month": month
    }


async def get_consolidated_profit_loss(conn):
    """
    Консолидированный расчет для "ВАШ ДОМ модель"
    
    Логика:
    - Выручка: из monthly_revenue для "ВАШ ДОМ модель" (ручная)
    - Расходы:
      * Большинство категорий ("так же"): только ВАШ ДОМ ФАКТ
      * Зарплата: ВАШ ДОМ ФАКТ - УФИЦ модель (ТОЛЬКО Зарплата, без ФОТ) помесячно
      * Налоги: 5% от выручки каждого месяца
      * Аутсорсинг персонала: из транзакций ВАШ ДОМ модель
      * Исключить: Кредиты, Швеи, Юридические услуги, Продукты питания
    """
    # Получаем ручную выручку для консолидированной модели
    revenue_rows = await conn.fetch("""
        SELECT month, revenue
        FROM monthly_revenue
        WHERE company = 'ВАШ ДОМ модель'
        ORDER BY month
    """)
    
    revenue_by_month = {row['month']: float(row['revenue']) for row in revenue_rows}
    
    # Получаем расходы ВАШ ДОМ ФАКТ по месяцам и категориям
    vasdom_expenses = await conn.fetch("""
        SELECT 
            project as month,
            category,
            SUM(amount) as amount
        FROM financial_transactions
        WHERE type = 'expense' AND company = 'ВАШ ДОМ ФАКТ'
        GROUP BY project, category
    """)
    
    # Получаем расходы УФИЦ модель по месяцам - ТОЛЬКО Зарплата (без ФОТ)
    ufic_expenses = await conn.fetch("""
        SELECT 
            project as month,
            category,
            SUM(amount) as amount
        FROM financial_transactions
        WHERE type = 'expense' AND company = 'УФИЦ модель'
          AND category = 'Зарплата'
        GROUP BY project, category
    """)
    
    # Получаем Аутсорсинг персонала из транзакций ВАШ ДОМ модель
    outsourcing_expenses = await conn.fetch("""
        SELECT 
            project as month,
            SUM(amount) as amount
        FROM financial_transactions
        WHERE type = 'expense' AND company = 'ВАШ ДОМ модель'
          AND category = 'Аутсорсинг персонала'
        GROUP BY project
    """)
    
    # Группируем расходы ВАШ ДОМ ФАКТ по месяцам
    vasdom_by_month = {}
    for row in vasdom_expenses:
        month = row['month']
        category = row['category']
        amount = float(row['amount'])
        
        if month not in vasdom_by_month:
            vasdom_by_month[month] = {}
        vasdom_by_month[month][category] = amount
    
    # Группируем расходы УФИЦ по месяцам (только Зарплата)
    ufic_salary_by_month = {}
    for row in ufic_expenses:
        month = row['month']
        amount = float(row['amount'])
        ufic_salary_by_month[month] = amount
    
    # Группируем Аутсорсинг персонала по месяцам
    outsourcing_by_month = {}
    for row in outsourcing_expenses:
        month = row['month']
        amount = float(row['amount'])
        outsourcing_by_month[month] = amount
    
    # Получаем все уникальные месяцы
    all_months_set = set(list(revenue_by_month.keys()) + list(vasdom_by_month.keys()) + list(outsourcing_by_month.keys()))
    
    # Правильная сортировка месяцев
    month_order = {
        'Январь 2025': 1, 'Февраль 2025': 2, 'Март 2025': 3,
        'Апрель 2025': 4, 'Май 2025': 5, 'Июнь 2025': 6,
        'Июль 2025': 7, 'Август 2025': 8, 'Сентябрь 2025': 9,
        'Октябрь 2025': 10, 'Ноябрь 2025': 11, 'Декабрь 2025': 12
    }
    all_months = sorted(all_months_set, key=lambda x: month_order.get(x, 99))
    
    # Вычисляем консолидированные данные
    profit_loss = []
    total_revenue = 0
    total_expenses = 0
    
    for month in all_months:
        revenue = revenue_by_month.get(month, 0)
        
        # Вычисляем расходы
        vasdom_exp = vasdom_by_month.get(month, {})
        
        month_expenses = 0
        
        for category, amount in vasdom_exp.items():
            # Исключаем категории
            if category in ['Кредиты', 'Швеи', 'Аутсорсинг персонала с Ю/ЦЛ', 'Юридические услуги', 'Продукты питания', 'Налоги']:
                continue
            
            # Специальная логика для Зарплаты: ВАШ ДОМ ФАКТ - УФИЦ Зарплата (без ФОТ)
            if category == 'Зарплата':
                ufic_salary = ufic_salary_by_month.get(month, 0)
                consolidated_salary = amount - ufic_salary
                month_expenses += max(0, consolidated_salary)
            else:
                # Для остальных категорий: только ВАШ ДОМ ФАКТ ("так же")
                month_expenses += amount
        
        # Добавляем Аутсорсинг персонала из транзакций ВАШ ДОМ модель
        outsourcing = outsourcing_by_month.get(month, 0)
        month_expenses += outsourcing
        
        # Добавляем Налоги: 5% от выручки
        taxes = revenue * 0.05
        month_expenses += taxes
        
        profit = revenue - month_expenses
        margin = (profit / revenue * 100) if revenue > 0 else 0
        
        profit_loss.append({
            "period": month,
            "revenue": revenue,
            "expenses": month_expenses,
            "profit": profit,
            "margin": round(margin, 2)
        })
        
        total_revenue += revenue
        total_expenses += month_expenses
    
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
    Консолидированные расходы для "ВАШ ДОМ модель"
    
    Логика:
    - Большинство категорий ("так же"): только ВАШ ДОМ ФАКТ
    - Зарплата: ВАШ ДОМ ФАКТ - УФИЦ Зарплата (ТОЛЬКО Зарплата, без ФОТ) помесячно
    - Налоги: 5% от выручки каждого месяца
    - Аутсорсинг персонала: из транзакций ВАШ ДОМ модель
    - Исключить: Кредиты, Швеи, Юридические услуги, Продукты питания
    """
    # Получаем выручку для расчета налогов
    if month:
        revenue_query = """
            SELECT month, revenue
            FROM monthly_revenue
            WHERE company = 'ВАШ ДОМ модель' AND month = $1
        """
        revenue_rows = await conn.fetch(revenue_query, month)
    else:
        revenue_query = """
            SELECT month, revenue
            FROM monthly_revenue
            WHERE company = 'ВАШ ДОМ модель'
        """
        revenue_rows = await conn.fetch(revenue_query)
    
    revenue_by_month = {row['month']: float(row['revenue']) for row in revenue_rows}
    
    # Получаем Аутсорсинг персонала из транзакций ВАШ ДОМ модель
    if month:
        outsourcing_query = """
            SELECT SUM(amount) as total_amount
            FROM financial_transactions
            WHERE type = 'expense' AND company = 'ВАШ ДОМ модель' 
              AND category = 'Аутсорсинг персонала' AND project = $1
        """
        outsourcing_row = await conn.fetchrow(outsourcing_query, month)
    else:
        outsourcing_query = """
            SELECT SUM(amount) as total_amount
            FROM financial_transactions
            WHERE type = 'expense' AND company = 'ВАШ ДОМ модель'
              AND category = 'Аутсорсинг персонала'
        """
        outsourcing_row = await conn.fetchrow(outsourcing_query)


@router.get("/finances/forecast")
async def get_forecast(
    company: Optional[str] = "ВАШ ДОМ ФАКТ",
    scenario: Optional[str] = "realistic"
):
    """Get forecast for 2026-2030 with three scenarios"""
    try:
        conn = await get_db_connection()
        try:
            # Коэффициенты роста для разных сценариев
            scenario_coefficients = {
                "pessimistic": {
                    "revenue_multiplier": 0.7,  # Снижение роста выручки на 30%
                    "expense_multiplier": 1.3,  # Увеличение роста расходов на 30%
                    "description": "Консервативный прогноз: снижение темпов роста выручки, увеличение расходов"
                },
                "realistic": {
                    "revenue_multiplier": 1.0,  # Базовый рост
                    "expense_multiplier": 1.0,  # Базовый рост
                    "description": "Базовый прогноз на основе текущих трендов 2025 года"
                },
                "optimistic": {
                    "revenue_multiplier": 1.4,  # Увеличение роста выручки на 40%
                    "expense_multiplier": 0.8,  # Снижение роста расходов на 20%
                    "description": "Оптимистичный прогноз: ускоренный рост выручки, оптимизация расходов"
                }
            }
            
            scenario_config = scenario_coefficients.get(scenario, scenario_coefficients["realistic"])
            
            # Для УФИЦ модель используем данные расчета на основе фактических данных 2025
            if company == "УФИЦ модель":
                # Получаем фактические данные УФИЦ за 2025
                ufic_revenue_query = """
                    SELECT SUM(revenue) as total_revenue
                    FROM monthly_revenue
                    WHERE company = 'УФИЦ модель'
                """
                ufic_revenue_result = await conn.fetchrow(ufic_revenue_query)
                ufic_revenue_2025 = float(ufic_revenue_result['total_revenue']) if ufic_revenue_result['total_revenue'] else 27104525
                
                ufic_expenses_query = """
                    SELECT SUM(amount) as total_expenses
                    FROM financial_transactions
                    WHERE type = 'expense' AND company = 'УФИЦ модель'
                """
                ufic_expenses_result = await conn.fetchrow(ufic_expenses_query)
                ufic_expenses_2025 = float(ufic_expenses_result['total_expenses']) if ufic_expenses_result['total_expenses'] else 19944709
                
                # Среднее количество рабочих мест в 2025 году (из Excel данных)
                avg_places_2025 = 47.0
                
                # Метрики на 1 рабочее место
                revenue_per_place = ufic_revenue_2025 / avg_places_2025
                expenses_per_place = ufic_expenses_2025 / avg_places_2025
                
                # Количество мест по сценариям на 2026
                places_by_scenario = {
                    "pessimistic": 60,
                    "realistic": 65,
                    "optimistic": 70
                }
                
                places_2026 = places_by_scenario.get(scenario, 65)
                
                # Базовые значения на Feb 2026 (пересчет на новое количество мест)
                base_revenue_2026 = revenue_per_place * places_2026
                base_expenses_2026 = expenses_per_place * places_2026
                
                # Генерируем прогноз с годовой индексацией 6%
                indexation_rate = 1.06
                
                ufic_data = {
                    "pessimistic": {
                        "years": [],
                        "base_revenue": ufic_revenue_2025,
                        "base_expenses": ufic_expenses_2025,
                        "description": f"Консервативный прогноз: {places_by_scenario['pessimistic']} рабочих мест. Индексация 6% ежегодно."
                    },
                    "realistic": {
                        "years": [],
                        "base_revenue": ufic_revenue_2025,
                        "base_expenses": ufic_expenses_2025,
                        "description": f"Реалистичный прогноз: {places_by_scenario['realistic']} рабочих мест. Индексация 6% ежегодно."
                    },
                    "optimistic": {
                        "years": [],
                        "base_revenue": ufic_revenue_2025,
                        "base_expenses": ufic_expenses_2025,
                        "description": f"Оптимистичный прогноз: {places_by_scenario['optimistic']} рабочих мест. Индексация 6% ежегодно."
                    }
                }
                
                # Заполняем данные для всех сценариев
                for scen_name, places_count in places_by_scenario.items():
                    # Базовые значения на Feb 2026 для этого сценария
                    scen_base_revenue = revenue_per_place * places_count
                    scen_base_expenses = expenses_per_place * places_count
                    
                    for year in range(2026, 2031):
                        years_passed = year - 2026
                        indexed_revenue = scen_base_revenue * (indexation_rate ** years_passed)
                        indexed_expenses = scen_base_expenses * (indexation_rate ** years_passed)
                        indexed_profit = indexed_revenue - indexed_expenses
                        
                        ufic_data[scen_name]["years"].append({
                            "year": year,
                            "revenue": round(indexed_revenue, 2),
                            "expenses": round(indexed_expenses, 2),
                            "profit": round(indexed_profit, 2),
                            "cleaners": places_count  # Фиксированное количество мест
                        })
                    
                    ufic_data[scen_name]["base_revenue"] = ufic_revenue_2025
                    ufic_data[scen_name]["base_expenses"] = ufic_expenses_2025
                
                ufic_scenario = ufic_data.get(scenario, ufic_data["realistic"])
                
                # Используем данные из Excel
                forecast = []
                for year_data in ufic_scenario["years"]:
                    margin = (year_data["profit"] / year_data["revenue"] * 100) if year_data["revenue"] > 0 else 0
                    forecast.append({
                        "year": year_data["year"],
                        "revenue": year_data["revenue"],
                        "expenses": year_data["expenses"],
                        "profit": year_data["profit"],
                        "margin": round(margin, 2),
                        "cleaners_count": year_data["cleaners"]  # Добавляем количество уборщиц
                    })
                
                # Базовые данные 2025
                base_revenue = ufic_scenario["base_revenue"]
                base_expenses = ufic_scenario["base_expenses"]
                base_profit = base_revenue - base_expenses
                base_margin = (base_profit / base_revenue * 100) if base_revenue > 0 else 0
                
                # Расчеты для инвестора
                total_forecast_profit = sum(f["profit"] for f in forecast)
                average_annual_profit = total_forecast_profit / len(forecast)
                average_margin = sum(f["margin"] for f in forecast) / len(forecast)
                investment_amount = base_expenses
                roi_5_years = (total_forecast_profit / investment_amount * 100) if investment_amount > 0 else 0
                
                # Срок окупаемости
                cumulative_profit = 0
                payback_period = None
                for i, f in enumerate(forecast):
                    cumulative_profit += f["profit"]
                    if cumulative_profit >= investment_amount and payback_period is None:
                        payback_period = i + 1
                
                if payback_period is None:
                    payback_period = "> 5 лет"
                
                # Рост выручки и расходов (из первого и последнего года)
                revenue_growth = ((forecast[-1]["revenue"] / forecast[0]["revenue"]) ** (1/5) - 1) * 100
                expense_growth = ((forecast[-1]["expenses"] / forecast[0]["expenses"]) ** (1/5) - 1) * 100
                
                return {
                    "company": company,
                    "scenario": scenario,
                    "base_year": 2025,
                    "base_data": {
                        "revenue": round(base_revenue, 2),
                        "expenses": round(base_expenses, 2),
                        "profit": round(base_profit, 2),
                        "margin": round(base_margin, 2)
                    },
                    "forecast": forecast,
                    "investor_metrics": {
                        "investment_amount": round(investment_amount, 2),
                        "total_profit_5_years": round(total_forecast_profit, 2),
                        "average_annual_profit": round(average_annual_profit, 2),
                        "average_margin": round(average_margin, 2),
                        "roi_5_years": round(roi_5_years, 2),
                        "payback_period": payback_period,
                        "revenue_growth_rate": round(revenue_growth, 2),
                        "expense_growth_rate": round(expense_growth, 2)
                    },
                    "scenario_info": {
                        "name": scenario,
                        "description": ufic_scenario["description"],
                        "revenue_growth_rate": round(revenue_growth, 2),
                        "expense_growth_rate": round(expense_growth, 2),
                        "cleaners_info": f"Количество уборщиц: {forecast[0]['cleaners_count']} (2026) → {forecast[-1]['cleaners_count']} (2030)"
                    }
                }
            
            # Получаем данные прибылей/убытков за 2025 год
            if company == "ВАШ ДОМ модель":
                result_2025 = await get_consolidated_profit_loss(conn)
            else:
                # Получаем выручку
                revenue_rows = await conn.fetch("""
                    SELECT month, revenue
                    FROM monthly_revenue
                    WHERE company = $1
                    ORDER BY month
                """, company)
                
                revenue_by_month = {row['month']: float(row['revenue']) for row in revenue_rows}
                
                # Получаем расходы
                expense_rows = await conn.fetch("""
                    SELECT 
                        project as month,
                        SUM(amount) as amount
                    FROM financial_transactions
                    WHERE type = 'expense' AND company = $1
                    GROUP BY project
                """, company)
                
                expenses_by_month = {row['month']: float(row['amount']) for row in expense_rows}
                
                # Формируем данные 2025
                result_2025 = {
                    "profit_loss": [],
                    "summary": {
                        "total_revenue": sum(revenue_by_month.values()),
                        "total_expenses": sum(expenses_by_month.values()),
                        "total_profit": sum(revenue_by_month.values()) - sum(expenses_by_month.values()),
                        "margin": 0
                    }
                }
                
                if result_2025["summary"]["total_revenue"] > 0:
                    result_2025["summary"]["margin"] = round(
                        (result_2025["summary"]["total_profit"] / result_2025["summary"]["total_revenue"] * 100), 2
                    )
            
            # Вычисляем средний месячный рост на основе данных 2025
            monthly_data = result_2025.get("profit_loss", [])
            
            # Если есть помесячные данные, вычисляем тренд
            if len(monthly_data) >= 2:
                # Простая линейная регрессия для определения тренда
                revenues = [m["revenue"] for m in monthly_data if m.get("revenue")]
                expenses = [m["expenses"] for m in monthly_data if m.get("expenses")]
                
                # Средний рост = (последний - первый) / первый / количество периодов
                if len(revenues) >= 2 and revenues[0] > 0:
                    revenue_growth_rate = ((revenues[-1] - revenues[0]) / revenues[0]) / len(revenues)
                else:
                    revenue_growth_rate = 0.05  # По умолчанию 5% рост
                
                if len(expenses) >= 2 and expenses[0] > 0:
                    expense_growth_rate = ((expenses[-1] - expenses[0]) / expenses[0]) / len(expenses)
                else:
                    expense_growth_rate = 0.03  # По умолчанию 3% рост
            else:
                # Если нет помесячных данных, используем консервативные оценки
                revenue_growth_rate = 0.05  # 5% годовой рост
                expense_growth_rate = 0.03  # 3% годовой рост
            
            # Базовые значения 2025
            base_revenue = result_2025["summary"]["total_revenue"]
            base_expenses = result_2025["summary"]["total_expenses"]
            base_profit = result_2025["summary"]["total_profit"]
            
            # Годовые коэффициенты роста (умножаем месячные на 12 для годового)
            # Применяем множители сценария
            annual_revenue_growth = 1 + (revenue_growth_rate * 12 * scenario_config["revenue_multiplier"])
            annual_expense_growth = 1 + (expense_growth_rate * 12 * scenario_config["expense_multiplier"])
            
            # Генерируем прогноз на 2026-2030
            forecast = []
            years = [2026, 2027, 2028, 2029, 2030]
            
            current_revenue = base_revenue
            current_expenses = base_expenses
            
            for year in years:
                # Применяем рост
                current_revenue *= annual_revenue_growth
                current_expenses *= annual_expense_growth
                current_profit = current_revenue - current_expenses
                current_margin = (current_profit / current_revenue * 100) if current_revenue > 0 else 0
                
                forecast.append({
                    "year": year,
                    "revenue": round(current_revenue, 2),
                    "expenses": round(current_expenses, 2),
                    "profit": round(current_profit, 2),
                    "margin": round(current_margin, 2)
                })
            
            # Расчеты для инвестора
            total_forecast_profit = sum(f["profit"] for f in forecast)
            average_annual_profit = total_forecast_profit / len(forecast)
            
            # Средняя рентабельность
            average_margin = sum(f["margin"] for f in forecast) / len(forecast)
            
            # ROI за 5 лет (если инвестор вкладывает сумму = годовым расходам 2025)
            investment_amount = base_expenses
            roi_5_years = (total_forecast_profit / investment_amount * 100) if investment_amount > 0 else 0
            
            # Срок окупаемости (в годах)
            cumulative_profit = 0
            payback_period = None
            for i, f in enumerate(forecast):
                cumulative_profit += f["profit"]
                if cumulative_profit >= investment_amount and payback_period is None:
                    payback_period = i + 1
            
            if payback_period is None:
                payback_period = "> 5 лет"
            
            investor_metrics = {
                "investment_amount": round(investment_amount, 2),
                "total_profit_5_years": round(total_forecast_profit, 2),
                "average_annual_profit": round(average_annual_profit, 2),
                "average_margin": round(average_margin, 2),
                "roi_5_years": round(roi_5_years, 2),
                "payback_period": payback_period,
                "revenue_growth_rate": round(annual_revenue_growth * 100 - 100, 2),
                "expense_growth_rate": round(annual_expense_growth * 100 - 100, 2)
            }
            
            return {
                "company": company,
                "scenario": scenario,
                "base_year": 2025,
                "base_data": {
                    "revenue": round(base_revenue, 2),
                    "expenses": round(base_expenses, 2),
                    "profit": round(base_profit, 2),
                    "margin": result_2025["summary"]["margin"]
                },
                "forecast": forecast,
                "investor_metrics": investor_metrics,
                "scenario_info": {
                    "name": scenario,
                    "description": scenario_config["description"],
                    "revenue_growth_rate": round(annual_revenue_growth * 100 - 100, 2),
                    "expense_growth_rate": round(annual_expense_growth * 100 - 100, 2)
                }
            }
            
        finally:
            await conn.close()
    except Exception as e:
        logger.error(f"Error calculating forecast: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    
    outsourcing_total = float(outsourcing_row['total_amount']) if outsourcing_row and outsourcing_row['total_amount'] else 0
    
    # Получаем расходы ВАШ ДОМ ФАКТ
    if month:
        vasdom_query = """
            SELECT category, SUM(amount) as total_amount
            FROM financial_transactions
            WHERE type = 'expense' AND project = $1 AND company = 'ВАШ ДОМ ФАКТ'
            GROUP BY category
        """
        vasdom_rows = await conn.fetch(vasdom_query, month)
        
        # Получаем ТОЛЬКО Зарплату УФИЦ (без ФОТ)
        ufic_query = """
            SELECT category, SUM(amount) as total_amount
            FROM financial_transactions
            WHERE type = 'expense' AND project = $1 AND company = 'УФИЦ модель'
              AND category = 'Зарплата'
            GROUP BY category
        """
        ufic_rows = await conn.fetch(ufic_query, month)
    else:
        vasdom_query = """
            SELECT category, SUM(amount) as total_amount
            FROM financial_transactions
            WHERE type = 'expense' AND company = 'ВАШ ДОМ ФАКТ'
            GROUP BY category
        """
        vasdom_rows = await conn.fetch(vasdom_query)
        
        # Получаем ТОЛЬКО Зарплату УФИЦ (без ФОТ)
        ufic_query = """
            SELECT category, SUM(amount) as total_amount
            FROM financial_transactions
            WHERE type = 'expense' AND company = 'УФИЦ модель'
              AND category = 'Зарплата'
            GROUP BY category
        """
        ufic_rows = await conn.fetch(ufic_query)
    
    # Группируем УФИЦ Зарплату
    ufic_salary = 0
    for row in ufic_rows:
        ufic_salary = float(row['total_amount'])
    
    # Формируем консолидированные расходы
    expenses = []
    total = 0
    
    for row in vasdom_rows:
        category = row['category']
        vasdom_amount = float(row['total_amount'])
        
        # Исключаем категории
        if category in ['Кредиты', 'Швеи', 'Аутсорсинг персонала с Ю/ЦЛ', 'Юридические услуги', 'Продукты питания', 'Налоги']:
            continue
        
        # Специальная логика для Зарплаты: ВАШ ДОМ ФАКТ - УФИЦ Зарплата (без ФОТ)
        if category == 'Зарплата':
            consolidated_salary = vasdom_amount - ufic_salary
            
            if consolidated_salary > 0:
                total += consolidated_salary
                expenses.append({
                    "category": category,
                    "amount": consolidated_salary
                })
        else:
            # Для остальных категорий: только ВАШ ДОМ ФАКТ ("так же")
            total += vasdom_amount
            expenses.append({
                "category": category,
                "amount": vasdom_amount
            })
    
    # Добавляем Аутсорсинг персонала из транзакций ВАШ ДОМ модель
    if outsourcing_total > 0:
        total += outsourcing_total
        expenses.append({
            "category": "Аутсорсинг персонала",
            "amount": outsourcing_total
        })
    
    # Добавляем Налоги: 5% от выручки
    total_revenue = sum(revenue_by_month.values())
    if total_revenue > 0:
        taxes = total_revenue * 0.05
        total += taxes
        expenses.append({
            "category": "Налоги",
            "amount": taxes
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

