p = '/opt/audiobot/backend/app/services/max_cleaning_bot.py'
s = open(p, encoding='utf-8').read()

# 1) Логировать сырой callback при получении (в handle_update)
OLD_RX = '''    elif ut == "message_callback":
        cb = update.get("callback", {})
        callback_id = cb.get("callback_id")
        payload = cb.get("payload", "")
        user_id = (cb.get("user") or {}).get("user_id")
        chat_id = ((update.get("message") or {}).get("recipient") or {}).get("chat_id")
        if callback_id:
            await handle_callback(chat_id, callback_id, payload, user_id)'''
NEW_RX = '''    elif ut == "message_callback":
        cb = update.get("callback", {})
        callback_id = cb.get("callback_id")
        payload = cb.get("payload", "")
        user_id = (cb.get("user") or {}).get("user_id")
        chat_id = ((update.get("message") or {}).get("recipient") or {}).get("chat_id")
        logger.info(f"[MAX cb] payload={payload!r} | len={len(payload)} | callback_id={callback_id!s:.20} | chat_id={chat_id} | user={user_id}")
        if callback_id:
            await handle_callback(chat_id, callback_id, payload, user_id)
        else:
            logger.warning(f"[MAX cb] нет callback_id! cb keys={list(cb.keys())}")'''
assert OLD_RX in s
s = s.replace(OLD_RX, NEW_RX)

# 2) Логировать вход в handle_callback и НЕОБРАБОТАННЫЕ payload
OLD_HC = '''async def handle_callback(chat_id, callback_id, payload, user_id=None):
    if payload == "menu":'''
NEW_HC = '''async def handle_callback(chat_id, callback_id, payload, user_id=None):
    logger.info(f"[MAX cb→handle] payload={payload!r} chat_id={chat_id} user={user_id}")
    if payload == "menu":'''
assert OLD_HC in s
s = s.replace(OLD_HC, NEW_HC)

# 3) Логировать ветку uk:
OLD_UK = '''    elif payload.startswith("uk:"):
        key = payload[3:]'''
NEW_UK = '''    elif payload.startswith("uk:"):
        key = payload[3:]
        logger.info(f"[MAX cb→uk] key={key!r} | в карте={key in _UK_BY_HASH} | размер карты={len(_UK_BY_HASH)}")'''
assert OLD_UK in s
s = s.replace(OLD_UK, NEW_UK)

# 4) В конец handle_callback добавим else — лог необработанных payload.
# Якорь — последняя ветка перед выходом. Найдём конец handle_callback.
# Лучше добавим явный else в конец цепочки elif. Ищем 'elif payload == "write":' — обычно одна из последних.
# Универсальнее: добавлю в самом конце функции через try-block? Проще — добавим явный else после "act_send".
# Но цепочка длинная. Сделаю иначе: проверим, есть ли явный else; если нет, добавим логгер по факту "unknown".
import re
# Найдём конец функции handle_callback — следующая def после неё
m = re.search(r'async def handle_callback\([^)]*\):(.+?)(?=\nasync def |\nclass |\Z)', s, re.S)
if m:
    body = m.group(1)
    if 'else:' not in body.split('payload == "write":')[-1] if 'payload == "write":' in body else True:
        # Вставим финальный else прямо после последней elif в handle_callback.
        # Найдём блок после "elif payload == \"write\":" до следующего "\nasync def"
        # Простейший способ: вставим логгер сразу перед "\nasync def handle_update"
        pass
# Универсально: добавим логгер в самый конец handle_callback через wrapper-маркер.
# Найдём строку с handle_update и вставим лог перед ней — НЕ годится (он сработает при импорте).
# Сделаем явно: после блока "write" (последняя ветка handle_callback).
OLD_END = '''    elif payload == "write":'''
# Заменим на: добавим перед write — общий fallback в конце через "else: log"
# Безопаснее: после "write"-блока добавить финальный else.
# Найдём блок:
m2 = re.search(r'(    elif payload == "write":\n(?:        .+\n)+)', s)
if m2 and '    else:\n        logger.warning(f"[MAX cb→handle] НЕОБРАБОТАН payload=' not in s:
    addition = '    else:\n        logger.warning(f"[MAX cb→handle] НЕОБРАБОТАН payload={payload!r}")\n'
    s = s[:m2.end()] + addition + s[m2.end():]

open(p, 'w', encoding='utf-8').write(s)
print("OK: подробное логирование callback включено")
