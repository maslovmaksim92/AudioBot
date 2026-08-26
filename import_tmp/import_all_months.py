#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Импорт графика уборок по ВСЕМ месяцам из Bitrix (категория 34) в cleaning_schedule.
Обновляет только дома, которые УЖЕ есть в БД (актуальные, с маем). Добавляет им остальные месяцы.
"""
import re, json, asyncio, datetime
import httpx, asyncpg

WH = "https://vas-dom.bitrix24.ru/rest/1/oeo7d2sabsjxia70/"
ENV = "/opt/audiobot/backend/.env"

# месяц -> список (поле_даты, поле_типа)
MONTH_FIELDS = {
    "october_2025":  [("UF_CRM_1741593004888","UF_CRM_1741593047994"), ("UF_CRM_1741593067418","UF_CRM_1741593115407")],
    "november_2025": [("UF_CRM_1741593156926","UF_CRM_1741593210242"), ("UF_CRM_1741593231558","UF_CRM_1762319871625")],
    "december_2025": [("UF_CRM_1762318428551","UF_CRM_1762318540952"), ("UF_CRM_1762423667826","UF_CRM_1762423723771")],
    "january_2026":  [("UF_CRM_1762425491572","UF_CRM_1762425599837"), ("UF_CRM_1762429244903","UF_CRM_1762429300919")],
    "february_2026": [("UF_CRM_1769065381093","UF_CRM_1769065500025"), ("UF_CRM_1769065391092","UF_CRM_1769065563889")],
    "march_2026":    [("UF_CRM_1769065592561","UF_CRM_1769065644299"), ("UF_CRM_1769065612297","UF_CRM_1769065764798")],
    "april_2026":    [("UF_CRM_1773294498515","UF_CRM_1773294627855"), ("UF_CRM_1773294698704","UF_CRM_1773294751122")],
    "may_2026":      [("UF_CRM_1773293797362","UF_CRM_1773293854012"), ("UF_CRM_1773293874331","UF_CRM_1773293930779")],
    "june_2026":     [("UF_CRM_1778649976403","UF_CRM_1778650027948"), ("UF_CRM_1778650050859","UF_CRM_1778650027948")],
    "july_2026":     [("UF_CRM_1778650166501","UF_CRM_1778650210878"), ("UF_CRM_1778650234999","UF_CRM_1778650210878")],
}
# месяц-ключ -> ожидаемый префикс YYYY-MM для валидации
MONTH_PREFIX = {
    "october_2025":"2025-10","november_2025":"2025-11","december_2025":"2025-12",
    "january_2026":"2026-01","february_2026":"2026-02","march_2026":"2026-03",
    "april_2026":"2026-04","may_2026":"2026-05","june_2026":"2026-06","july_2026":"2026-07",
}

ENUM_TYPES = json.load(open('/opt/audiobot/import_tmp/enum_types.json', encoding='utf-8'))

ALL_FIELDS = sorted({f for pairs in MONTH_FIELDS.values() for pair in pairs for f in pair})
SELECT = ["ID"] + ALL_FIELDS

def db_url():
    for line in open(ENV, encoding="utf-8"):
        if line.startswith("DATABASE_URL="):
            u = line.split("=",1)[1].strip().strip('"').strip("'")
            return u.replace("postgresql+asyncpg://","postgresql://").replace("postgresql+psycopg://","postgresql://")
    raise RuntimeError("no DATABASE_URL")

def iso_dates(v):
    out=[]
    vals = v if isinstance(v,list) else [v]
    for x in vals:
        m=re.match(r"(\d{4}-\d{2}-\d{2})", str(x or ""))
        if m: out.append(m.group(1))
    return out

def build_schedule(deal):
    sched={}
    for mkey, pairs in MONTH_FIELDS.items():
        prefix = MONTH_PREFIX[mkey]
        entries=[]
        for fdate, ftype in pairs:
            dts = iso_dates(deal.get(fdate))
            ttext = ENUM_TYPES.get(str(deal.get(ftype) or ""), "")
            for d in dts:
                if d.startswith(prefix):   # валидация месяца
                    entries.append({"date": d, "type": ttext})
        if entries:
            seen=set(); uniq=[]
            for e in sorted(entries, key=lambda x:x["date"]):
                if e["date"] in seen: continue
                seen.add(e["date"]); uniq.append(e)
            sched[mkey]=uniq
    return sched

async def main():
    import sys
    dry = "--dry" in sys.argv[1:]
    conn = await asyncpg.connect(db_url())
    existing = set()
    try:
        rows = await conn.fetch("SELECT id FROM houses")
        existing = {r["id"] for r in rows}
    finally:
        if dry: await conn.close()
    print(f"Домов в БД: {len(existing)}")

    deals=[]
    async with httpx.AsyncClient(timeout=60) as c:
        start=0
        while True:
            r=await c.get(WH+"crm.deal.list.json", params=[
                ("filter[CATEGORY_ID]","34"),("order[ID]","DESC"),("start",str(start)),
                *[("select[]",f) for f in SELECT]])
            d=r.json(); res=d.get("result") or []; deals.extend(res)
            nxt=d.get("next")
            if nxt is None: break
            start=nxt; await asyncio.sleep(0.2)
    print(f"Сделок получено: {len(deals)}")

    # статистика по месяцам
    from collections import Counter
    mcount=Counter()
    updates=[]
    for deal in deals:
        did=str(deal["ID"])
        if did not in existing: continue
        sched=build_schedule(deal)
        if not sched: continue
        for mk in sched: mcount[mk]+=1
        updates.append((did, json.dumps(sched, ensure_ascii=False)))
    print("Месяцы (сколько домов имеют график):")
    for mk in MONTH_FIELDS:
        if mcount.get(mk): print(f"  {mk}: {mcount[mk]}")
    print(f"Домов к обновлению: {len(updates)}")

    if dry:
        print("[dry] без записи"); return
    conn2 = await asyncpg.connect(db_url())
    try:
        ts=datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        await conn2.execute(f'CREATE TABLE "houses_bak_{ts}" AS TABLE houses;')
        print(f"[backup] houses_bak_{ts}")
        for did, sched in updates:
            await conn2.execute(
                "UPDATE houses SET cleaning_schedule=$1::json, updated_at=now() WHERE id=$2",
                sched, did)
        print(f"[ok] обновлено домов: {len(updates)}")
    finally:
        await conn2.close()

asyncio.run(main())
