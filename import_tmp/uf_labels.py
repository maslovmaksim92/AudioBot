import json, re
d = json.load(open('/tmp/uf.json'))
fields = {f['FIELD_NAME']: f for f in d['result']}

# Для каждого даты-поля найдём метку и соседнее поле типа.
# Идём по ВСЕМ enumeration/string полям, ищем метки со словами месяцев.
RU_MON = ['январ','феврал','март','апрел','ма','июн','июл','август','сентябр','октябр','ноябр','декабр']

def label(f):
    for key in ('EDIT_FORM_LABEL','LIST_COLUMN_LABEL','LIST_FILTER_LABEL'):
        v = f.get(key)
        if isinstance(v, dict):
            v = v.get('ru') or v.get('en')
        if v:
            return v
    return ''

# выведем все поля, чья метка содержит 'уборк' или название месяца
print("=== Поля с метками про уборку/месяцы ===")
rows = []
for fn, f in fields.items():
    lbl = label(f)
    ll = lbl.lower()
    if 'уборк' in ll or 'убоки' in ll or 'тип убор' in ll:
        rows.append((fn, f.get('USER_TYPE_ID'), lbl))
for fn, t, lbl in sorted(rows, key=lambda x: x[2]):
    print(f"{fn} | {t:12} | {lbl}")
print(f"\nВсего полей про уборку: {len(rows)}")
