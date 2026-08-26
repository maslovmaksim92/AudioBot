"""
MAX Bot API — переиспользуемый клиент (для нескольких ботов).
Каждый бот = свой экземпляр MaxBot(token).
Документация: https://dev.max.ru/docs-api
"""
import logging
import httpx
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

MAX_API_BASE = "https://platform-api.max.ru"


def btn_callback(text: str, payload: str) -> Dict[str, Any]:
    return {"type": "callback", "text": text, "payload": payload}


def btn_link(text: str, url: str) -> Dict[str, Any]:
    return {"type": "link", "text": text, "url": url}


def _kb(rows: List[List[Dict[str, Any]]]) -> Dict[str, Any]:
    return {"type": "inline_keyboard", "payload": {"buttons": rows}}


class MaxBot:
    """Клиент MAX Bot API для конкретного бота (по его токену)."""

    def __init__(self, token: str, name: str = "max"):
        self.token = token or ""
        self.name = name

    def _headers(self) -> Dict[str, str]:
        return {"Authorization": self.token, "Content-Type": "application/json"}

    @property
    def configured(self) -> bool:
        return bool(self.token)

    async def get_me(self) -> Optional[Dict[str, Any]]:
        if not self.configured:
            return None
        try:
            async with httpx.AsyncClient(timeout=20) as cli:
                r = await cli.get(f"{MAX_API_BASE}/me", headers=self._headers())
                return r.json() if r.content else None
        except Exception as e:
            logger.error(f"[{self.name}] get_me error: {e}")
            return None

    async def send_message(self, chat_id: int, text: str,
                           buttons: Optional[List[List[Dict[str, Any]]]] = None,
                           fmt: Optional[str] = None) -> Optional[Dict[str, Any]]:
        if not self.configured:
            return None
        body: Dict[str, Any] = {"text": text}
        if buttons:
            body["attachments"] = [_kb(buttons)]
        if fmt:
            body["format"] = fmt
        try:
            async with httpx.AsyncClient(timeout=30) as cli:
                r = await cli.post(f"{MAX_API_BASE}/messages",
                                   params={"chat_id": chat_id},
                                   headers=self._headers(), json=body)
                if r.status_code >= 400:
                    logger.error(f"[{self.name}] send_message {r.status_code}: {r.text[:300]}")
                return r.json() if r.content else None
        except Exception as e:
            logger.error(f"[{self.name}] send_message error: {e}")
            return None

    async def send_photos(self, chat_id: int, photo_tokens: List[str],
                          caption: str = "") -> Optional[Dict[str, Any]]:
        if not self.configured:
            return None
        attachments = [{"type": "image", "payload": {"token": t}} for t in photo_tokens]
        body: Dict[str, Any] = {"attachments": attachments}
        if caption:
            body["text"] = caption
        try:
            async with httpx.AsyncClient(timeout=60) as cli:
                r = await cli.post(f"{MAX_API_BASE}/messages",
                                   params={"chat_id": chat_id},
                                   headers=self._headers(), json=body)
                if r.status_code >= 400:
                    logger.error(f"[{self.name}] send_photos {r.status_code}: {r.text[:300]}")
                return r.json() if r.content else None
        except Exception as e:
            logger.error(f"[{self.name}] send_photos error: {e}")
            return None

    async def answer_callback(self, callback_id: str, text: Optional[str] = None,
                              new_text: Optional[str] = None,
                              buttons: Optional[List[List[Dict[str, Any]]]] = None) -> Optional[Dict[str, Any]]:
        if not self.configured:
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
                r = await cli.post(f"{MAX_API_BASE}/answers",
                                   params={"callback_id": callback_id},
                                   headers=self._headers(), json=body)
                if r.status_code >= 400:
                    logger.error(f"[{self.name}] answer_callback {r.status_code}: {r.text[:300]}")
                return r.json() if r.content else None
        except Exception as e:
            logger.error(f"[{self.name}] answer_callback error: {e}")
            return None

    async def subscribe_webhook(self, url: str, secret: str = "",
                                update_types: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
        if not self.configured:
            return None
        if update_types is None:
            update_types = ["message_created", "message_callback", "bot_started"]
        body: Dict[str, Any] = {"url": url, "update_types": update_types}
        if secret:
            body["secret"] = secret
        try:
            async with httpx.AsyncClient(timeout=20) as cli:
                r = await cli.post(f"{MAX_API_BASE}/subscriptions",
                                   headers=self._headers(), json=body)
                logger.info(f"[{self.name}] subscribe_webhook {r.status_code}: {r.text[:200]}")
                return r.json() if r.content else None
        except Exception as e:
            logger.error(f"[{self.name}] subscribe_webhook error: {e}")
            return None

    async def list_subscriptions(self) -> Optional[Dict[str, Any]]:
        if not self.configured:
            return None
        try:
            async with httpx.AsyncClient(timeout=20) as cli:
                r = await cli.get(f"{MAX_API_BASE}/subscriptions", headers=self._headers())
                return r.json() if r.content else None
        except Exception as e:
            logger.error(f"[{self.name}] list_subscriptions error: {e}")
            return None
