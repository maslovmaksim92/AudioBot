"""
MAX Bot API — низкоуровневый сервис.
Документация: https://dev.max.ru/docs-api
База: https://platform-api.max.ru, заголовок Authorization: {token}
"""
import os
import logging
import re as _re_uk

_UK_KEEP_UPPER = {"ЖРЭУ", "РКЦ", "ГУП", "УК", "МЖД"}


def _uk_is_abbr(word: str) -> bool:
    return word.strip("-").upper() in _UK_KEEP_UPPER


def pretty_uk(name: str) -> str:
    """Красивое отображение названия УК: без ООО/кавычек, аккуратная капитализация.
    Используется ТОЛЬКО для показа пользователю; в БД и payload остаётся оригинал."""
    if not name:
        return name or ""
    s = name.strip()
    s = _re_uk.sub(r'(\S)(["«“])', r'\1 \2', s)        # пробел перед слипшейся кавычкой
    for q in '"«»”“':
        s = s.replace(q, '')
    s = _re_uk.sub(r'^\s*(ООО|ОАО|ЗАО|АО|ИП|ПАО)\b\s*', '', s, flags=_re_uk.IGNORECASE)
    s = _re_uk.sub(r'^\s*УК\s+(?=\S)', '', s)          # ведущее "УК " перед именем
    s = _re_uk.sub(r'\s*-\s*', '-', s)                  # дефис без пробелов
    s = _re_uk.sub(r'\s+', ' ', s).strip()
    out, first_done = [], False
    for word in s.split():
        if any(ch.isdigit() for ch in word):
            out.append(word)
            if not _uk_is_abbr(word):
                first_done = True
            continue
        if '-' in word:
            sub = []
            for x in word.split('-'):
                if _uk_is_abbr(x):
                    sub.append(x.upper())
                else:
                    sub.append(x[:1].upper() + x[1:].lower())
            out.append('-'.join(sub)); first_done = True
            continue
        if _uk_is_abbr(word):
            out.append(word.upper()); continue
        if not first_done:
            out.append(word[:1].upper() + word[1:].lower()); first_done = True
        else:
            out.append(word.lower())
    return ' '.join(out).strip()



import httpx
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

MAX_API_BASE = "https://platform-api.max.ru"
MAX_BOT_TOKEN = os.environ.get("MAX_BOT_TOKEN", "")
MAX_WEBHOOK_SECRET = os.environ.get("MAX_WEBHOOK_SECRET", "")


def _headers() -> Dict[str, str]:
    return {"Authorization": MAX_BOT_TOKEN, "Content-Type": "application/json"}


def _kb(rows: List[List[Dict[str, Any]]]) -> Dict[str, Any]:
    """Собрать inline-клавиатуру MAX из массива рядов кнопок."""
    return {"type": "inline_keyboard", "payload": {"buttons": rows}}


def btn_callback(text: str, payload: str) -> Dict[str, Any]:
    """Кнопка callback (присылает событие message_callback с payload)."""
    return {"type": "callback", "text": text, "payload": payload}


def btn_link(text: str, url: str) -> Dict[str, Any]:
    """Кнопка-ссылка."""
    return {"type": "link", "text": text, "url": url}


async def get_me() -> Optional[Dict[str, Any]]:
    """Информация о боте — проверка токена."""
    if not MAX_BOT_TOKEN:
        logger.warning("[MAX] MAX_BOT_TOKEN не настроен")
        return None
    try:
        async with httpx.AsyncClient(timeout=20) as cli:
            r = await cli.get(f"{MAX_API_BASE}/me", headers=_headers())
            r.raise_for_status()
            return r.json()
    except Exception as e:
        logger.exception(f"[MAX] get_me error: {e}")
        return None


async def send_message(
    chat_id: int,
    text: str,
    buttons: Optional[List[List[Dict[str, Any]]]] = None,
    fmt: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Отправить сообщение в чат. buttons — массив рядов кнопок (btn_callback/btn_link)."""
    if not MAX_BOT_TOKEN:
        logger.warning("[MAX] send_message: токен не настроен")
        return None
    body: Dict[str, Any] = {"text": text}
    if buttons:
        body["attachments"] = [_kb(buttons)]
    if fmt:
        body["format"] = fmt  # "markdown" | "html"
    n_rows = len(buttons) if buttons else 0
    logger.debug(f"[MAX] send_message → chat={chat_id} text={text[:80]!r} rows={n_rows}")
    try:
        async with httpx.AsyncClient(timeout=30) as cli:
            r = await cli.post(
                f"{MAX_API_BASE}/messages",
                params={"chat_id": chat_id},
                headers=_headers(),
                json=body,
            )
            if r.status_code >= 400:
                logger.error(f"[MAX] send_message {r.status_code} chat={chat_id} rows={n_rows} body={r.text[:300]}")
            else:
                logger.info(f"[MAX] send_message ok chat={chat_id} rows={n_rows} status={r.status_code}")
            return r.json() if r.content else None
    except Exception as e:
        logger.exception(f"[MAX] send_message error chat={chat_id} rows={n_rows}: {e}")
        return None


async def answer_callback(
    callback_id: str,
    text: Optional[str] = None,
    new_text: Optional[str] = None,
    buttons: Optional[List[List[Dict[str, Any]]]] = None,
) -> Optional[Dict[str, Any]]:
    """Ответ на нажатие кнопки. new_text/buttons — заменить сообщение; text — всплывающее уведомление."""
    if not MAX_BOT_TOKEN:
        return None
    body: Dict[str, Any] = {}
    if new_text is not None:
        msg: Dict[str, Any] = {"text": new_text}
        if buttons:
            msg["attachments"] = [_kb(buttons)]
        body["message"] = msg
    if text:
        body["notification"] = text
    n_rows = len(buttons) if buttons else 0
    logger.debug(f"[MAX] answer_callback → cb={callback_id[:12]} new_text={(new_text or text or '')[:80]!r} rows={n_rows}")
    try:
        async with httpx.AsyncClient(timeout=20) as cli:
            r = await cli.post(
                f"{MAX_API_BASE}/answers",
                params={"callback_id": callback_id},
                headers=_headers(),
                json=body,
            )
            if r.status_code >= 400:
                logger.error(f"[MAX] answer_callback {r.status_code} cb={callback_id[:12]} rows={n_rows} body={r.text[:300]}")
            else:
                logger.info(f"[MAX] answer_callback ok cb={callback_id[:12]} rows={n_rows} status={r.status_code}")
            return r.json() if r.content else None
    except Exception as e:
        logger.exception(f"[MAX] answer_callback error cb={callback_id[:12]} rows={n_rows}: {e}")
        return None


async def subscribe_webhook(url: str, update_types: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
    """Подписать бота на webhook. По умолчанию слушаем нужные нам типы событий."""
    if not MAX_BOT_TOKEN:
        return None
    if update_types is None:
        update_types = ["message_created", "message_callback", "bot_started"]
    body: Dict[str, Any] = {"url": url, "update_types": update_types}
    if MAX_WEBHOOK_SECRET:
        body["secret"] = MAX_WEBHOOK_SECRET
    try:
        async with httpx.AsyncClient(timeout=20) as cli:
            r = await cli.post(f"{MAX_API_BASE}/subscriptions", headers=_headers(), json=body)
            logger.info(f"[MAX] subscribe_webhook {r.status_code}: {r.text[:200]}")
            return r.json() if r.content else None
    except Exception as e:
        logger.exception(f"[MAX] subscribe_webhook error: {e}")
        return None


async def list_subscriptions() -> Optional[Dict[str, Any]]:
    if not MAX_BOT_TOKEN:
        return None
    try:
        async with httpx.AsyncClient(timeout=20) as cli:
            r = await cli.get(f"{MAX_API_BASE}/subscriptions", headers=_headers())
            return r.json() if r.content else None
    except Exception as e:
        logger.exception(f"[MAX] list_subscriptions error: {e}")
        return None


async def send_photos(
    chat_id: int,
    photo_tokens: List[str],
    caption: str = "",
    fmt: Optional[str] = None,
    buttons: Optional[List[List[Dict[str, Any]]]] = None,
) -> Optional[Dict[str, Any]]:
    """Опубликовать фото (по их token) в чат/канал с подписью.
    fmt — "markdown"/"html" для форматирования подписи.
    buttons — ряды кнопок (btn_callback/btn_link), добавляются под постом."""
    if not MAX_BOT_TOKEN:
        return None
    attachments: List[Dict[str, Any]] = [
        {"type": "image", "payload": {"token": t}} for t in photo_tokens
    ]
    if buttons:
        attachments.append(_kb(buttons))
    body: Dict[str, Any] = {"attachments": attachments}
    if caption:
        body["text"] = caption
    if fmt:
        body["format"] = fmt
    try:
        async with httpx.AsyncClient(timeout=60) as cli:
            r = await cli.post(
                f"{MAX_API_BASE}/messages",
                params={"chat_id": chat_id},
                headers=_headers(),
                json=body,
            )
            if r.status_code >= 400:
                logger.error(f"[MAX] send_photos {r.status_code}: {r.text[:300]}")
            return r.json() if r.content else None
    except Exception as e:
        logger.exception(f"[MAX] send_photos error: {e}")
        return None
