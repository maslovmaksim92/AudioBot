from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel
import logging
import asyncpg
import os

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
        # Mock данные для демонстрации
        # В продакшене здесь будет запрос к БД
        cash_flow = []
        
        today = datetime.now(timezone.utc)
        for i in range(30, 0, -1):
            date = today - timedelta(days=i)
            cash_flow.append({
                "date": date.strftime("%Y-%m-%d"),
                "income": 150000 + (i * 5000),
                "expense": 120000 + (i * 3000),
                "balance": 30000 + (i * 2000)
            })
        
        return {
            "cash_flow": cash_flow,
            "summary": {
                "total_income": sum(item["income"] for item in cash_flow),
                "total_expense": sum(item["expense"] for item in cash_flow),
                "net_cash_flow": sum(item["balance"] for item in cash_flow)
            }
        }
    except Exception as e:
        logger.error(f"Error fetching cash flow: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/finances/profit-loss")
async def get_profit_loss(
    period: Optional[str] = "year"
):
    """
    Получить отчёт о прибылях и убытках
    """
    try:
        # Mock данные
        profit_loss = [
            {"period": "Январь 2025", "revenue": 5000000, "expenses": 3800000, "profit": 1200000, "margin": 24.0},
            {"period": "Февраль 2025", "revenue": 5500000, "expenses": 4100000, "profit": 1400000, "margin": 25.5},
            {"period": "Март 2025", "revenue": 6000000, "expenses": 4300000, "profit": 1700000, "margin": 28.3},
            {"period": "Апрель 2025", "revenue": 5800000, "expenses": 4200000, "profit": 1600000, "margin": 27.6},
            {"period": "Май 2025", "revenue": 6200000, "expenses": 4400000, "profit": 1800000, "margin": 29.0},
            {"period": "Июнь 2025", "revenue": 6500000, "expenses": 4600000, "profit": 1900000, "margin": 29.2}
        ]
        
        return {
            "profit_loss": profit_loss,
            "summary": {
                "total_revenue": sum(item["revenue"] for item in profit_loss),
                "total_expenses": sum(item["expenses"] for item in profit_loss),
                "net_profit": sum(item["profit"] for item in profit_loss),
                "average_margin": sum(item["margin"] for item in profit_loss) / len(profit_loss)
            }
        }
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
async def get_expense_analysis():
    """
    Анализ расходов по категориям
    """
    try:
        conn = await get_db_connection()
        try:
            # Получаем реальные данные из БД
            query = """
                SELECT category, SUM(amount) as total_amount
                FROM financial_transactions
                WHERE type = 'expense'
                GROUP BY category
                ORDER BY total_amount DESC
            """
            rows = await conn.fetch(query)
            
            if not rows:
                # Если данных нет, возвращаем пустой результат
                return {
                    "expenses": [],
                    "total": 0
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
                "total": total
            }
        finally:
            await conn.close()
    except Exception as e:
        logger.error(f"Error fetching expense analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/finances/debts")
async def get_debts():
    """
    Получить список задолженностей
    """
    try:
        # Mock данные
        debts = [
            {
                "id": "debt-1",
                "creditor": "Банк ВТБ",
                "amount": 5000000,
                "due_date": "2025-12-31",
                "status": "active",
                "type": "loan"
            },
            {
                "id": "debt-2",
                "creditor": "Сбербанк",
                "amount": 3000000,
                "due_date": "2026-06-30",
                "status": "active",
                "type": "credit_line"
            },
            {
                "id": "debt-3",
                "creditor": "Поставщик ООО Стройматериалы",
                "amount": 800000,
                "due_date": "2025-11-15",
                "status": "overdue",
                "type": "accounts_payable"
            },
            {
                "id": "debt-4",
                "creditor": "Лизинговая компания",
                "amount": 2000000,
                "due_date": "2027-03-20",
                "status": "active",
                "type": "lease"
            }
        ]
        
        total_debt = sum(item["amount"] for item in debts)
        overdue_debt = sum(item["amount"] for item in debts if item["status"] == "overdue")
        
        return {
            "debts": debts,
            "summary": {
                "total": total_debt,
                "overdue": overdue_debt,
                "active": total_debt - overdue_debt,
                "count": len(debts)
            }
        }
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
        logger.error(f"Error fetching finances dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))
