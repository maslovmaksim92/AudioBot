... (весь код до функции telegram_webhook без изменений) ...

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
    if mode == "simple":
        response_text = f"Ты сказал: {user_text}"
    else:
        response_text = await dialog.generate_response(chat_id, user_text)

    await send_text(chat_id, response_text)
    tts_path = await tts.synthesize(response_text)
    await send_voice(chat_id, tts_path)

    return {"ok": True}