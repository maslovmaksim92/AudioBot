"""
Extend intents (Stage 6): YoY and category trends
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from .brain_intents import detect_intent as _detect_intent_base


def detect_intent(message: str) -> Optional[Dict[str, Any]]:
    ent = _detect_intent_base(message)
    if ent:
        return ent
    tl = message.lower() if message else ""
    if any(k in tl for k in ["yoy", "г/г", "год к году"]):
        return {"type": "finance_yoy"}
    if any(k in tl for k in ["топ", "рост", "падени", "лидеры", "просели"]):
        return {"type": "finance_cat_trends"}
    return None