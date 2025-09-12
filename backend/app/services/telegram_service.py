import logging
import httpx
from typing import Optional
from ..config.settings import TELEGRAM_BOT_TOKEN

logger = logging.getLogger(__name__)

class TelegramService:
    def __init__(self):
        self.bot_token = TELEGRAM_BOT_TOKEN
        logger.info("📱 Telegram service initialized")
    
    async def send_message(self, chat_id: int, text: str) -> bool:
        """Отправка сообщения в Telegram"""
        try:
            if not self.bot_token:
                logger.warning("⚠️ No Telegram bot token configured")
                return False
                
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "HTML"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, timeout=10)
                
                if response.status_code == 200:
                    logger.info(f"✅ Telegram message sent successfully to {chat_id}")
                    return True
                else:
                    logger.error(f"❌ Telegram API error: {response.status_code} - {response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Send Telegram message error: {e}")
            return False
    
    async def get_bot_info(self) -> Optional[dict]:
        """Получение информации о боте"""
        try:
            if not self.bot_token:
                return None
                
            url = f"https://api.telegram.org/bot{self.bot_token}/getMe"
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=5)
                
                if response.status_code == 200:
                    bot_info = response.json()
                    if bot_info.get("ok"):
                        return bot_info["result"]
                    
        except Exception as e:
            logger.error(f"❌ Get bot info error: {e}")
            
        return None
    
    def extract_message_data(self, update: dict) -> Optional[dict]:
        """Извлечение данных сообщения из webhook update"""
        if "message" not in update:
            return None
            
        message = update["message"]
        return {
            "chat_id": message.get("chat", {}).get("id"),
            "text": message.get("text", ""),
            "user_name": message.get("from", {}).get("first_name", "Пользователь"),
            "user_id": message.get("from", {}).get("id"),
            "message_id": message.get("message_id")
        }