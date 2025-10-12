"""
Observability (Stage 9): structured logging, matched_rules trace, sources in debug
"""
from __future__ import annotations

from typing import Any, Optional, Dict, List, Tuple
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
    resolve_contractor_contacts,
    resolve_tasks_by_address,
    resolve_tasks_by_brigade,
)
from backend.app.services.brain_resolvers_stage6 import (
    resolve_finance_yoy,
    resolve_finance_category_trends,
)

logger = logging.getLogger(__name__)


async def try_fast_answer(message: str, db: Any = None, return_debug: bool = False) -> Optional[Dict[str, Any]]:
    t0 = time.monotonic()
    ent = detect_intent(message)
    trace: List[Dict[str, Any]] = []

    async def attempt(rule: str, fn, *args, **kwargs) -> Optional[Dict[str, Any]]:
        t_rule = time.monotonic()
        try:
            res = await fn(*args, **kwargs)
        except Exception as e:
            logger.warning(f"brain_resolver_error rule={rule}: {e}")
            res = None
        elapsed = int((time.monotonic() - t_rule) * 1000)
        status = "hit" if (res and res.get("success")) else "miss"
        trace.append({"rule": rule, "status": status, "elapsed_ms": elapsed})
        if res and res.get("success"):
            # Structured log with sources and cache meta if present
            sources = res.get("sources") or {}
            log_obj = {
                "event": "brain_answer",
                "rule": rule,
                "elapsed_ms": elapsed,
                "total_ms": int((time.monotonic() - t0) * 1000),
                "sources": sources,
            }
            # Try to surface cache meta if exists
            cache_meta = {}
            if isinstance(sources, dict):
                if "cache" in sources:
                    cache_meta["root"] = sources.get("cache")
                # common nested shapes we used earlier
                for k in ("houses", "elder", "cleaning", "finance"):
                    if k in sources and isinstance(sources[k], dict) and "cache" in sources[k]:
                        cache_meta[k] = sources[k]["cache"]
                if cache_meta:
                    log_obj["cache_meta"] = cache_meta
            logger.info(log_obj)
            if return_debug:
                res.setdefault("debug", {})
                res["debug"].update({
                    "matched_rule": rule,
                    "matched_rules": [tr["rule"] for tr in trace if tr.get("status") == "hit"],
                    "elapsed_ms": int((time.monotonic() - t0) * 1000),
                    "trace": trace,
                })
            return res
        return None

    # Intent-driven attempts first
    if ent:
        t = ent.get("type")
        if t == "elder_contact":
            res = await attempt("elder_contact", resolve_elder_contact, message, ent)
            if res: return res
        elif t == "cleaning_month":
            res = await attempt("cleaning_month", resolve_cleaning_month, message, ent)
            if res: return res
        elif t == "brigade":
            res = await attempt("brigade", resolve_brigade_by_address, message, ent)
            if res: return res
        elif t == "structural_totals" and db is not None:
            res = await attempt("structural_totals", resolve_structural_totals, message, db, ent)
            if res: return res
        elif t == "finance_basic" and db is not None:
            res = await attempt("finance_basic", resolve_finance_basic, message, db, ent)
            if res: return res
        elif t == "finance_breakdown" and db is not None:
            res = await attempt("finance_breakdown", resolve_finance_breakdown, message, db, ent)
            if res: return res
        elif t == "finance_mom" and db is not None:
            res = await attempt("finance_mom", resolve_finance_mom, message, db, ent)
            if res: return res
        elif t == "finance_yoy" and db is not None:
            res = await attempt("finance_yoy", resolve_finance_yoy, message, db, ent)
            if res: return res
        elif t == "finance_cat_trends" and db is not None:
            res = await attempt("finance_cat_trends", resolve_finance_category_trends, message, db, ent)
            if res: return res
        elif t == "contractor_contacts":
            res = await attempt("contractor_contacts", resolve_contractor_contacts, message, ent)
            if res: return res
        elif t == "tasks_by_address" and db is not None:
            res = await attempt("tasks_by_address", resolve_tasks_by_address, message, db, ent)
            if res: return res
        elif t == "tasks_by_brigade" and db is not None:
            res = await attempt("tasks_by_brigade", resolve_tasks_by_brigade, message, db, ent)
            if res: return res

    # Legacy fallback order
    order_wo_db: List[Tuple[str, Any]] = [
        ("elder_contact", resolve_elder_contact),
        ("cleaning_month", resolve_cleaning_month),
        ("brigade", resolve_brigade_by_address),
        ("contractor_contacts", resolve_contractor_contacts),
    ]
    for rule, fn in order_wo_db:
        res = await attempt(rule, fn, message)
        if res:
            return res

    if db is not None:
        order_with_db: List[Tuple[str, Any]] = [
            ("structural_totals", lambda m: resolve_structural_totals(m, db)),
            ("finance_basic", lambda m: resolve_finance_basic(m, db)),
            ("finance_breakdown", lambda m: resolve_finance_breakdown(m, db)),
            ("finance_mom", lambda m: resolve_finance_mom(m, db)),
            ("finance_yoy", lambda m: resolve_finance_yoy(m, db)),
            ("finance_cat_trends", lambda m: resolve_finance_category_trends(m, db)),
            ("tasks_by_address", lambda m: resolve_tasks_by_address(m, db)),
            ("tasks_by_brigade", lambda m: resolve_tasks_by_brigade(m, db)),
        ]
        for rule, fn in order_with_db:
            res = await attempt(rule, fn, message)
            if res:
                return res

    # No match — structured log with trace
    logger.info({
        "event": "brain_answer",
        "rule": None,
        "elapsed_ms": int((time.monotonic() - t0) * 1000),
        "trace": trace,
        "status": "no_match"
    })
    if return_debug:
        return {
            "success": False,
            "error": "no_match",
            "debug": {
                "matched_rule": None,
                "matched_rules": [],
                "elapsed_ms": int((time.monotonic() - t0) * 1000),
                "trace": trace,
            }
        }
    return None