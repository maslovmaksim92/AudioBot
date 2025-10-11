"""
Brain resolvers (Stage 5 additions): finance breakdown/shares, MoM, and improved formatting already live.
"""
from __future__ import annotations

from typing import Any, Dict, Optional
import logging
from datetime import date, timedelta

from backend.app.services.brain_store import brain_store
from backend.app.services.brain import (
    parse_address_candidate,
    detect_month_key,
    format_cleaning_for_month,
    format_elder_contact,
    CleaningDates,
)
from backend.app.services.brain_math import (
    compute_finance_basic,
    compute_structural_totals,
    compute_finance_breakdown,
    compute_finance_change,
)

logger = logging.getLogger(__name__)

# existing helpers _success/_fail remain


async def resolve_finance_breakdown(text: str, db: Any, ent: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    tl = (text or "").lower()
    if not any(k in tl for k in ["категор", "доля", "структура", "разбивка"]) and not (ent and ent.get("type") == "finance_breakdown"):
        return None
    # detect side: расходы или доходы
    side = 'expense'
    if 'доход' in tl:
        side = 'income'
    # detect window
    range_days = ent and ent.get('range_days')
    date_from = None
    date_to = None
    if range_days:
        date_to = date.today().isoformat()
        date_from = (date.today() - timedelta(days=int(range_days))).isoformat()
    fb = await compute_finance_breakdown(db, date_from=date_from, date_to=date_to, side=side)
    lines = [f"Сводка по категориям ({'расходы' if side=='expense' else 'доходы'}):"]
    for cat, vals in fb.by_category.items():
        share = fb.shares.get(cat, 0.0)
        val = vals['expense'] if side == 'expense' else vals['income']
        lines.append(f"- {cat}: {val:.2f} ({share:.1f}%)")
    lines.append(f"Итого {('расход' if side=='expense' else 'доход')}: {(fb.expense if side=='expense' else fb.income):.2f}")
    lines.append(f"Прибыль: {fb.profit:.2f}")
    return {"success": True, "answer": "\n".join(lines), "data": {"breakdown": fb.__dict__}, "rule": "finance_breakdown"}


async def resolve_finance_mom(text: str, db: Any, ent: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    tl = (text or "").lower()
    if not any(k in tl for k in ["мом", "месяц к месяцу", "м/м", "рост", "динамика"]) and not (ent and ent.get("type") == "finance_mom"):
        return None
    # window detection
    days = 30
    if 'квартал' in tl or '90' in tl:
        days = 90
    ch = await compute_finance_change(db, days=days)
    ans = (
        f"Динамика за {days} дней (М/М):\n"
        f"Доход: {ch['income_now']:.2f} (было {ch['income_prev']:.2f}, {ch['mom_income']:.1f}%)\n"
        f"Расход: {ch['expense_now']:.2f} (было {ch['expense_prev']:.2f}, {ch['mom_expense']:.1f}%)\n"
        f"Прибыль: {ch['profit_now']:.2f} (было {ch['profit_prev']:.2f}, {ch['mom_profit']:.1f}%)"
    )
    return {"success": True, "answer": ans, "data": ch, "rule": "finance_mom"}