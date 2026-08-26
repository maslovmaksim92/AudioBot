"""
Webhook-роутер для клиентского MAX-бота (УК / жители).
Путь: /api/max-client/webhook
"""
import os
import logging
from fastapi import APIRouter, Request, Header, BackgroundTasks
from fastapi.responses import JSONResponse

from backend.app.services import max_client_bot as cbot

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/max-client", tags=["max-client"])

CLIENT_WEBHOOK_SECRET = os.environ.get("MAX_CLIENT_WEBHOOK_SECRET", "")


@router.get("/health")
async def client_health():
    me = await cbot.bot.get_me()
    return {"ok": me is not None, "bot": me}


@router.post("/webhook")
async def client_webhook(request: Request, background_tasks: BackgroundTasks,
                         x_max_bot_api_secret: str = Header(default="")):
    if CLIENT_WEBHOOK_SECRET and x_max_bot_api_secret != CLIENT_WEBHOOK_SECRET:
        logger.warning("[max-client webhook] неверный секрет")
        return JSONResponse({"ok": False}, status_code=403)
    try:
        update = await request.json()
    except Exception:
        return JSONResponse({"ok": True})
    logger.info(f"[max-client webhook] update_type={update.get('update_type')}")
    background_tasks.add_task(cbot.handle_update, update)
    return JSONResponse({"ok": True})


@router.post("/subscribe")
async def client_subscribe():
    url = "https://ai.vd40.ru/api/max-client/webhook"
    res = await cbot.bot.subscribe_webhook(url, secret=CLIENT_WEBHOOK_SECRET)
    return {"requested_url": url, "result": res}


@router.get("/subscriptions")
async def client_subscriptions():
    return await cbot.bot.list_subscriptions()
