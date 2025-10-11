"""
BrainRouter: routes a user message to appropriate resolver.
Returns either a fast answer (dict) or None to allow fallback (LLM or other).
"""
from __future__ import annotations

from typing import Any, Optional, Dict
import logging

from backend.app.services.brain_resolvers import (
    resolve_elder_contact,
    resolve_cleaning_month,
    resolve_brigade_by_address,
    resolve_finance_basic,
)

logger = logging.getLogger(__name__)


async def try_fast_answer(message: str, db: Any = None) -> Optional[Dict[str, Any]]:
    # Priority order: elder contact, cleaning, brigade, finance
    # 1) Elder contact
    ans = await resolve_elder_contact(message)
    if ans and ans.get("success"):
        return ans
    # 2) Cleaning by month
    ans = await resolve_cleaning_month(message)
    if ans and ans.get("success"):
        return ans
    # 3) Brigade by address
    ans = await resolve_brigade_by_address(message)
    if ans and ans.get("success"):
        return ans
    # 4) Finance (requires db)
    if db is not None:
        ans = await resolve_finance_basic(message, db)
        if ans and ans.get("success"):
            return ans
    return ans if ans else None