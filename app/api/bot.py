from fastapi import APIRouter
import os
import tempfile
import subprocess
from pathlib import Path
import httpx
from pydantic import BaseModel

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


async def send_text(chat_id: int, text: str, buttons: bool = False):
    payload = {"chat_id": chat_id, "text": text}
    if buttons:
        payload["reply_markup"] = {
            "inline_keyboard": [[
                {"text": "GPT-4", "callback_data": "/model gpt-4"},
                {"text": "Mistral", "callback_data": "/model mistral"},
                {"text": "LLaMA 3", "callback_data": "/model llama3"},
                {"text": "📊 Статистика", "callback_data": "/usage"}
            ]]
        }
    async with httpx.AsyncClient() as client:
        await client.post(f"{API_URL}/sendMessage", json=payload)


async def send_voice(chat_id: int, audio_path: Path):
    async with httpx.AsyncClient() as client:
        with open(audio_path, "rb") as f:
            files = {"voice": (audio_path.name, f, "audio/ogg")}
            data = {"chat_id": chat_id}
            await client.post(f"{API_URL}/sendVoice", data=data, files=files)


async def reply(chat_id: int, text: str, buttons: bool = False):
    await send_text(chat_id, text, buttons)
    voice_path = await tts.synthesize(text)
    await send_voice(chat_id, voice_path)


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
        return {"ok": False, "reason": "no message"}

    msg = update.message
    chat_id = msg["chat"]["id"]

    if "text" in msg:
        text = msg["text"].strip()
        if text == "/start":
            return await reply(chat_id, "Привет! Я голосовой бот. Просто скажи что-нибудь.", buttons=True)
        if text == "/reset":
            dialog.reset_context(chat_id)
            return await reply(chat_id, "Контекст очищен ✅")
        if text.startswith("/voice"):
            _, voice = text.split(maxsplit=1)
            user_settings[chat_id] = {"voice": voice}
            return await reply(chat_id, f"Голос будет сменён на {voice}")
        if text.startswith("/mode"):
            _, mode = text.split(maxsplit=1)
            user_settings[chat_id] = user_settings.get(chat_id, {})
            user_settings[chat_id]["mode"] = mode
            return await reply(chat_id, f"Режим {mode.upper()} активирован ✅")
        if text.startswith("/model"):
            _, model = text.split(maxsplit=1)
            user_settings[chat_id] = user_settings.get(chat_id, {})
            user_settings[chat_id]["model"] = model
            dialog.gpt.model = model
            return await reply(chat_id, f"Модель {model.upper()} активирована ✅")
        if text == "/usage":
            stats = dialog.sessions.get_usage(chat_id)
            usage = f"Запросов к ИИ: {stats['requests']}\nСимволов: {stats['tokens']}"
            return await reply(chat_id, usage)
        if text == "/help":
            help_text = (
                "/start — приветствие\n"
                "/reset — очистить память\n"
                "/voice female|male — выбрать голос\n"
                "/mode simple|gpt — выбрать режим\n"
                "/model gpt-4|mistral|llama3 — выбор модели\n"
                "/usage — статистика общения\n"
                "/help — список команд"
            )
            return await reply(chat_id, help_text, buttons=True)
        return await reply(chat_id, "Я умею работать с голосом. Просто скажи что-нибудь 🎙️")

    if "voice" not in msg:
        return {"ok": False, "reason": "not a voice message"}

    file_id = msg["voice"]["file_id"]
    oga_path = await download_file(file_id)
    wav_path = convert_oga_to_wav(oga_path)
    user_text = whisper.transcribe(wav_path)

    mode = user_settings.get(chat_id, {}).get("mode", "gpt")
    model = user_settings.get(chat_id, {}).get("model", "gpt-4")
    dialog.gpt.model = model

    if mode == "simple":
        response_text = f"Ты сказал: {user_text}"
    else:
        response_text = await dialog.generate_response(chat_id, user_text)

    await send_text(chat_id, response_text)
    tts_path = await tts.synthesize(response_text)
    await send_voice(chat_id, tts_path)
    return {"ok": True}