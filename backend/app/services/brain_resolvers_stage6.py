"""
Stage 6 resolvers for YoY and category trends
"""
from __future__ import annotations

from typing import Any, Dict, Optional
from datetime import date, timedelta

from backend.app.services.brain_math import compute_finance_yoy, compute_category_trends


def _success(response: str, data: Optional[Dict[str, Any]] = None, rule: Optional[str] = None) -> Dict[str, Any]:
    """Helper to create success response"""
    result = {
        "success": True,
        "response": response
    }
    if data:
        result["data"] = data
    if rule:
        result["rule"] = rule
    return result


def _fail(error: str) -> Dict[str, Any]:
    """Helper to create failure response"""
    return {
        "success": False,
        "error": error
    }


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
    trends = await compute_category_trends(db, days=90)  # квартал = 90 дней
    ans = "Топ изменения категорий за квартал:\n"
    
    # Show top growth
    if trends.get("top_growth"):
        ans += "Рост:\n"
        for cat, now_val, delta in trends["top_growth"][:3]:
            ans += f"  + {cat}: {now_val:.2f} (Δ {delta:.2f})\n"
    
    # Show top decline
    if trends.get("top_decline"):
        ans += "Падение:\n"
        for cat, now_val, delta in trends["top_decline"][:3]:
            ans += f"  - {cat}: {now_val:.2f} (Δ {delta:.2f})\n"
    
    return _success(ans, data=trends, rule="finance_cat_trends")