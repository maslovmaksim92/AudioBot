"""
Extended Brain Math: finance by categories, shares, MoM/YoY; address parser upgrades are in brain.py
"""
from __future__ import annotations

from typing import Any, Dict, Optional
from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text


@dataclass
class FinanceBreakdown:
    income: float
    expense: float
    profit: float
    by_category: Dict[str, Dict[str, float]]  # {category: {income, expense, net}}
    shares: Dict[str, float]  # category -> share of total expense (or income)


async def compute_finance_breakdown(
    db: AsyncSession,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    side: str = "expense",
) -> FinanceBreakdown:
    """Breakdown by category; side: 'expense' to compute expense shares by default."""
    q = text(
        """
        SELECT category,
               SUM(CASE WHEN type='income' THEN amount ELSE 0 END) AS income,
               SUM(CASE WHEN type='expense' THEN amount ELSE 0 END) AS expense
        FROM financial_transactions
        WHERE (:date_from IS NULL OR date >= :date_from)
          AND (:date_to IS NULL OR date <= :date_to)
        GROUP BY category
        """
    )
    res = await db.execute(q, {"date_from": date_from, "date_to": date_to})
    rows = res.fetchall() or []
    by_cat: Dict[str, Dict[str, float]] = {}
    total_expense = 0.0
    total_income = 0.0
    for r in rows:
        cat = r[0]
        inc = float(r[1] or 0.0)
        exp = float(r[2] or 0.0)
        by_cat[cat] = {"income": inc, "expense": exp, "net": inc - exp}
        total_expense += exp
        total_income += inc
    shares: Dict[str, float] = {}
    denom = total_expense if side == 'expense' else total_income
    if denom > 0:
        for k, v in by_cat.items():
            num = v['expense'] if side == 'expense' else v['income']
            shares[k] = (num / denom) * 100.0
    return FinanceBreakdown(
        income=total_income,
        expense=total_expense,
        profit=total_income - total_expense,
        by_category=by_cat,
        shares=shares,
    )


async def compute_finance_change(
    db: AsyncSession,
    days: int = 30,
    baseline_days: Optional[int] = None,
) -> Dict[str, float]:
    """Compute change between recent window and prior window of equal (or provided) length.
    Returns {income_now, expense_now, profit_now, income_prev, expense_prev, profit_prev, mom_income, mom_expense, mom_profit}
    """
    if days <= 0:
        days = 30
    if baseline_days is None:
        baseline_days = days
    q = text(
        """
        WITH 
        recent AS (
            SELECT SUM(CASE WHEN type='income' THEN amount ELSE 0 END) AS inc,
                   SUM(CASE WHEN type='expense' THEN amount ELSE 0 END) AS exp
            FROM financial_transactions
            WHERE date >= (CURRENT_DATE - INTERVAL :days || ' day')
        ),
        previous AS (
            SELECT SUM(CASE WHEN type='income' THEN amount ELSE 0 END) AS inc,
                   SUM(CASE WHEN type='expense' THEN amount ELSE 0 END) AS exp
            FROM financial_transactions
            WHERE date < (CURRENT_DATE - INTERVAL :gap || ' day')
              AND date >= (CURRENT_DATE - INTERVAL (:gap + :days) || ' day')
        )
        SELECT r.inc, r.exp, p.inc, p.exp
        FROM recent r CROSS JOIN previous p
        """
    )
    res = await db.execute(q, {"days": days, "gap": baseline_days})
    row = res.first()
    inc_now = float(row[0] or 0.0) if row else 0.0
    exp_now = float(row[1] or 0.0) if row else 0.0
    inc_prev = float(row[2] or 0.0) if row else 0.0
    exp_prev = float(row[3] or 0.0) if row else 0.0
    prof_now = inc_now - exp_now
    prof_prev = inc_prev - exp_prev
    def pct(cur: float, prev: float) -> float:
        if prev == 0:
            return 0.0
        return (cur - prev) / prev * 100.0
    return {
        "income_now": inc_now,
        "expense_now": exp_now,
        "profit_now": prof_now,
        "income_prev": inc_prev,
        "expense_prev": exp_prev,
        "profit_prev": prof_prev,
        "mom_income": pct(inc_now, inc_prev),
        "mom_expense": pct(exp_now, exp_prev),
        "mom_profit": pct(prof_now, prof_prev),
    }