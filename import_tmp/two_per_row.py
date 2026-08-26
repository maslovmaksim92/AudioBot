p = '/opt/audiobot/backend/app/services/max_cleaning_bot.py'
s = open(p, encoding='utf-8').read()

# Заменим обе функции show_uk_houses и show_brigade_houses: 2 кнопки в ряд × 10 рядов = 20 на страницу.

OLD_UK = '''async def show_uk_houses(chat_id, uk, callback_id=None, page=1):
    houses = [h for h in await _all_houses() if h.company_title == uk]
    PAGE = 10
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

NEW_UK = '''async def show_uk_houses(chat_id, uk, callback_id=None, page=1):
    houses = [h for h in await _all_houses() if h.company_title == uk]
    PER_PAGE = 20   # 10 рядов × 2 кнопки
    total = len(houses)
    pages = max(1, (total + PER_PAGE - 1) // PER_PAGE)
    page = max(1, min(page, pages))
    start = (page - 1) * PER_PAGE
    chunk = houses[start:start + PER_PAGE]
    # пакуем по 2 кнопки в ряд (адрес покороче — 18 символов, чтобы помещался)
    rows = []
    for i in range(0, len(chunk), 2):
        row = [M.btn_callback(f"🏠 {chunk[i].address[:18]}", f"h:{chunk[i].id}")]
        if i + 1 < len(chunk):
            row.append(M.btn_callback(f"🏠 {chunk[i+1].address[:18]}", f"h:{chunk[i+1].id}"))
        rows.append(row)
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

OLD_BR = '''async def show_brigade_houses(chat_id, brigade, callback_id=None, page=1):
    houses = [h for h in await _all_houses() if h.brigade_number == brigade]
    PAGE = 10
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

NEW_BR = '''async def show_brigade_houses(chat_id, brigade, callback_id=None, page=1):
    houses = [h for h in await _all_houses() if h.brigade_number == brigade]
    PER_PAGE = 20   # 10 рядов × 2 кнопки
    total = len(houses)
    pages = max(1, (total + PER_PAGE - 1) // PER_PAGE)
    page = max(1, min(page, pages))
    start = (page - 1) * PER_PAGE
    chunk = houses[start:start + PER_PAGE]
    rows = []
    for i in range(0, len(chunk), 2):
        row = [M.btn_callback(f"🏠 {chunk[i].address[:18]}", f"h:{chunk[i].id}")]
        if i + 1 < len(chunk):
            row.append(M.btn_callback(f"🏠 {chunk[i+1].address[:18]}", f"h:{chunk[i+1].id}"))
        rows.append(row)
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

open(p, 'w', encoding='utf-8').write(s)
print("OK: 2 кнопки в ряд × 10 рядов = 20 домов на страницу")
