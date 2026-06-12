#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Дозаливка месячной суммы (OPPORTUNITY) из Bitrix категории 34 в houses.amount_monthly."""
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
    amounts = {}
    async with httpx.AsyncClient(timeout=60) as c:
        start = 0
        while True:
            r = await c.get(WH+"crm.deal.list.json", params=[
                ("filter[CATEGORY_ID]","34"), ("order[ID]","DESC"), ("start",str(start)),
                ("select[]","ID"), ("select[]","OPPORTUNITY")])
            d = r.json(); res = d.get("result") or []
            for deal in res:
                opp = deal.get("OPPORTUNITY")
                try:
                    val = float(opp) if opp not in (None,"") else None
                except Exception:
                    val = None
                if val is not None:
                    amounts[str(deal["ID"])] = val
            nxt = d.get("next")
            if nxt is None: break
            start = nxt
            await asyncio.sleep(0.2)
    print(f"Сумм получено из Bitrix: {len(amounts)}")
    conn = await asyncpg.connect(db_url())
    try:
        await conn.execute("ALTER TABLE houses ADD COLUMN IF NOT EXISTS amount_monthly numeric;")
        upd = 0
        for hid, val in amounts.items():
            res = await conn.execute("UPDATE houses SET amount_monthly=$1, updated_at=now() WHERE id=$2", val, hid)
            if res.endswith("1"): upd += 1
        print(f"Обновлено сумм в БД: {upd}")
        stats = await conn.fetchrow(
            "SELECT count(*) AS всего, count(amount_monthly) AS с_суммой, "
            "round(sum(amount_monthly)) AS суммарно FROM houses;")
        print(f"Домов: {stats['всего']}, с суммой: {stats['с_суммой']}, суммарно/мес: {stats['суммарно']} ₽")
    finally:
        await conn.close()

asyncio.run(main())
