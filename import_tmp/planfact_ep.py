p = '/opt/audiobot/backend/app/routers/cleaning.py'
s = open(p, encoding='utf-8').read()

anchor = '@router.get("/brigades")'
assert anchor in s

ep = '''@router.get("/plan-fact")
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
                frows = await conn.fetch(
                    "SELECT DISTINCT house_id FROM cleaning_photos WHERE cleaning_date=$1", date)
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


@router.get("/brigades")'''

s = s.replace(anchor, ep, 1)
open(p, 'w', encoding='utf-8').write(s)
print("OK: эндпоинт /plan-fact добавлен")
