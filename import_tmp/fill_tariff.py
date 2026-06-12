#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Дозаливка тарифа (enum UF_CRM_1669706387893) всем домам из Bitrix категории 34."""
import re, asyncio, httpx, asyncpg

WH = "https://vas-dom.bitrix24.ru/rest/1/oeo7d2sabsjxia70/"
ENV = "/opt/audiobot/backend/.env"
F_TARIFF = "UF_CRM_1669706387893"
TARIFF_ENUM = {
    "604": "1 // 170", "606": "2 // 140", "608": "3 // 125",
    "610": "4 // 110", "612": "5 // 200", "614": "6 // 150", "1226": "7 // 120",
}

def db_url():
    for line in open(ENV, encoding="utf-8"):
        if line.startswith("DATABASE_URL="):
            u = line.split("=",1)[1].strip().strip('"').strip("'")
            return u.replace("postgresql+asyncpg://","postgresql://").replace("postgresql+psycopg://","postgresql://")
    raise RuntimeError("no DATABASE_URL")

async def main():
    # тянем id+тариф всех домов категории 34
    tariffs = {}
    async with httpx.AsyncClient(timeout=60) as c:
        start = 0
        while True:
            r = await c.get(WH+"crm.deal.list.json", params=[
                ("filter[CATEGORY_ID]","34"), ("order[ID]","DESC"), ("start",str(start)),
                ("select[]","ID"), ("select[]",F_TARIFF)])
            d = r.json(); res = d.get("result") or []
            for deal in res:
                code = str(deal.get(F_TARIFF) or "")
                if code in TARIFF_ENUM:
                    tariffs[str(deal["ID"])] = TARIFF_ENUM[code]
            nxt = d.get("next")
            if nxt is None: break
            start = nxt
            await asyncio.sleep(0.2)
    print(f"Тарифов получено: {len(tariffs)}")
    conn = await asyncpg.connect(db_url())
    try:
        upd = 0
        for hid, t in tariffs.items():
            res = await conn.execute("UPDATE houses SET tariff=$1, updated_at=now() WHERE id=$2", t, hid)
            if res.endswith("1"): upd += 1
        print(f"Обновлено тарифов в БД: {upd}")
        total = await conn.fetchval("SELECT count(*) FROM houses WHERE tariff LIKE '%//%';")
        print(f"Домов с тарифом теперь: {total}")
    finally:
        await conn.close()

asyncio.run(main())
