"""
Клиентский MAX-бот VasDom (для УК / жителей / потенциальных клиентов).
Меню: Написать нам | График уборок | Сотрудничество.
Клиент выбирает дом из списка по УК (общая информация).
Обращения фиксируются в client_requests и передаются менеджеру.
"""
import os
import logging
from datetime import date, datetime, timezone
from typing import List, Dict, Any, Optional

from sqlalchemy import select, text as sa_text
from backend.app.config.database import AsyncSessionLocal
from backend.app.models.house import House
from backend.app.services.max_client import MaxBot, btn_callback, btn_link
from backend.app.services.max_service import pretty_uk

logger = logging.getLogger(__name__)

CLIENT_TOKEN = os.environ.get("MAX_CLIENT_BOT_TOKEN", "")
MANAGER_PHONE = os.environ.get("VASDOM_MANAGER_PHONE", "8 (4842) 75-08-75")
MANAGER_CONTACT = os.environ.get("VASDOM_MANAGER_CONTACT", "")  # напр. ссылка на чат менеджера в MAX
# Канал, куда дублируются обращения для менеджера (по умолчанию — общий канал фото)
MANAGER_CHANNEL_ID = os.environ.get("MAX_MANAGER_CHANNEL_ID", os.environ.get("MAX_PHOTOS_CHANNEL_ID", ""))

bot = MaxBot(CLIENT_TOKEN, name="max-client")

RU_MONTHS = {1: "january", 2: "february", 3: "march", 4: "april", 5: "may", 6: "june",
             7: "july", 8: "august", 9: "september", 10: "october", 11: "november", 12: "december"}
RU_MONTHS_NAME = {1: "январь", 2: "февраль", 3: "март", 4: "апрель", 5: "май", 6: "июнь",
                  7: "июль", 8: "август", 9: "сентябрь", 10: "октябрь", 11: "ноябрь", 12: "декабрь"}

# Сессия: режим (вопрос/сотрудничество)
_SESSIONS: Dict[int, Dict[str, Any]] = {}


async def _all_houses() -> List[House]:
    async with AsyncSessionLocal() as s:
        res = await s.execute(select(House))
        return list(res.scalars().all())


async def _house(house_id: str) -> Optional[House]:
    async with AsyncSessionLocal() as s:
        res = await s.execute(select(House).where(House.id == house_id))
        return res.scalar_one_or_none()


def _schedule_dates(h: House, year: int, month: int) -> List[Dict[str, str]]:
    sched = h.cleaning_schedule or {}
    return [i for i in (sched.get(f"{RU_MONTHS[month]}_{year}") or []) if i.get("date")]


def _fmt_schedule_full(h: House) -> str:
    """Полный график по всем доступным месяцам."""
    sched = h.cleaning_schedule or {}
    inv = {v: k for k, v in RU_MONTHS.items()}

    def _key(k):
        try:
            name, yr = k.rsplit("_", 1)
            return (int(yr), inv.get(name, 0))
        except Exception:
            return (0, 0)

    lines = [f"🏠 {h.address}"]
    if h.company_title:
        lines.append(f"🏢 {pretty_uk(h.company_title)}")
    months = sorted([k for k in sched.keys() if sched.get(k)], key=_key)
    if not months:
        lines.append("\n📅 График уборок пока не загружен.")
        return "\n".join(lines)
    for k in months:
        try:
            name, yr = k.rsplit("_", 1)
            title = f"{RU_MONTHS_NAME.get(inv.get(name, 0), name)} {yr}"
        except Exception:
            title = k
        lines.append(f"\n📅 {title}:")
        for it in sched[k]:
            try:
                dd = datetime.fromisoformat(it["date"]).strftime("%d.%m")
            except Exception:
                dd = it.get("date", "")
            t = it.get("type", "")
            short = "1 этаж" if "1 этаж" in t else ("все этажи" if "всех этаж" in t else t[:28])
            lines.append(f"  • {dd} — {short}" if short else f"  • {dd}")
    return "\n".join(lines)


# ---------- экраны ----------

def _main_menu():
    return [
        [btn_callback("✍️ Написать нам", "ask")],
        [btn_callback("📅 График уборок", "schedule")],
        [btn_callback("🤝 Сотрудничество", "partner")],
    ]


async def show_main_menu(chat_id, callback_id=None):
    txt = ("👋 Здравствуйте! Это бот компании ВасДом — уборка подъездов.\n"
           "Чем можем помочь?")
    if callback_id:
        await bot.answer_callback(callback_id, new_text=txt, buttons=_main_menu())
    else:
        await bot.send_message(chat_id, txt, buttons=_main_menu())


async def show_uk_list(chat_id, callback_id=None):
    houses = await _all_houses()
    uks = sorted({h.company_title for h in houses if h.company_title})
    rows = [[btn_callback(f"🏢 {pretty_uk(uk)[:38]}", f"uk:{uk}")] for uk in uks]
    rows.append([btn_callback("⬅️ Назад", "menu")])
    txt = "Выберите вашу управляющую компанию:" if uks else "Список домов пока пуст."
    await (bot.answer_callback(callback_id, new_text=txt, buttons=rows) if callback_id
           else bot.send_message(chat_id, txt, buttons=rows))


async def show_uk_houses(chat_id, uk, callback_id=None):
    houses = [h for h in await _all_houses() if h.company_title == uk]
    rows = [[btn_callback(f"🏠 {h.address[:40]}", f"d:{h.id}")] for h in houses[:30]]
    rows.append([btn_callback("⬅️ Назад", "schedule")])
    txt = f"🏢 {pretty_uk(uk)}\nВыберите дом:"
    await (bot.answer_callback(callback_id, new_text=txt, buttons=rows) if callback_id
           else bot.send_message(chat_id, txt, buttons=rows))


async def _is_subscribed(house_id, chat_id) -> bool:
    try:
        async with AsyncSessionLocal() as s:
            r = await s.execute(sa_text(
                "SELECT 1 FROM house_subscribers WHERE house_id=:h AND chat_id=:c"
            ), {"h": house_id, "c": chat_id})
            return r.first() is not None
    except Exception:
        return False


async def show_schedule(chat_id, house_id, callback_id=None):
    h = await _house(house_id)
    if not h:
        if callback_id:
            await bot.answer_callback(callback_id, text="Дом не найден")
        return
    subscribed = await _is_subscribed(house_id, chat_id)
    if subscribed:
        sub_btn = btn_callback("🔕 Не уведомлять об уборках", f"unsub:{house_id}")
    else:
        sub_btn = btn_callback("🔔 Уведомлять об уборках", f"sub:{house_id}")
    rows = [[sub_btn], [btn_callback("⬅️ К домам", "schedule")], [btn_callback("🏠 В меню", "menu")]]
    await (bot.answer_callback(callback_id, new_text=_fmt_schedule_full(h), buttons=rows) if callback_id
           else bot.send_message(chat_id, _fmt_schedule_full(h), buttons=rows))


async def subscribe_house(chat_id, user_id, house_id, callback_id):
    try:
        async with AsyncSessionLocal() as s:
            await s.execute(sa_text("""
                INSERT INTO house_subscribers (house_id, chat_id, user_id, created_at)
                VALUES (:h, :c, :u, :now)
                ON CONFLICT (house_id, chat_id) DO NOTHING
            """), {"h": house_id, "c": chat_id, "u": user_id,
                   "now": datetime.utcnow()})
            await s.commit()
    except Exception as e:
        logger.error(f"[max-client] subscribe: {e}")
    await show_schedule(chat_id, house_id, callback_id)


async def unsubscribe_house(chat_id, user_id, house_id, callback_id):
    try:
        async with AsyncSessionLocal() as s:
            await s.execute(sa_text(
                "DELETE FROM house_subscribers WHERE house_id=:h AND chat_id=:c"
            ), {"h": house_id, "c": chat_id})
            await s.commit()
    except Exception as e:
        logger.error(f"[max-client] unsubscribe: {e}")
    await show_schedule(chat_id, house_id, callback_id)


async def start_ask(chat_id, user_id, callback_id):
    _SESSIONS[user_id] = {"mode": "ask"}
    txt = ("✍️ Напишите ваше сообщение одним текстом — вопрос, замечание или просьбу.\n"
           "Мы передадим его менеджеру и ответим в течение рабочего дня.\n\n"
           f"📞 Срочно: {MANAGER_PHONE}")
    rows = [[btn_callback("⬅️ В меню", "menu")]]
    await bot.answer_callback(callback_id, new_text=txt, buttons=rows)


async def start_partner(chat_id, user_id, callback_id):
    _SESSIONS[user_id] = {"mode": "partner"}
    txt = ("🤝 Хотите, чтобы ВасДом убирал ваш дом или объект?\n\n"
           "Напишите одним сообщением: адрес, этажность, количество подъездов "
           "и контакт для связи. Менеджер подготовит расчёт и свяжется с вами.\n\n"
           f"📞 {MANAGER_PHONE}")
    rows = [[btn_callback("⬅️ В меню", "menu")]]
    if MANAGER_CONTACT:
        rows.insert(0, [btn_link("💼 Написать менеджеру", MANAGER_CONTACT)])
    await bot.answer_callback(callback_id, new_text=txt, buttons=rows)


async def _forward_to_manager(kind: str, user_id, chat_id, body_text: str):
    head = "✍️ ОБРАЩЕНИЕ КЛИЕНТА" if kind == "ask" else "🤝 ЗАЯВКА НА СОТРУДНИЧЕСТВО"
    payload = f"{head}\nchat_id={chat_id}, user_id={user_id}\n\n{body_text}"
    if MANAGER_CHANNEL_ID:
        try:
            await bot.send_message(int(MANAGER_CHANNEL_ID), payload)
        except Exception as e:
            logger.error(f"[max-client] forward_to_manager: {e}")
    # лог в БД
    try:
        async with AsyncSessionLocal() as s:
            await s.execute(sa_text("""
                INSERT INTO client_requests (kind, user_id, chat_id, body, created_at)
                VALUES (:k, :uid, :cid, :body, :now)
            """), {"k": kind, "uid": user_id, "cid": chat_id,
                   "body": body_text, "now": datetime.utcnow()})
            await s.commit()
    except Exception:
        # запасной путь — в общий logs
        try:
            async with AsyncSessionLocal() as s:
                await s.execute(sa_text("""
                    INSERT INTO logs (level, message, source, created_at)
                    VALUES ('info', :msg, :src, :now)
                """), {"msg": f"{head} (user {user_id}): {body_text}",
                       "src": f"max_client_{kind}", "now": datetime.utcnow()})
                await s.commit()
        except Exception as e:
            logger.error(f"[max-client] save request: {e}")


async def handle_text(chat_id, user_id, txt):
    sess = _SESSIONS.get(user_id)
    if not sess:
        # клиент пишет боту без выбора пункта — считаем это обращением «Написать нам»
        await _forward_to_manager("ask", user_id, chat_id, txt)
        await bot.send_message(
            chat_id,
            "✍️ Спасибо! Передали ваше сообщение менеджеру — ответим в течение рабочего дня.",
            buttons=[[btn_callback("🏠 В меню", "menu")]],
        )
        return
    mode = sess.get("mode")
    if mode in ("ask", "partner"):
        await _forward_to_manager(mode, user_id, chat_id, txt)
        _SESSIONS.pop(user_id, None)
        if mode == "ask":
            reply = "✍️ Спасибо! Передали менеджеру — ответим в течение рабочего дня."
        else:
            reply = "🤝 Спасибо! Заявка принята, менеджер свяжется с вами для расчёта."
        await bot.send_message(chat_id, reply, buttons=[[btn_callback("🏠 В меню", "menu")]])
    else:
        await show_main_menu(chat_id)


# ---------- роутинг ----------

async def handle_callback(chat_id, callback_id, payload, user_id=None):
    if payload == "menu":
        if user_id:
            _SESSIONS.pop(user_id, None)
        await show_main_menu(chat_id, callback_id)
    elif payload == "schedule":
        await show_uk_list(chat_id, callback_id)
    elif payload.startswith("uk:"):
        await show_uk_houses(chat_id, payload[3:], callback_id)
    elif payload.startswith("d:"):
        await show_schedule(chat_id, payload[2:], callback_id)
    elif payload.startswith("sub:"):
        await subscribe_house(chat_id, user_id, payload[4:], callback_id)
    elif payload.startswith("unsub:"):
        await unsubscribe_house(chat_id, user_id, payload[6:], callback_id)
    elif payload == "ask":
        await start_ask(chat_id, user_id, callback_id)
    elif payload == "partner":
        await start_partner(chat_id, user_id, callback_id)
    else:
        await bot.answer_callback(callback_id, text="Неизвестная команда")


def _chat_id_from_started(update: Dict[str, Any]):
    """MAX по-разному кладёт chat_id в bot_started — ищем во всех местах."""
    return (
        update.get("chat_id")
        or (update.get("chat") or {}).get("chat_id")
        or ((update.get("message") or {}).get("recipient") or {}).get("chat_id")
        or (update.get("user") or {}).get("user_id")
        or update.get("user_id")
    )


async def handle_update(update: Dict[str, Any]):
    ut = update.get("update_type")
    logger.info(f"[max-client DIAG] update_type={ut} keys={list(update.keys())}")
    if ut == "bot_started":
        chat_id = _chat_id_from_started(update)
        if chat_id:
            await show_main_menu(chat_id)
        else:
            logger.warning(f"[max-client] bot_started без chat_id: {update}")
    elif ut == "message_created":
        msg = update.get("message", {})
        chat_id = (msg.get("recipient") or {}).get("chat_id")
        sender = msg.get("sender") or {}
        user_id = sender.get("user_id")
        if sender.get("is_bot"):
            return
        body = msg.get("body") or {}
        txt = (body.get("text") or "").strip()
        sess = _SESSIONS.get(user_id) if user_id else None
        if txt:
            await handle_text(chat_id, user_id, txt)
        elif chat_id:
            await show_main_menu(chat_id)
    elif ut == "message_callback":
        cb = update.get("callback", {})
        callback_id = cb.get("callback_id")
        payload = cb.get("payload", "")
        user_id = (cb.get("user") or {}).get("user_id")
        chat_id = ((update.get("message") or {}).get("recipient") or {}).get("chat_id")
        if callback_id:
            await handle_callback(chat_id, callback_id, payload, user_id)
