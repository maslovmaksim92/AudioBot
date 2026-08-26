import json
d = json.load(open('/tmp/uf.json'))
# Все поля-типы уборки (enum), которые мы встретили
TYPE_FIELDS = [
    "UF_CRM_1741593047994","UF_CRM_1741593115407","UF_CRM_1741593210242",
    "UF_CRM_1762423723771","UF_CRM_1762429300919",
    "UF_CRM_1769065500025","UF_CRM_1769065563889","UF_CRM_1769065644299",
    "UF_CRM_1773294627855","UF_CRM_1773294751122",
    "UF_CRM_1773293854012","UF_CRM_1773293930779",
    "UF_CRM_1778650027948","UF_CRM_1778650210878",
    "UF_CRM_1769065764798","UF_CRM_1773294498515",
]
fields = {f['FIELD_NAME']: f for f in d['result']}
enum_map = {}
for fn in set(TYPE_FIELDS):
    f = fields.get(fn)
    if not f: continue
    for it in f.get('LIST', []):
        enum_map[str(it.get('ID'))] = it.get('VALUE')
# печатаем уникальные значения
print("=== Расшифровка enum-типов уборки ===")
seen=set()
for eid, val in sorted(enum_map.items()):
    if val in seen: continue
    seen.add(val)
    print(f"  {eid} = {val}")
print(f"\nВсего уникальных формулировок: {len(seen)}")
# сохраним полную карту id->текст
json.dump(enum_map, open('/opt/audiobot/import_tmp/enum_types.json','w'), ensure_ascii=False, indent=1)
print("Сохранено в enum_types.json:", len(enum_map), "id")
