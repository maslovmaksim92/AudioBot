from app.services.gpt_service import GPTService
from app.services.session_manager import SessionManager


class DialogService:
    def __init__(self):
        self.gpt = GPTService()
        self.sessions = SessionManager()

    async def generate_response(self, chat_id: int, user_text: str) -> str:
        self.sessions.append(chat_id, "user", user_text)
        context = self.sessions.get_context(chat_id)
        reply = await self.gpt.generate(context)
        self.sessions.append(chat_id, "assistant", reply)
        return reply

    def reset_context(self, chat_id: int):
        self.sessions.reset(chat_id)