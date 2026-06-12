#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Парсер выгрузки Bitrix24 (воронка "Уборка подъездов") -> БД houses.
Грузим: адрес, УК, бригада, тариф, кол-во квартир/этажей/подъездов,
дата начала обслуживания, график уборок по месяцам.
НЕ грузим: площадь, директор, № договора, сумму.
"""
import re, json, sys
from collections import Counter

RU_MONTHS = {1:"january",2:"february",3:"march",4:"april",5:"may",6:"june",
             7:"july",8:"august",9:"september",10:"october",11:"november",12:"december"}
DATE_RE = re.compile(r'\b(\d{2})\.(\d{2})\.(\d{4})\b')
TYPE_RE = re.compile(r'(Влажная уборка|Подметание)')

IDX = {"id":0,"company":3,"responsible":4,"deal":5,"director":7,"address":8,
       "service_start":9,"apartments":11,"floors":12,"entrances":13,"tariff":14}
SCHEDULE_START = 16

def clean_addr(deal, addr_full):
    d = (deal or "").strip()
    a = re.sub(r'\s*\([^)]*\)\s*$', '', (addr_full or "").strip()).strip().rstrip(',')
    if d and len(d) >= 3:
        return d
    return a or d

def norm_brigade(resp):
    m = re.search(r'(\d+)\s*бригад', (resp or ""), re.IGNORECASE)
    return m.group(1) if m else None

def to_int(s):
    m = re.search(r'\d+', (s or "").replace(" ", ""))
    return int(m.group()) if m else None

def build_schedule(cells):
    """
    Шаблон выгрузки: иногда несколько ячеек дат подряд, затем столько же ячеек
    типов подряд. Накапливаем ОЧЕРЕДЬ групп дат (FIFO); каждый встреченный тип
    привязываем к самой ранней необработанной группе дат.
    """
    sched, seen = {}, set()
    date_queue = []
    for cell in cells[SCHEDULE_START:]:
        c = (cell or "").strip()
        if not c: continue
        is_type = bool(TYPE_RE.search(c))
        dates = DATE_RE.findall(c)
        if dates and not is_type:
            grp = []
            for dd,mm,yyyy in dates:
                try:
                    d,m,y = int(dd),int(mm),int(yyyy)
                    grp.append((f"{y:04d}-{m:02d}-{d:02d}", m, y))
                except: pass
            if grp: date_queue.append(grp)
        elif is_type:
            t = re.sub(r'\s+',' ',c).strip()
            if not date_queue: continue
            grp = date_queue.pop(0)
            for iso,m,y in grp:
                key=f"{RU_MONTHS.get(m)}_{y}"
                if (key,iso) in seen: continue
                seen.add((key,iso))
                sched.setdefault(key,[]).append({"date":iso,"type":t})
    for k in sched: sched[k].sort(key=lambda x:x["date"])
    return sched

def parse_line(line):
    cells = line.rstrip("\n").split("\t")
    if len(cells) < SCHEDULE_START: return None
    bid = (cells[IDX["id"]] or "").strip()
    if not bid.isdigit(): return None
    return {
        "bitrix_id": bid,
        "company_title": (cells[IDX["company"]] or "").strip() or None,
        "brigade_number": norm_brigade(cells[IDX["responsible"]]),
        "address": clean_addr(cells[IDX["deal"]], cells[IDX["address"]]),
        "service_start_date": (cells[IDX["service_start"]] or "").strip() or None,
        "apartments_count": to_int(cells[IDX["apartments"]]),
        "floors_count": to_int(cells[IDX["floors"]]),
        "entrances_count": to_int(cells[IDX["entrances"]]),
        "tariff": (cells[IDX["tariff"]] or "").strip() or None,
        "cleaning_schedule": build_schedule(cells),
    }

def main():
    src = sys.argv[1] if len(sys.argv)>1 else "/opt/audiobot/data_import/raw.tsv"
    with open(src, encoding="utf-8") as f:
        lines = f.readlines()
    out = [r for line in lines[1:] if line.strip() for r in [parse_line(line)] if r]
    with open("/opt/audiobot/data_import/parsed.json","w",encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    uk = Counter(r["company_title"] for r in out)
    nbrig = sum(1 for r in out if r["brigade_number"])
    td = sum(len(v) for r in out for v in r["cleaning_schedule"].values())
    print(f"Распарсено домов: {len(out)}")
    print(f"С номером бригады: {nbrig} | без номера: {len(out)-nbrig}")
    print(f"Всего дат уборок: {td} | УК: {len(uk)}")
    print("\nТоп УК:")
    for k,v in uk.most_common(15): print(f"  {v:>3}  {k}")
    print("\nПример (первый дом):")
    r=out[0]
    for k in ("bitrix_id","address","company_title","brigade_number","apartments_count","floors_count","entrances_count","tariff","service_start_date"):
        print(f"   {k}: {r[k]}")
    print("   schedule:", {k:len(v) for k,v in r["cleaning_schedule"].items()})

if __name__=="__main__":
    main()
