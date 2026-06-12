p = '/opt/audiobot/backend/app/routers/cleaning.py'
s = open(p, encoding='utf-8').read()

# Заменяем тело расчёта денег в /daily-calc на корректное: OPPORTUNITY / уборок_в_месяце
OLD = '''    def _tariff_price(t):
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
            bb["money"] += money'''

NEW = '''    try:
        rows = (await db.execute(select(House))).scalars().all()
    except Exception as e:
        logger.error(f"[daily-calc] DB: {e}")
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
            bb["money"] += per_clean'''

assert OLD in s, "блок расчёта /daily-calc не найден"
s = s.replace(OLD, NEW)
open(p, 'w', encoding='utf-8').write(s)
print("OK: деньги в /daily-calc = OPPORTUNITY / уборок в месяце")
