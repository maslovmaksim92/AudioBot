#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ПОЛНАЯ чистая выгрузка домов из Bitrix24 (категория 34).
Берём ТОЛЬКО дома с майской датой уборки (актуальные). Тестовые/неактуальные отсеиваются.
Тянем сразу всё: адрес, кв/эт/подъезды, бригаду (через user.get), тариф, сумму (OPPORTUNITY),
дату старта, договор, график мая. Полная замена houses (TRUNCATE + INSERT) с бэкапом.
"""
import re, json, asyncio, datetime
import httpx, asyncpg

WH = "https://vas-dom.bitrix24.ru/rest/1/oeo7d2sabsjxia70/"
ENV = "/opt/audiobot/backend/.env"
CATEGORY_ID = "34"

F_ADDR   = "UF_CRM_1669561599956"
F_APT    = "UF_CRM_1669704529022"
F_FLOORS = "UF_CRM_1669704631166"
F_ENTR   = "UF_CRM_1669705507390"
F_START  = "UF_CRM_1669704382720"
F_DOGOV  = "UF_CRM_1674011703855"
F_TARIFF = "UF_CRM_1669706387893"
F_MAY_D1 = "UF_CRM_1773293797362"
F_MAY_T1 = "UF_CRM_1773293854012"
F_MAY_D2 = "UF_CRM_1773293874331"
F_MAY_T2 = "UF_CRM_1773293930779"

ENUM_TYPES = {
    "3166": "Подметание лестничных площадок и маршей всех этажей, влажная уборка 1 этажа и лифта (при наличии); Профилактическая дезинфекция МОП;",
    "3168": "Влажная уборка лестничных площадок всех этажей и лифта (при наличии); Профилактическая дезинфекция МОП;",
    "3170": "Влажная уборка 1 этажа и лифта (при наличии); Профилактическая дезинфекция МОП;",
    "3172": "Подметание лестничных площадок и маршей всех этажей, влажная уборка 1 этажа и лифта (при наличии); Профилактическая дезинфекция МОП;",
    "3174": "Влажная уборка лестничных площадок всех этажей и лифта (при наличии); Профилактическая дезинфекция МОП;",
    "3176": "Влажная уборка 1 этажа и лифта (при наличии); Профилактическая дезинфекция МОП;",
}
TARIFF_ENUM = {"604":"1 // 170","606":"2 // 140","608":"3 // 125","610":"4 // 110","612":"5 // 200","614":"6 // 150","1226":"7 // 120"}

SELECT = ["ID","TITLE","CATEGORY_ID","COMPANY_ID","COMPANY_TITLE","ASSIGNED_BY_ID","OPPORTUNITY",
          F_ADDR,F_APT,F_FLOORS,F_ENTR,F_START,F_DOGOV,F_TARIFF,F_MAY_D1,F_MAY_T1,F_MAY_D2,F_MAY_T2]

def db_url():
    for line in open(ENV, encoding="utf-8"):
        if line.startswith("DATABASE_URL="):
            u = line.split("=",1)[1].strip().strip('"').strip("'")
            return u.replace("postgresql+asyncpg://","postgresql://").replace("postgresql+psycopg://","postgresql://")
    raise RuntimeError("no DATABASE_URL")

def clean_address(a, title=""):
    raw = a or ""
    s = str(raw).split("|")[0].strip()
    if not s:  # из TITLE убираем ведущий ID
        s = re.sub(r"^\d+\s*,?\s*", "", str(title)).strip()
    s = re.sub(r"\s*\([^)]*\)\s*$", "", s).strip().rstrip(", ").strip()
    s = re.sub(r",?\s*Россия\b", "", s)
    s = re.sub(r",?\s*\b\d{6}\b", "", s)
    s = re.sub(r",?\s*Калужская область", "", s)
    s = re.sub(r"\s*,\s*,+", ", ", s)
    s = re.sub(r"\s{2,}", " ", s).strip().strip(",").strip()
    return s or str(title).strip()

def parse_brigade(resp):
    if not resp: return None
    m = re.search(r"(\d+)\s*бригада", str(resp), re.IGNORECASE)
    return m.group(1) if m else None

def to_int(v):
    try: return int(float(str(v).replace(",", "."))) if v not in (None,"") else None
    except: return None

def iso_date(v):
    if isinstance(v, list): v = v[0] if v else None
    if not v: return None
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", str(v))
    return f"{m.group(1)}-{m.group(2)}-{m.group(3)}" if m else None

def start_date(v):
    iso = iso_date(v)
    if not iso: return None
    y,mn,dd = iso.split("-"); return f"{dd}.{mn}.{y}"

def build_may(deal):
    entries=[]
    for fd,ft in [(F_MAY_D1,F_MAY_T1),(F_MAY_D2,F_MAY_T2)]:
        raw=deal.get(fd); dates=raw if isinstance(raw,list) else ([raw] if raw else [])
        ttext=ENUM_TYPES.get(str(deal.get(ft) or ""),"")
        for dv in dates:
            iso=iso_date(dv)
            if iso: entries.append({"date":iso,"type":ttext})
    if not entries: return {}
    seen=set(); uniq=[]
    for e in sorted(entries,key=lambda x:x["date"]):
        if e["date"] in seen: continue
        seen.add(e["date"]); uniq.append(e)
    return {"may_2026":uniq}

USER_NAMES={}
async def fetch_users(deals, client):
    ids=sorted({str(d.get("ASSIGNED_BY_ID")) for d in deals if d.get("ASSIGNED_BY_ID")})
    for uid in ids:
        try:
            r=await client.get(WH+"user.get.json", params={"ID":uid})
            res=r.json().get("result") or []
            if res:
                u=res[0]; USER_NAMES[uid]=(str(u.get("NAME","")) + " " + str(u.get("LAST_NAME",""))).strip()
            await asyncio.sleep(0.12)
        except: pass

def to_rec(deal):
    sched=build_may(deal)
    if not sched: return None  # фильтр: только актуальные (с маем)
    rid=str(deal.get("ID"))
    uid=str(deal.get("ASSIGNED_BY_ID") or "")
    resp=USER_NAMES.get(uid,"")
    dogovor=(deal.get(F_DOGOV) or "").strip()
    notes=f"Договор: {dogovor}" if dogovor and "нет акт" not in dogovor.lower() else None
    try: amount=float(deal.get("OPPORTUNITY") or 0) or None
    except: amount=None
    return {
        "id":rid,"bitrix_id":rid,
        "address":clean_address(deal.get(F_ADDR), deal.get("TITLE")),
        "company_title":deal.get("COMPANY_TITLE") or None,
        "assigned_by_id":uid or None,"assigned_by_name":resp or None,
        "brigade_number":parse_brigade(resp),
        "apartments_count":to_int(deal.get(F_APT)),
        "floors_count":to_int(deal.get(F_FLOORS)),
        "entrances_count":to_int(deal.get(F_ENTR)),
        "tariff":TARIFF_ENUM.get(str(deal.get(F_TARIFF) or "")),
        "amount_monthly":amount,
        "service_start_date":start_date(deal.get(F_START)),
        "notes":notes,"cleaning_schedule":sched,
    }

INSERT="""
INSERT INTO houses (id,bitrix_id,address,company_title,assigned_by_id,assigned_by_name,
  brigade_number,apartments_count,floors_count,entrances_count,tariff,amount_monthly,
  service_start_date,notes,cleaning_schedule,created_at,updated_at,synced_at)
VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15::json,now(),now(),now())
ON CONFLICT (id) DO UPDATE SET
  address=EXCLUDED.address,company_title=EXCLUDED.company_title,
  assigned_by_id=EXCLUDED.assigned_by_id,assigned_by_name=EXCLUDED.assigned_by_name,
  brigade_number=EXCLUDED.brigade_number,apartments_count=EXCLUDED.apartments_count,
  floors_count=EXCLUDED.floors_count,entrances_count=EXCLUDED.entrances_count,
  tariff=EXCLUDED.tariff,amount_monthly=EXCLUDED.amount_monthly,
  service_start_date=EXCLUDED.service_start_date,notes=COALESCE(EXCLUDED.notes,houses.notes),
  cleaning_schedule=EXCLUDED.cleaning_schedule,updated_at=now(),synced_at=now();
"""

async def main():
    import sys
    dry="--dry" in sys.argv[1:]
    async with httpx.AsyncClient(timeout=60) as client:
        deals=[]; start=0
        while True:
            r=await client.get(WH+"crm.deal.list.json", params=[
                ("filter[CATEGORY_ID]",CATEGORY_ID),("order[ID]","DESC"),("start",str(start)),
                *[("select[]",f) for f in SELECT]])
            d=r.json(); res=d.get("result") or []; deals.extend(res)
            nxt=d.get("next")
            if nxt is None: break
            start=nxt; await asyncio.sleep(0.2)
        print(f"Сделок в кат.34: {len(deals)}")
        await fetch_users(deals, client)
        print(f"Имён ответственных: {len(USER_NAMES)}")
    recs=[r for r in (to_rec(d) for d in deals) if r]
    print(f"Актуальных (с майской датой): {len(recs)}")
    print(f"  с бригадой: {sum(1 for r in recs if r['brigade_number'])}")
    print(f"  с суммой: {sum(1 for r in recs if r['amount_monthly'])}")
    print(f"  с тарифом: {sum(1 for r in recs if r['tariff'])}")
    if dry:
        print("[dry] без записи"); return
    conn=await asyncpg.connect(db_url())
    try:
        ts=datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        await conn.execute(f'CREATE TABLE "houses_bak_{ts}" AS TABLE houses;')
        print(f"[backup] houses_bak_{ts}")
        # полная чистая замена: убираем все дома, которых нет в актуальной выгрузке
        keep_ids=tuple(r["id"] for r in recs)
        # сохраняем связанные фото/таски: чистим только дома вне списка
        await conn.execute("DELETE FROM cleaning_photos WHERE house_id <> ALL($1::text[])", list(keep_ids))
        await conn.execute("DELETE FROM tasks WHERE house_id <> ALL($1::text[])", list(keep_ids))
        deleted=await conn.fetchval("SELECT count(*) FROM houses WHERE id <> ALL($1::text[])", list(keep_ids))
        await conn.execute("DELETE FROM houses WHERE id <> ALL($1::text[])", list(keep_ids))
        print(f"[clean] удалено неактуальных домов: {deleted}")
        ins=upd=0
        for r in recs:
            sched=json.dumps(r["cleaning_schedule"],ensure_ascii=False)
            was=await conn.fetchval("SELECT 1 FROM houses WHERE id=$1", r["id"])
            await conn.execute(INSERT,
                r["id"],r["bitrix_id"],r["address"],r["company_title"],r["assigned_by_id"],
                r["assigned_by_name"],r["brigade_number"],r["apartments_count"],r["floors_count"],
                r["entrances_count"],r["tariff"],r["amount_monthly"],r["service_start_date"],
                r["notes"],sched)
            if was: upd+=1
            else: ins+=1
        print(f"[upsert] вставлено:{ins} обновлено:{upd}")
        total=await conn.fetchval("SELECT count(*) FROM houses;")
        tot_amount=await conn.fetchval("SELECT round(sum(amount_monthly)) FROM houses;")
        print(f"[итог] домов в таблице: {total} | сумма/мес: {tot_amount} ₽")
    finally:
        await conn.close()

asyncio.run(main())
