from typing import Optional


class DialogService:
    def generate_response(self, user_text: str) -> str:
        user_text = user_text.lower()

        if "привет" in user_text:
            return "Привет! Рад тебя слышать."
        if "как дела" in user_text:
            return "У меня всё отлично! А у тебя как?"
        if "который час" in user_text:
            from datetime import datetime
            return f"Сейчас {datetime.now().strftime('%H:%M')}"

        # по умолчанию — эхо
        return f"Ты сказал: {user_text}"