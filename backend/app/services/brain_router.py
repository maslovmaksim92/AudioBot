"""
Wire Stage 6 resolvers and add debug timing to try_fast_answer return (propagated up by brain API)
"""
from __future__ import annotations

from typing import Any, Optional, Dict
import logging
import time

from backend.app.services.brain_intents import detect_intent
from backend.app.services.brain_resolvers import (
    resolve_elder_contact,
    resolve_cleaning_month,
    resolve_brigade_by_address,
    resolve_finance_basic,
    resolve_structural_totals,
    resolve_finance_breakdown,
    resolve_finance_mom,
)
from backend.app.services.brain_resolvers_stage6 import (
    resolve_finance_yoy,
    resolve_finance_category_trends,
)

logger = logging.getLogger(__name__)


async def try_fast_answer(message: str, db: Any = None, return_debug: bool = False) -> Optional[Dict[str, Any]]:
    t0 = time.monotonic()
    ent = detect_intent(message)
    matched_rule = None
    ans: Optional[Dict[str, Any]] = None

    async def _ret(a: Optional[Dict[str, Any]], rule: Optional[str]) -> Optional[Dict[str, Any]]:
        nonlocal matched_rule
        if a and a.get("success"):
            matched_rule = a.get("rule") or rule
            if return_debug:
                a["debug"] = {"matched_rule": matched_rule, "elapsed_ms": int((time.monotonic() - t0) * 1000)}
            return a
        return None

    if ent:
        t = ent.get("type")
        if t == "elder_contact":
            ans = await _ret(await resolve_elder_contact(message, ent), "elder_contact")
            if ans:
                return ans
        elif t == "cleaning_month":
            ans = await _ret(await resolve_cleaning_month(message, ent), "cleaning_month")
            if ans:
                return ans
        elif t == "brigade":
            ans = await _ret(await resolve_brigade_by_address(message, ent), "brigade")
            if ans:
                return ans
        elif t == "structural_totals" and db is not None:
            ans = await _ret(await resolve_structural_totals(message, db, ent), "structural_totals")
            if ans:
                return ans
        elif t == "finance_basic" and db is not None:
            ans = await _ret(await resolve_finance_basic(message, db, ent), "finance_basic")
            if ans:
                return ans
        elif t == "finance_breakdown" and db is not None:
            ans = await _ret(await resolve_finance_breakdown(message, db, ent), "finance_breakdown")
            if ans: return ans
        elif t == "finance_mom" and db is not None:
            ans = await _ret(await resolve_finance_mom(message, db, ent), "finance_mom")
            if ans: return ans
        elif t == "finance_yoy" and db is not None:
            ans = await _ret(await resolve_finance_yoy(message, db, ent), "finance_yoy")
            if ans: return ans
        elif t == "finance_cat_trends" and db is not None:
            ans = await _ret(await resolve_finance_category_trends(message, db, ent), "finance_cat_trends")
            if ans: return ans

    # Legacy fallback order
    for rule, fn in [
        ("elder_contact", resolve_elder_contact),
        ("cleaning_month", resolve_cleaning_month),
        ("brigade", resolve_brigade_by_address),
    ]:
        a = await fn(message)
        ans = await _ret(a, rule)
        if ans:
            return ans
    if db is not None:
        for rule, fn in [
            ("structural_totals", lambda m: resolve_structural_totals(m, db)),
            ("finance_basic", lambda m: resolve_finance_basic(m, db)),
            ("finance_breakdown", lambda m: resolve_finance_breakdown(m, db)),
            ("finance_mom", lambda m: resolve_finance_mom(m, db)),
            ("finance_yoy", lambda m: resolve_finance_yoy(m, db)),
            ("finance_cat_trends", lambda m: resolve_finance_category_trends(m, db)),
        ]:
            a = await fn(message)
            ans = await _ret(a, rule)
            if ans:
                return ans

    if ans and return_debug:
        ans["debug"] = {"matched_rule": matched_rule, "elapsed_ms": int((time.monotonic() - t0) * 1000)}
    return ans