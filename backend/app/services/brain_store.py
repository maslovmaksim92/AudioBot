"""
BrainStore (Stage 2): Aggregation + Indexing
- Aggregates data from Bitrix24 and DB into unified DTOs
- Provides fast, cached lookups by normalized address
- Prepares data for resolvers (Stage 3)

Notes:
- Uses brain.py DTOs and normalization helpers
- Depends on existing bitrix24_service for remote data access
- DB access kept optional (dependency-injected AsyncSession)
"""
from __future__ import annotations

from dataclasses import asdict
from typing import Any, Dict, List, Optional, Tuple
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
        # Short TTLs to keep answers fresh while avoiding bursty calls
        self.addr_cache = TTLCache(180)  # 3 minutes: houses by address
        self.contact_cache = TTLCache(300)  # 5 minutes: elder contacts by address
        self.finance_cache = TTLCache(180)  # 3 minutes: finance aggregates

    # ------------- Mapping helpers -------------
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

    # ------------- Public API -------------
    async def get_houses_by_address(self, address: str, limit: int = 3) -> List[HouseDTO]:
        addr_norm = normalize_address(address)
        cache_key = f"addr:{addr_norm}:{limit}"
        cached = self.addr_cache.get(cache_key)
        if cached is not None:
            return cached
        try:
            data = await bitrix24_service.list_houses(address=address, limit=limit)
            houses = (data or {}).get("houses") or []
            result = [self._map_house_dict(h) for h in houses[:limit]]
            self.addr_cache.set(cache_key, result)
            logger.info(f"BrainStore: cached houses for {addr_norm}: {len(result)}")
            return result
        except Exception as e:
            logger.error(f"BrainStore.get_houses_by_address error: {e}")
            return []

    async def get_elder_contact_by_address(self, address: str) -> Optional[ElderContact]:
        addr_norm = normalize_address(address)
        cache_key = f"elder:{addr_norm}"
        cached = self.contact_cache.get(cache_key)
        if cached is not None:
            return cached
        try:
            houses = await self.get_houses_by_address(address, limit=1)
            if not houses:
                return None
            h = houses[0]
            # Try existing elder in house record first
            if h.elder_contact and not h.elder_contact.is_empty():
                self.contact_cache.set(cache_key, h.elder_contact)
                return h.elder_contact
            # Else fetch deal details for richer contact info
            details = await bitrix24_service.get_deal_details(h.id)
            contact_dict = (details or {}).get("elder_contact") or {}
            phones = contact_dict.get("phones") or []
            emails = contact_dict.get("emails") or []
            name = contact_dict.get("name") or ""
            # fallback to company phones/emails
            company = (details or {}).get("company") or {}
            if not phones:
                phones = company.get("phones") or []
            if not emails:
                emails = company.get("emails") or []
            elder = ElderContact(name=str(name or ""), phones=[str(p) for p in phones], emails=[str(em) for em in emails])
            self.contact_cache.set(cache_key, elder)
            return elder
        except Exception as e:
            logger.error(f"BrainStore.get_elder_contact_by_address error: {e}")
            return None

    async def get_cleaning_for_month_by_address(self, address: str, month_key: str) -> Optional[CleaningDates]:
        houses = await self.get_houses_by_address(address, limit=1)
        if not houses:
            return None
        return houses[0].cleaning_dates

    # ------------- Finance (optional DB) -------------
    async def get_finance_aggregate(self, db: Any, date_from: Optional[str] = None, date_to: Optional[str] = None) -> Dict[str, Any]:
        """Compute basic aggregates over financial_transactions table using injected DB session/connection.
        db: Async DB session/connection (e.g., AsyncSession or asyncpg connection wrapper)
        """
        cache_key = f"fin:{date_from}:{date_to}"
        cached = self.finance_cache.get(cache_key)
        if cached is not None:
            return cached
        try:
            # Support SQLAlchemy AsyncSession if available
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
                # Unknown db type; return empty aggregate
                out = {"transactions": 0, "income": 0.0, "expense": 0.0}
            self.finance_cache.set(cache_key, out)
            return out
        except Exception as e:
            logger.error(f"BrainStore.get_finance_aggregate error: {e}")
            return {"transactions": 0, "income": 0.0, "expense": 0.0}


# Singleton
brain_store = BrainStore()