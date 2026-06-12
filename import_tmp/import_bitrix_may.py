#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Импорт домов из Bitrix24 (категория 34) в таблицу houses.
Берём ТОЛЬКО дома, где есть майская дата уборки (2026-05).
Upsert по id; cleaning_schedule пишется нативным JSON (may_2026).
Запуск:
  import_bitrix_may.py --dry   # только показать, без записи
  import_bitrix_may.py         # реальная заливка (с бэкапом houses)
"""
import sys, re, json, asyncio, datetime
import httpx, asyncpg

WH = "https://vas-dom.bitrix24.ru/rest/1/oeo7d2sabsjxia70/"
ENV = "/opt/audiobot/backend/.env"
CATEGORY_ID = "34"

# UF-поля (по результатам инспекции Bitrix)
F_ADDR   = "UF_CRM_1669561599956"   # "Степана Разина, 60|0;0|10292"
F_APT    = "UF_CRM_1669704529022"   # квартиры
F_FLOORS = "UF_CRM_1669704631166"   # этажи
F_ENTR   = "UF_CRM_1669705507390"   # подъезды
F_START  = "UF_CRM_1669704382720"   # дата начала обслуживания
F_DOGOV  = "UF_CRM_1674011703855"   # № договора
F_MAY_D1 = "UF_CRM_1773293797362"   # дата уборки 1 май (list)
F_MAY_T1 = "UF_CRM_1773293854012"   # тип 1 (enum)
F_MAY_D2 = "UF_CRM_1773293874331"   # дата уборки 2 май (list)
F_MAY_T2 = "UF_CRM_1773293930779"   # тип 2 (enum)

# enum типов уборки -> текст
ENUM_TYPES = {
    "3166": "Подметание лестничных площадок и маршей всех этажей, влажная уборка 1 этажа и лифта (при наличии); Профилактическая дезинфекция МОП;",
    "3168": "Влажная уборка лестничных площадок всех этажей и лифта (при наличии); Профилактическая дезинфекция МОП;",
    "3170": "Влажная уборка 1 этажа и лифта (при наличии); Профилактическая дезинфекция МОП;",
    "3172": "Подметание лестничных площадок и маршей всех этажей, влажная уборка 1 этажа и лифта (при наличии); Профилактическая дезинфекция МОП;",
    "3174": "Влажная уборка лестничных площадок всех этажей и лифта (при наличии); Профилактическая дезинфекция МОП;",
    "3176": "Влажная уборка 1 этажа и лифта (при наличии); Профилактическая дезинфекция МОП;",
}

SELECT = ["ID","TITLE","CATEGORY_ID","COMPANY_ID","COMPANY_TITLE",
          "ASSIGNED_BY_ID","ASSIGNED_BY_NAME",
          F_ADDR,F_APT,F_FLOORS,F_ENTR,F_START,F_DOGOV,
          F_MAY_D1,F_MAY_T1,F_MAY_D2,F_MAY_T2]


def db_url():
    for line in open(ENV, encoding="utf-8"):
        if line.startswith("DATABASE_URL="):
            u = line.split("=",1)[1].strip().strip('"').strip("'")
            for a,b in [("postgresql+asyncpg://","postgresql://"),
                        ("postgresql+psycopg://","postgresql://"),
                        ("postgresql+psycopg2://","postgresql://")]:
                u = u.replace(a,b)
            return u
    raise RuntimeError("DATABASE_URL не найден")


def clean_address(a):
    if not a:
        return a
    s = str(a).split("|")[0].strip()   # "Адрес|coords|id" -> адрес
    s = re.sub(r"\s*\([^)]*\)\s*$", "", s).strip().rstrip(", ").strip()
    s = re.sub(r",?\s*Россия\b", "", s)
    s = re.sub(r",?\s*\b\d{6}\b", "", s)
    s = re.sub(r",?\s*Калужская область", "", s)
    s = re.sub(r"\s*,\s*,+", ", ", s)
    s = re.sub(r"\s{2,}", " ", s).strip().strip(",").strip()
    return s or str(a).strip()


def parse_brigade(resp):
    if not resp:
        return None
    m = re.search(r"(\d+)\s*бригада", str(resp), re.IGNORECASE)
    return m.group(1) if m else None


def to_int(v):
    try:
        return int(float(str(v).replace(",", "."))) if v not in (None,"") else None
    except Exception:
        return None


def iso_date(v):
    """'2026-05-15T03:00:00+03:00' -> '2026-05-15'"""
    if not v:
        return None
    if isinstance(v, list):
        v = v[0] if v else None
    if not v:
        return None
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", str(v))
    return f"{m.group(1)}-{m.group(2)}-{m.group(3)}" if m else None


def start_date(v):
    """дата начала -> DD.MM.YYYY (как в TSV)"""
    iso = iso_date(v)
    if not iso:
        return None
    y,mn,dd = iso.split("-")
    return f"{dd}.{mn}.{y}"


def build_may_schedule(deal):
    """Собираем may_2026 из двух пар (дата, тип-enum)."""
    entries = []
    for fd, ft in [(F_MAY_D1, F_MAY_T1), (F_MAY_D2, F_MAY_T2)]:
        raw = deal.get(fd)
        dates = raw if isinstance(raw, list) else ([raw] if raw else [])
        tcode = str(deal.get(ft) or "")
        ttext = ENUM_TYPES.get(tcode, "")
        for dv in dates:
            iso = iso_date(dv)
            if iso:
                entries.append({"date": iso, "type": ttext})
    if not entries:
        return {}
    # дедуп + сортировка
    seen = set(); uniq = []
    for e in sorted(entries, key=lambda x: x["date"]):
        if e["date"] in seen:
            continue
        seen.add(e["date"]); uniq.append(e)
    return {"may_2026": uniq}


async def fetch_all_houses():
    out = []
    async with httpx.AsyncClient(timeout=60) as client:
        start = 0
        while True:
            r = await client.get(WH+"crm.deal.list.json", params=[
                ("filter[CATEGORY_ID]", CATEGORY_ID),
                ("order[ID]", "DESC"),
                ("start", str(start)),
                *[("select[]", f) for f in SELECT],
            ])
            d = r.json()
            res = d.get("result") or []
            out.extend(res)
            nxt = d.get("next")
            if nxt is None:
                break
            start = nxt
            await asyncio.sleep(0.3)
    return out


# карта user_id -> отображаемое имя ответственного (часто "N бригада")
USER_NAMES = {}

async def fetch_user_names(deals):
    ids = sorted({str(d.get("ASSIGNED_BY_ID")) for d in deals if d.get("ASSIGNED_BY_ID")})
    async with httpx.AsyncClient(timeout=60) as client:
        for uid in ids:
            try:
                r = await client.get(WH+"user.get.json", params={"ID": uid})
                res = r.json().get("result") or []
                if res:
                    u = res[0]
                    name = (str(u.get("NAME","")) + " " + str(u.get("LAST_NAME",""))).strip()
                    USER_NAMES[uid] = name
                await asyncio.sleep(0.15)
            except Exception:
                pass
    return USER_NAMES


def deal_to_rec(deal):
    rid = str(deal.get("ID"))
    sched = build_may_schedule(deal)
    if not sched:               # фильтр: только дома с майской датой
        return None
    addr = clean_address(deal.get(F_ADDR) or deal.get("TITLE") or rid)
    dogovor = (deal.get(F_DOGOV) or "").strip()
    notes = f"Договор: {dogovor}" if dogovor and "нет акт" not in dogovor.lower() else None
    uid = str(deal.get("ASSIGNED_BY_ID") or "")
    resp = USER_NAMES.get(uid) or deal.get("ASSIGNED_BY_NAME") or ""
    return {
        "id": rid, "bitrix_id": rid, "address": addr,
        "company_title": deal.get("COMPANY_TITLE") or None,
        "assigned_by_id": uid or None,
        "assigned_by_name": resp or None,
        "brigade_number": parse_brigade(resp),
        "apartments_count": to_int(deal.get(F_APT)),
        "floors_count": to_int(deal.get(F_FLOORS)),
        "entrances_count": to_int(deal.get(F_ENTR)),
        "service_start_date": start_date(deal.get(F_START)),
        "notes": notes,
        "cleaning_schedule": sched,
    }


UPSERT = """
INSERT INTO houses (
  id,bitrix_id,address,company_title,assigned_by_id,assigned_by_name,brigade_number,
  apartments_count,floors_count,entrances_count,service_start_date,notes,
  cleaning_schedule,created_at,updated_at,synced_at
) VALUES (
  $1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13::json,now(),now(),now()
)
ON CONFLICT (id) DO UPDATE SET
  bitrix_id=EXCLUDED.bitrix_id, address=EXCLUDED.address,
  company_title=EXCLUDED.company_title, assigned_by_id=EXCLUDED.assigned_by_id,
  assigned_by_name=EXCLUDED.assigned_by_name, brigade_number=EXCLUDED.brigade_number,
  apartments_count=EXCLUDED.apartments_count, floors_count=EXCLUDED.floors_count,
  entrances_count=EXCLUDED.entrances_count, service_start_date=EXCLUDED.service_start_date,
  notes=COALESCE(EXCLUDED.notes,houses.notes),
  cleaning_schedule=EXCLUDED.cleaning_schedule,
  updated_at=now(), synced_at=now()
RETURNING (xmax=0) AS inserted;
"""


async def apply(recs, dry):
    if dry:
        print("[dry] записи НЕ пишутся")
        return
    conn = await asyncpg.connect(db_url())
    try:
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        await conn.execute(f'CREATE TABLE "houses_bak_{ts}" AS TABLE houses;')
        print(f"[backup] houses_bak_{ts}")
        ins=upd=0
        for r in recs:
            sched = json.dumps(r["cleaning_schedule"], ensure_ascii=False)
            was = await conn.fetchval(UPSERT,
                r["id"],r["bitrix_id"],r["address"],r["company_title"],
                r["assigned_by_id"],r["assigned_by_name"],r["brigade_number"],
                r["apartments_count"],r["floors_count"],r["entrances_count"],
                r["service_start_date"],r["notes"],sched)
            ins += 1 if was else 0
            upd += 0 if was else 1
        print(f"[upsert] вставлено:{ins} обновлено:{upd} всего:{len(recs)}")
        total = await conn.fetchval("SELECT count(*) FROM houses;")
        print(f"[итог] домов в таблице: {total}")
    finally:
        await conn.close()


async def main():
    dry = "--dry" in sys.argv[1:]
    print("Тяну дома из Bitrix (категория 34)...")
    deals = await fetch_all_houses()
    print(f"Получено сделок: {len(deals)}")
    await fetch_user_names(deals)
    print(f"Загружено имён ответственных: {len(USER_NAMES)}")
    recs = [r for r in (deal_to_rec(d) for d in deals) if r]
    print(f"С майской датой уборки: {len(recs)}")
    with_brig = sum(1 for r in recs if r["brigade_number"])
    print(f"  из них с бригадой: {with_brig}")
    if recs:
        r0 = recs[0]
        print(f"[пример] id={r0['id']} | {r0['address']} | бриг={r0['brigade_number']} | "
              f"кв={r0['apartments_count']} под={r0['entrances_count']} эт={r0['floors_count']}")
        print(f"         {json.dumps(r0['cleaning_schedule'], ensure_ascii=False)[:140]}")
    await apply(recs, dry)


if __name__ == "__main__":
    asyncio.run(main())
