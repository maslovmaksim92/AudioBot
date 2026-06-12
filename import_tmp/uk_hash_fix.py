p = '/opt/audiobot/backend/app/services/max_cleaning_bot.py'
s = open(p, encoding='utf-8').read()

# 1) В начало модуля добавим карту хэшей УК и хелпер. Якорь — _SESSIONS (он точно есть).
anchor_top = "_SESSIONS"
assert anchor_top in s

helper = """# Карта хэш -> полное название УК (для callback-кнопок MAX,
# где имя может содержать кавычки/спецсимволы, ломающие payload).
_UK_BY_HASH = {}

def _uk_hash(name: str) -> str:
    import hashlib
    h = hashlib.md5((name or "").encode("utf-8")).hexdigest()[:10]
    _UK_BY_HASH[h] = name
    return h


"""
# вставим helper перед первым появлением _SESSIONS (это самое начало логики)
s = s.replace(anchor_top, helper + anchor_top, 1)

# 2) В show_uk_list используем хэш вместо полного имени в callback
OLD1 = '    rows = [[M.btn_callback(f"🏢 {M.pretty_uk(uk)[:38]}", f"uk:{uk}")] for uk in uks]'
NEW1 = '    rows = [[M.btn_callback(f"🏢 {M.pretty_uk(uk)[:38]}", f"uk:{_uk_hash(uk)}")] for uk in uks]'
assert OLD1 in s, "строка кнопок УК не найдена"
s = s.replace(OLD1, NEW1)

# 3) В обработчике callback "uk:..." — восстанавливаем имя по хэшу
OLD2 = '''    elif payload.startswith("uk:"):
        await show_uk_houses(chat_id, payload[3:], callback_id)'''
NEW2 = '''    elif payload.startswith("uk:"):
        key = payload[3:]
        # сначала пробуем как хэш, иначе как сырое имя (обратная совместимость со старыми callback)
        uk_name = _UK_BY_HASH.get(key, key)
        # если карта пуста (после рестарта) — прогреем её
        if uk_name == key and key and len(key) <= 10 and all(c in "0123456789abcdef" for c in key):
            try:
                _hs = await _all_houses()
                for _h in _hs:
                    if _h.company_title:
                        _uk_hash(_h.company_title)
                uk_name = _UK_BY_HASH.get(key, key)
            except Exception:
                pass
        await show_uk_houses(chat_id, uk_name, callback_id)'''
assert OLD2 in s, "обработчик uk: не найден"
s = s.replace(OLD2, NEW2)

open(p, 'w', encoding='utf-8').write(s)
print("OK: УК теперь передаются хэшем — кавычки не ломают callback")
