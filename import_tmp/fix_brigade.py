p = '/opt/audiobot/import_tmp/import_bitrix_may.py'
s = open(p, encoding='utf-8').read()

# 1) добавить загрузку имён пользователей (бригад) и резолв бригады из ASSIGNED_BY_ID
old_fetch = '''async def fetch_all_houses():
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
    return out'''

new_fetch = '''async def fetch_all_houses():
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
    return USER_NAMES'''

assert old_fetch in s
s = s.replace(old_fetch, new_fetch)

# 2) в deal_to_rec использовать имя пользователя для бригады и assigned_by_name
old_rec = '''    resp = deal.get("ASSIGNED_BY_NAME") or ""
    return {
        "id": rid, "bitrix_id": rid, "address": addr,
        "company_title": deal.get("COMPANY_TITLE") or None,
        "assigned_by_id": str(deal.get("ASSIGNED_BY_ID") or "") or None,
        "assigned_by_name": resp or None,
        "brigade_number": parse_brigade(resp),'''

new_rec = '''    uid = str(deal.get("ASSIGNED_BY_ID") or "")
    resp = USER_NAMES.get(uid) or deal.get("ASSIGNED_BY_NAME") or ""
    return {
        "id": rid, "bitrix_id": rid, "address": addr,
        "company_title": deal.get("COMPANY_TITLE") or None,
        "assigned_by_id": uid or None,
        "assigned_by_name": resp or None,
        "brigade_number": parse_brigade(resp),'''

assert old_rec in s
s = s.replace(old_rec, new_rec)

# 3) в main() вызвать fetch_user_names перед обработкой
old_main = '''    deals = await fetch_all_houses()
    print(f"Получено сделок: {len(deals)}")
    recs = [r for r in (deal_to_rec(d) for d in deals) if r]'''
new_main = '''    deals = await fetch_all_houses()
    print(f"Получено сделок: {len(deals)}")
    await fetch_user_names(deals)
    print(f"Загружено имён ответственных: {len(USER_NAMES)}")
    recs = [r for r in (deal_to_rec(d) for d in deals) if r]'''
assert old_main in s
s = s.replace(old_main, new_main)

open(p, 'w', encoding='utf-8').write(s)
print("OK: добавлен резолв бригады через user.get")
