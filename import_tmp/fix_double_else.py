p = '/opt/audiobot/backend/app/services/max_cleaning_bot.py'
s = open(p, encoding='utf-8').read()

OLD = '''    elif payload == "write":
        await start_write(chat_id, user_id, callback_id)
    else:
        logger.warning(f"[MAX cb→handle] НЕОБРАБОТАН payload={payload!r}")
    else:
        await M.answer_callback(callback_id, text="Неизвестная команда")'''
NEW = '''    elif payload == "write":
        await start_write(chat_id, user_id, callback_id)
    else:
        logger.warning(f"[MAX cb→handle] НЕОБРАБОТАН payload={payload!r}")
        await M.answer_callback(callback_id, text="Неизвестная команда")'''
assert OLD in s
s = s.replace(OLD, NEW)
open(p, 'w', encoding='utf-8').write(s)
print("OK: двойной else убран")
