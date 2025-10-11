"""
Brain intents (Stage 5 additions): finance breakdown/shares and MoM/YoY
"""
from __future__ import annotations

from typing import Any, Dict, Optional
import re

from backend.app.services.brain import (
    parse_address_candidate,
    detect_month_key,
    detect_period_index,
)

from .brain_intents import detect_intent as _detect_intent_base


def detect_intent(message: str) -> Optional[Dict[str, Any]]:
    ent = _detect_intent_base(message)
    if ent:
        return ent
    tl = message.lower() if message else ""
    # finance breakdown/shares
    if any(k in tl for k in ["категор", "доля", "структур", "разбивка"]):
        days = None
        if re.search(r"\b30\b", tl) or "месяц" in tl:
            days = 30
        elif re.search(r"\b90\b", tl) or "квартал" in tl:
            days = 90
        elif re.search(r"\b365\b", tl) or "год" in tl:
            days = 365
        elif "недел" in tl:
            days = 7
        return {"type": "finance_breakdown", "range_days": days}
    # finance mom/yoy (we implement MoM now)
    if any(k in tl for k in ["м/м", "месяц к месяцу", "мом", "динамика"]):
        return {"type": "finance_mom"}
    return None