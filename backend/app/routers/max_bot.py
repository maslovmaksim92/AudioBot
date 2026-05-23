"""
Webhook-роутер для MAX-бота уборщиц.
Принимает события MAX (message_created, message_callback, bot_started),
проверяет секрет, отвечает 200 быстро, обработку запускает в фоне.
"""
import os
import logging
from fastapi import APIRouter, Request, Header, BackgroundTasks
from fastapi.responses import JSONResponse

from backend.app.services import max_cleaning_bot as bot
from backend.app.services import max_service as M

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/max", tags=["max"])

MAX_WEBHOOK_SECRET = os.environ.get("MAX_WEBHOOK_SECRET", "")


@router.get("/health")
async def max_health():
    """Проверка: видит ли бэкенд бота (валиден ли токен)."""
    me = await M.get_me()
    return {"ok": me is not None, "bot": me}


@router.post("/webhook")
async def max_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_max_bot_api_secret: str = Header(default=""),
):
    # Проверка секрета (если задан)
    if MAX_WEBHOOK_SECRET and x_max_bot_api_secret != MAX_WEBHOOK_SECRET:
        logger.warning("[MAX webhook] неверный секрет, запрос отклонён")
        return JSONResponse({"ok": False}, status_code=403)

    try:
        update = await request.json()
    except Exception as e:
        logger.error(f"[MAX webhook] не удалось распарсить JSON: {e}")
        return JSONResponse({"ok": True})

    logger.info(f"[MAX webhook] update_type={update.get('update_type')}")
    # Обработку — в фон, чтобы быстро ответить 200 (у MAX лимит отклика)
    background_tasks.add_task(bot.handle_update, update)
    return JSONResponse({"ok": True})


@router.post("/subscribe")
async def max_subscribe():
    """Подписать бота на webhook ai.vd40.ru/api/max/webhook."""
    url = "https://ai.vd40.ru/api/max/webhook"
    res = await M.subscribe_webhook(url)
    return {"requested_url": url, "result": res}


@router.get("/subscriptions")
async def max_subscriptions():
    """Список текущих подписок."""
    return await M.list_subscriptions()
