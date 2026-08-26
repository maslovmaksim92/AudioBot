#!/usr/bin/env python3
"""Заливка тестовых домов из выгрузки Bitrix24 (воронка «Уборка подъездов»).
Данные взяты со скриншотов выгрузки. График — на май 2026 (2 даты + типы уборки)."""
import psycopg2, json, re
from datetime import datetime, timezone

dsn = re.search(r'^DATABASE_URL=(.+)$', open('/root/audiobot-secrets/db.env').read(), re.M).group(1)

# Типы уборки (из колонок «Тип уборки 1/2»)
T1 = "Влажная уборка лестничных площадок этажей и лифта (при наличии)"
T2 = "Профилактическая дезинфекция, влажная уборка 1-го этажа"

# Реальные дома из выгрузки. Поля:
# bitrix_id, address, company(УК), brigade, apartments, floors, entrances, tariff, contract, lat, lon, may_date1, may_date2
HOUSES = [
    ("13328", "Степана Разина, 60, Калуга", "УК ГУП Калуги", None, 72, 9, 2, "4 // 110", "№ 17/19 от 01.12.2019", None, None, "2026-05-05", "2026-05-22"),
    ("13326", "улица Максима Горького, 88, Калуга, 248023", 'ООО "ДОМОУПРАВЛЕНИЕ - МОНОЛИТ"', "2", 20, 5, 1, "4 // 110", "№ 22-1/19 от 01.12.2020", 54.50584485, 36.2826360714, "2026-05-12", "2026-05-27"),
    ("13324", "улица Салтыкова-Щедрина, 37, Калуга, 248019", "УК ГУП Калуги", "4", 36, 6, 2, "4 // 110", "№ 17/19 от 01.12.2019", 54.50108305, 36.26676105, "2026-05-05", "2026-05-19"),
    ("13322", "Телевизионная улица, 10, Калуга, 248010", 'ООО "Техно-Р"', None, 48, 4, 2, "4 // 110", "№ 07/25 от 20.03.2025", 54.53202885, 36.260507478893, "2026-05-12", "2026-05-27"),
    ("13320", "улица Тельмана, 10, Калуга, 248910", 'ООО "Техно-Р"', None, 110, 5, 8, "4 // 110", "№ 07/25 от 20.03.2025", 54.5339509, 36.264853642246, "2026-05-12", "2026-05-25"),
    ("13318", "улица Ленина, 67, Калуга, 248016", 'ООО "Техно-Р"', "4", 70, 5, 4, "4 // 110", "№ 07/25 от 20.03.2025", 54.51595215, 36.265855208689, "2026-05-13", "2026-05-28"),
    ("13316", "Высокая улица, 4, Калуга, 248010", 'ООО "Техно-Р"', "6", 40, 5, 2, "4 // 110", "№ 07/25 от 20.03.2025", 54.52874615, 36.24971275, "2026-05-16", "2026-05-28"),
    ("13314", "улица Багговута, 12, Калуга, 248001", 'ООО "Техно-Р"', None, 60, 5, 4, "4 // 110", "№ 07/25 от 20.03.2025", 54.53220555, 36.25234705, "2026-05-14", "2026-05-28"),
    ("13312", "Телевизионная улица, 6 к.1, Калуга", 'ООО "Техно-Р"', None, 20, 5, 1, "4 // 110", "№ 07/25 от 20.03.2025", None, None, "2026-05-13", "2026-05-27"),
    ("13310", "Телевизионная, 2, Калуга", 'ООО "Техно-Р"', None, 38, 5, 2, "4 // 110", "№ 07/25 от 20.03.2025", None, None, "2026-05-13", "2026-05-27"),
    ("13308", "переулок Чичерина, 28, Калуга, 248001", 'ООО "Техно-Р"', None, 70, 5, 4, "4 // 110", "№ 07/25 от 20.03.2025", 54.5317137, 36.2568848, "2026-05-13", "2026-05-27"),
    ("13306", "переулок Чичерина, 24, Калуга, 248001", 'ООО "Техно-Р"', None, 98, 5, 6, "4 // 110", "№ 07/25 от 20.03.2025", 54.5317137, 36.2568848, "2026-05-13", "2026-05-27"),
]

def build_schedule(d1, d2):
    sched = {"may_2026": []}
    if d1: sched["may_2026"].append({"date": d1, "type": T1})
    if d2: sched["may_2026"].append({"date": d2, "type": T2})
    return sched

conn = psycopg2.connect(dsn); cur = conn.cursor()
now = datetime.now(timezone.utc)
n = 0
for (bid, addr, comp, brig, apt, fl, ent, tariff, contract, lat, lon, d1, d2) in HOUSES:
    addr_full = addr if (lat is None) else f"{addr} ({lat}, {lon})"
    sched = build_schedule(d1, d2)
    notes = f"Договор: {contract}" + (f" | Координаты: {lat},{lon}" if lat else "")
    cur.execute("""
        INSERT INTO houses (id, bitrix_id, address, company_title, brigade_number,
            apartments_count, floors_count, entrances_count, tariff, cleaning_schedule,
            notes, created_at, updated_at, synced_at)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (bitrix_id) DO UPDATE SET
            address=EXCLUDED.address, company_title=EXCLUDED.company_title,
            brigade_number=EXCLUDED.brigade_number, cleaning_schedule=EXCLUDED.cleaning_schedule,
            tariff=EXCLUDED.tariff, notes=EXCLUDED.notes, updated_at=EXCLUDED.updated_at
    """, (bid, bid, addr_full, comp, brig, apt, fl, ent, tariff,
          json.dumps(sched, ensure_ascii=False), notes, now, now, now))
    n += 1

conn.commit()
cur.execute("SELECT count(*) FROM houses"); total = cur.fetchone()[0]
cur.execute("SELECT count(DISTINCT company_title) FROM houses"); uks = cur.fetchone()[0]
cur.close(); conn.close()
print(f"✅ Залито/обновлено: {n} домов | Всего в базе: {total} | Уникальных УК: {uks}")
