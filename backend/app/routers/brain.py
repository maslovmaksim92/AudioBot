"""
Brain API router: debug returns matched_rules and sources; logs already handled in brain_router
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.config.database import get_db
from backend.app.services.brain_router import try_fast_answer
from backend.app.services.brain_metrics import brain_metrics

router = APIRouter(prefix="/brain", tags=["brain"])


class BrainAskRequest(BaseModel):
    message: str
    user_id: Optional[str] = None
    debug: Optional[bool] = False


@router.post("/ask")
async def brain_ask(req: BrainAskRequest, db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    if not req.message or not req.message.strip():
        raise HTTPException(status_code=400, detail="message is required")
    ans = await try_fast_answer(req.message, db=db, return_debug=bool(req.debug))
    if ans is None:
        # Extended diagnostics for no_match
        hints = []
        tl = req.message.lower()
        if 'уборк' in tl and 'окт' not in tl and 'ноя' not in tl and 'дек' not in tl:
            hints.append('уточните месяц (например, октябрь)')
        if 'уборк' in tl and 'на ' not in tl and 'по адресу' not in tl:
            hints.append('уточните адрес (например, "на Билибина 6")')
        out = {"success": False, "error": "no_match"}
        if hints:
            out["hints"] = hints
        if req.debug:
            out["debug"] = {"matched_rule": None, "matched_rules": []}
        return out
    # record metrics if debug present
    if req.debug and isinstance(ans, dict) and ans.get("debug"):
        dbg = ans["debug"]
        rule = dbg.get("matched_rule") or ans.get("rule") or "unknown"
        brain_metrics.record_resolver(rule, dbg.get("elapsed_ms", 0))
    return ans


@router.get("/metrics")
async def get_brain_metrics() -> Dict[str, Any]:
    """Получить метрики работы Brain"""
    return brain_metrics.snapshot()