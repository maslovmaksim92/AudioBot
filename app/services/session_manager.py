from collections import defaultdict
from typing import List
from pathlib import Path
import os

class SessionManager:
    def __init__(self, max_messages: int = 10):
        self.max_messages = max_messages
        self.sessions = defaultdict(list)  # chat_id: List[dict]
        self.history_dir = Path("history")
        self.history_dir.mkdir(exist_ok=True)
        self.usage_stats = defaultdict(lambda: {"requests": 0, "tokens": 0})

    def append(self, chat_id: int, role: str, content: str):
        self.sessions[chat_id].append({"role": role, "content": content})
        if len(self.sessions[chat_id]) > self.max_messages:
            self.sessions[chat_id] = self.sessions[chat_id][-self.max_messages:]

        self._write_to_file(chat_id, role, content)

        if role == "user":
            self.usage_stats[chat_id]["requests"] += 1
            self.usage_stats[chat_id]["tokens"] += len(content)

    def get_context(self, chat_id: int) -> List[dict]:
        return self.sessions[chat_id]

    def get_usage(self, chat_id: int) -> dict:
        return self.usage_stats[chat_id]

    def reset(self, chat_id: int):
        self.sessions[chat_id] = []
        self.usage_stats[chat_id] = {"requests": 0, "tokens": 0}
        file_path = self.history_dir / f"{chat_id}.txt"
        if file_path.exists():
            file_path.unlink()

    def _write_to_file(self, chat_id: int, role: str, content: str):
        file_path = self.history_dir / f"{chat_id}.txt"
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(f"{role.upper()}: {content}\n\n")