from collections import defaultdict
from typing import List

class SessionManager:
    def __init__(self, max_messages: int = 10):
        self.max_messages = max_messages
        self.sessions = defaultdict(list)  # chat_id: List[str]

    def append(self, chat_id: int, role: str, content: str):
        self.sessions[chat_id].append({"role": role, "content": content})
        if len(self.sessions[chat_id]) > self.max_messages:
            self.sessions[chat_id] = self.sessions[chat_id][-self.max_messages:]

    def get_context(self, chat_id: int) -> List[dict]:
        return self.sessions[chat_id]

    def reset(self, chat_id: int):
        self.sessions[chat_id] = []