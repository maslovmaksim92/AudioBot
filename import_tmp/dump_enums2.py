import json
d = json.load(open('/tmp/uf.json'))
enum_map = {}
for f in d['result']:
    if f.get('USER_TYPE_ID') == 'enumeration':
        for it in f.get('LIST', []):
            v = it.get('VALUE','')
            if 'уборк' in v.lower() or 'подметан' in v.lower() or 'дезинфек' in v.lower():
                enum_map[str(it.get('ID'))] = v
json.dump(enum_map, open('/opt/audiobot/import_tmp/enum_types.json','w'), ensure_ascii=False, indent=1)
print("Типов уборки (id->текст):", len(enum_map))
# короткие коды для периодичности
shorts = {}
for eid, v in enum_map.items():
    vl = v.lower()
    if 'подметание' in vl and 'всех этажей' in vl:
        shorts[eid] = 'подметание+мытьё 1эт'   # подметание всех + мытьё 1 этажа
    elif 'лестничных площадок всех этажей' in vl:
        shorts[eid] = 'мытьё всех этажей'
    elif '1 этажа' in vl:
        shorts[eid] = 'мытьё 1 этажа'
    else:
        shorts[eid] = 'уборка'
json.dump(shorts, open('/opt/audiobot/import_tmp/enum_shorts.json','w'), ensure_ascii=False, indent=1)
print("Короткие коды:", len(set(shorts.values())), "вида:", set(shorts.values()))
