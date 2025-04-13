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

BOT_TOKEN = "7850360375:AAEVEQCbsqCnP-aHJGlgQCHaTwginuLNm0E"
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

whisper = WhisperService()
tts = TTSService()
dialog = DialogService()

user_settings = {}

class TelegramMessage(BaseModel):
    update_id: int
    message: dict


def convert_oga_to_wav(oga_path: Path) -> Path:
    wav_path = oga_path.with_suffix(".wav")
    subprocess.run(["ffmpeg", "-i", str(oga_path), str(wav_path)], check=True)
    return wav_path


async def download_file(file_id: str) -> Path:
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{API_URL}/getFile", params={"file_id": file_id})
        file_path = r.json()["result"]["file_path"]
        file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"
        r = await client.get(file_url)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".oga") as tmp:
            tmp.write(r.content)
            return Path(tmp.name)


async def send_text(chat_id: int, text: str):
    async with httpx.AsyncClient() as client:
        await client.post(f"{API_URL}/sendMessage", json={"chat_id": chat_id, "text": text})


async def send_voice(chat_id: int, audio_path: Path):
    async with httpx.AsyncClient() as client:
        with open(audio_path, "rb") as f:
            files = {"voice": (audio_path.name, f, "audio/ogg")}
            data = {"chat_id": chat_id}
            await client.post(f"{API_URL}/sendVoice", data=data, files=files)


@router.post("/webhook")
async def telegram_webhook(update: TelegramMessage):
    msg = update.message
    chat_id = msg["chat"]["id"]

    # Команды (текст)
    if "text" in msg:
        text = msg["text"].strip()

        if text == "/reset":
            dialog.reset_context(chat_id)
            return await send_text(chat_id, "Контекст очищен ✅")

        elif text.startswith("/voice"):
            _, voice = text.split(maxsplit=1)
            user_settings[chat_id] = {"voice": voice}
            return await send_text(chat_id, f"Голос сменён на {voice}")

        elif text.startswith("/mode"):
            _, mode = text.split(maxsplit=1)
            user_settings[chat_id] = {"mode": mode}
            return await send_text(chat_id, f"Режим переключён на {mode}")

        elif text == "/help":
            return await send_text(chat_id, "/reset – очистить память\n/voice female|male\n/mode simple|gpt")

        return await send_text(chat_id, "Я умею работать с голосом. Просто скажи что-нибудь 🎙️")

    # Голос
    if "voice" not in msg:
        return {"ok": False, "reason": "not a voice message"}

    file_id = msg["voice"]["file_id"]
    oga_path = await download_file(file_id)
    wav_path = convert_oga_to_wav(oga_path)
    user_text = whisper.transcribe(wav_path)
    response_text = await dialog.generate_response(chat_id, user_text)

    await send_text(chat_id, response_text)
    tts_path = await tts.synthesize(response_text)
    await send_voice(chat_id, tts_path)

    return {"ok": True}