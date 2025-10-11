"""
Add YoY and category trends (Stage 6)
"""
from __future__ import annotations

from typing import Any, Dict, Optional, List, Tuple
from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

# keep existing functions ...


def _pct(cur: float, prev: float) -> float:
    if prev == 0:
        return 0.0
    return (cur - prev) / prev * 100.0


async def compute_finance_yoy(db: AsyncSession, days: int = 365) -> Dict[str, float]:
    q = text(
        """
        WITH 
        recent AS (
            SELECT SUM(CASE WHEN type='income' THEN amount ELSE 0 END) AS inc,
                   SUM(CASE WHEN type='expense' THEN amount ELSE 0 END) AS exp
            FROM financial_transactions
            WHERE date >= (CURRENT_DATE - INTERVAL '%s days')
        ),
        previous AS (
            SELECT SUM(CASE WHEN type='income' THEN amount ELSE 0 END) AS inc,
                   SUM(CASE WHEN type='expense' THEN amount ELSE 0 END) AS exp
            FROM financial_transactions
            WHERE date < (CURRENT_DATE - INTERVAL '%s days')
              AND date >= (CURRENT_DATE - INTERVAL '%s days')
        )
        SELECT r.inc, r.exp, p.inc, p.exp FROM recent r CROSS JOIN previous p
        """ % (days, days, 2 * days)
    )
    res = await db.execute(q)
    row = res.first()
    inc_now = float(row[0] or 0.0) if row else 0.0
    exp_now = float(row[1] or 0.0) if row else 0.0
    inc_prev = float(row[2] or 0.0) if row else 0.0
    exp_prev = float(row[3] or 0.0) if row else 0.0
    prof_now = inc_now - exp_now
    prof_prev = inc_prev - exp_prev
    return {
        "income_now": inc_now,
        "expense_now": exp_now,
        "profit_now": prof_now,
        "income_prev": inc_prev,
        "expense_prev": exp_prev,
        "profit_prev": prof_prev,
        "yoy_income": _pct(inc_now, inc_prev),
        "yoy_expense": _pct(exp_now, exp_prev),
        "yoy_profit": _pct(prof_now, prof_prev),
    }


async def compute_category_trends(db: AsyncSession, days: int = 30, side: str = 'expense') -> Dict[str, List[Tuple[str, float, float]]]:
    """Return top growth/decline categories by delta for window vs prior window.
    Returns {"top_growth": [(cat, cur, delta), ...], "top_decline": [...]} for selected side (expense/income).
    """
    q = text(
        """
        WITH 
        recent AS (
            SELECT category,
                   SUM(CASE WHEN type='income' THEN amount ELSE 0 END) AS inc,
                   SUM(CASE WHEN type='expense' THEN amount ELSE 0 END) AS exp
            FROM financial_transactions
            WHERE date >= (CURRENT_DATE - INTERVAL '%s days')
            GROUP BY category
        ),
        previous AS (
            SELECT category,
                   SUM(CASE WHEN type='income' THEN amount ELSE 0 END) AS inc,
                   SUM(CASE WHEN type='expense' THEN amount ELSE 0 END) AS exp
            FROM financial_transactions
            WHERE date < (CURRENT_DATE - INTERVAL '%s days')
              AND date >= (CURRENT_DATE - INTERVAL '%s days')
            GROUP BY category
        )
        SELECT 
            COALESCE(r.category, p.category) AS category,
            COALESCE(r.inc, 0) AS inc_now,
            COALESCE(r.exp, 0) AS exp_now,
            COALESCE(p.inc, 0) AS inc_prev,
            COALESCE(p.exp, 0) AS exp_prev
        FROM recent r
        FULL OUTER JOIN previous p ON r.category = p.category
        """ % (days, days, 2 * days)
    )
    res = await db.execute(q)
    rows = res.fetchall() or []
    items: List[Tuple[str, float, float]] = []
    for r in rows:
        cat = r[0]
        now_val = float(r[2] if side == 'expense' else r[1])
        prev_val = float(r[4] if side == 'expense' else r[3])
        delta = now_val - prev_val
        items.append((cat, now_val, delta))
    # sort
    top_growth = sorted([it for it in items if it[2] > 0], key=lambda x: x[2], reverse=True)[:5]
    top_decline = sorted([it for it in items if it[2] < 0], key=lambda x: x[2])[:5]
    return {"top_growth": top_growth, "top_decline": top_decline}