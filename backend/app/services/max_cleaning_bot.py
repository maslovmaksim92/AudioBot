"""
MAX-бот для уборщиц VasDom.
Меню: По УК | По бригадам | На сегодня → карточка адреса → отправка фото.
Работает на данных таблицы houses (cleaning_schedule по месяцам).
"""
import logging
import json
from datetime import date, datetime
from typing import List, Dict, Any, Optional

from sqlalchemy import select
from backend.app.config.database import AsyncSessionLocal
from backend.app.models.house import House
from backend.app.services import max_service as M

logger = logging.getLogger(__name__)

RU_MONTHS = {
    1: "january", 2: "february", 3: "march", 4: "april", 5: "may", 6: "june",
    7: "july", 8: "august", 9: "september", 10: "october", 11: "november", 12: "december",
}
RU_MONTHS_NAME = {
    1: "январь", 2: "февраль", 3: "март", 4: "апрель", 5: "май", 6: "июнь",
    7: "июль", 8: "август", 9: "сентябрь", 10: "октябрь", 11: "ноябрь", 12: "декабрь",
}


# ---------- работа с данными ----------

async def _all_houses() -> List[House]:
    async with AsyncSessionLocal() as s:
        res = await s.execute(select(House))
        return list(res.scalars().all())


async def _house(house_id: str) -> Optional[House]:
    async with AsyncSessionLocal() as s:
        res = await s.execute(select(House).where(House.id == house_id))
        return res.scalar_one_or_none()


def _schedule_dates(h: House, year: int, month: int) -> List[Dict[str, str]]:
    """Достать список {date,type} из cleaning_schedule для месяца."""
    sched = h.cleaning_schedule or {}
    key = f"{RU_MONTHS[month]}_{year}"
    items = sched.get(key) or []
    return [i for i in items if i.get("date")]


def _dates_for_today(houses: List[House], today: date) -> List[House]:
    iso = today.isoformat()
    out = []
    for h in houses:
        for it in _schedule_dates(h, today.year, today.month):
            if it["date"] == iso:
                out.append(h)
                break
    return out


def _fmt_card(h: House) -> str:
    """Текст карточки адреса."""
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
            d = it["date"]
            try:
                dd = datetime.fromisoformat(d).strftime("%d.%m")
            except Exception:
                dd = d
            t = it.get("type", "")
            lines.append(f"  • {dd} — {t}" if t else f"  • {dd}")
    else:
        lines.append("\n📅 На этот месяц уборки не запланированы")
    return "\n".join(lines)


# ---------- экраны меню ----------

def _main_menu_buttons():
    return [
        [M.btn_callback("📋 По УК", "uk")],
        [M.btn_callback("👷 По бригадам", "br")],
        [M.btn_callback("📅 Адреса на сегодня", "today")],
    ]


async def show_main_menu(chat_id: int):
    await M.send_message(
        chat_id,
        "👋 Добро пожаловать!\nВыберите, как искать адрес для уборки:",
        buttons=_main_menu_buttons(),
    )


async def show_uk_list(chat_id: int, callback_id: Optional[str] = None):
    houses = await _all_houses()
    uks = sorted({h.company_title for h in houses if h.company_title})
    rows = [[M.btn_callback(f"🏢 {uk}", f"uk:{uk}")] for uk in uks]
    rows.append([M.btn_callback("⬅️ Назад", "menu")])
    text = "Выберите управляющую компанию:" if uks else "Пока нет домов с указанной УК."
    if callback_id:
        await M.answer_callback(callback_id, new_text=text, buttons=rows)
    else:
        await M.send_message(chat_id, text, buttons=rows)


async def show_uk_houses(chat_id: int, uk: str, callback_id: Optional[str] = None):
    houses = [h for h in await _all_houses() if h.company_title == uk]
    rows = [[M.btn_callback(f"🏠 {h.address[:40]}", f"h:{h.id}")] for h in houses[:30]]
    rows.append([M.btn_callback("⬅️ Назад", "uk")])
    text = f"🏢 {uk}\nАдресов: {len(houses)}"
    if callback_id:
        await M.answer_callback(callback_id, new_text=text, buttons=rows)
    else:
        await M.send_message(chat_id, text, buttons=rows)


async def show_brigade_list(chat_id: int, callback_id: Optional[str] = None):
    houses = await _all_houses()
    brigades = sorted({h.brigade_number for h in houses if h.brigade_number}, key=lambda x: (len(x), x))
    rows = [[M.btn_callback(f"👷 Бригада {b}", f"br:{b}")] for b in brigades]
    rows.append([M.btn_callback("⬅️ Назад", "menu")])
    text = "Выберите бригаду:" if brigades else "Пока нет домов с назначенной бригадой."
    if callback_id:
        await M.answer_callback(callback_id, new_text=text, buttons=rows)
    else:
        await M.send_message(chat_id, text, buttons=rows)


async def show_brigade_houses(chat_id: int, brigade: str, callback_id: Optional[str] = None):
    houses = [h for h in await _all_houses() if h.brigade_number == brigade]
    rows = [[M.btn_callback(f"🏠 {h.address[:40]}", f"h:{h.id}")] for h in houses[:30]]
    rows.append([M.btn_callback("⬅️ Назад", "br")])
    text = f"👷 Бригада {brigade}\nАдресов: {len(houses)}"
    if callback_id:
        await M.answer_callback(callback_id, new_text=text, buttons=rows)
    else:
        await M.send_message(chat_id, text, buttons=rows)


async def show_today(chat_id: int, callback_id: Optional[str] = None):
    houses = await _all_houses()
    today = date.today()
    todays = _dates_for_today(houses, today)
    if todays:
        rows = [[M.btn_callback(f"🏠 {h.address[:40]}", f"h:{h.id}")] for h in todays[:30]]
        text = f"📅 На сегодня ({today.strftime('%d.%m.%Y')}) уборок: {len(todays)}"
    else:
        rows = []
        text = f"📅 На сегодня ({today.strftime('%d.%m.%Y')}) уборок не запланировано."
    rows.append([M.btn_callback("⬅️ Назад", "menu")])
    if callback_id:
        await M.answer_callback(callback_id, new_text=text, buttons=rows)
    else:
        await M.send_message(chat_id, text, buttons=rows)


async def show_house_card(chat_id: int, house_id: str, callback_id: Optional[str] = None):
    h = await _house(house_id)
    if not h:
        if callback_id:
            await M.answer_callback(callback_id, text="Адрес не найден")
        return
    text = _fmt_card(h)
    rows = [
        [M.btn_callback("📸 Отправить фото уборки", f"photo:{h.id}")],
        [M.btn_callback("⬅️ В меню", "menu")],
    ]
    if callback_id:
        await M.answer_callback(callback_id, new_text=text, buttons=rows)
    else:
        await M.send_message(chat_id, text, buttons=rows)


# ---------- роутинг callback ----------

async def handle_callback(chat_id: int, callback_id: str, payload: str):
    """Разобрать payload кнопки и показать нужный экран."""
    if payload == "menu":
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
        await M.answer_callback(
            callback_id,
            new_text="📸 Отправьте фото уборки одним сообщением (можно несколько).\nПосле загрузки они будут опубликованы с подписью адрес/дата.",
            buttons=[[M.btn_callback("⬅️ В меню", "menu")]],
        )
        # TODO: сохранить house_id в сессию пользователя для привязки фото
    else:
        await M.answer_callback(callback_id, text="Неизвестная команда")


async def handle_update(update: Dict[str, Any]):
    """Главная точка обработки события MAX."""
    ut = update.get("update_type")
    if ut == "bot_started":
        chat_id = update.get("chat_id")
        if chat_id:
            await show_main_menu(chat_id)
    elif ut == "message_created":
        msg = update.get("message", {})
        chat_id = (msg.get("recipient") or {}).get("chat_id") or msg.get("chat_id")
        body = (msg.get("body") or {}).get("text", "") if isinstance(msg.get("body"), dict) else msg.get("text", "")
        if chat_id and (body or "").strip().lower() in ("/start", "start", "меню", "menu"):
            await show_main_menu(chat_id)
        # TODO: обработка присланных фото (attachments с type=image)
    elif ut == "message_callback":
        cb = update.get("callback", {})
        callback_id = cb.get("callback_id")
        payload = cb.get("payload", "")
        chat_id = (update.get("message", {}).get("recipient") or {}).get("chat_id") or update.get("chat_id")
        if callback_id:
            await handle_callback(chat_id, callback_id, payload)
