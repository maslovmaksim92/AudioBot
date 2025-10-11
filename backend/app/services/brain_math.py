"""
Brain Math utilities: safe math and aggregations for Single Brain
- Financial arithmetic (sum, avg, change %)
- Structural arithmetic over houses: totals for floors/entrances/apartments
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text


@dataclass
class FinanceAggregate:
    transactions: int
    income: float
    expense: float
    profit: float


async def compute_finance_basic(db: AsyncSession, date_from: Optional[str] = None, date_to: Optional[str] = None) -> FinanceAggregate:
    q = text(
        """
        SELECT 
            COUNT(*) as total_transactions,
            SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END) as total_income,
            SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END) as total_expense
        FROM financial_transactions
        WHERE (:date_from IS NULL OR date >= :date_from)
          AND (:date_to IS NULL OR date <= :date_to)
        """
    )
    res = await db.execute(q, {"date_from": date_from, "date_to": date_to})
    row = res.first()
    income = float(row[1] or 0.0) if row else 0.0
    expense = float(row[2] or 0.0) if row else 0.0
    return FinanceAggregate(
        transactions=int(row[0] or 0) if row else 0,
        income=income,
        expense=expense,
        profit=income - expense,
    )


async def compute_structural_totals(db: AsyncSession) -> Dict[str, int]:
    """Totals by houses: floors, entrances, apartments.
    Assumes houses table with numeric columns floors, entrances, apartments.
    """
    q = text(
        """
        SELECT 
            COALESCE(SUM(floors), 0) as floors,
            COALESCE(SUM(entrances), 0) as entrances,
            COALESCE(SUM(apartments), 0) as apartments
        FROM houses
        """
    )
    res = await db.execute(q)
    row = res.first()
    return {
        "floors": int(row[0] or 0) if row else 0,
        "entrances": int(row[1] or 0) if row else 0,
        "apartments": int(row[2] or 0) if row else 0,
    }


def percent_change(current: float, previous: float) -> float:
    if previous == 0:
        return 0.0
    return (current - previous) / previous * 100.0