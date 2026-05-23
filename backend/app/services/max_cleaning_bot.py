"""
MAX-бот для уборщиц VasDom (один общий бот на всех).
Меню: По УК | По бригадам | На сегодня → карточка адреса → отправка фото.
Фото публикуются в канал с подписью адрес/дата + фиксируются в cleaning_photos.
Бригада берётся из поля brigade_number (из «Ответственный» Bitrix).
"""
import os
import logging
from datetime import date, datetime, timezone
from typing import List, Dict, Any, Optional

from sqlalchemy import select, text as sa_text
from backend.app.config.database import AsyncSessionLocal
from backend.app.models.house import House
from backend.app.services import max_service as M

logger = logging.getLogger(__name__)

MAX_PHOTOS_CHANNEL_ID = os.environ.get("MAX_PHOTOS_CHANNEL_ID", "")

RU_MONTHS = {1: "january", 2: "february", 3: "march", 4: "april", 5: "may", 6: "june",
             7: "july", 8: "august", 9: "september", 10: "october", 11: "november", 12: "december"}
RU_MONTHS_NAME = {1: "январь", 2: "февраль", 3: "март", 4: "апрель", 5: "май", 6: "июнь",
                  7: "июль", 8: "август", 9: "сентябрь", 10: "октябрь", 11: "ноябрь", 12: "декабрь"}

# Простая in-memory сессия: какой дом выбрал пользователь для отправки фото
# {user_id: {"house_id": str, "awaiting_photo": bool}}
_SESSIONS: Dict[int, Dict[str, Any]] = {}


# ---------- данные ----------

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
    key = f"{RU_MONTHS[month]}_{year}"
    return [i for i in (sched.get(key) or []) if i.get("date")]


def _dates_for_today(houses: List[House], today: date) -> List[House]:
    iso = today.isoformat()
    out = []
    for h in houses:
        for it in _schedule_dates(h, today.year, today.month):
            if it["date"] == iso:
                out.append(h); break
    return out


def _fmt_card(h: House) -> str:
    lines = [f"🏠 {h.address}"]
    if h.company_title:
        lines.append(f"🏢 УК: {h.company_title}")
    if h.brigade_number:
        lines.append(f"👷 Бригада: {h.brigade_number}")
    if h.entrances_count:
        lines.append(f"🚪 Подъездов: {h.entrances_count}")
    now = datetime.now()
    items = _schedule_dates(h, now.year, now.month)
    if items:
        lines.append(f"\n📅 Уборки на {RU_MONTHS_NAME[now.month]} {now.year}:")
        for it in items:
            try:
                dd = datetime.fromisoformat(it["date"]).strftime("%d.%m")
            except Exception:
                dd = it["date"]
            t = it.get("type", "")
            lines.append(f"  • {dd} — {t}" if t else f"  • {dd}")
    else:
        lines.append("\n📅 На этот месяц уборки не запланированы")
    return "\n".join(lines)


# ---------- экраны ----------

def _main_menu_buttons():
    return [
        [M.btn_callback("📋 По УК", "uk")],
        [M.btn_callback("👷 По бригадам", "br")],
        [M.btn_callback("📅 Адреса на сегодня", "today")],
    ]


async def show_main_menu(chat_id: int, callback_id: Optional[str] = None):
    txt = "👋 Добро пожаловать!\nВыберите, как искать адрес для уборки:"
    if callback_id:
        await M.answer_callback(callback_id, new_text=txt, buttons=_main_menu_buttons())
    else:
        await M.send_message(chat_id, txt, buttons=_main_menu_buttons())


async def show_uk_list(chat_id, callback_id=None):
    houses = await _all_houses()
    uks = sorted({h.company_title for h in houses if h.company_title})
    rows = [[M.btn_callback(f"🏢 {uk}", f"uk:{uk}")] for uk in uks]
    rows.append([M.btn_callback("⬅️ Назад", "menu")])
    txt = "Выберите управляющую компанию:" if uks else "Пока нет домов с указанной УК."
    await (M.answer_callback(callback_id, new_text=txt, buttons=rows) if callback_id
           else M.send_message(chat_id, txt, buttons=rows))


async def show_uk_houses(chat_id, uk, callback_id=None):
    houses = [h for h in await _all_houses() if h.company_title == uk]
    rows = [[M.btn_callback(f"🏠 {h.address[:40]}", f"h:{h.id}")] for h in houses[:30]]
    rows.append([M.btn_callback("⬅️ Назад", "uk")])
    txt = f"🏢 {uk}\nАдресов: {len(houses)}"
    await (M.answer_callback(callback_id, new_text=txt, buttons=rows) if callback_id
           else M.send_message(chat_id, txt, buttons=rows))


async def show_brigade_list(chat_id, callback_id=None):
    houses = await _all_houses()
    brigades = sorted({h.brigade_number for h in houses if h.brigade_number}, key=lambda x: (len(x), x))
    rows = [[M.btn_callback(f"👷 Бригада {b}", f"br:{b}")] for b in brigades]
    rows.append([M.btn_callback("⬅️ Назад", "menu")])
    txt = "Выберите бригаду:" if brigades else "Пока нет домов с назначенной бригадой."
    await (M.answer_callback(callback_id, new_text=txt, buttons=rows) if callback_id
           else M.send_message(chat_id, txt, buttons=rows))


async def show_brigade_houses(chat_id, brigade, callback_id=None):
    houses = [h for h in await _all_houses() if h.brigade_number == brigade]
    rows = [[M.btn_callback(f"🏠 {h.address[:40]}", f"h:{h.id}")] for h in houses[:30]]
    rows.append([M.btn_callback("⬅️ Назад", "br")])
    txt = f"👷 Бригада {brigade}\nАдресов: {len(houses)}"
    await (M.answer_callback(callback_id, new_text=txt, buttons=rows) if callback_id
           else M.send_message(chat_id, txt, buttons=rows))


async def show_today(chat_id, callback_id=None):
    houses = await _all_houses()
    today = date.today()
    todays = _dates_for_today(houses, today)
    if todays:
        rows = [[M.btn_callback(f"🏠 {h.address[:40]}", f"h:{h.id}")] for h in todays[:30]]
        txt = f"📅 На сегодня ({today.strftime('%d.%m.%Y')}) уборок: {len(todays)}"
    else:
        rows = []
        txt = f"📅 На сегодня ({today.strftime('%d.%m.%Y')}) уборок не запланировано."
    rows.append([M.btn_callback("⬅️ Назад", "menu")])
    await (M.answer_callback(callback_id, new_text=txt, buttons=rows) if callback_id
           else M.send_message(chat_id, txt, buttons=rows))


async def show_house_card(chat_id, house_id, callback_id=None):
    h = await _house(house_id)
    if not h:
        if callback_id:
            await M.answer_callback(callback_id, text="Адрес не найден")
        return
    rows = [
        [M.btn_callback("📸 Отправить фото уборки", f"photo:{h.id}")],
        [M.btn_callback("⬅️ В меню", "menu")],
    ]
    await (M.answer_callback(callback_id, new_text=_fmt_card(h), buttons=rows) if callback_id
           else M.send_message(chat_id, _fmt_card(h), buttons=rows))


# ---------- приём фото ----------

def _today_cleaning_label(h: House) -> str:
    """Подобрать дату уборки для подписи: сегодня, иначе ближайшую в этом месяце."""
    now = datetime.now()
    items = _schedule_dates(h, now.year, now.month)
    iso = date.today().isoformat()
    for it in items:
        if it["date"] == iso:
            return datetime.fromisoformat(it["date"]).strftime("%d.%m.%Y")
    return date.today().strftime("%d.%m.%Y")


async def handle_photos(chat_id: int, user_id: int, image_attachments: List[Dict[str, Any]]):
    """Принять фото от уборщицы, опубликовать в канал, зафиксировать в БД."""
    sess = _SESSIONS.get(user_id)
    if not sess or not sess.get("awaiting_photo") or not sess.get("house_id"):
        await M.send_message(
            chat_id,
            "📸 Сначала выберите адрес и нажмите «Отправить фото уборки», затем пришлите фото.",
            buttons=[[M.btn_callback("📋 В меню", "menu")]],
        )
        return

    h = await _house(sess["house_id"])
    if not h:
        await M.send_message(chat_id, "❌ Адрес не найден. Откройте меню заново.",
                             buttons=[[M.btn_callback("📋 В меню", "menu")]])
        return

    tokens = [a["payload"]["token"] for a in image_attachments
              if a.get("type") == "image" and a.get("payload", {}).get("token")]
    if not tokens:
        await M.send_message(chat_id, "❌ Не удалось получить фото, попробуйте ещё раз.")
        return

    date_label = _today_cleaning_label(h)
    caption = f"🏠 {h.address}\n📅 {date_label}"
    if h.company_title:
        caption += f"\n🏢 {h.company_title}"
    if h.brigade_number:
        caption += f"\n👷 Бригада {h.brigade_number}"

    # 1) публикуем в канал
    published = False
    if MAX_PHOTOS_CHANNEL_ID:
        res = await M.send_photos(int(MAX_PHOTOS_CHANNEL_ID), tokens, caption)
        published = bool(res and not res.get("code"))

    # 2) фиксируем в БД (cleaning_photos)
    try:
        async with AsyncSessionLocal() as s:
            await s.execute(sa_text("""
                INSERT INTO cleaning_photos
                  (house_id, house_address, brigade_id, telegram_user_id,
                   cleaning_date, photo_file_ids, photo_count, ai_caption, status,
                   sent_to_group_at, created_at, updated_at)
                VALUES
                  (:hid, :addr, :brig, :uid, :cdate, :tokens, :cnt, :cap, :status,
                   :sent_at, :now, :now)
                ON CONFLICT (house_id, cleaning_date, brigade_id) DO UPDATE SET
                   photo_file_ids = EXCLUDED.photo_file_ids,
                   photo_count = EXCLUDED.photo_count,
                   status = EXCLUDED.status,
                   updated_at = EXCLUDED.updated_at
            """), {
                "hid": h.id, "addr": h.address, "brig": h.brigade_number,
                "uid": user_id, "cdate": date.today(),
                "tokens": tokens, "cnt": len(tokens), "cap": caption,
                "status": "sent_to_group" if published else "uploaded",
                "sent_at": datetime.now(timezone.utc) if published else None,
                "now": datetime.now(timezone.utc),
            })
            await s.commit()
    except Exception as e:
        logger.error(f"[MAX bot] не удалось записать cleaning_photos: {e}")

    # 3) подтверждаем уборщице
    _SESSIONS.pop(user_id, None)
    if published:
        msg = f"✅ Принято {len(tokens)} фото!\n{h.address} — {date_label}\nОпубликовано в канал отчётов."
    else:
        msg = f"✅ Принято {len(tokens)} фото для:\n{h.address} — {date_label}\n(зафиксировано в системе)"
    await M.send_message(chat_id, msg, buttons=[[M.btn_callback("📋 В меню", "menu")]])


# ---------- роутинг ----------

async def handle_callback(chat_id, callback_id, payload, user_id=None):
    if payload == "menu":
        if user_id:
            _SESSIONS.pop(user_id, None)
        await M.answer_callback(callback_id, new_text="👋 Главное меню:", buttons=_main_menu_buttons())
    elif payload == "uk":
        await show_uk_list(chat_id, callback_id)
    elif payload.startswith("uk:"):
        await show_uk_houses(chat_id, payload[3:], callback_id)
    elif payload == "br":
        await show_brigade_list(chat_id, callback_id)
    elif payload.startswith("br:"):
        await show_brigade_houses(chat_id, payload[3:], callback_id)
    elif payload == "today":
        await show_today(chat_id, callback_id)
    elif payload.startswith("h:"):
        await show_house_card(chat_id, payload[2:], callback_id)
    elif payload.startswith("photo:"):
        house_id = payload[6:]
        if user_id:
            _SESSIONS[user_id] = {"house_id": house_id, "awaiting_photo": True}
        await M.answer_callback(
            callback_id,
            new_text="📸 Пришлите фото уборки (можно несколько одним сообщением).\nОни будут опубликованы в канал с адресом и датой.",
            buttons=[[M.btn_callback("⬅️ В меню", "menu")]],
        )
    else:
        await M.answer_callback(callback_id, text="Неизвестная команда")


async def handle_update(update: Dict[str, Any]):
    ut = update.get("update_type")

    if ut == "bot_started":
        chat_id = update.get("chat_id")
        if chat_id:
            await show_main_menu(chat_id)

    elif ut == "message_created":
        msg = update.get("message", {})
        recipient = msg.get("recipient") or {}
        chat_id = recipient.get("chat_id")
        sender = msg.get("sender") or {}
        user_id = sender.get("user_id")
        body = msg.get("body") or {}
        attachments = body.get("attachments") or []
        images = [a for a in attachments if a.get("type") == "image"]

        # Не реагируем на сообщения от самого бота
        if sender.get("is_bot"):
            return

        if images and user_id:
            await handle_photos(chat_id, user_id, images)
        else:
            # Любое текстовое сообщение → показываем меню (без необходимости /start)
            if chat_id:
                await show_main_menu(chat_id)

    elif ut == "message_callback":
        cb = update.get("callback", {})
        callback_id = cb.get("callback_id")
        payload = cb.get("payload", "")
        user_id = (cb.get("user") or {}).get("user_id")
        chat_id = ((update.get("message") or {}).get("recipient") or {}).get("chat_id")
        if callback_id:
            await handle_callback(chat_id, callback_id, payload, user_id)
