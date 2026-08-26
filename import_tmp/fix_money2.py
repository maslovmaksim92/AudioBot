p = '/opt/audiobot/backend/app/routers/cleaning.py'
s = open(p, encoding='utf-8').read()

# revenue по бригаде = сумма amount_monthly домов бригады (готовая стоимость из Bitrix)
OLD = '''        # стоимость по тарифу: уборок_в_мес * подъезды * цена_за_подъезд
        cnt, price = _parse_tariff(h.tariff)
        if cnt is not None and price is not None:
            a["tariff_known"] += 1
            ent = h.entrances_count or 0
            a["revenue"] += cnt * ent * price'''
NEW = '''        # выручка = месячная стоимость дома (amount_monthly из Bitrix OPPORTUNITY)
        amount = float(getattr(h, "amount_monthly", None) or 0)
        if amount:
            a["tariff_known"] += 1
            a["revenue"] += amount'''
assert OLD in s
s = s.replace(OLD, NEW)
open(p, 'w', encoding='utf-8').write(s)
print("OK: revenue в /brigade-calc = сумма amount_monthly")
