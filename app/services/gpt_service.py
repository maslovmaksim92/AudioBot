import httpx
from typing import List

SYSTEM_PROMPT = "Ты — голосовой помощник. Отвечай кратко, дружелюбно, в стиле собеседника."
API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "mistralai/mistral-7b-instruct"
HEADERS = {
    "Authorization": "Bearer sk-or-public1234567890",  # Публичный ключ openrouter (пример)
    "Content-Type": "application/json"
}


class GPTService:
    async def generate(self, chat_history: List[dict]) -> str:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + chat_history

        payload = {
            "model": MODEL,
            "messages": messages,
            "temperature": 0.7
        }

        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.post(API_URL, json=payload, headers=HEADERS)
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]