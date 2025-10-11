"""
Brain API router: add debug flag to return matched_rule, sources, elapsed time, cache meta
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.config.database import get_db
from backend.app.services.brain_router import try_fast_answer

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
        out = {"success": False, "error": "no_match"}
        if req.debug:
            out["debug"] = {"matched_rule": None}
        return out
    return ans