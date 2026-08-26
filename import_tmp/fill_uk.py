#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Дозаливка названий УК (company_title) из Bitrix по COMPANY_ID."""
import asyncio, httpx, asyncpg

WH = "https://vas-dom.bitrix24.ru/rest/1/oeo7d2sabsjxia70/"
ENV = "/opt/audiobot/backend/.env"

def db_url():
    for line in open(ENV, encoding="utf-8"):
        if line.startswith("DATABASE_URL="):
            u = line.split("=",1)[1].strip().strip('"').strip("'")
            return u.replace("postgresql+asyncpg://","postgresql://").replace("postgresql+psycopg://","postgresql://")
    raise RuntimeError("no DATABASE_URL")

async def main():
    # 1) тянем id -> company_id для домов кат.34
    deal_company = {}
    company_ids = set()
    async with httpx.AsyncClient(timeout=60) as c:
        start = 0
        while True:
            r = await c.get(WH+"crm.deal.list.json", params=[
                ("filter[CATEGORY_ID]","34"),("order[ID]","DESC"),("start",str(start)),
                ("select[]","ID"),("select[]","COMPANY_ID")])
            d = r.json(); res = d.get("result") or []
            for deal in res:
                cid = str(deal.get("COMPANY_ID") or "")
                if cid and cid != "0":
                    deal_company[str(deal["ID"])] = cid
                    company_ids.add(cid)
            nxt = d.get("next")
            if nxt is None: break
            start = nxt; await asyncio.sleep(0.2)
        # 2) имена компаний
        names = {}
        for cid in company_ids:
            try:
                r = await c.get(WH+"crm.company.get.json", params={"id": cid})
                res = r.json().get("result") or {}
                if res.get("TITLE"):
                    names[cid] = res["TITLE"]
                await asyncio.sleep(0.1)
            except Exception:
                pass
    print(f"Домов с УК: {len(deal_company)} | уникальных УК: {len(names)}")
    # 3) обновляем БД
    conn = await asyncpg.connect(db_url())
    try:
        upd = 0
        for hid, cid in deal_company.items():
            title = names.get(cid)
            if not title: continue
            res = await conn.execute(
                "UPDATE houses SET company_id=$1, company_title=$2, updated_at=now() WHERE id=$3",
                cid, title, hid)
            if res.endswith("1"): upd += 1
        print(f"Обновлено домов с названием УК: {upd}")
        rows = await conn.fetch(
            "SELECT company_title, count(*) c FROM houses WHERE company_title IS NOT NULL "
            "GROUP BY 1 ORDER BY 2 DESC LIMIT 12;")
        print("Топ УК:")
        for r in rows:
            print(f"   {r['company_title']}: {r['c']}")
    finally:
        await conn.close()

asyncio.run(main())
