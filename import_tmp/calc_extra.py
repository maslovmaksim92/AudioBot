p = '/opt/audiobot/backend/app/routers/cleaning.py'
s = open(p, encoding='utf-8').read()

OLD = '''        a["avg_entrances_per_house"] = round(a["entrances"] / a["houses"], 1) if a["houses"] else 0'''
NEW = '''        a["avg_entrances_per_house"] = round(a["entrances"] / a["houses"], 1) if a["houses"] else 0
        a["avg_floors_per_house"] = round(a["floors"] / a["houses"], 1) if a["houses"] else 0
        a["revenue_per_house"] = round(a["revenue"] / a["houses"], 0) if a["houses"] else 0
        a["revenue_per_entrance"] = round(a["revenue"] / a["entrances"], 0) if a["entrances"] else 0
        a["completion_pct"] = round(a["fact_cleanings"] / a["plan_cleanings"] * 100, 1) if a["plan_cleanings"] else 0'''
assert OLD in s
s = s.replace(OLD, NEW)
open(p, 'w', encoding='utf-8').write(s)
print("OK: добавлены revenue_per_house/entrance, avg_floors, completion_pct")
