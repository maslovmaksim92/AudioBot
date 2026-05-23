"""
MAX Bot API — низкоуровневый сервис.
Документация: https://dev.max.ru/docs-api
База: https://platform-api.max.ru, заголовок Authorization: {token}
"""
import os
import logging
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
        logger.error(f"[MAX] get_me error: {e}")
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
    try:
        async with httpx.AsyncClient(timeout=30) as cli:
            r = await cli.post(
                f"{MAX_API_BASE}/messages",
                params={"chat_id": chat_id},
                headers=_headers(),
                json=body,
            )
            if r.status_code >= 400:
                logger.error(f"[MAX] send_message {r.status_code}: {r.text[:300]}")
            return r.json() if r.content else None
    except Exception as e:
        logger.error(f"[MAX] send_message error: {e}")
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
    try:
        async with httpx.AsyncClient(timeout=20) as cli:
            r = await cli.post(
                f"{MAX_API_BASE}/answers",
                params={"callback_id": callback_id},
                headers=_headers(),
                json=body,
            )
            if r.status_code >= 400:
                logger.error(f"[MAX] answer_callback {r.status_code}: {r.text[:300]}")
            return r.json() if r.content else None
    except Exception as e:
        logger.error(f"[MAX] answer_callback error: {e}")
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
        logger.error(f"[MAX] subscribe_webhook error: {e}")
        return None


async def list_subscriptions() -> Optional[Dict[str, Any]]:
    if not MAX_BOT_TOKEN:
        return None
    try:
        async with httpx.AsyncClient(timeout=20) as cli:
            r = await cli.get(f"{MAX_API_BASE}/subscriptions", headers=_headers())
            return r.json() if r.content else None
    except Exception as e:
        logger.error(f"[MAX] list_subscriptions error: {e}")
        return None
