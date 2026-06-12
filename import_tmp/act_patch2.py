p = '/opt/audiobot/backend/app/services/max_cleaning_bot.py'
s = open(p, encoding='utf-8').read()

ANCHOR = "# ---------- свободное сообщение боту ----------"

ACT_CODE = '''# ---------- акт подписан: сбор фото акта -> БД -> канал -> (хук Bitrix/почта) ----------

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
    txt = (f"📝 Фото акта для: {addr}\\n\\n"
           "Сфотографируйте подписанный акт — можно несколько листов, "
           "разными сообщениями или альбомом.\\n"
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
    txt = (f"Проверьте перед отправкой акта:\\n\\n"
           f"🏠 {h.address}\\n"
           f"📅 Месяц акта: {month_label}\\n"
           f"📄 Фото акта: {n}\\n\\n"
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
        logger.error(f"[MAX bot] _push_act_to_bitrix: {e}")
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
    caption = f"📝 АКТ ПОДПИСАН\\n🏠 {h.address} — **{month_label}**"
    if h.company_title:
        caption += f"\\n🏢 {M.pretty_uk(h.company_title)}"
    if cleaning_count:
        caption += f"\\n🧹 Уборок за месяц: {cleaning_count}"
    published = False
    if MAX_ACTS_CHANNEL_ID:
        try:
            res = await M.send_photos(int(MAX_ACTS_CHANNEL_ID), tokens, caption, fmt="markdown")
            published = bool(res and not res.get("code"))
        except Exception as e:
            logger.error(f"[MAX bot] публикация акта: {e}")

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
        logger.error(f"[MAX bot] запись house_acts: {e}")

    # 4) Хук Bitrix/почта (заглушка) — не блокирует
    await _push_act_to_bitrix(h, act_month, tokens, signed_by)

    _SESSIONS.pop(user_id, None)
    msg = (f"✅ Акт принят: {len(tokens)} фото\\n"
           f"🏠 {h.address}\\n📅 {month_label}\\n"
           f"Спасибо! Информация зафиксирована.")
    rows = [
        [M.btn_callback("📸 Фото уборки для другого адреса", "today")],
        [M.btn_callback("📋 В меню", "menu")],
    ]
    await M.answer_callback(callback_id, new_text=msg, buttons=rows)


''' + ANCHOR

assert ANCHOR in s, "якорь 'свободное сообщение' не найден"
s = s.replace(ANCHOR, ACT_CODE, 1)
open(p, 'w', encoding='utf-8').write(s)
print("OK: функции конвейера актов добавлены")
