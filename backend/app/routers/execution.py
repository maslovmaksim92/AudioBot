"""
Управленческий дашборд выполнения уборок.
Сопоставляет план (cleaning_schedule домов) с фактом (cleaning_photos = фото отправлено).
Статусы: done (выполнено), pending (ожидается), overdue (просрочено).
"""
import logging
from datetime import date, datetime
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, text as sa_text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config.database import get_db
from backend.app.models.house import House

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/execution", tags=["execution"])

RU_MONTHS = {1: "january", 2: "february", 3: "march", 4: "april", 5: "may", 6: "june",
             7: "july", 8: "august", 9: "september", 10: "october", 11: "november", 12: "december"}


def _month_key(year: int, month: int) -> str:
    return f"{RU_MONTHS[month]}_{year}"


def _planned_dates(house: House, year: int, month: int) -> List[Dict[str, str]]:
    sched = house.cleaning_schedule or {}
    return [i for i in (sched.get(_month_key(year, month)) or []) if i.get("date")]


async def _fact_map(db: AsyncSession, year: int, month: int) -> Dict[str, set]:
    """{house_id: {даты, по которым есть фотоотчёт}} за месяц."""
    res = await db.execute(sa_text("""
        SELECT house_id, cleaning_date
        FROM cleaning_photos
        WHERE EXTRACT(YEAR FROM cleaning_date) = :y
          AND EXTRACT(MONTH FROM cleaning_date) = :m
    """), {"y": year, "m": month})
    fact: Dict[str, set] = {}
    for hid, cdate in res.fetchall():
        fact.setdefault(str(hid), set()).add(cdate.isoformat() if hasattr(cdate, "isoformat") else str(cdate))
    return fact


def _status(planned_date: str, has_fact: bool, today: date) -> str:
    if has_fact:
        return "done"
    try:
        d = datetime.fromisoformat(planned_date).date()
    except Exception:
        return "pending"
    return "overdue" if d < today else "pending"


@router.get("/summary")
async def execution_summary(
    year: Optional[int] = Query(None),
    month: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Сводка выполнения за месяц: план / факт / просрочено + срезы по бригадам и УК."""
    today = date.today()
    year = year or today.year
    month = month or today.month

    houses = list((await db.execute(select(House))).scalars().all())
    fact = await _fact_map(db, year, month)

    total_planned = total_done = total_overdue = total_pending = 0
    by_brigade: Dict[str, Dict[str, int]] = {}
    by_uk: Dict[str, Dict[str, int]] = {}
    overdue_list: List[Dict[str, Any]] = []

    for h in houses:
        planned = _planned_dates(h, year, month)
        if not planned:
            continue
        brig = h.brigade_number or "—"
        uk = h.company_title or "—"
        by_brigade.setdefault(brig, {"planned": 0, "done": 0, "overdue": 0, "pending": 0})
        by_uk.setdefault(uk, {"planned": 0, "done": 0, "overdue": 0, "pending": 0})
        house_facts = fact.get(str(h.id), set())

        for it in planned:
            d = it["date"]
            st = _status(d, d in house_facts, today)
            total_planned += 1
            by_brigade[brig]["planned"] += 1
            by_uk[uk]["planned"] += 1
            if st == "done":
                total_done += 1; by_brigade[brig]["done"] += 1; by_uk[uk]["done"] += 1
            elif st == "overdue":
                total_overdue += 1; by_brigade[brig]["overdue"] += 1; by_uk[uk]["overdue"] += 1
                overdue_list.append({
                    "house_id": h.id, "address": h.address,
                    "brigade": brig, "uk": uk, "date": d,
                    "type": it.get("type", ""),
                })
            else:
                total_pending += 1; by_brigade[brig]["pending"] += 1; by_uk[uk]["pending"] += 1

    def _pct(done, planned):
        return round(done / planned * 100, 1) if planned else 0.0

    return {
        "period": {"year": year, "month": month},
        "totals": {
            "planned": total_planned,
            "done": total_done,
            "pending": total_pending,
            "overdue": total_overdue,
            "completion_pct": _pct(total_done, total_planned),
        },
        "by_brigade": [
            {"brigade": b, **v, "completion_pct": _pct(v["done"], v["planned"])}
            for b, v in sorted(by_brigade.items(), key=lambda x: x[0])
        ],
        "by_uk": [
            {"uk": u, **v, "completion_pct": _pct(v["done"], v["planned"])}
            for u, v in sorted(by_uk.items(), key=lambda x: x[0])
        ],
        "overdue": sorted(overdue_list, key=lambda x: x["date"]),
    }


@router.get("/recent")
async def execution_recent(limit: int = 20, db: AsyncSession = Depends(get_db)):
    """Лента последних фотоотчётов (факт выполнения в реальном времени)."""
    res = await db.execute(sa_text("""
        SELECT house_address, brigade_id, cleaning_date, photo_count, status, created_at
        FROM cleaning_photos
        ORDER BY created_at DESC
        LIMIT :lim
    """), {"lim": limit})
    out = []
    for addr, brig, cdate, cnt, status, created in res.fetchall():
        out.append({
            "address": addr,
            "brigade": brig or "—",
            "date": cdate.isoformat() if hasattr(cdate, "isoformat") else str(cdate),
            "photo_count": cnt,
            "status": status,
            "created_at": created.isoformat() if hasattr(created, "isoformat") else str(created),
        })
    return {"items": out}
