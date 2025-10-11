"""
Add resolvers for YoY and category trends (Stage 6)
"""
from __future__ import annotations

from typing import Any, Dict, Optional
from datetime import date, timedelta

from backend.app.services.brain_math import compute_finance_yoy, compute_category_trends

from .brain_resolvers import _success, _fail  # reuse helpers


async def resolve_finance_yoy(text: str, db: Any, ent: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    tl = (text or "").lower()
    if not any(k in tl for k in ["yoy", "г/г", "год к году"]) and not (ent and ent.get("type") == "finance_yoy"):
        return None
    yoy = await compute_finance_yoy(db)
    ans = (
        f"Г/Г динамика за 365 дней:\n"
        f"Доход: {yoy['income_now']:.2f} (было {yoy['income_prev']:.2f}, {yoy['yoy_income']:.1f}%)\n"
        f"Расход: {yoy['expense_now']:.2f} (было {yoy['expense_prev']:.2f}, {yoy['yoy_expense']:.1f}%)\n"
        f"Прибыль: {yoy['profit_now']:.2f} (было {yoy['profit_prev']:.2f}, {yoy['yoy_profit']:.1f}%)"
    )
    return _success(ans, data=yoy, rule="finance_yoy")


async def resolve_finance_category_trends(text: str, db: Any, ent: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    tl = (text or "").lower()
    if not any(k in tl for k in ["топ", "рост", "падени", "лидеры", "просели"]) and not (ent and ent.get("type") == "finance_cat_trends"):
        return None
    days = 30
    if 'квартал' in tl or '90' in tl:
        days = 90
    side = 'expense'
    if 'доход' in tl:
        side = 'income'
    trends = await compute_category_trends(db, days=days, side=side)
    lines = [f"Топ категорий за {days} дней ({'расходы' if side=='expense' else 'доходы'}):"]
    if trends['top_growth']:
        lines.append("Рост:")
        for cat, now_val, delta in trends['top_growth']:
            lines.append(f"  + {cat}: {now_val:.2f} (Δ {delta:.2f})")
    if trends['top_decline']:
        lines.append("Падение:")
        for cat, now_val, delta in trends['top_decline']:
            lines.append(f"  - {cat}: {now_val:.2f} (Δ {delta:.2f})")
    return _success("\n".join(lines), data=trends, rule="finance_cat_trends")