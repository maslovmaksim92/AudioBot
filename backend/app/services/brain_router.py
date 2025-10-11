"""
BrainRouter: routes a user message to appropriate resolver.
"""
from __future__ import annotations

from typing import Any, Optional, Dict
import logging

from backend.app.services.brain_intents import detect_intent
from backend.app.services.brain_resolvers import (
    resolve_elder_contact,
    resolve_cleaning_month,
    resolve_brigade_by_address,
    resolve_finance_basic,
    resolve_structural_totals,
)

logger = logging.getLogger(__name__)


async def try_fast_answer(message: str, db: Any = None) -> Optional[Dict[str, Any]]:
    ent = detect_intent(message)
    if ent:
        t = ent.get("type")
        if t == "elder_contact":
            ans = await resolve_elder_contact(message, ent)
            if ans and ans.get("success"):
                return ans
        elif t == "cleaning_month":
            ans = await resolve_cleaning_month(message, ent)
            if ans and ans.get("success"):
                return ans
        elif t == "brigade":
            ans = await resolve_brigade_by_address(message, ent)
            if ans and ans.get("success"):
                return ans
        elif t == "structural_totals" and db is not None:
            ans = await resolve_structural_totals(message, db, ent)
            if ans and ans.get("success"):
                return ans
        elif t == "finance_basic" and db is not None:
            ans = await resolve_finance_basic(message, db, ent)
            if ans and ans.get("success"):
                return ans

    # Legacy fallback priority
    ans = await resolve_elder_contact(message)
    if ans and ans.get("success"):
        return ans
    ans = await resolve_cleaning_month(message)
    if ans and ans.get("success"):
        return ans
    ans = await resolve_brigade_by_address(message)
    if ans and ans.get("success"):
        return ans
    if db is not None:
        ans = await resolve_structural_totals(message, db)
        if ans and ans.get("success"):
            return ans
        ans = await resolve_finance_basic(message, db)
        if ans and ans.get("success"):
            return ans
    return None