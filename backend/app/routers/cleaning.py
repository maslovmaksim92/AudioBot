"""
Cleaning router: Bitrix listing + brigade filtering (assigned) + details
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import logging

from backend.app.config.database import get_db
from backend.app.services.bitrix24_service import bitrix24_service
from backend.app.utils.auth_deps import get_current_user_optional, CurrentUser

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/cleaning", tags=["Cleaning"])

@router.get("/houses")
async def get_cleaning_houses(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=1000),
    address: Optional[str] = None,
    brigade: Optional[str] = None,
    status: Optional[str] = None,
    management_company: Optional[str] = None,
    cleaning_date: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    month: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current: Optional[CurrentUser] = Depends(get_current_user_optional)
):
    # ИСТОЧНИК ПРАВДЫ — БД houses (автономно от Bitrix; Bitrix = фоновый синк).
    # Та же таблица, что питает MAX-бот, поэтому веб и бот всегда согласованы.
    try:
        from sqlalchemy import select, func
        from backend.app.models.house import House
        from backend.app.routers._houses_front_mapper import house_to_front

        effective_brigade = brigade
        if current and current.is_brigade() and not brigade:
            if current.brigade_number:
                effective_brigade = current.brigade_number

        base = select(House)
        if effective_brigade:
            base = base.where(House.brigade_number == str(effective_brigade))
        if management_company:
            base = base.where(House.company_title == management_company)
        if address:
            like = f"%{address.lower()}%"
            base = base.where(func.lower(House.address).like(like))

        total = (await db.execute(select(func.count()).select_from(base.subquery()))).scalar() or 0
        rows = (await db.execute(
            base.order_by(House.address).offset((page - 1) * limit).limit(limit)
        )).scalars().all()

        # month (YYYY-MM) -> ключ графика month_key (may_2026)
        _MEN = {1:"january",2:"february",3:"march",4:"april",5:"may",6:"june",
                7:"july",8:"august",9:"september",10:"october",11:"november",12:"december"}
        month_key = None
        if month:
            try:
                yy, mm = month.split("-"); month_key = f"{_MEN[int(mm)]}_{int(yy)}"
            except Exception:
                month_key = None

        houses = [house_to_front(h, month_key=month_key) for h in rows]

        # подтянуть статус актов за выбранный месяц
        try:
            from backend.app.config.database import get_db_pool
            pool = await get_db_pool()
            act_month = month or None
            if pool and act_month and houses:
                ids = [h["id"] for h in houses]
                async with pool.acquire() as conn:
                    arows = await conn.fetch(
                        "SELECT house_id, act_signed_date, act_photo_count, bitrix_status "
                        "FROM house_acts WHERE act_month=$1 AND house_id = ANY($2::text[])",
                        act_month, ids)
                    acts = {str(a["house_id"]): a for a in arows}
                for h in houses:
                    a = acts.get(h["id"])
                    h["act_signed"] = bool(a)
                    h["act_photo_count"] = (a["act_photo_count"] if a else 0)
                    h["act_status"] = (a["bitrix_status"] if a else None)
            else:
                for h in houses:
                    h["act_signed"] = False
        except Exception as _e:
            logger.warning(f"[cleaning] acts join: {_e}")
            for h in houses:
                h.setdefault("act_signed", False)

        if cleaning_date or date_from or date_to:
            def _match(h):
                alld = []
                for v in (h.get("cleaning_dates") or {}).values():
                    alld += (v.get("dates") or [])
                if cleaning_date and cleaning_date not in alld:
                    return False
                if date_from and not any(d >= date_from for d in alld):
                    return False
                if date_to and not any(d <= date_to for d in alld):
                    return False
                return True
            houses = [h for h in houses if _match(h)]
            total = len(houses)

        if total > 0 or address or effective_brigade or management_company:
            return {
                "houses": houses, "total": total, "page": page, "limit": limit,
                "pages": (total + limit - 1) // limit if total > 0 else 0,
                "source": "db",
            }
        logger.warning("[cleaning] houses table empty, fallback to Bitrix")
        return await bitrix24_service.list_houses(
            brigade=effective_brigade, status=status,
            management_company=management_company, cleaning_date=cleaning_date,
            date_from=date_from, date_to=date_to, page=page, limit=limit,
        )
    except Exception as e:
        logger.exception(f"[cleaning] DB read failed, fallback to Bitrix: {e}")
        try:
            return await bitrix24_service.list_houses(
                brigade=brigade, status=status, management_company=management_company,
                cleaning_date=cleaning_date, date_from=date_from, date_to=date_to,
                page=page, limit=limit,
            )
        except Exception as e2:
            logger.exception(f"[cleaning] Bitrix fallback failed: {e2}")
            return {"houses": [], "total": 0, "page": 1, "limit": limit, "pages": 0, "source": "error"}

@router.get("/filters")
async def get_cleaning_filters(db: AsyncSession = Depends(get_db)):
    statuses = [{"id": "NEW", "name": "Новая"}, {"id": "WON", "name": "Закрыта"}]
    # Бригады и УК — из БД houses (автономно от Bitrix)
    try:
        from sqlalchemy import select, distinct
        from backend.app.models.house import House

        brig_rows = (await db.execute(
            select(distinct(House.brigade_number)).where(House.brigade_number.isnot(None))
        )).scalars().all()
        # сортировка: по числовому значению, потом строкой
        def _key(b):
            try:
                return (0, int(b))
            except Exception:
                return (1, str(b))
        brigades = [
            {"id": str(b), "name": f"{b} бригада"}
            for b in sorted([b for b in brig_rows if str(b).strip()], key=_key)
        ]
        companies = (await db.execute(
            select(distinct(House.company_title)).where(House.company_title.isnot(None))
        )).scalars().all()
        companies = sorted([c for c in companies if str(c).strip()])
        if brigades:
            return {"brigades": brigades, "statuses": statuses,
                    "companies": [{"id": c, "name": c} for c in companies], "source": "db"}
    except Exception as e:
        logger.exception(f"[cleaning] filters DB read failed: {e}")
    # fallback на Bitrix
    try:
        brigades = await bitrix24_service.get_brigade_options()
        return {"brigades": brigades, "statuses": statuses}
    except Exception as e:
        logger.exception(f"Error getting filters: {e}")
        return {"brigades": [], "statuses": statuses}

@router.get("/house/{house_id}/details")
async def get_house_details(house_id: str, db: AsyncSession = Depends(get_db)):
    # Сначала БД (автономно), затем Bitrix как fallback
    try:
        from sqlalchemy import select
        from backend.app.models.house import House
        from backend.app.routers._houses_front_mapper import house_to_details

        row = (await db.execute(select(House).where(House.id == str(house_id)))).scalar_one_or_none()
        if row is None:
            row = (await db.execute(select(House).where(House.bitrix_id == str(house_id)))).scalar_one_or_none()
        if row is not None:
            return {"house": house_to_details(row), "source": "db"}
    except Exception as e:
        logger.exception(f"[cleaning] details DB read failed: {e}")
    try:
        details = await bitrix24_service.get_deal_details(house_id)
        if details:
            return {"house": details, "source": "bitrix"}
        return {"error": "Дом не найден"}
    except Exception as e:
        logger.exception(f"Error getting house details: {e}")
        return {"error": str(e)}

@router.post("/sync")
async def sync_houses_from_bitrix24(db: AsyncSession = Depends(get_db)):
    try:
        result = await bitrix24_service.sync_houses(db)
        return {"success": True, **result}
    except Exception as e:
        logger.exception(f"Error syncing from Bitrix24: {e}")
        return {"success": False, "error": str(e)}

@router.get("/brigade-calc")
async def get_brigade_calc(month: str = None, db: AsyncSession = Depends(get_db)):
    """
    Побригадные расчёты для вкладки "Расчёты".
    Источник — БД houses (план/график) + cleaning_photos (факт).
    month: YYYY-MM (по умолчанию — текущий). Уборки по графику берём за этот месяц.
    Возвращает по каждой бригаде: дома, подъезды, этажи, квартиры,
    уборок по графику (план), уборок по факту (фото), стоимость по тарифу.
    """
    import re as _re
    from datetime import datetime as _dt
    from sqlalchemy import select
    from backend.app.models.house import House

    if not month:
        now = _dt.now()
        month = f"{now.year}-{now.month:02d}"
    # ключ графика вида may_2026
    _MONTHS_EN = {1:"january",2:"february",3:"march",4:"april",5:"may",6:"june",
                  7:"july",8:"august",9:"september",10:"october",11:"november",12:"december"}
    try:
        y, m = month.split("-")
        sched_key = f"{_MONTHS_EN[int(m)]}_{int(y)}"
    except Exception:
        sched_key = None

    def _parse_tariff(t):
        # "4 // 110" -> (уборок_в_мес=4, цена=110.0); иначе (None, None)
        if not t:
            return None, None
        mm = _re.match(r"\s*(\d+)\s*//\s*([\d.,]+)", str(t))
        if not mm:
            return None, None
        try:
            return int(mm.group(1)), float(mm.group(2).replace(",", "."))
        except Exception:
            return None, None

    try:
        rows = (await db.execute(select(House).where(House.brigade_number.isnot(None)))).scalars().all()
    except Exception as e:
        logger.exception(f"[brigade-calc] DB read: {e}")
        return {"month": month, "brigades": [], "totals": {}, "error": str(e)}

    # факт уборок за месяц (из cleaning_photos) по бригадам
    fact_by_brigade = {}
    try:
        from backend.app.config.database import get_db_pool
        pool = await get_db_pool()
        if pool:
            async with pool.acquire() as conn:
                frows = await conn.fetch(
                    "SELECT brigade_id, COUNT(*) AS c FROM cleaning_photos "
                    "WHERE TO_CHAR(cleaning_date,'YYYY-MM')=$1 GROUP BY brigade_id", month)
                for fr in frows:
                    fact_by_brigade[str(fr["brigade_id"])] = int(fr["c"])
    except Exception as e:
        logger.warning(f"[brigade-calc] факт уборок не получен: {e}")

    agg = {}
    for h in rows:
        b = str(h.brigade_number)
        a = agg.setdefault(b, {
            "brigade": b, "houses": 0, "entrances": 0, "floors": 0, "apartments": 0,
            "plan_cleanings": 0, "revenue": 0.0, "tariff_known": 0,
        })
        a["houses"] += 1
        a["entrances"] += (h.entrances_count or 0)
        a["floors"] += (h.floors_count or 0)
        a["apartments"] += (h.apartments_count or 0)
        # уборок по графику за месяц
        sched = h.cleaning_schedule or {}
        n_clean = 0
        if sched_key and isinstance(sched, dict):
            arr = sched.get(sched_key) or []
            n_clean = len([x for x in arr if isinstance(x, dict) and x.get("date")])
        a["plan_cleanings"] += n_clean
        # выручка = месячная стоимость дома (amount_monthly из Bitrix OPPORTUNITY)
        amount = float(getattr(h, "amount_monthly", None) or 0)
        if amount:
            a["tariff_known"] += 1
            a["revenue"] += amount

    brigades = []
    for b in sorted(agg.keys(), key=lambda x: (len(x), x)):
        a = agg[b]
        a["fact_cleanings"] = fact_by_brigade.get(b, 0)
        a["revenue"] = round(a["revenue"], 2)
        # средние нагрузки
        a["avg_entrances_per_house"] = round(a["entrances"] / a["houses"], 1) if a["houses"] else 0
        a["avg_floors_per_house"] = round(a["floors"] / a["houses"], 1) if a["houses"] else 0
        a["revenue_per_house"] = round(a["revenue"] / a["houses"], 0) if a["houses"] else 0
        a["revenue_per_entrance"] = round(a["revenue"] / a["entrances"], 0) if a["entrances"] else 0
        a["completion_pct"] = round(a["fact_cleanings"] / a["plan_cleanings"] * 100, 1) if a["plan_cleanings"] else 0
        brigades.append(a)

    totals = {
        "houses": sum(a["houses"] for a in brigades),
        "entrances": sum(a["entrances"] for a in brigades),
        "floors": sum(a["floors"] for a in brigades),
        "apartments": sum(a["apartments"] for a in brigades),
        "plan_cleanings": sum(a["plan_cleanings"] for a in brigades),
        "fact_cleanings": sum(a["fact_cleanings"] for a in brigades),
        "revenue": round(sum(a["revenue"] for a in brigades), 2),
    }
    return {"month": month, "sched_key": sched_key, "brigades": brigades, "totals": totals, "source": "db"}


@router.get("/daily-calc")
async def get_daily_calc(month: str = None, db: AsyncSession = Depends(get_db)):
    """
    Расчёты ПО ДНЯМ за месяц: на каждый день уборки —
    уборок, домов, подъездов, этажей, деньги (по тарифу: цена_за_подъезд * подъезды).
    Деньги начисляются по факту даты уборки (за каждый выезд).
    """
    import re as _re
    from datetime import datetime as _dt
    from sqlalchemy import select
    from backend.app.models.house import House

    if not month:
        now = _dt.now()
        month = f"{now.year}-{now.month:02d}"
    _MONTHS_EN = {1:"january",2:"february",3:"march",4:"april",5:"may",6:"june",
                  7:"july",8:"august",9:"september",10:"october",11:"november",12:"december"}
    try:
        y, m = month.split("-")
        sched_key = f"{_MONTHS_EN[int(m)]}_{int(y)}"
    except Exception:
        return {"month": month, "days": [], "totals": {}, "error": "bad month"}

    try:
        rows = (await db.execute(select(House))).scalars().all()
    except Exception as e:
        logger.exception(f"[daily-calc] DB: {e}")
        return {"month": month, "days": [], "totals": {}, "error": str(e)}

    # day -> агрегаты
    # Деньги: месячная стоимость дома (amount_monthly, из Bitrix OPPORTUNITY)
    # распределяется поровну по числу уборок дома в этом месяце.
    days = {}
    for h in rows:
        sched = h.cleaning_schedule or {}
        if not isinstance(sched, dict):
            continue
        arr = [it for it in (sched.get(sched_key) or []) if isinstance(it, dict) and it.get("date")]
        if not arr:
            continue
        ent = h.entrances_count or 0
        flr = h.floors_count or 0
        amount = float(getattr(h, "amount_monthly", None) or 0)
        n_clean = len(arr)
        per_clean = (amount / n_clean) if n_clean else 0.0
        for it in arr:
            d = it.get("date")
            day = days.setdefault(d, {
                "date": d, "cleanings": 0, "houses": 0,
                "entrances": 0, "floors": 0, "money": 0.0,
                "brigades": {},
            })
            day["cleanings"] += 1
            day["houses"] += 1
            day["entrances"] += ent
            day["floors"] += flr
            day["money"] += per_clean
            b = str(h.brigade_number) if h.brigade_number else "—"
            bb = day["brigades"].setdefault(b, {"cleanings": 0, "entrances": 0, "floors": 0, "money": 0.0})
            bb["cleanings"] += 1
            bb["entrances"] += ent
            bb["floors"] += flr
            bb["money"] += per_clean

    day_list = []
    for d in sorted(days.keys()):
        x = days[d]
        x["money"] = round(x["money"], 2)
        # бригады -> отсортированный список
        x["brigades"] = [
            {"brigade": b, **{k: (round(v, 2) if k == "money" else v) for k, v in vals.items()}}
            for b, vals in sorted(x["brigades"].items(), key=lambda kv: (len(kv[0]), kv[0]))
        ]
        # день недели (рус.)
        try:
            wd = _dt.strptime(d, "%Y-%m-%d").weekday()
            x["weekday"] = ["Пн","Вт","Ср","Чт","Пт","Сб","Вс"][wd]
        except Exception:
            x["weekday"] = ""
        day_list.append(x)

    totals = {
        "days": len(day_list),
        "cleanings": sum(x["cleanings"] for x in day_list),
        "entrances": sum(x["entrances"] for x in day_list),
        "floors": sum(x["floors"] for x in day_list),
        "money": round(sum(x["money"] for x in day_list), 2),
    }
    return {"month": month, "sched_key": sched_key, "days": day_list, "totals": totals, "source": "db"}


@router.get("/owner-overview")
async def owner_overview(month: str = None, db: AsyncSession = Depends(get_db)):
    """
    Сводка для собственника/руководителя: деньги, дома, бригады, выполнение, риски.
    Всё в одном ответе для cockpit-дашборда.
    """
    import re as _re
    from datetime import datetime as _dt, date as _date
    from sqlalchemy import select
    from backend.app.models.house import House

    if not month:
        now = _dt.now()
        month = f"{now.year}-{now.month:02d}"
    _M = {1:"january",2:"february",3:"march",4:"april",5:"may",6:"june",7:"july",
          8:"august",9:"september",10:"october",11:"november",12:"december"}
    try:
        y, m = month.split("-"); sched_key = f"{_M[int(m)]}_{int(y)}"
    except Exception:
        return {"month": month, "error": "bad month"}

    try:
        rows = (await db.execute(select(House))).scalars().all()
    except Exception as e:
        logger.exception(f"[owner] DB: {e}")
        return {"month": month, "error": str(e)}

    total_houses = len(rows)
    total_revenue = 0.0
    total_entrances = total_floors = total_apartments = 0
    plan_cleanings = 0
    by_brigade = {}
    by_company = {}
    no_brigade = no_amount = no_schedule = 0
    days_map = {}

    for h in rows:
        amount = float(getattr(h, "amount_monthly", None) or 0)
        ent = h.entrances_count or 0
        flr = h.floors_count or 0
        apt = h.apartments_count or 0
        total_revenue += amount
        total_entrances += ent
        total_floors += flr
        total_apartments += apt
        if not amount: no_amount += 1

        sched = h.cleaning_schedule or {}
        arr = [it for it in (sched.get(sched_key) or []) if isinstance(it, dict) and it.get("date")]
        if not arr: no_schedule += 1
        plan_cleanings += len(arr)
        per = (amount/len(arr)) if arr else 0.0
        for it in arr:
            d = it["date"]
            dm = days_map.setdefault(d, {"date": d, "cleanings": 0, "money": 0.0})
            dm["cleanings"] += 1
            dm["money"] += per

        b = str(h.brigade_number) if h.brigade_number else None
        if not b: no_brigade += 1
        bk = b or "—"
        bb = by_brigade.setdefault(bk, {"brigade": bk, "houses": 0, "entrances": 0,
                                        "cleanings": 0, "revenue": 0.0})
        bb["houses"] += 1; bb["entrances"] += ent
        bb["cleanings"] += len(arr); bb["revenue"] += amount

        comp = (h.company_title or "Без УК").strip() or "Без УК"
        cc = by_company.setdefault(comp, {"company": comp, "houses": 0, "revenue": 0.0})
        cc["houses"] += 1; cc["revenue"] += amount

    # топ-УК по выручке
    companies = sorted(by_company.values(), key=lambda x: -x["revenue"])
    for c in companies: c["revenue"] = round(c["revenue"], 2)
    brigades = sorted(by_brigade.values(), key=lambda x: (len(x["brigade"]), x["brigade"]))
    for b in brigades:
        b["revenue"] = round(b["revenue"], 2)
        b["avg_revenue_per_house"] = round(b["revenue"]/b["houses"], 0) if b["houses"] else 0

    # динамика по дням (для графика)
    daily = []
    for d in sorted(days_map.keys()):
        x = days_map[d]; x["money"] = round(x["money"], 2)
        try:
            wd = _dt.strptime(d, "%Y-%m-%d").weekday()
            x["weekday"] = ["Пн","Вт","Ср","Чт","Пт","Сб","Вс"][wd]
            x["day"] = int(d.split("-")[2])
        except Exception:
            x["weekday"] = ""; x["day"] = 0
        daily.append(x)

    # факт уборок за месяц (из фото-отчётов)
    fact = 0
    try:
        from backend.app.config.database import get_db_pool
        pool = await get_db_pool()
        if pool:
            async with pool.acquire() as conn:
                fact = await conn.fetchval(
                    "SELECT COUNT(*) FROM cleaning_photos WHERE TO_CHAR(cleaning_date,'YYYY-MM')=$1", month) or 0
    except Exception as e:
        logger.warning(f"[owner] факт: {e}")

    completion = round((fact/plan_cleanings*100), 1) if plan_cleanings else 0

    return {
        "month": month,
        "kpi": {
            "total_houses": total_houses,
            "total_revenue": round(total_revenue, 2),
            "avg_check": round(total_revenue/total_houses, 0) if total_houses else 0,
            "total_entrances": total_entrances,
            "total_floors": total_floors,
            "total_apartments": total_apartments,
            "plan_cleanings": plan_cleanings,
            "fact_cleanings": fact,
            "completion_pct": completion,
            "brigades_count": len([b for b in brigades if b["brigade"] != "—"]),
            "companies_count": len([c for c in companies if c["company"] != "Без УК"]),
        },
        "risks": {
            "no_brigade": no_brigade,
            "no_amount": no_amount,
            "no_schedule": no_schedule,
        },
        "brigades": brigades,
        "top_companies": companies[:8],
        "daily": daily,
        "source": "db",
    }


@router.get("/plan-fact")
async def plan_fact(date: str = None, db: AsyncSession = Depends(get_db)):
    """
    План/факт за день: какие дома должны убираться (по графику) и кто отчитался (фото).
    date: YYYY-MM-DD (по умолчанию сегодня). Группировка по бригадам.
    """
    from datetime import datetime as _dt, date as _date
    from sqlalchemy import select
    from backend.app.models.house import House

    if not date:
        date = _date.today().isoformat()
    _M = {1:"january",2:"february",3:"march",4:"april",5:"may",6:"june",7:"july",
          8:"august",9:"september",10:"october",11:"november",12:"december"}
    try:
        y, mo, d = date.split("-")
        sched_key = f"{_M[int(mo)]}_{int(y)}"
    except Exception:
        return {"date": date, "error": "bad date"}

    # 1) План: дома, у которых в графике есть эта дата
    try:
        rows = (await db.execute(select(House))).scalars().all()
    except Exception as e:
        logger.exception(f"[plan-fact] DB: {e}")
        return {"date": date, "error": str(e)}

    planned = []  # дома, которые должны убираться сегодня
    for h in rows:
        sched = h.cleaning_schedule or {}
        if not isinstance(sched, dict):
            continue
        arr = sched.get(sched_key) or []
        if any(isinstance(it, dict) and it.get("date") == date for it in arr):
            planned.append(h)

    # 2) Факт: какие дома отчитались за эту дату
    fact_ids = set()
    try:
        from backend.app.config.database import get_db_pool
        pool = await get_db_pool()
        if pool:
            async with pool.acquire() as conn:
                from datetime import date as _d
                frows = await conn.fetch(
                    "SELECT DISTINCT house_id FROM cleaning_photos WHERE cleaning_date=$1", _d.fromisoformat(date))
                fact_ids = {str(r["house_id"]) for r in frows}
    except Exception as e:
        logger.warning(f"[plan-fact] факт: {e}")

    # 3) Группируем по бригадам
    brigades = {}
    done_list, pending_list = [], []
    for h in planned:
        b = str(h.brigade_number) if h.brigade_number else "—"
        bb = brigades.setdefault(b, {"brigade": b, "planned": 0, "done": 0, "pending": 0,
                                     "done_addr": [], "pending_addr": []})
        bb["planned"] += 1
        item = {"id": str(h.id), "address": h.address, "brigade": h.brigade_number}
        if str(h.id) in fact_ids:
            bb["done"] += 1
            bb["done_addr"].append(h.address)
            done_list.append(item)
        else:
            bb["pending"] += 1
            bb["pending_addr"].append(h.address)
            pending_list.append(item)

    brig_list = []
    for b in sorted(brigades.keys(), key=lambda x: (len(x), x)):
        bb = brigades[b]
        bb["completion_pct"] = round(bb["done"] / bb["planned"] * 100, 0) if bb["planned"] else 0
        brig_list.append(bb)

    total_plan = len(planned)
    total_done = len([h for h in planned if str(h.id) in fact_ids])
    try:
        wd = _dt.strptime(date, "%Y-%m-%d").weekday()
        weekday = ["Понедельник","Вторник","Среда","Четверг","Пятница","Суббота","Воскресенье"][wd]
    except Exception:
        weekday = ""

    return {
        "date": date,
        "weekday": weekday,
        "total_planned": total_plan,
        "total_done": total_done,
        "total_pending": total_plan - total_done,
        "completion_pct": round(total_done / total_plan * 100, 1) if total_plan else 0,
        "brigades": brig_list,
        "pending": pending_list,
        "done": done_list,
        "source": "db",
    }


@router.get("/brigades")
async def get_brigades_list():
    """Получить список всех бригад для выбора"""
    try:
        brigades = await bitrix24_service.get_all_brigades()
        return {"brigades": brigades}
    except Exception as e:
        logger.exception(f"Error getting brigades: {e}")
        return {"brigades": []}

@router.get("/cleaning-types")
async def get_cleaning_types():
    """Получить список типов уборки (enum)"""
    try:
        types = await bitrix24_service.get_cleaning_types()
        return {"types": types}
    except Exception as e:
        logger.exception(f"Error getting cleaning types: {e}")
        return {"types": []}

@router.get("/contacts")
async def get_contacts_list():
    """Получить список всех контактов для выбора"""
    try:
        contacts = await bitrix24_service.get_all_contacts()
        return {"contacts": contacts}
    except Exception as e:
        logger.exception(f"Error getting contacts: {e}")
        return {"contacts": []}

@router.get("/debug-enum/{field_code}")
async def debug_enum_field(field_code: str):
    """Отладка: получить enum значения для поля"""
    try:
        import httpx
        async with httpx.AsyncClient(timeout=httpx.Timeout(40.0)) as client:
            # Очищаем кеш для этого поля
            cache_key = f"enum:{field_code}"
            bitrix24_service.enum_cache.store.pop(cache_key, None)
            
            # Получаем заново
            enum_map = await bitrix24_service._get_enum_map(client, field_code)
            
            return {
                "field_code": field_code,
                "enum_map": enum_map,
                "count": len(enum_map)
            }
    except Exception as e:
        logger.exception(f"Error getting enum: {e}")
        return {"error": str(e)}

@router.get("/clear-cache")
async def clear_bitrix_cache():
    """Очистить весь кеш Bitrix24"""
    try:
        bitrix24_service.enum_cache.store.clear()
        bitrix24_service.company_cache.store.clear()
        bitrix24_service.user_cache.store.clear()
        bitrix24_service.deals_cache.store.clear()
        return {"success": True, "message": "Кеш очищен"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.put("/house/{house_id}")
async def update_house(house_id: str, data: dict):
    """Обновить данные дома в Bitrix24"""
    try:
        result = await bitrix24_service.update_deal(house_id, data)
        if result:
            return {"success": True, "house": result}
        return {"success": False, "error": "Не удалось обновить дом"}
    except Exception as e:
        logger.exception(f"Error updating house {house_id}: {e}")
        return {"success": False, "error": str(e)}

@router.get("/house/{house_id}/photo-history")
async def get_house_photo_history(
    house_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Получить историю фото уборок для конкретного дома
    Возвращает список всех уборок с фото, датами и ссылками на посты в TG
    """
    try:
        from app.config.database import get_db_pool
        
        db_pool = await get_db_pool()
        if not db_pool:
            logger.error("[cleaning] DB pool not available")
            return {"error": "Database connection error", "cleanings": []}
        
        async with db_pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT 
                    id,
                    house_id,
                    house_address,
                    brigade_id,
                    cleaning_date,
                    photo_file_ids,
                    photo_count,
                    ai_caption,
                    telegram_message_id,
                    telegram_chat_id,
                    telegram_post_url,
                    status,
                    sent_to_group_at,
                    created_at
                FROM cleaning_photos
                WHERE house_id = $1
                ORDER BY cleaning_date DESC
                """,
                house_id
            )
            
            cleanings = []
            for row in rows:
                cleanings.append({
                    "id": str(row['id']),
                    "house_id": row['house_id'],
                    "house_address": row['house_address'],
                    "brigade_id": row['brigade_id'],
                    "cleaning_date": row['cleaning_date'].isoformat() if row['cleaning_date'] else None,
                    "photo_file_ids": row['photo_file_ids'] or [],
                    "photo_count": row['photo_count'],
                    "ai_caption": row['ai_caption'],
                    "telegram_message_id": row['telegram_message_id'],
                    "telegram_chat_id": row['telegram_chat_id'],
                    "telegram_post_url": row['telegram_post_url'],
                    "status": row['status'],
                    "sent_to_group_at": row['sent_to_group_at'].isoformat() if row['sent_to_group_at'] else None,
                    "created_at": row['created_at'].isoformat() if row['created_at'] else None
                })
            
            logger.info(f"[cleaning] Found {len(cleanings)} cleanings for house {house_id}")
            return {"cleanings": cleanings}
            
    except Exception as e:
        logger.exception(f"[cleaning] Error getting photo history for house {house_id}: {e}")
        return {"error": str(e), "cleanings": []}

@router.post("/resend-photos")
async def resend_photos_to_telegram(data: dict):
    """
    Повторно отправить фото в Telegram группы
    """
    try:
        cleaning_id = data.get('cleaning_id')
        
        if not cleaning_id:
            return {"success": False, "error": "cleaning_id is required"}
        
        from app.config.database import get_db_pool
        import os
        
        db_pool = await get_db_pool()
        if not db_pool:
            return {"success": False, "error": "Database connection error"}
        
        # Получаем данные уборки
        async with db_pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT 
                    house_address,
                    photo_file_ids,
                    ai_caption
                FROM cleaning_photos
                WHERE id = $1
                """,
                cleaning_id
            )
            
            if not row:
                return {"success": False, "error": "Cleaning not found"}
            
            photo_file_ids = row['photo_file_ids'] or []
            caption = row['ai_caption']
            
            if not photo_file_ids:
                return {"success": False, "error": "No photos to send"}
            
            # Отправляем в группы
            from backend.app.services.telegram_cleaning_bot import send_photo, send_media_group
            
            target_chat_id = os.getenv('TELEGRAM_TARGET_CHAT_ID')
            report_chat_id = os.getenv('TELEGRAM_REPORT_CHAT_ID')
            
            sent_count = 0
            
            # Отправка в публичную группу
            if target_chat_id:
                if len(photo_file_ids) == 1:
                    result = await send_photo(target_chat_id, photo_file_ids[0], caption)
                else:
                    result = await send_media_group(target_chat_id, photo_file_ids, caption)
                
                if result and result.get('success'):
                    sent_count += 1
            
            # Отправка в отчетную группу
            if report_chat_id and report_chat_id != target_chat_id:
                if len(photo_file_ids) == 1:
                    result = await send_photo(report_chat_id, photo_file_ids[0], caption)
                else:
                    result = await send_media_group(report_chat_id, photo_file_ids, caption)
                
                if result and result.get('success'):
                    sent_count += 1
            
            return {
                "success": True,
                "sent_to_groups": sent_count,
                "message": f"Фото отправлено в {sent_count} группу(ы)"
            }
            
    except Exception as e:
        logger.exception(f"[cleaning] Error resending photos: {e}")
        return {"success": False, "error": str(e)}

@router.get("/missing-data-report")
async def get_missing_data_report(with_contacts: bool = False):
    """
    Генерирует CSV отчет по домам с недостающими данными
    Проверяет: address, management_company, entrances, floors, apartments, cleaning_schedule, elder_contact
    
    Параметры:
    - with_contacts: bool = False - загружать контакты старшего (медленно, ~10 минут)
    
    По умолчанию генерирует быстрый отчет без контактов (1-2 секунды)
    Для полного отчета: ?with_contacts=true
    """
    try:
        from fastapi.responses import StreamingResponse
        import io
        import csv
        import asyncio
        
        logger.info(f"[cleaning] Generating missing data report (with_contacts={with_contacts})...")
        
        # Загружаем ВСЕ дома из Bitrix24 (с учетом пагинации)
        all_houses = []
        page = 1
        page_limit = 50  # Bitrix24 лимит на страницу
        
        while True:
            logger.info(f"[cleaning] Loading page {page}...")
            data = await bitrix24_service.list_houses(page=page, limit=page_limit)
            houses = data.get('houses', [])
            
            if not houses:
                break
            
            all_houses.extend(houses)
            
            # Проверяем, есть ли еще страницы
            total_pages = data.get('pages', 1)
            if page >= total_pages:
                break
            
            page += 1
        
        logger.info(f"[cleaning] Loaded {len(all_houses)} houses for report")
        
        if with_contacts:
            logger.info("[cleaning] Loading elder contacts for each house (this may take 10+ minutes)...")
        
        # Проверяем каждый дом на недостающие данные
        missing_data_houses = []
        
        # Счетчик для логирования прогресса
        processed_count = 0
        
        for house in all_houses:
            processed_count += 1
            
            # Логируем прогресс каждые 50 домов (только если загружаем контакты)
            if with_contacts and processed_count % 50 == 0:
                logger.info(f"[cleaning] Progress: {processed_count}/{len(all_houses)} houses processed")
            
            missing_fields = []
            
            # Проверка адреса
            if not house.get('address') or len(house.get('address', '')) < 10:
                missing_fields.append('Адрес')
            
            # Проверка УК
            if not house.get('management_company') or house.get('management_company') == '':
                missing_fields.append('УК')
            
            # Проверка старшего/ответственного
            if not house.get('brigade_name') or house.get('brigade_name') in ['Бригада не назначена', '']:
                missing_fields.append('Бригада')
            
            # Проверка подъездов
            if not house.get('entrances') or house.get('entrances') == 0:
                missing_fields.append('Подъезды')
            
            # Проверка этажей
            if not house.get('floors') or house.get('floors') == 0:
                missing_fields.append('Этажи')
            
            # Проверка квартир
            if not house.get('apartments') or house.get('apartments') == 0:
                missing_fields.append('Квартиры')
            
            # Проверка графика уборки (октябрь и ноябрь)
            cleaning_dates = house.get('cleaning_dates', {})
            has_october = (cleaning_dates.get('october_1', {}).get('dates') or 
                          cleaning_dates.get('october_2', {}).get('dates'))
            has_november = (cleaning_dates.get('november_1', {}).get('dates') or 
                           cleaning_dates.get('november_2', {}).get('dates'))
            
            if not has_october and not has_november:
                missing_fields.append('График уборки')
            
            # ЗАГРУЖАЕМ ДЕТАЛИ ДОМА для получения контактов старшего (ТОЛЬКО если with_contacts=True)
            elder_name = 'Не указан'
            elder_phone = 'Не указан'
            elder_email = 'Не указан'
            
            if with_contacts:
                try:
                    house_details = await bitrix24_service.get_deal_details(house.get('id'))
                    if house_details:
                        elder_contact = house_details.get('elder_contact', {})
                        if elder_contact and isinstance(elder_contact, dict):
                            elder_name = elder_contact.get('name', 'Не указан')
                            phones = elder_contact.get('phones', [])
                            emails = elder_contact.get('emails', [])
                            elder_phone = phones[0] if phones else 'Не указан'
                            elder_email = emails[0] if emails else 'Не указан'
                        
                        # Проверка наличия контактов
                        if elder_name == 'Не указан' or not elder_name:
                            missing_fields.append('Старший (ФИО)')
                        if elder_phone == 'Не указан' or not elder_phone:
                            missing_fields.append('Старший (телефон)')
                except Exception as e:
                    logger.warning(f"[cleaning] Failed to load details for house {house.get('id')}: {e}")
                    missing_fields.append('Старший (ФИО)')
                    missing_fields.append('Старший (телефон)')
            else:
                # Без контактов просто отмечаем как недостающие
                missing_fields.append('Старший (ФИО)')
                missing_fields.append('Старший (телефон)')
            
            # Добавляем в отчет (всегда, не только если есть недостающие поля)
            # Это позволит видеть полную информацию по всем домам
            missing_data_houses.append({
                'id': house.get('id', ''),
                'address': house.get('address') or house.get('title', 'Не указан'),
                'management_company': house.get('management_company', 'Не указана'),
                'brigade_name': house.get('brigade_name', 'Не назначена'),
                'entrances': house.get('entrances', 0),
                'floors': house.get('floors', 0),
                'apartments': house.get('apartments', 0),
                'periodicity': house.get('periodicity', 'Не указана'),
                'elder_name': elder_name,
                'elder_phone': elder_phone,
                'elder_email': elder_email,
                'missing_fields': ', '.join(missing_fields) if missing_fields else 'Нет'
            })
        
        logger.info(f"[cleaning] Finished processing all {len(all_houses)} houses")
        
        logger.info(f"[cleaning] Found {len(missing_data_houses)} houses with missing data")
        
        # Создаем CSV с правильным разделителем для Excel
        output = io.StringIO()
        
        # Используем точку с запятой как разделитель для совместимости с Excel
        writer = csv.DictWriter(
            output, 
            fieldnames=[
                'ID', 'Адрес', 'УК', 'Бригада', 'Подъезды', 'Этажи', 
                'Квартиры', 'Периодичность', 'Старший (ФИО)', 'Старший (телефон)', 
                'Старший (email)', 'Недостающие поля'
            ],
            delimiter=';',  # Точка с запятой для Excel
            quoting=csv.QUOTE_MINIMAL
        )
        
        writer.writeheader()
        
        for house in missing_data_houses:
            writer.writerow({
                'ID': house['id'],
                'Адрес': house['address'],
                'УК': house['management_company'],
                'Бригада': house['brigade_name'],
                'Подъезды': house['entrances'],
                'Этажи': house['floors'],
                'Квартиры': house['apartments'],
                'Периодичность': house['periodicity'],
                'Старший (ФИО)': house['elder_name'],
                'Старший (телефон)': house['elder_phone'],
                'Старший (email)': house['elder_email'],
                'Недостающие поля': house['missing_fields']
            })
        
        # Возвращаем CSV как downloadable file
        output.seek(0)
        
        from datetime import datetime
        filename = f"missing_data_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode('utf-8-sig')),  # BOM для корректного отображения в Excel
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
        
    except Exception as e:
        logger.exception(f"[cleaning] Error generating report: {e}")
        return {"error": str(e), "houses_with_issues": []}