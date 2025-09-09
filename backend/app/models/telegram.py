from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class TelegramUser(BaseModel):
    id: int
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None
    is_bot: Optional[bool] = False

class TelegramChat(BaseModel):
    id: int
    type: str  # "private", "group", "supergroup", "channel"
    title: Optional[str] = None
    username: Optional[str] = None

class TelegramMessage(BaseModel):
    message_id: int
    from_user: Optional[TelegramUser] = Field(None, alias="from")
    chat: TelegramChat
    date: int
    text: Optional[str] = None
    
    class Config:
        populate_by_name = True  # Pydantic v2 equivalent of allow_population_by_field_name

class TelegramUpdate(BaseModel):
    update_id: int
    message: Optional[TelegramMessage] = None
    
    @field_validator('message')
    @classmethod
    def validate_message(cls, v):
        if v is None:
            logger.warning("⚠️ Telegram update without message received")
        return v
    
    def extract_message_data(self) -> Optional[Dict[str, Any]]:
        """Извлечение данных сообщения из update"""
        if not self.message:
            return None
            
        return {
            "chat_id": self.message.chat.id,
            "text": self.message.text or "",
            "user_name": self.message.from_user.first_name if self.message.from_user else "Пользователь",
            "user_id": self.message.from_user.id if self.message.from_user else None,
            "message_id": self.message.message_id,
            "chat_type": self.message.chat.type
        }
    
    def has_text_message(self) -> bool:
        """Проверка что update содержит текстовое сообщение"""
        return (
            self.message is not None and 
            self.message.text is not None and 
            len(self.message.text.strip()) > 0
        )