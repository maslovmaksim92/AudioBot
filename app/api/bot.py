import os
import tempfile
import subprocess
from pathlib import Path
from fastapi import APIRouter
from pydantic import BaseModel
import httpx

from app.services.whisper_service import WhisperService
from app.services.tts_service import TTSService
from app.services.dialog_service import DialogService

router = APIRouter()
BOT_TOKEN = os.getenv("BOT_TOKEN")
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

whisper = WhisperService()
tts = TTSService()
dialog = DialogService()
user_settings = {}

class TelegramMessage(BaseModel):
    update_id: int
    message: dict | None = None
    callback_query: dict | None = None

@router.post("/webhook")
async def telegram_webhook(update: TelegramMessage):
    if update.callback_query:
        query = update.callback_query
        chat_id = query["from"]["id"]
        data = query["data"]
        async with httpx.AsyncClient() as client:
            await client.post(f"{API_URL}/answerCallbackQuery", json={"callback_query_id": query["id"]})
        update.message = {"chat": {"id": chat_id}, "text": data}

    if not update.message:
        return {"ok": False}

    msg = update.message
    chat_id = msg["chat"]["id"]

    if "text" in msg:
        text = msg["text"].strip()
        if text.startswith("/reply_mode"):
            _, mode = text.split(maxsplit=1)
            user_settings[chat_id] = user_settings.get(chat_id, {})
            user_settings[chat_id]["reply_mode"] = mode
            async with httpx.AsyncClient() as client:
                await client.post(f"{API_URL}/sendMessage", json={"chat_id": chat_id, "text": f"Режим ответа: {mode.upper()} ✅"})
            return {"ok": True}

    return {"ok": True}