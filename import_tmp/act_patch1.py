p = '/opt/audiobot/backend/app/services/max_cleaning_bot.py'
s = open(p, encoding='utf-8').read()

OLD = '''    rows = [
        [M.btn_callback("📸 Отправить фото уборки", f"photo:{h.id}")],
        [M.btn_callback("⬅️ В меню", "menu")],
    ]
    await (M.answer_callback(callback_id, new_text=_fmt_card(h), buttons=rows) if callback_id
           else M.send_message(chat_id, _fmt_card(h), buttons=rows))'''

NEW = '''    rows = [
        [M.btn_callback("📸 Отправить фото уборки", f"photo:{h.id}")],
        [M.btn_callback("📝 Акт подписан", f"act:{h.id}")],
        [M.btn_callback("⬅️ В меню", "menu")],
    ]
    await (M.answer_callback(callback_id, new_text=_fmt_card(h), buttons=rows) if callback_id
           else M.send_message(chat_id, _fmt_card(h), buttons=rows))'''

assert OLD in s, "карточка дома (кнопки) не найдена"
s = s.replace(OLD, NEW)
open(p, 'w', encoding='utf-8').write(s)
print("OK: кнопка 'Акт подписан' добавлена на карточку")
