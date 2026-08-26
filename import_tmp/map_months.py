import httpx, asyncio, re, json
from collections import defaultdict
WH = "https://vas-dom.bitrix24.ru/rest/1/oeo7d2sabsjxia70/"

# даты-поля по месяцам (из инспекции)
DATE_FIELDS = {
    "2025-10": ["UF_CRM_1741593004888","UF_CRM_1741593067418"],
    "2025-11": ["UF_CRM_1741593156926","UF_CRM_1741593231558","UF_CRM_1762319871625","UF_CRM_1762319986051"],
    "2025-12": ["UF_CRM_1762318428551","UF_CRM_1762318540952","UF_CRM_1762423667826","UF_CRM_1762423753267"],
    "2026-01": ["UF_CRM_1762425491572","UF_CRM_1762425599837","UF_CRM_1762429244903","UF_CRM_1762429330128"],
    "2026-02": ["UF_CRM_1769065381093","UF_CRM_1769065391092"],
    "2026-03": ["UF_CRM_1769065592561","UF_CRM_1769065612297"],
    "2026-04": ["UF_CRM_1773294498515","UF_CRM_1773294698704"],
    "2026-05": ["UF_CRM_1773293797362","UF_CRM_1773293874331"],
    "2026-06": ["UF_CRM_1778649976403","UF_CRM_1778650050859"],
    "2026-07": ["UF_CRM_1778650166501","UF_CRM_1778650234999"],
}

async def main():
    # берём дом, где много месяцев заполнено
    async with httpx.AsyncClient(timeout=60) as c:
        r = await c.get(WH+"crm.deal.list.json", params=[
            ("filter[CATEGORY_ID]","34"),("order[ID]","DESC"),("start","0"),("select[]","ID")])
        ids = [str(x['ID']) for x in (r.json().get('result') or [])][:60]
        # ищем дом с максимумом заполненных date-полей
        best=None; best_n=-1; best_data=None
        for did in ids:
            rr = await c.get(WH+"crm.deal.get.json", params={"id":did})
            d = rr.json().get('result') or {}
            n = sum(1 for fs in DATE_FIELDS.values() for f in fs if d.get(f))
            if n>best_n: best_n=n; best=did; best_data=d
            await asyncio.sleep(0.08)
    d = best_data
    print(f"Дом {best}: заполнено {best_n} дата-полей")
    # для каждого месяца показываем значение даты + значение СОСЕДНИХ enum-полей (тип)
    # перечислим все непустые UF, отсортируем по "числовому хвосту" имени
    uf = {k:v for k,v in d.items() if k.startswith('UF_CRM') and v not in (None,'',[],'0',0)}
    def tail(k): 
        m=re.search(r'(\d+)$', k); return int(m.group(1)) if m else 0
    ordered = sorted(uf.keys(), key=tail)
    # для каждого date-поля ищем ближайшее по ID enum-поле (значение-число = id типа)
    for mk, dfs in DATE_FIELDS.items():
        for df in dfs:
            if not d.get(df): continue
            dft = tail(df)
            # ищем enum-сосед: поле с близким ID и значением-числом (id enum типа)
            best_t=None; best_dist=10**9
            for k in uf:
                if k==df: continue
                v=uf[k]
                sv=str(v[0] if isinstance(v,list) else v)
                if re.fullmatch(r'\d{3,5}', sv):  # похоже на enum-id
                    dist=abs(tail(k)-dft)
                    if dist<best_dist: best_dist=dist; best_t=(k,sv)
            dval = d[df]; dval=dval[0] if isinstance(dval,list) else dval
            print(f"  {mk}: дата {df}={str(dval)[:10]} | ближайший тип {best_t}")
asyncio.run(main())
