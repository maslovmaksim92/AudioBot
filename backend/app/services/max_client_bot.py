"""
Клиентский MAX-бот VasDom (для УК / старших по дому).
Меню: график своего дома | фотоотчёты | задать вопрос (AI) | заявка/жалоба.
Без строгой привязки: клиент выбирает дом из списка по УК (общая информация).
AI-ответы — через OpenClaw (подключим позже).
"""
import os
import logging
from datetime import date, datetime, timezone
from typing import List, Dict, Any, Optional

from sqlalchemy import select, text as sa_text
from backend.app.config.database import AsyncSessionLocal
from backend.app.models.house import House
from backend.app.services.max_client import MaxBot, btn_callback, btn_link

logger = logging.getLogger(__name__)

CLIENT_TOKEN = os.environ.get("MAX_CLIENT_BOT_TOKEN", "")
PHOTOS_CHANNEL_LINK = "https://max.ru/id4028069602_biz"

bot = MaxBot(CLIENT_TOKEN, name="max-client")

RU_MONTHS = {1: "january", 2: "february", 3: "march", 4: "april", 5: "may", 6: "june",
             7: "july", 8: "august", 9: "september", 10: "october", 11: "november", 12: "december"}
RU_MONTHS_NAME = {1: "январь", 2: "февраль", 3: "март", 4: "апрель", 5: "май", 6: "июнь",
                  7: "июль", 8: "август", 9: "сентябрь", 10: "октябрь", 11: "ноябрь", 12: "декабрь"}

# Сессия: какой дом выбрал клиент + режим (вопрос/заявка)
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


# ---------- экраны ----------

def _main_menu():
    return [
        [btn_callback("📅 График уборок", "schedule")],
        [btn_callback("📸 Фотоотчёты", "photos")],
        [btn_callback("💬 Задать вопрос", "ask")],
        [btn_callback("📝 Заявка / жалоба", "complaint")],
    ]


async def show_main_menu(chat_id, callback_id=None):
    txt = ("👋 Здравствуйте! Это бот компании ВасДом — уборка подъездов.\n"
           "Выберите, что вас интересует:")
    if callback_id:
        await bot.answer_callback(callback_id, new_text=txt, buttons=_main_menu())
    else:
        await bot.send_message(chat_id, txt, buttons=_main_menu())


async def show_uk_list(chat_id, action, callback_id=None):
    """Список УК. action = schedule | photos (что показываем после выбора дома)."""
    houses = await _all_houses()
    uks = sorted({h.company_title for h in houses if h.company_title})
    rows = [[btn_callback(f"🏢 {uk}", f"uk:{action}:{uk}")] for uk in uks]
    rows.append([btn_callback("⬅️ Назад", "menu")])
    txt = "Выберите вашу управляющую компанию:" if uks else "Список домов пока пуст."
    await (bot.answer_callback(callback_id, new_text=txt, buttons=rows) if callback_id
           else bot.send_message(chat_id, txt, buttons=rows))


async def show_uk_houses(chat_id, action, uk, callback_id=None):
    houses = [h for h in await _all_houses() if h.company_title == uk]
    rows = [[btn_callback(f"🏠 {h.address[:40]}", f"d:{action}:{h.id}")] for h in houses[:30]]
    rows.append([btn_callback("⬅️ Назад", f"act:{action}")])
    txt = f"🏢 {uk}\nВыберите дом:"
    await (bot.answer_callback(callback_id, new_text=txt, buttons=rows) if callback_id
           else bot.send_message(chat_id, txt, buttons=rows))


async def show_schedule(chat_id, house_id, callback_id=None):
    h = await _house(house_id)
    if not h:
        if callback_id:
            await bot.answer_callback(callback_id, text="Дом не найден")
        return
    now = datetime.now()
    items = _schedule_dates(h, now.year, now.month)
    lines = [f"🏠 {h.address}"]
    if h.company_title:
        lines.append(f"🏢 УК: {h.company_title}")
    if items:
        lines.append(f"\n📅 График уборок на {RU_MONTHS_NAME[now.month]} {now.year}:")
        for it in items:
            try:
                dd = datetime.fromisoformat(it["date"]).strftime("%d.%m")
            except Exception:
                dd = it["date"]
            t = it.get("type", "")
            lines.append(f"  • {dd} — {t}" if t else f"  • {dd}")
    else:
        lines.append("\n📅 На этот месяц график не заполнен.")
    rows = [[btn_callback("📸 Фотоотчёты", "photos")], [btn_callback("⬅️ В меню", "menu")]]
    await (bot.answer_callback(callback_id, new_text="\n".join(lines), buttons=rows) if callback_id
           else bot.send_message(chat_id, "\n".join(lines), buttons=rows))


async def show_photos(chat_id, house_id, callback_id=None):
    """Показать последние фотоотчёты дома + ссылку на публичный канал."""
    h = await _house(house_id)
    addr = h.address if h else "дом"
    # Берём последние записи из cleaning_photos
    rows_db = []
    try:
        async with AsyncSessionLocal() as s:
            res = await s.execute(sa_text("""
                SELECT cleaning_date, photo_count, sent_to_group_at
                FROM cleaning_photos
                WHERE house_id = :hid
                ORDER BY created_at DESC LIMIT 5
            """), {"hid": house_id})
            rows_db = res.fetchall()
    except Exception as e:
        logger.error(f"[max-client] photos query: {e}")

    lines = [f"📸 Фотоотчёты уборок:\n🏠 {addr}\n"]
    if rows_db:
        for cd, cnt, sent in rows_db:
            try:
                dd = cd.strftime("%d.%m.%Y")
            except Exception:
                dd = str(cd)
            mark = "✅ опубликовано" if sent else "загружено"
            lines.append(f"  • {dd} — {cnt} фото ({mark})")
    else:
        lines.append("Пока нет загруженных фотоотчётов по этому адресу.")
    lines.append(f"\nВсе фотоотчёты публикуются в нашем канале:")
    rows = [
        [btn_link("📷 Открыть канал с фото", PHOTOS_CHANNEL_LINK)],
        [btn_callback("⬅️ В меню", "menu")],
    ]
    await (bot.answer_callback(callback_id, new_text="\n".join(lines), buttons=rows) if callback_id
           else bot.send_message(chat_id, "\n".join(lines), buttons=rows))


async def start_ask(chat_id, user_id, callback_id):
    _SESSIONS[user_id] = {"mode": "ask"}
    txt = ("💬 Напишите ваш вопрос — например, «когда следующая уборка нашего дома?».\n"
           "(AI-ассистент скоро заработает; пока вопрос будет передан менеджеру.)")
    await bot.answer_callback(callback_id, new_text=txt, buttons=[[btn_callback("⬅️ В меню", "menu")]])


async def start_complaint(chat_id, user_id, callback_id):
    _SESSIONS[user_id] = {"mode": "complaint"}
    txt = ("📝 Опишите заявку или жалобу одним сообщением — например, «не убран 3-й подъезд».\n"
           "Мы зарегистрируем обращение.")
    await bot.answer_callback(callback_id, new_text=txt, buttons=[[btn_callback("⬅️ В меню", "menu")]])


async def handle_text(chat_id, user_id, txt):
    """Обработка текста в режимах вопрос/заявка."""
    sess = _SESSIONS.get(user_id)
    if not sess:
        await show_main_menu(chat_id)
        return
    mode = sess.get("mode")
    if mode == "complaint":
        # Регистрируем как лог-обращение (позже можно в задачи/Bitrix)
        try:
            async with AsyncSessionLocal() as s:
                await s.execute(sa_text("""
                    INSERT INTO logs (level, message, source, created_at)
                    VALUES ('info', :msg, 'max_client_complaint', :now)
                """), {"msg": f"Заявка от клиента (user {user_id}): {txt}",
                       "now": datetime.now(timezone.utc)})
                await s.commit()
        except Exception as e:
            logger.error(f"[max-client] complaint save: {e}")
        _SESSIONS.pop(user_id, None)
        await bot.send_message(chat_id, "✅ Спасибо! Ваше обращение зарегистрировано, мы рассмотрим его.",
                               buttons=[[btn_callback("⬅️ В меню", "menu")]])
    elif mode == "ask":
        # AI пока не подключён (OpenClaw) — фиксируем вопрос
        try:
            async with AsyncSessionLocal() as s:
                await s.execute(sa_text("""
                    INSERT INTO logs (level, message, source, created_at)
                    VALUES ('info', :msg, 'max_client_question', :now)
                """), {"msg": f"Вопрос клиента (user {user_id}): {txt}",
                       "now": datetime.now(timezone.utc)})
                await s.commit()
        except Exception as e:
            logger.error(f"[max-client] question save: {e}")
        _SESSIONS.pop(user_id, None)
        await bot.send_message(
            chat_id,
            "💬 Спасибо за вопрос! AI-ассистент скоро заработает, а пока ваш вопрос передан менеджеру.",
            buttons=[[btn_callback("⬅️ В меню", "menu")]],
        )
    else:
        await show_main_menu(chat_id)


# ---------- роутинг ----------

async def handle_callback(chat_id, callback_id, payload, user_id=None):
    if payload == "menu":
        if user_id:
            _SESSIONS.pop(user_id, None)
        await show_main_menu(chat_id, callback_id)
    elif payload == "schedule":
        await show_uk_list(chat_id, "schedule", callback_id)
    elif payload == "photos":
        await show_uk_list(chat_id, "photos", callback_id)
    elif payload == "ask":
        await start_ask(chat_id, user_id, callback_id)
    elif payload == "complaint":
        await start_complaint(chat_id, user_id, callback_id)
    elif payload.startswith("act:"):
        await show_uk_list(chat_id, payload[4:], callback_id)
    elif payload.startswith("uk:"):
        _, action, uk = payload.split(":", 2)
        await show_uk_houses(chat_id, action, uk, callback_id)
    elif payload.startswith("d:"):
        _, action, house_id = payload.split(":", 2)
        if action == "schedule":
            await show_schedule(chat_id, house_id, callback_id)
        else:
            await show_photos(chat_id, house_id, callback_id)
    else:
        await bot.answer_callback(callback_id, text="Неизвестная команда")


async def handle_update(update: Dict[str, Any]):
    ut = update.get("update_type")
    if ut == "bot_started":
        chat_id = update.get("chat_id")
        if chat_id:
            await show_main_menu(chat_id)
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
        if sess and txt:
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
