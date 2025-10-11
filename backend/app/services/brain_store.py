"""
BrainStore (Stage 6 updates): optional debug meta (cache hit/miss)
"""
from __future__ import annotations

from dataclasses import asdict
from typing import Any, Dict, List, Optional, Tuple, Union
from datetime import datetime, timezone
import logging

from backend.app.services.brain import (
    HouseDTO,
    CleaningDates,
    ElderContact,
    CompanyInfo,
    normalize_address,
)
from backend.app.services.bitrix24_service import bitrix24_service

logger = logging.getLogger(__name__)


class TTLCache:
    def __init__(self, ttl_seconds: int):
        self.ttl = ttl_seconds
        self.store: Dict[str, Tuple[float, Any]] = {}

    def get(self, key: str) -> Any:
        rec = self.store.get(key)
        if not rec:
            return None
        ts, val = rec
        if (datetime.now(timezone.utc).timestamp() - ts) > self.ttl:
            self.store.pop(key, None)
            return None
        return val

    def set(self, key: str, val: Any) -> None:
        self.store[key] = (datetime.now(timezone.utc).timestamp(), val)


class BrainStore:
    def __init__(self):
        self.addr_cache = TTLCache(180)
        self.contact_cache = TTLCache(300)
        self.finance_cache = TTLCache(180)

    @staticmethod
    def _map_house_dict(h: Dict[str, Any]) -> HouseDTO:
        cd = CleaningDates.from_dict(h.get("cleaning_dates") or {})
        elder = None
        if h.get("elder_contact"):
            e = h["elder_contact"]
            elder = ElderContact(
                name=str(e.get("name") or ""),
                phones=[str(p) for p in (e.get("phones") or [])],
                emails=[str(em) for em in (e.get("emails") or [])],
            )
        company = None
        if h.get("company"):
            c = h["company"]
            company = CompanyInfo(
                id=str(c.get("id")) if c.get("id") is not None else None,
                title=str(c.get("title") or ""),
                phones=[str(p) for p in (c.get("phones") or [])],
                emails=[str(em) for em in (c.get("emails") or [])],
            )
        return HouseDTO(
            id=str(h.get("id")),
            title=str(h.get("title") or h.get("address") or ""),
            address=str(h.get("address") or ""),
            brigade_name=h.get("brigade_name"),
            brigade_number=h.get("brigade_number"),
            assigned_by_id=str(h.get("assigned_by_id")) if h.get("assigned_by_id") else None,
            management_company=h.get("management_company"),
            status=h.get("status"),
            cleaning_dates=cd,
            periodicity=h.get("periodicity"),
            bitrix_url=h.get("bitrix_url"),
            elder_contact=elder,
            company=company,
        )

    async def get_houses_by_address(self, address: str, limit: int = 3, return_debug: bool = False) -> Union[List[HouseDTO], Tuple[List[HouseDTO], Dict[str, Any]]]:
        addr_norm = normalize_address(address)
        cache_key = f"addr:{addr_norm}:{limit}"
        cached = self.addr_cache.get(cache_key)
        meta = {"cache": "hit" if cached is not None else "miss", "cache_key": cache_key}
        if cached is not None:
            return (cached, meta) if return_debug else cached
        try:
            data = await bitrix24_service.list_houses(address=address, limit=limit)
            houses = (data or {}).get("houses") or []
            result = [self._map_house_dict(h) for h in houses[:limit]]
            self.addr_cache.set(cache_key, result)
            return (result, meta) if return_debug else result
        except Exception as e:
            logger.error(f"BrainStore.get_houses_by_address error: {e}")
            return ([], meta) if return_debug else []

    async def get_elder_contact_by_address(self, address: str, return_debug: bool = False) -> Union[Optional[ElderContact], Tuple[Optional[ElderContact], Dict[str, Any]]]:
        addr_norm = normalize_address(address)
        cache_key = f"elder:{addr_norm}"
        cached = self.contact_cache.get(cache_key)
        meta = {"cache": "hit" if cached is not None else "miss", "cache_key": cache_key}
        if cached is not None:
            return (cached, meta) if return_debug else cached
        try:
            hb = await self.get_houses_by_address(address, limit=1, return_debug=True)
            houses, hmeta = hb if isinstance(hb, tuple) else (hb, {})
            meta["houses"] = hmeta
            if not houses:
                return (None, meta) if return_debug else None
            h = houses[0]
            if h.elder_contact and not h.elder_contact.is_empty():
                self.contact_cache.set(cache_key, h.elder_contact)
                return (h.elder_contact, meta) if return_debug else h.elder_contact
            details = await bitrix24_service.get_deal_details(h.id)
            contact_dict = (details or {}).get("elder_contact") or {}
            phones = contact_dict.get("phones") or []
            emails = contact_dict.get("emails") or []
            name = contact_dict.get("name") or ""
            company = (details or {}).get("company") or {}
            if not phones:
                phones = company.get("phones") or []
            if not emails:
                emails = company.get("emails") or []
            elder = ElderContact(name=str(name or ""), phones=[str(p) for p in phones], emails=[str(em) for em in emails])
            self.contact_cache.set(cache_key, elder)
            return (elder, meta) if return_debug else elder
        except Exception as e:
            logger.error(f"BrainStore.get_elder_contact_by_address error: {e}")
            return (None, meta) if return_debug else None

    async def get_cleaning_for_month_by_address(self, address: str, month_key: str, return_debug: bool = False) -> Union[Optional[CleaningDates], Tuple[Optional[CleaningDates], Dict[str, Any]]]:
        hb = await self.get_houses_by_address(address, limit=1, return_debug=True)
        houses, hmeta = hb if isinstance(hb, tuple) else (hb, {})
        meta = {"houses": hmeta}
        if not houses:
            return (None, meta) if return_debug else None
        return (houses[0].cleaning_dates, meta) if return_debug else houses[0].cleaning_dates

    async def get_finance_aggregate(self, db: Any, date_from: Optional[str] = None, date_to: Optional[str] = None, return_debug: bool = False) -> Union[Dict[str, Any], Tuple[Dict[str, Any], Dict[str, Any]]]:
        cache_key = f"fin:{date_from}:{date_to}"
        cached = self.finance_cache.get(cache_key)
        meta = {"cache": "hit" if cached is not None else "miss", "cache_key": cache_key}
        if cached is not None:
            return (cached, meta) if return_debug else cached
        try:
            from sqlalchemy import text
            if hasattr(db, "execute"):
                q = text(
                    """
                    SELECT 
                        COUNT(*) as total_transactions,
                        SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END) as total_income,
                        SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END) as total_expense
                    FROM financial_transactions
                    WHERE (:date_from IS NULL OR date >= :date_from)
                      AND (:date_to IS NULL OR date <= :date_to)
                    """
                )
                res = await db.execute(q, {"date_from": date_from, "date_to": date_to})
                row = res.first()
                out = {
                    "transactions": int(row[0] or 0) if row else 0,
                    "income": float(row[1] or 0) if row else 0.0,
                    "expense": float(row[2] or 0) if row else 0.0,
                }
            else:
                out = {"transactions": 0, "income": 0.0, "expense": 0.0}
            self.finance_cache.set(cache_key, out)
            return (out, meta) if return_debug else out
        except Exception as e:
            logger.error(f"BrainStore.get_finance_aggregate error: {e}")
            out = {"transactions": 0, "income": 0.0, "expense": 0.0}
            return (out, meta) if return_debug else out