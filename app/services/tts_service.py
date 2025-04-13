import asyncio
import edge_tts
from pathlib import Path
import uuid

VOICE = "ru-RU-DmitryNeural"  # можно заменить на Aria, Jane и т.д.
OUTPUT_DIR = Path("/tmp")


class TTSService:
    def __init__(self, voice: str = VOICE):
        self.voice = voice

    async def synthesize(self, text: str) -> Path:
        filename = OUTPUT_DIR / f"tts_{uuid.uuid4().hex}.ogg"
        communicate = edge_tts.Communicate(text, self.voice)
        await communicate.save(str(filename))
        return filename


# Пример вызова:
# tts = TTSService()
# asyncio.run(tts.synthesize("Привет!"))