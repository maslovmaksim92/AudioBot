p = '/opt/audiobot/backend/app/routers/cleaning.py'
s = open(p, encoding='utf-8').read()

anchor = '@router.get("/brigades")'
assert anchor in s

new_ep = '''@router.get("/daily-calc")
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

    def _tariff_price(t):
        # "4 // 110" -> цена за подъезд = 110.0
        if not t:
            return None
        mm = _re.match(r"\\s*(\\d+)\\s*//\\s*([\\d.,]+)", str(t))
        if not mm:
            return None
        try:
            return float(mm.group(2).replace(",", "."))
        except Exception:
            return None

    try:
        rows = (await db.execute(select(House))).scalars().all()
    except Exception as e:
        logger.error(f"[daily-calc] DB: {e}")
        return {"month": month, "days": [], "totals": {}, "error": str(e)}

    # day -> агрегаты
    days = {}
    for h in rows:
        sched = h.cleaning_schedule or {}
        if not isinstance(sched, dict):
            continue
        arr = sched.get(sched_key) or []
        if not arr:
            continue
        ent = h.entrances_count or 0
        flr = h.floors_count or 0
        price = _tariff_price(h.tariff)
        money = (price * ent) if (price is not None and ent) else 0.0
        for it in arr:
            if not isinstance(it, dict):
                continue
            d = it.get("date")
            if not d:
                continue
            day = days.setdefault(d, {
                "date": d, "cleanings": 0, "houses": 0,
                "entrances": 0, "floors": 0, "money": 0.0,
                "brigades": {},
            })
            day["cleanings"] += 1
            day["houses"] += 1
            day["entrances"] += ent
            day["floors"] += flr
            day["money"] += money
            b = str(h.brigade_number) if h.brigade_number else "—"
            bb = day["brigades"].setdefault(b, {"cleanings": 0, "entrances": 0, "floors": 0, "money": 0.0})
            bb["cleanings"] += 1
            bb["entrances"] += ent
            bb["floors"] += flr
            bb["money"] += money

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


@router.get("/brigades")'''

s = s.replace(anchor, new_ep, 1)
open(p, 'w', encoding='utf-8').write(s)
print("OK: эндпоинт /daily-calc добавлен")
