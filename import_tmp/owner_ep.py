p = '/opt/audiobot/backend/app/routers/cleaning.py'
s = open(p, encoding='utf-8').read()

anchor = '@router.get("/brigades")'
assert anchor in s

ep = '''@router.get("/owner-overview")
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
        logger.error(f"[owner] DB: {e}")
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


@router.get("/brigades")'''

s = s.replace(anchor, ep, 1)
open(p, 'w', encoding='utf-8').write(s)
print("OK: эндпоинт /owner-overview добавлен")
