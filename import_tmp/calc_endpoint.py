p = '/opt/audiobot/backend/app/routers/cleaning.py'
s = open(p, encoding='utf-8').read()

anchor = '@router.get("/brigades")'
assert anchor in s

new_endpoint = '''@router.get("/brigade-calc")
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
        mm = _re.match(r"\\s*(\\d+)\\s*//\\s*([\\d.,]+)", str(t))
        if not mm:
            return None, None
        try:
            return int(mm.group(1)), float(mm.group(2).replace(",", "."))
        except Exception:
            return None, None

    try:
        rows = (await db.execute(select(House).where(House.brigade_number.isnot(None)))).scalars().all()
    except Exception as e:
        logger.error(f"[brigade-calc] DB read: {e}")
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
        # стоимость по тарифу: уборок_в_мес * подъезды * цена_за_подъезд
        cnt, price = _parse_tariff(h.tariff)
        if cnt is not None and price is not None:
            a["tariff_known"] += 1
            ent = h.entrances_count or 0
            a["revenue"] += cnt * ent * price

    brigades = []
    for b in sorted(agg.keys(), key=lambda x: (len(x), x)):
        a = agg[b]
        a["fact_cleanings"] = fact_by_brigade.get(b, 0)
        a["revenue"] = round(a["revenue"], 2)
        # средние нагрузки
        a["avg_entrances_per_house"] = round(a["entrances"] / a["houses"], 1) if a["houses"] else 0
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


@router.get("/brigades")'''

s = s.replace(anchor, new_endpoint, 1)
open(p, 'w', encoding='utf-8').write(s)
print("OK: эндпоинт /brigade-calc добавлен")
