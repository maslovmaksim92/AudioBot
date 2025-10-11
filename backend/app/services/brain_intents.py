"""
Brain intents (Stage 4): rule-based intent detection and entity extraction
Detects: elder_contact, cleaning_month, brigade, structural_totals, finance_basic
Extracts: address, month_key (october/november/december), period_idx (1/2), range_days
"""
from __future__ import annotations

from typing import Any, Dict, Optional
import re

from backend.app.services.brain import (
    parse_address_candidate,
    detect_month_key,
    detect_period_index,
)


def _has_any(s: str, kws) -> bool:
    return any(k in s for k in kws)


def detect_intent(message: str) -> Optional[Dict[str, Any]]:
    if not message or not message.strip():
        return None
    tl = message.lower()

    # 1) Elder contact by address
    if _has_any(tl, ["контакт", "телефон", "почта", "email"]) and ("старш" in tl):
        addr = parse_address_candidate(message)
        if addr:
            return {"type": "elder_contact", "address": addr}

    # 2) Cleaning by month (+ optional period index)
    if "уборк" in tl:
        addr = parse_address_candidate(message)
        if addr:
            mk = detect_month_key(message) or "october"
            pi = detect_period_index(message)
            return {"type": "cleaning_month", "address": addr, "month_key": mk, "period_idx": pi}

    # 3) Brigade by address
    if _has_any(tl, ["бригад", "ответствен"]):
        addr = parse_address_candidate(message)
        if addr:
            return {"type": "brigade", "address": addr}

    # 4) Structural totals (no address required)
    if _has_any(tl, ["этаж", "подъезд", "квартир", "апартамент"]):
        return {"type": "structural_totals"}

    # 5) Finance (basic) with optional time window
    if _has_any(tl, ["финанс", "расход", "доход", "прибыль", "пнл", "p&amp;l", "cashflow", "деньги"]):
        days = None
        # detect common ranges
        if re.search(r"\b30\b", tl) or "месяц" in tl:
            days = 30
        elif re.search(r"\b90\b", tl) or "квартал" in tl:
            days = 90
        elif re.search(r"\b365\b", tl) or "год" in tl:
            days = 365
        elif "недел" in tl:
            days = 7
        return {"type": "finance_basic", "range_days": days}

    return None