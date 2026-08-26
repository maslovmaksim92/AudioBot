#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Импорт домов из TSV-порций в таблицу houses (upsert по id).
Использование: import_tsv.py <part.tsv> [--first]
  --first : перед записью создать резервную копию houses_bak_<ts>
TSV: первая строка — заголовок (мапим колонки по именам, динамически).
Дата DD.MM.YYYY. Ячейки расписания могут содержать 2 даты через запятую.
cleaning_schedule пишется как НАТИВНЫЙ json (фикс старого бага со строками).
"""
import sys, os, re, csv, json, asyncio, datetime
import asyncpg

ENV = "/opt/audiobot/backend/.env"

def db_url():
    for line in open(ENV, encoding="utf-8"):
        if line.startswith("DATABASE_URL="):
            u = line.split("=", 1)[1].strip().strip('"').strip("'")
            u = u.replace("postgresql+asyncpg://", "postgresql://")
            u = u.replace("postgresql+psycopg://", "postgresql://")
            u = u.replace("postgresql+psycopg2://", "postgresql://")
            return u
    raise RuntimeError("DATABASE_URL не найден в .env")

# ---------- парсеры ----------
def clean_address(a):
    if not a:
        return a
    s = a.strip()
    # убрать координаты/пустые скобки в конце: (54.5, 36.2) или (0, 0) или (, )
    s = re.sub(r"\s*\([^)]*\)\s*$", "", s).strip()
    # убрать хвостовую запятую
    s = s.rstrip(", ").strip()
    # убрать "Россия"
    s = re.sub(r",?\s*Россия\b", "", s)
    # убрать почтовый индекс (6 цифр)
    s = re.sub(r",?\s*\b\d{6}\b", "", s)
    # убрать "Калужская область"
    s = re.sub(r",?\s*Калужская область", "", s)
    # схлопнуть повторные запятые/пробелы
    s = re.sub(r"\s*,\s*,+", ", ", s)
    s = re.sub(r"\s{2,}", " ", s)
    s = s.strip().strip(",").strip()
    return s or a.strip()

def parse_brigade(resp):
    if not resp:
        return None
    m = re.search(r"(\d+)\s*бригада", resp, re.IGNORECASE)
    if m:
        return m.group(1)
    return None  # ФИО ответственного -> бригады нет

def to_int(v):
    if v is None:
        return None
    v = str(v).strip()
    if not v:
        return None
    try:
        return int(float(v.replace(",", ".")))
    except Exception:
        return None

def to_iso(d):
    """DD.MM.YYYY -> YYYY-MM-DD ; иначе None"""
    if not d:
        return None
    d = d.strip()
    m = re.match(r"(\d{1,2})\.(\d{1,2})\.(\d{4})", d)
    if not m:
        return None
    dd, mm, yy = m.groups()
    return f"{yy}-{int(mm):02d}-{int(dd):02d}"

MONTHS_RU = {
    1: "january", 2: "february", 3: "march", 4: "april", 5: "may", 6: "june",
    7: "july", 8: "august", 9: "september", 10: "october", 11: "november", 12: "december",
}

def split_dates(cell):
    """'06.05.2026, 20.05.2026' -> ['06.05.2026','20.05.2026']"""
    if not cell:
        return []
    return [p.strip() for p in cell.split(",") if p.strip()]

def add_entry(sched, iso_date, ctype):
    if not iso_date:
        return
    y, m, d = iso_date.split("-")
    key = f"{MONTHS_RU[int(m)]}_{y}"
    sched.setdefault(key, [])
    # дедуп по дате
    if any(e["date"] == iso_date for e in sched[key]):
        return
    sched[key].append({"date": iso_date, "type": (ctype or "").strip()})

def build_schedule(row, cmap):
    """Собирает cleaning_schedule из всех пар (Дата уборки N .. / Тип уборки N ..)."""
    sched = {}
    # ищем все колонки с 'Дата уборки' / 'Дата убоки' (опечатка в шапке) и парный тип
    pairs = []
    headers = list(cmap.keys())
    for h in headers:
        hl = h.lower()
        if ("дата уборки" in hl) or ("дата убоки" in hl):
            # соответствующий тип: заменяем 'дата уборки'/'дата убоки' на 'тип уборки'
            suffix = re.sub(r"дата\s+уб\w*ки", "", hl).strip()  # напр '1 май 2026'
            type_col = None
            for h2 in headers:
                if h2.lower().startswith("тип уборки") and h2.lower().strip().endswith(suffix):
                    type_col = h2
                    break
            pairs.append((h, type_col))
    for date_h, type_h in pairs:
        cell = row[cmap[date_h]] if cmap[date_h] < len(row) else ""
        ctype = row[cmap[type_h]] if (type_h and cmap[type_h] < len(row)) else ""
        for d in split_dates(cell):
            add_entry(sched, to_iso(d), ctype)
    # сортировка по дате внутри месяца
    for k in sched:
        sched[k].sort(key=lambda e: e["date"])
    return sched

def find_col(cmap, *needles):
    for h, i in cmap.items():
        hl = h.lower()
        if all(n in hl for n in needles):
            return i
    return None

# ---------- основная загрузка ----------
def load_tsv(path):
    with open(path, encoding="utf-8") as f:
        reader = csv.reader(f, delimiter="\t")
        rows = [r for r in reader if any(c.strip() for c in r)]
    if not rows:
        return []
    header = rows[0]
    cmap = {h.strip(): i for i, h in enumerate(header)}
    # индексы ключевых колонок (по подстрокам, устойчиво к вариациям шапки)
    i_id    = find_col(cmap, "id")
    if i_id is None:
        i_id = 0
    i_comp  = find_col(cmap, "компания")
    i_resp  = find_col(cmap, "ответственный")
    i_addr  = find_col(cmap, "адрес")
    i_start = find_col(cmap, "дата начала")
    i_apt   = find_col(cmap, "количество квартир")
    i_flr   = find_col(cmap, "количество этажей")
    i_entr  = find_col(cmap, "количество подъездов")
    i_tarif = find_col(cmap, "тариф")
    i_dogovor = find_col(cmap, "договора")

    out = []
    for r in rows[1:]:
        # дополняем строку до длины заголовка
        if len(r) < len(header):
            r = r + [""] * (len(header) - len(r))
        rid = (r[i_id] or "").strip()
        if not rid or not rid.isdigit():
            continue
        addr_raw = r[i_addr] if i_addr is not None else ""
        name_raw = r[find_col(cmap, "название")] if find_col(cmap, "название") else ""
        address = clean_address(addr_raw) or (name_raw.strip() if name_raw else rid)
        dogovor = (r[i_dogovor] or "").strip() if i_dogovor is not None else ""
        notes = None
        if dogovor and "нет акт" not in dogovor.lower():
            notes = f"Договор: {dogovor}"
        rec = {
            "id": rid,
            "bitrix_id": rid,
            "address": address,
            "company_title": (r[i_comp] or "").strip() if i_comp is not None else None,
            "assigned_by_name": (r[i_resp] or "").strip() if i_resp is not None else None,
            "brigade_number": parse_brigade(r[i_resp] if i_resp is not None else ""),
            "apartments_count": to_int(r[i_apt]) if i_apt is not None else None,
            "floors_count": to_int(r[i_flr]) if i_flr is not None else None,
            "entrances_count": to_int(r[i_entr]) if i_entr is not None else None,
            "tariff": (r[i_tarif] or "").strip() or None if i_tarif is not None else None,
            "service_start_date": (r[i_start] or "").strip() or None if i_start is not None else None,
            "notes": notes,
            "cleaning_schedule": build_schedule(r, cmap),
        }
        out.append(rec)
    return out

UPSERT = """
INSERT INTO houses (
    id, bitrix_id, address, company_title, assigned_by_name, brigade_number,
    apartments_count, floors_count, entrances_count, tariff,
    service_start_date, notes, cleaning_schedule, created_at, updated_at, synced_at
) VALUES (
    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13::json, now(), now(), now()
)
ON CONFLICT (id) DO UPDATE SET
    bitrix_id          = EXCLUDED.bitrix_id,
    address            = EXCLUDED.address,
    company_title      = EXCLUDED.company_title,
    assigned_by_name   = EXCLUDED.assigned_by_name,
    brigade_number     = EXCLUDED.brigade_number,
    apartments_count   = EXCLUDED.apartments_count,
    floors_count       = EXCLUDED.floors_count,
    entrances_count    = EXCLUDED.entrances_count,
    tariff             = EXCLUDED.tariff,
    service_start_date = EXCLUDED.service_start_date,
    notes              = COALESCE(EXCLUDED.notes, houses.notes),
    cleaning_schedule  = EXCLUDED.cleaning_schedule,
    updated_at         = now(),
    synced_at          = now()
RETURNING (xmax = 0) AS inserted;
"""

async def apply(rows, first=False):
    url = db_url()
    conn = await asyncpg.connect(url)
    try:
        if first:
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            bak = f"houses_bak_{ts}"
            await conn.execute(f'CREATE TABLE "{bak}" AS TABLE houses;')
            print(f"[backup] создан {bak}")
        ins = upd = 0
        for rec in rows:
            sched_json = json.dumps(rec["cleaning_schedule"], ensure_ascii=False) if rec["cleaning_schedule"] else json.dumps({})
            was_inserted = await conn.fetchval(
                UPSERT,
                rec["id"], rec["bitrix_id"], rec["address"], rec["company_title"],
                rec["assigned_by_name"], rec["brigade_number"], rec["apartments_count"],
                rec["floors_count"], rec["entrances_count"], rec["tariff"],
                rec["service_start_date"], rec["notes"], sched_json,
            )
            if was_inserted:
                ins += 1
            else:
                upd += 1
        print(f"[upsert] вставлено: {ins}, обновлено: {upd}, всего в порции: {len(rows)}")
        total = await conn.fetchval("SELECT count(*) FROM houses;")
        print(f"[итог] всего домов в таблице: {total}")
    finally:
        await conn.close()

def main():
    if len(sys.argv) < 2:
        print("usage: import_tsv.py <part.tsv> [--first]")
        sys.exit(1)
    path = sys.argv[1]
    first = "--first" in sys.argv[2:]
    rows = load_tsv(path)
    print(f"[parse] распарсено строк: {len(rows)}")
    with_sched = sum(1 for r in rows if r["cleaning_schedule"])
    with_brig = sum(1 for r in rows if r["brigade_number"])
    print(f"[parse] с расписанием: {with_sched}, с бригадой: {with_brig}")
    if rows:
        r0 = rows[0]
        print(f"[пример] id={r0['id']} | {r0['address']} | бриг={r0['brigade_number']} | "
              f"кв={r0['apartments_count']} | старт={r0['service_start_date']}")
        print(f"         расписание={json.dumps(r0['cleaning_schedule'], ensure_ascii=False)[:160]}")
    if "--dry" in sys.argv[2:]:
        print("[dry-run] запись не выполнялась")
        return
    asyncio.run(apply(rows, first=first))

if __name__ == "__main__":
    main()
