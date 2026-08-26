"""
MAX-бот для уборщиц VasDom (neuro). Только для сотрудников:
Меню: По УК | По бригадам | На сегодня → карточка адреса → сбор фото →
подтверждение → отправка. После отправки можно сразу отправить для другого адреса.

Сбор фото: уборщица грузит несколько фото (в т.ч. как файлы .png/.jpg),
они копятся в буфер, затем кнопка «Отправить» → подтверждение адреса →
публикация в канал + запись в cleaning_photos + уведомление подписчиков дома.
Вход без /start: bot_started и любое сообщение показывают меню.
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
# Ссылка на клиентский бот (Тестировщик) — для кнопки «Задать вопрос» под постом
CLIENT_BOT_LINK = os.environ.get("MAX_CLIENT_BOT_LINK", "https://max.ru/id4028069602_1_bot")

RU_MONTHS = {1: "january", 2: "february", 3: "march", 4: "april", 5: "may", 6: "june",
             7: "july", 8: "august", 9: "september", 10: "october", 11: "november", 12: "december"}
RU_MONTHS_NAME = {1: "январь", 2: "февраль", 3: "март", 4: "апрель", 5: "май", 6: "июнь",
                  7: "июль", 8: "август", 9: "сентябрь", 10: "октябрь", 11: "ноябрь", 12: "декабрь"}

# {user_id: {"house_id","awaiting_photo","photos":[...],"seen_msg_ids":set,"awaiting_message":bool}}
# Карта хэш -> полное название УК (для callback-кнопок MAX,
# где имя может содержать кавычки/спецсимволы, ломающие payload).
_UK_BY_HASH = {}

def _uk_hash(name: str) -> str:
    import hashlib
    h = hashlib.md5((name or "").encode("utf-8")).hexdigest()[:10]
    _UK_BY_HASH[h] = name
    return h


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
        lines.append(f"🏢 УК: {M.pretty_uk(h.company_title)}")
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


# ---------- меню ----------

def _main_menu_buttons():
    return [
        [M.btn_callback("📅 Адреса на сегодня", "today")],
        [M.btn_callback("📋 По УК", "uk")],
        [M.btn_callback("👷 По бригадам", "br")],
        [M.btn_callback("✍️ Написать боту", "write")],
    ]


async def show_main_menu(chat_id, callback_id=None):
    txt = ("👋 Здравствуйте! Это бот для уборки подъездов.\n"
           "Выберите адрес — и отправьте фото уборки.")
    await (M.answer_callback(callback_id, new_text=txt, buttons=_main_menu_buttons()) if callback_id
           else M.send_message(chat_id, txt, buttons=_main_menu_buttons()))


async def show_uk_list(chat_id, callback_id=None):
    houses = await _all_houses()
    uks = sorted({h.company_title for h in houses if h.company_title})
    rows = [[M.btn_callback(f"🏢 {M.pretty_uk(uk)[:38]}", f"uk:{_uk_hash(uk)}")] for uk in uks]
    rows.append([M.btn_callback("⬅️ Назад", "menu")])
    txt = "Выберите управляющую компанию:" if uks else "Пока нет домов с указанной УК."
    await (M.answer_callback(callback_id, new_text=txt, buttons=rows) if callback_id
           else M.send_message(chat_id, txt, buttons=rows))


async def show_uk_houses(chat_id, uk, callback_id=None, page=1):
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
    txt = f"🏢 {M.pretty_uk(uk)}\nАдресов: {total}" + (f"  (стр. {page}/{pages})" if pages > 1 else "")
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


async def show_brigade_houses(chat_id, brigade, callback_id=None, page=1):
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
    txt = f"👷 Бригада {brigade}\nАдресов: {total}" + (f"  (стр. {page}/{pages})" if pages > 1 else "")
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
        txt = f"📅 На сегодня ({today.strftime('%d.%m.%Y')}) уборок не запланировано.\nМожно выбрать адрес через «По УК» или «По бригадам»."
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
        [M.btn_callback("📝 Акт подписан", f"act:{h.id}")],
        [M.btn_callback("⬅️ В меню", "menu")],
    ]
    await (M.answer_callback(callback_id, new_text=_fmt_card(h), buttons=rows) if callback_id
           else M.send_message(chat_id, _fmt_card(h), buttons=rows))


# ---------- сбор и отправка фото ----------

def _collect_buttons(count: int):
    rows = []
    if count > 0:
        rows.append([M.btn_callback(f"✅ Отправить ({count} фото)", "confirm")])
    rows.append([M.btn_callback("❌ Отмена", "menu")])
    return rows


async def start_photo_collection(chat_id, house_id, callback_id, user_id):
    _SESSIONS[user_id] = {"house_id": house_id, "awaiting_photo": True,
                          "photos": [], "seen_msg_ids": set()}
    h = await _house(house_id)
    addr = h.address if h else "адрес"
    txt = (f"📸 Фото для: {addr}\n\n"
           "Присылайте фото уборки — можно несколько, разными сообщениями или альбомом.\n"
           "Когда загрузите все, нажмите «Отправить».")
    await M.answer_callback(callback_id, new_text=txt, buttons=_collect_buttons(0))


def _extract_tokens(attachments: List[Dict[str, Any]]) -> List[str]:
    """
    Токены фото из вложений MAX. Принимаем не только image, но и file/video/photo —
    уборщицы часто шлют скриншоты как ФАЙЛЫ. Токен ищем в разных полях payload.
    """
    tokens: List[str] = []
    for a in attachments or []:
        atype = (a.get("type") or "").lower()
        if atype not in ("image", "photo", "file", "video", "share"):
            continue
        p = a.get("payload") or {}
        tok = (p.get("token") or p.get("photo_token") or p.get("fileId")
               or p.get("file_id") or p.get("code") or p.get("url"))
        if tok:
            tokens.append(tok)
    return tokens


async def collect_photo(chat_id, user_id, attachments, msg_id=None):
    sess = _SESSIONS.get(user_id)
    if not sess or not sess.get("awaiting_photo"):
        await M.send_message(
            chat_id,
            "📸 Сначала выберите адрес и нажмите «Отправить фото уборки», потом присылайте фото.",
            buttons=[[M.btn_callback("📋 В меню", "menu")]],
        )
        return

    seen = sess.setdefault("seen_msg_ids", set())
    if msg_id is not None:
        if msg_id in seen:
            return
        seen.add(msg_id)

    tokens = _extract_tokens(attachments)
    if not tokens:
        logger.warning(f"[MAX bot] collect_photo: не извлёк токены из {attachments}")
        await M.send_message(
            chat_id,
            "⚠️ Не получилось распознать вложение. Пришлите фото ещё раз.",
            buttons=_collect_buttons(len(sess.get("photos", []))),
        )
        return

    sess["photos"].extend(tokens)
    n = len(sess["photos"])
    await M.send_message(
        chat_id,
        f"📷 Принято фото: {n}. Можно прислать ещё или нажать «Отправить».",
        buttons=_collect_buttons(n),
    )


def _today_cleaning_label(h: House) -> str:
    now = datetime.now()
    items = _schedule_dates(h, now.year, now.month)
    iso = date.today().isoformat()
    for it in items:
        if it["date"] == iso:
            return datetime.fromisoformat(it["date"]).strftime("%d.%m.%Y")
    return date.today().strftime("%d.%m.%Y")


async def confirm_send(chat_id, user_id, callback_id):
    """Шаг подтверждения адреса перед публикацией (защита от ошибки выбора)."""
    sess = _SESSIONS.get(user_id)
    if not sess or not sess.get("photos"):
        await M.answer_callback(callback_id, text="Нет фото для отправки")
        return
    h = await _house(sess["house_id"])
    if not h:
        await M.answer_callback(callback_id, text="Адрес не найден")
        _SESSIONS.pop(user_id, None)
        return
    n = len(sess["photos"])
    date_label = _today_cleaning_label(h)
    txt = (f"Проверьте перед отправкой:\n\n"
           f"🏠 {h.address}\n"
           f"📅 {date_label}\n"
           f"📷 Фото: {n}\n\n"
           f"Всё верно?")
    rows = [
        [M.btn_callback("✅ Да, отправить", "send_photos")],
        [M.btn_callback("✏️ Выбрать другой адрес", "menu")],
        [M.btn_callback("❌ Отмена", "menu")],
    ]
    await M.answer_callback(callback_id, new_text=txt, buttons=rows)


async def _notify_house_subscribers(h: House, date_label: str, post_url: str = ""):
    """Уведомить подписчиков дома (через клиентский бот) об уборке + ссылка на пост."""
    try:
        async with AsyncSessionLocal() as s:
            rows = await s.execute(sa_text(
                "SELECT chat_id FROM house_subscribers WHERE house_id = :hid"
            ), {"hid": h.id})
            chat_ids = [r[0] for r in rows.fetchall()]
    except Exception as e:
        logger.info(f"[MAX bot] подписчики не получены (таблица?): {e}")
        return
    if not chat_ids:
        return
    text = (f"✅ Уборка выполнена!\n🏠 {h.address}\n📅 {date_label}")
    btns = None
    if post_url:
        # кнопка-ссылка на конкретный пост с фото
        btns = [[M.btn_link("📸 Посмотреть фотоотчёт", post_url)]]
    else:
        text += "\n\nФотоотчёт опубликован в нашем канале."
    # шлём через клиентский бот, чтобы сообщение пришло клиенту от «его» бота
    try:
        from backend.app.services import max_client_bot as CB
        for cid in chat_ids:
            try:
                await CB.bot.send_message(int(cid), text, buttons=btns)
            except Exception as e:
                logger.warning(f"[MAX bot] уведомление {cid}: {e}")
    except Exception as e:
        logger.exception(f"[MAX bot] notify subscribers: {e}")


async def send_collected_photos(chat_id, user_id, callback_id):
    sess = _SESSIONS.get(user_id)
    if not sess or not sess.get("photos"):
        await M.answer_callback(callback_id, text="Нет фото для отправки")
        return
    h = await _house(sess["house_id"])
    if not h:
        await M.answer_callback(callback_id, text="Адрес не найден")
        _SESSIONS.pop(user_id, None)
        return

    tokens = sess["photos"]
    date_label = _today_cleaning_label(h)
    # Подпись (markdown): адрес и ЖИРНАЯ дата в одной строке, УК — отдельной строкой.
    caption = f"🏠 {h.address} — **{date_label}**"
    if h.company_title:
        caption += f"\n🏢 {M.pretty_uk(h.company_title)}"

    # Кнопка «Задать вопрос» под постом → ведёт в клиентский бот
    post_buttons = [[M.btn_link("💬 Задать вопрос", CLIENT_BOT_LINK)]]

    published = False
    post_url = ""
    if MAX_PHOTOS_CHANNEL_ID:
        res = await M.send_photos(int(MAX_PHOTOS_CHANNEL_ID), tokens, caption,
                                  fmt="markdown", buttons=post_buttons)
        published = bool(res and not res.get("code"))
        # ссылка на опубликованный пост (для уведомления подписчиков)
        post_url = ((res or {}).get("message") or {}).get("url", "") if published else ""

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
            """), {
                "hid": h.id, "addr": h.address, "brig": h.brigade_number,
                "uid": user_id, "cdate": date.today(),
                "tokens": tokens, "cnt": len(tokens), "cap": caption,
                "status": "sent_to_group" if published else "uploaded",
                "sent_at": datetime.utcnow() if published else None,
                "now": datetime.utcnow(),
            })
            await s.commit()
    except Exception as e:
        logger.exception(f"[MAX bot] запись cleaning_photos: {e}")

    # обновим last_cleaning в доме
    try:
        async with AsyncSessionLocal() as s:
            await s.execute(sa_text("UPDATE houses SET last_cleaning = :now WHERE id = :hid"),
                            {"now": datetime.utcnow(), "hid": h.id})
            await s.commit()
    except Exception:
        pass

    # уведомить подписчиков дома (клиентов) со ссылкой на пост
    await _notify_house_subscribers(h, date_label, post_url)

    _SESSIONS.pop(user_id, None)
    if published:
        msg = f"✅ Отправлено {len(tokens)} фото!\n{h.address} — {date_label}\nСпасибо за работу 👍"
    else:
        msg = f"✅ Принято {len(tokens)} фото\n{h.address} — {date_label}\n(зафиксировано в системе)"
    # после отправки — удобные кнопки: сразу новый адрес или в меню
    rows = [
        [M.btn_callback("📸 Отправить для другого адреса", "today")],
        [M.btn_callback("📋 В меню", "menu")],
    ]
    await M.answer_callback(callback_id, new_text=msg, buttons=rows)


# ---------- акт подписан: сбор фото акта -> БД -> канал -> (хук Bitrix/почта) ----------

# Отдельный канал для актов (если задан), иначе общий фотоканал
MAX_ACTS_CHANNEL_ID = os.environ.get("MAX_ACTS_CHANNEL_ID", "") or MAX_PHOTOS_CHANNEL_ID


def _act_collect_buttons(count: int):
    rows = []
    if count > 0:
        rows.append([M.btn_callback(f"✅ Отправить акт ({count} фото)", "act_confirm")])
    rows.append([M.btn_callback("❌ Отмена", "menu")])
    return rows


async def start_act_collection(chat_id, house_id, callback_id, user_id):
    """Запуск сбора фото акта (отдельный режим от фото уборки)."""
    _SESSIONS[user_id] = {"house_id": house_id, "awaiting_act": True,
                          "act_photos": [], "seen_msg_ids": set()}
    h = await _house(house_id)
    addr = h.address if h else "адрес"
    txt = (f"📝 Фото акта для: {addr}\n\n"
           "Сфотографируйте подписанный акт — можно несколько листов, "
           "разными сообщениями или альбомом.\n"
           "Когда загрузите все, нажмите «Отправить акт».")
    await M.answer_callback(callback_id, new_text=txt, buttons=_act_collect_buttons(0))


async def collect_act_photo(chat_id, user_id, attachments, msg_id=None):
    """Накопление фото акта в буфер сессии."""
    sess = _SESSIONS.get(user_id)
    if not sess or not sess.get("awaiting_act"):
        await M.send_message(
            chat_id,
            "📝 Сначала выберите адрес и нажмите «Акт подписан», потом присылайте фото акта.",
            buttons=[[M.btn_callback("📋 В меню", "menu")]],
        )
        return
    seen = sess.setdefault("seen_msg_ids", set())
    if msg_id is not None:
        if msg_id in seen:
            return
        seen.add(msg_id)
    tokens = _extract_tokens(attachments)
    if not tokens:
        logger.warning(f"[MAX bot] collect_act_photo: не извлёк токены из {attachments}")
        await M.send_message(
            chat_id,
            "⚠️ Не получилось распознать вложение. Пришлите фото акта ещё раз.",
            buttons=_act_collect_buttons(len(sess.get("act_photos", []))),
        )
        return
    sess["act_photos"].extend(tokens)
    n = len(sess["act_photos"])
    await M.send_message(
        chat_id,
        f"📄 Принято фото акта: {n}. Можно прислать ещё или нажать «Отправить акт».",
        buttons=_act_collect_buttons(n),
    )


async def confirm_act_send(chat_id, user_id, callback_id):
    """Подтверждение адреса/месяца перед сохранением акта."""
    sess = _SESSIONS.get(user_id)
    if not sess or not sess.get("act_photos"):
        await M.answer_callback(callback_id, text="Нет фото акта для отправки")
        return
    h = await _house(sess["house_id"])
    if not h:
        await M.answer_callback(callback_id, text="Адрес не найден")
        _SESSIONS.pop(user_id, None)
        return
    n = len(sess["act_photos"])
    now = datetime.now()
    month_label = f"{RU_MONTHS_NAME[now.month]} {now.year}"
    txt = (f"Проверьте перед отправкой акта:\n\n"
           f"🏠 {h.address}\n"
           f"📅 Месяц акта: {month_label}\n"
           f"📄 Фото акта: {n}\n\n"
           f"Подтвердить, что акт подписан?")
    rows = [
        [M.btn_callback("✅ Да, акт подписан", "act_send")],
        [M.btn_callback("✏️ Выбрать другой адрес", "menu")],
        [M.btn_callback("❌ Отмена", "menu")],
    ]
    await M.answer_callback(callback_id, new_text=txt, buttons=rows)


async def _push_act_to_bitrix(h: House, act_month: str, tokens: List[str],
                              signed_by: Optional[str], notes: str = "") -> bool:
    """
    ЗАГЛУШКА под будущую интеграцию: отправка инфо об акте в Bitrix24 + на почту.
    Сейчас только логирует и НЕ блокирует основной поток. Настроим позже.
    Возвращает True если успешно «отправлено» (пока всегда False -> статус pending).
    """
    try:
        logger.info(f"[MAX bot][act->bitrix STUB] дом={h.id} ({h.address}), "
                    f"месяц={act_month}, фото={len(tokens)}, кем={signed_by}. "
                    f"Bitrix/почта будут настроены позже.")
        # TODO: när настроим Bitrix —
        #   1) bitrix24_service: прикрепить фото акта к сделке h.bitrix_id
        #   2) отправить письмо на почту УК/руководителя
        return False
    except Exception as e:
        logger.exception(f"[MAX bot] _push_act_to_bitrix: {e}")
        return False


async def send_act(chat_id, user_id, callback_id):
    """Сохранить акт в БД (house_acts), опубликовать в канал, дернуть хук Bitrix."""
    sess = _SESSIONS.get(user_id)
    if not sess or not sess.get("act_photos"):
        await M.answer_callback(callback_id, text="Нет фото акта для отправки")
        return
    h = await _house(sess["house_id"])
    if not h:
        await M.answer_callback(callback_id, text="Адрес не найден")
        _SESSIONS.pop(user_id, None)
        return

    tokens = sess["act_photos"]
    now = datetime.now()
    act_month = f"{now.year}-{now.month:02d}"            # YYYY-MM
    signed_date = date.today()
    month_label = f"{RU_MONTHS_NAME[now.month]} {now.year}"
    signed_by = h.brigade_number and f"Бригада {h.brigade_number}" or None

    # 1) Сколько уборок было в этом месяце (для тела акта)
    cleaning_count = 0
    try:
        async with AsyncSessionLocal() as s:
            r = await s.execute(sa_text(
                "SELECT COUNT(*) FROM cleaning_photos "
                "WHERE house_id = :hid AND TO_CHAR(cleaning_date, 'YYYY-MM') = :m"
            ), {"hid": h.id, "m": act_month})
            cleaning_count = r.scalar() or 0
    except Exception as e:
        logger.warning(f"[MAX bot] act cleaning_count: {e}")

    # 2) Публикация фото акта в канал
    caption = f"📝 АКТ ПОДПИСАН\n🏠 {h.address} — **{month_label}**"
    if h.company_title:
        caption += f"\n🏢 {M.pretty_uk(h.company_title)}"
    if cleaning_count:
        caption += f"\n🧹 Уборок за месяц: {cleaning_count}"
    published = False
    if MAX_ACTS_CHANNEL_ID:
        try:
            res = await M.send_photos(int(MAX_ACTS_CHANNEL_ID), tokens, caption, fmt="markdown")
            published = bool(res and not res.get("code"))
        except Exception as e:
            logger.exception(f"[MAX bot] публикация акта: {e}")

    # 3) Сохранение в house_acts (upsert по house_id+act_month)
    try:
        async with AsyncSessionLocal() as s:
            await s.execute(sa_text("""
                INSERT INTO house_acts
                  (house_id, house_address, act_month, act_signed_date, signed_by,
                   brigade_id, cleaning_count, act_photo_ids, act_photo_count,
                   bitrix_status, created_at, updated_at)
                VALUES
                  (:hid, :addr, :m, :sd, :sb, :brig, :cnt, :tokens, :pcnt,
                   'pending', :now, :now)
                ON CONFLICT (house_id, act_month) DO UPDATE SET
                   act_signed_date = EXCLUDED.act_signed_date,
                   signed_by       = EXCLUDED.signed_by,
                   cleaning_count  = EXCLUDED.cleaning_count,
                   act_photo_ids   = EXCLUDED.act_photo_ids,
                   act_photo_count = EXCLUDED.act_photo_count,
                   updated_at      = EXCLUDED.updated_at
            """), {
                "hid": h.id, "addr": h.address, "m": act_month, "sd": signed_date,
                "sb": signed_by, "brig": h.brigade_number, "cnt": cleaning_count,
                "tokens": tokens, "pcnt": len(tokens), "now": datetime.utcnow(),
            })
            await s.commit()
    except Exception as e:
        logger.exception(f"[MAX bot] запись house_acts: {e}")

    # 4) Хук Bitrix/почта (заглушка) — не блокирует
    await _push_act_to_bitrix(h, act_month, tokens, signed_by)

    _SESSIONS.pop(user_id, None)
    msg = (f"✅ Акт принят: {len(tokens)} фото\n"
           f"🏠 {h.address}\n📅 {month_label}\n"
           f"Спасибо! Информация зафиксирована.")
    rows = [
        [M.btn_callback("📸 Фото уборки для другого адреса", "today")],
        [M.btn_callback("📋 В меню", "menu")],
    ]
    await M.answer_callback(callback_id, new_text=msg, buttons=rows)


# ---------- свободное сообщение боту ----------

async def start_write(chat_id, user_id, callback_id):
    """Включить режим: следующее текстовое сообщение уйдёт менеджеру."""
    if user_id:
        _SESSIONS[user_id] = {"awaiting_message": True}
    txt = ("✍️ Напишите сообщение одним текстом — вопрос, замечание или просьбу.\n"
           "Мы передадим его руководителю.")
    await M.answer_callback(callback_id, new_text=txt, buttons=[[M.btn_callback("⬅️ В меню", "menu")]])


async def forward_message(chat_id, user_id, text_body):
    """Передать сообщение сотрудника менеджеру (в канал) + записать в лог."""
    payload = f"✍️ СООБЩЕНИЕ ОТ СОТРУДНИКА\nchat_id={chat_id}, user_id={user_id}\n\n{text_body}"
    if MAX_PHOTOS_CHANNEL_ID:
        try:
            await M.send_message(int(MAX_PHOTOS_CHANNEL_ID), payload)
        except Exception as e:
            logger.exception(f"[MAX bot] forward_message: {e}")
    try:
        async with AsyncSessionLocal() as s:
            await s.execute(sa_text("""
                INSERT INTO client_requests (kind, user_id, chat_id, body, created_at)
                VALUES ('staff_message', :uid, :cid, :body, :now)
            """), {"uid": user_id, "cid": chat_id, "body": text_body,
                   "now": datetime.utcnow()})
            await s.commit()
    except Exception as e:
        logger.exception(f"[MAX bot] forward_message save: {e}")
    if user_id:
        _SESSIONS.pop(user_id, None)
    await M.send_message(
        chat_id,
        "✅ Сообщение передано руководителю. Спасибо!",
        buttons=[[M.btn_callback("📋 В меню", "menu")]],
    )


# ---------- роутинг ----------

async def handle_callback(chat_id, callback_id, payload, user_id=None):
    logger.info(f"[MAX cb→handle] payload={payload!r} chat_id={chat_id} user={user_id}")
    if payload == "menu":
        if user_id:
            _SESSIONS.pop(user_id, None)
        await M.answer_callback(callback_id, new_text="👋 Главное меню:", buttons=_main_menu_buttons())
    elif payload == "uk":
        await show_uk_list(chat_id, callback_id)
    elif payload.startswith("uk:"):
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
        await show_uk_houses(chat_id, uk_name, callback_id, page=page)
    elif payload == "br":
        await show_brigade_list(chat_id, callback_id)
    elif payload.startswith("br:"):
        rest = payload[3:]
        page = 1
        if ":p" in rest:
            rest, _, pp = rest.rpartition(":p")
            try: page = int(pp)
            except: page = 1
        await show_brigade_houses(chat_id, rest, callback_id, page=page)
    elif payload == "today":
        await show_today(chat_id, callback_id)
    elif payload.startswith("h:"):
        await show_house_card(chat_id, payload[2:], callback_id)
    elif payload.startswith("photo:"):
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
        await send_act(chat_id, user_id, callback_id)
    elif payload == "write":
        await start_write(chat_id, user_id, callback_id)
    elif payload == "noop":
        await M.answer_callback(callback_id, text="")
    else:
        logger.warning(f"[MAX cb→handle] НЕОБРАБОТАН payload={payload!r}")
        await M.answer_callback(callback_id, text="Неизвестная команда")


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

    if ut == "bot_started":
        chat_id = _chat_id_from_started(update)
        if chat_id:
            await show_main_menu(chat_id)
        else:
            logger.warning(f"[MAX bot] bot_started без chat_id: {update}")

    elif ut == "message_created":
        msg = update.get("message", {})
        chat_id = (msg.get("recipient") or {}).get("chat_id")
        sender = msg.get("sender") or {}
        user_id = sender.get("user_id")
        body = msg.get("body") or {}
        attachments = body.get("attachments") or []
        msg_id = body.get("mid") or msg.get("timestamp")

        if sender.get("is_bot"):
            return

        sess = _SESSIONS.get(user_id) if user_id else None
        has_attach = bool(_extract_tokens(attachments))
        text_in = (body.get("text") or "").strip()

        if sess and sess.get("awaiting_act") and has_attach and user_id:
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
            )
        elif chat_id:
            await show_main_menu(chat_id)

    elif ut == "message_callback":
        cb = update.get("callback", {})
        callback_id = cb.get("callback_id")
        payload = cb.get("payload", "")
        user_id = (cb.get("user") or {}).get("user_id")
        chat_id = ((update.get("message") or {}).get("recipient") or {}).get("chat_id")
        logger.info(f"[MAX cb] payload={payload!r} | len={len(payload)} | callback_id={callback_id!s:.20} | chat_id={chat_id} | user={user_id}")
        if callback_id:
            await handle_callback(chat_id, callback_id, payload, user_id)
        else:
            logger.warning(f"[MAX cb] нет callback_id! cb keys={list(cb.keys())}")
