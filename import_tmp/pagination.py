p = '/opt/audiobot/backend/app/services/max_cleaning_bot.py'
s = open(p, encoding='utf-8').read()

# Лимит MAX на ряды клавиатуры = ~10. Берём 8 домов на страницу + ряды навигации.
PAGE = 8

# 1) show_uk_houses — пагинация
OLD_UK = '''async def show_uk_houses(chat_id, uk, callback_id=None):
    houses = [h for h in await _all_houses() if h.company_title == uk]
    rows = [[M.btn_callback(f"🏠 {h.address[:40]}", f"h:{h.id}")] for h in houses[:30]]
    rows.append([M.btn_callback("⬅️ Назад", "uk")])
    txt = f"🏢 {M.pretty_uk(uk)}\\nАдресов: {len(houses)}"
    await (M.answer_callback(callback_id, new_text=txt, buttons=rows) if callback_id
           else M.send_message(chat_id, txt, buttons=rows))'''

NEW_UK = '''async def show_uk_houses(chat_id, uk, callback_id=None, page=1):
    houses = [h for h in await _all_houses() if h.company_title == uk]
    PAGE = 8
    total = len(houses)
    pages = max(1, (total + PAGE - 1) // PAGE)
    page = max(1, min(page, pages))
    start = (page - 1) * PAGE
    chunk = houses[start:start + PAGE]
    rows = [[M.btn_callback(f"🏠 {h.address[:38]}", f"h:{h.id}")] for h in chunk]
    # навигация (если страниц больше одной)
    if pages > 1:
        uk_h = _uk_hash(uk)
        nav = []
        if page > 1:
            nav.append(M.btn_callback("◀️", f"uk:{uk_h}:p{page-1}"))
        nav.append(M.btn_callback(f"{page}/{pages}", "noop"))
        if page < pages:
            nav.append(M.btn_callback("▶️", f"uk:{uk_h}:p{page+1}"))
        rows.append(nav)
    rows.append([M.btn_callback("⬅️ Назад", "uk")])
    txt = f"🏢 {M.pretty_uk(uk)}\\nАдресов: {total}" + (f"  (стр. {page}/{pages})" if pages > 1 else "")
    await (M.answer_callback(callback_id, new_text=txt, buttons=rows) if callback_id
           else M.send_message(chat_id, txt, buttons=rows))'''

assert OLD_UK in s
s = s.replace(OLD_UK, NEW_UK)

# 2) show_brigade_houses — пагинация
OLD_BR = '''async def show_brigade_houses(chat_id, brigade, callback_id=None):
    houses = [h for h in await _all_houses() if h.brigade_number == brigade]
    rows = [[M.btn_callback(f"🏠 {h.address[:40]}", f"h:{h.id}")] for h in houses[:30]]
    rows.append([M.btn_callback("⬅️ Назад", "br")])
    txt = f"👷 Бригада {brigade}\\nАдресов: {len(houses)}"
    await (M.answer_callback(callback_id, new_text=txt, buttons=rows) if callback_id
           else M.send_message(chat_id, txt, buttons=rows))'''

NEW_BR = '''async def show_brigade_houses(chat_id, brigade, callback_id=None, page=1):
    houses = [h for h in await _all_houses() if h.brigade_number == brigade]
    PAGE = 8
    total = len(houses)
    pages = max(1, (total + PAGE - 1) // PAGE)
    page = max(1, min(page, pages))
    start = (page - 1) * PAGE
    chunk = houses[start:start + PAGE]
    rows = [[M.btn_callback(f"🏠 {h.address[:38]}", f"h:{h.id}")] for h in chunk]
    if pages > 1:
        nav = []
        if page > 1:
            nav.append(M.btn_callback("◀️", f"br:{brigade}:p{page-1}"))
        nav.append(M.btn_callback(f"{page}/{pages}", "noop"))
        if page < pages:
            nav.append(M.btn_callback("▶️", f"br:{brigade}:p{page+1}"))
        rows.append(nav)
    rows.append([M.btn_callback("⬅️ Назад", "br")])
    txt = f"👷 Бригада {brigade}\\nАдресов: {total}" + (f"  (стр. {page}/{pages})" if pages > 1 else "")
    await (M.answer_callback(callback_id, new_text=txt, buttons=rows) if callback_id
           else M.send_message(chat_id, txt, buttons=rows))'''

assert OLD_BR in s
s = s.replace(OLD_BR, NEW_BR)

# 3) обработчик uk: — поддержка "uk:<hash>:p<N>"
OLD_HUK = '''    elif payload.startswith("uk:"):
        key = payload[3:]
        logger.info(f"[MAX cb→uk] key={key!r} | в карте={key in _UK_BY_HASH} | размер карты={len(_UK_BY_HASH)}")
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

NEW_HUK = '''    elif payload.startswith("uk:"):
        rest = payload[3:]
        # формат: uk:<key>  или  uk:<key>:p<N>
        page = 1
        if ":p" in rest:
            rest, _, pp = rest.rpartition(":p")
            try: page = int(pp)
            except: page = 1
        key = rest
        logger.info(f"[MAX cb→uk] key={key!r} page={page} | в карте={key in _UK_BY_HASH} | размер карты={len(_UK_BY_HASH)}")
        uk_name = _UK_BY_HASH.get(key, key)
        if uk_name == key and key and len(key) <= 10 and all(c in "0123456789abcdef" for c in key):
            try:
                _hs = await _all_houses()
                for _h in _hs:
                    if _h.company_title:
                        _uk_hash(_h.company_title)
                uk_name = _UK_BY_HASH.get(key, key)
            except Exception:
                pass
        await show_uk_houses(chat_id, uk_name, callback_id, page=page)'''

assert OLD_HUK in s
s = s.replace(OLD_HUK, NEW_HUK)

# 4) обработчик br: — поддержка "br:<N>:p<P>"
OLD_HBR = '''    elif payload.startswith("br:"):
        await show_brigade_houses(chat_id, payload[3:], callback_id)'''
NEW_HBR = '''    elif payload.startswith("br:"):
        rest = payload[3:]
        page = 1
        if ":p" in rest:
            rest, _, pp = rest.rpartition(":p")
            try: page = int(pp)
            except: page = 1
        await show_brigade_houses(chat_id, rest, callback_id, page=page)'''
assert OLD_HBR in s
s = s.replace(OLD_HBR, NEW_HBR)

# 5) "noop" — игнор-кнопка (индикатор страницы)
OLD_END = '''    elif payload == "write":
        await start_write(chat_id, user_id, callback_id)'''
NEW_END = '''    elif payload == "write":
        await start_write(chat_id, user_id, callback_id)
    elif payload == "noop":
        await M.answer_callback(callback_id, text="")'''
assert OLD_END in s
s = s.replace(OLD_END, NEW_END)

open(p, 'w', encoding='utf-8').write(s)
print("OK: пагинация для УК и бригад (8 кнопок на страницу)")
