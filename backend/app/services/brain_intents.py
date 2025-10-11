"""
Extend intents (Stage 6): YoY and category trends
"""
from __future__ import annotations

from typing import Any, Dict, Optional
import re


def _detect_intent_base(message: str) -> Optional[Dict[str, Any]]:
    """Base intent detection for common patterns"""
    if not message:
        return None
    
    tl = message.lower()
    
    # Address/contact patterns
    if any(k in tl for k in ["контакт", "телефон", "номер", "старш"]):
        return {"type": "elder_contact"}
    
    # Cleaning schedule patterns  
    if any(k in tl for k in ["уборк", "когда", "дат", "расписан"]):
        return {"type": "cleaning_schedule"}
    
    # Finance patterns
    if any(k in tl for k in ["расход", "доход", "финанс", "деньги", "категори"]):
        return {"type": "finance"}
    
    return None


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