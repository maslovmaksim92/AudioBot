import httpx
import os
from typing import List

SYSTEM_PROMPT = (
    "Ты — персональный голосовой ассистент. Отвечай уверенно, дружелюбно, говори кратко и понятно. "
    "Ты умеешь вести расписание, напоминать о задачах, помогать с планированием, отвечать на вопросы. "
    "Твоя задача — быть полезным собеседником и помощником в делах пользователя."
)

API_URL = "https://api.openai.com/v1/chat/completions"
MODEL = os.getenv("GPT_MODEL", "gpt-4")
HEADERS = {
    "Authorization": f"Bearer {os.getenv('OPEN_AI_KEY')}",
    "Content-Type": "application/json"
}

class GPTService:
    def __init__(self):
        self.model = MODEL

    async def generate(self, chat_history: List[dict]) -> str:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + chat_history

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.7
        }

        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.post(API_URL, json=payload, headers=HEADERS)
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]