p = '/opt/audiobot/backend/app/services/max_cleaning_bot.py'
s = open(p, encoding='utf-8').read()

# 1) callbacks для актов
OLD_CB = '''    elif payload.startswith("photo:"):
        await start_photo_collection(chat_id, payload[6:], callback_id, user_id)
    elif payload == "confirm":
        await confirm_send(chat_id, user_id, callback_id)
    elif payload == "send_photos":
        await send_collected_photos(chat_id, user_id, callback_id)'''

NEW_CB = '''    elif payload.startswith("photo:"):
        await start_photo_collection(chat_id, payload[6:], callback_id, user_id)
    elif payload == "confirm":
        await confirm_send(chat_id, user_id, callback_id)
    elif payload == "send_photos":
        await send_collected_photos(chat_id, user_id, callback_id)
    elif payload.startswith("act:"):
        await start_act_collection(chat_id, payload[4:], callback_id, user_id)
    elif payload == "act_confirm":
        await confirm_act_send(chat_id, user_id, callback_id)
    elif payload == "act_send":
        await send_act(chat_id, user_id, callback_id)'''

assert OLD_CB in s, "блок callback (photo/confirm/send) не найден"
s = s.replace(OLD_CB, NEW_CB)

# 2) приём фото акта в message_created (перед веткой awaiting_photo)
OLD_MSG = '''        if sess and sess.get("awaiting_photo") and has_attach and user_id:
            await collect_photo(chat_id, user_id, attachments, msg_id)
        elif sess and sess.get("awaiting_message") and text_in and user_id:
            await forward_message(chat_id, user_id, text_in)
        elif sess and sess.get("awaiting_photo"):
            n = len(sess.get("photos", []))
            await M.send_message(
                chat_id,
                f"📸 Жду фото (принято: {n}). Пришлите фото или нажмите «Отправить».",
                buttons=_collect_buttons(n),
            )'''

NEW_MSG = '''        if sess and sess.get("awaiting_act") and has_attach and user_id:
            await collect_act_photo(chat_id, user_id, attachments, msg_id)
        elif sess and sess.get("awaiting_photo") and has_attach and user_id:
            await collect_photo(chat_id, user_id, attachments, msg_id)
        elif sess and sess.get("awaiting_message") and text_in and user_id:
            await forward_message(chat_id, user_id, text_in)
        elif sess and sess.get("awaiting_act"):
            n = len(sess.get("act_photos", []))
            await M.send_message(
                chat_id,
                f"📝 Жду фото акта (принято: {n}). Пришлите фото или нажмите «Отправить акт».",
                buttons=_act_collect_buttons(n),
            )
        elif sess and sess.get("awaiting_photo"):
            n = len(sess.get("photos", []))
            await M.send_message(
                chat_id,
                f"📸 Жду фото (принято: {n}). Пришлите фото или нажмите «Отправить».",
                buttons=_collect_buttons(n),
            )'''

assert OLD_MSG in s, "блок message_created (awaiting_photo) не найден"
s = s.replace(OLD_MSG, NEW_MSG)

open(p, 'w', encoding='utf-8').write(s)
print("OK: роутинг актов подключён (callback + приём фото)")
