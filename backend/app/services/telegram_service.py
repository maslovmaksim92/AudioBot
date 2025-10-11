"""
Сервис Telegram Bot - прием фото от бригад и уведомления
- Прием ~300 фото/день от бригад
- Автоматическая публикация в ТГ группу
- Уведомления персоналу о задачах/планерках
"""
import httpx
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import os

from backend.app.config.settings import settings

logger = logging.getLogger(__name__)

class TelegramService:
    """Сервис для работы с Telegram Bot API"""
    
    def __init__(self):
        self.bot_token = settings.TELEGRAM_BOT_TOKEN
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}"
        self.timeout = httpx.Timeout(30.0)
        
        # Группа для публикации фото (нужно будет настроить)
        self.photos_channel_id = os.getenv("TELEGRAM_PHOTOS_CHANNEL_ID", "")
    
    async def send_message(
        self,
        chat_id: str,
        text: str,
        parse_mode: str = "HTML",
        reply_markup: Optional[Dict] = None
    ) -> bool:
        """Отправка текстового сообщения"""
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                url = f"{self.api_url}/sendMessage"
                payload = {
                    "chat_id": chat_id,
                    "text": text,
                    "parse_mode": parse_mode
                }
                
                if reply_markup:
                    payload["reply_markup"] = reply_markup
                
                response = await client.post(url, json=payload)
                
                if response.status_code == 200:
                    logger.info(f"✅ Сообщение отправлено в чат {chat_id}")
                    return True
                else:
                    logger.error(f"❌ Ошибка отправки сообщения: {response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Исключение при отправке сообщения: {e}")
            return False
    
    async def send_photo(
        self,
        chat_id: str,
        photo_url: Optional[str] = None,
        photo_file: Optional[bytes] = None,
        caption: Optional[str] = None,
        parse_mode: str = "HTML"
    ) -> bool:
        """Отправка фото"""
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                url = f"{self.api_url}/sendPhoto"
                
                if photo_url:
                    # Отправка по URL
                    payload = {
                        "chat_id": chat_id,
                        "photo": photo_url,
                        "caption": caption or "",
                        "parse_mode": parse_mode
                    }
                    response = await client.post(url, json=payload)
                    
                elif photo_file:
                    # Отправка файла
                    files = {"photo": ("photo.jpg", photo_file, "image/jpeg")}
                    data = {
                        "chat_id": chat_id,
                        "caption": caption or "",
                        "parse_mode": parse_mode
                    }
                    response = await client.post(url, data=data, files=files)
                    
                else:
                    logger.error("Не указано ни photo_url, ни photo_file")
                    return False
                
                if response.status_code == 200:
                    logger.info(f"✅ Фото отправлено в чат {chat_id}")
                    return True
                else:
                    logger.error(f"❌ Ошибка отправки фото: {response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Исключение при отправке фото: {e}")
            return False
    
    async def forward_photo_to_channel(
        self,
        photo_file_id: str,
        caption: Optional[str] = None,
        sender_info: Optional[str] = None
    ) -> bool:
        """
        Пересылка фото в канал/группу для публикации
        Используется для автоматической публикации фото от бригад
        """
        
        if not self.photos_channel_id:
            logger.warning("TELEGRAM_PHOTOS_CHANNEL_ID не настроен")
            return False
        
        # Формирование описания
        full_caption = f"📸 {sender_info}\n" if sender_info else ""
        full_caption += f"{caption}\n\n" if caption else ""
        full_caption += f"🕒 {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                url = f"{self.api_url}/sendPhoto"
                payload = {
                    "chat_id": self.photos_channel_id,
                    "photo": photo_file_id,
                    "caption": full_caption,
                    "parse_mode": "HTML"
                }
                
                response = await client.post(url, json=payload)
                
                if response.status_code == 200:
                    logger.info(f"✅ Фото опубликовано в канале")
                    return True
                else:
                    logger.error(f"❌ Ошибка публикации фото: {response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Исключение при публикации фото: {e}")
            return False
    
    async def send_bulk_notification(
        self,
        chat_ids: List[str],
        text: str,
        parse_mode: str = "HTML"
    ) -> Dict[str, int]:
        """
        Массовая рассылка уведомлений
        Возвращает количество успешных/неудачных отправок
        """
        
        results = {"success": 0, "failed": 0}
        
        for chat_id in chat_ids:
            success = await self.send_message(chat_id, text, parse_mode)
            if success:
                results["success"] += 1
            else:
                results["failed"] += 1
        
        logger.info(f"📊 Массовая рассылка: успешно {results['success']}, ошибок {results['failed']}")
        
        return results
    
    async def send_plannerka_reminder(self, chat_ids: List[str], time: str = "8:30") -> bool:
        """
        Отправка напоминания о планерке
        Используется в AI задачах (каждый день в 8:25)
        """
        
        text = f"""
🔔 <b>Напоминание о планерке!</b>

📅 Сегодня в {time}
📍 Zoom / Офис

⏰ Не опаздывайте!
        """
        
        results = await self.send_bulk_notification(chat_ids, text)
        
        return results["success"] > 0
    
    async def notify_new_task(
        self,
        chat_id: str,
        task_title: str,
        task_description: Optional[str] = None,
        due_date: Optional[str] = None,
        priority: str = "medium"
    ) -> bool:
        """Уведомление о новой задаче"""
        
        priority_emoji = {
            "low": "🟢",
            "medium": "🟡",
            "high": "🟠",
            "urgent": "🔴"
        }
        
        emoji = priority_emoji.get(priority, "🟡")
        
        text = f"""
{emoji} <b>Новая задача!</b>

📋 {task_title}
"""
        
        if task_description:
            text += f"\n📝 {task_description}\n"
        
        if due_date:
            text += f"\n⏰ Срок: {due_date}"
        
        text += "\n\n👉 Проверьте дашборд для деталей"
        
        return await self.send_message(chat_id, text)
    
    async def get_webhook_info(self) -> Dict[str, Any]:
        """Получение информации о webhook"""
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                url = f"{self.api_url}/getWebhookInfo"
                response = await client.get(url)
                
                if response.status_code == 200:
                    return response.json().get("result", {})
                else:
                    return {}
                    
        except Exception as e:
            logger.error(f"Ошибка получения webhook info: {e}")
            return {}
    
    async def set_webhook(self, webhook_url: str) -> bool:
        """Установка webhook для бота"""
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                url = f"{self.api_url}/setWebhook"
                payload = {
                    "url": webhook_url,
                    "allowed_updates": ["message", "callback_query"]
                }
                
                response = await client.post(url, json=payload)
                
                if response.status_code == 200:
                    logger.info(f"✅ Webhook установлен: {webhook_url}")
                    return True
                else:
                    logger.error(f"❌ Ошибка установки webhook: {response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Исключение при установке webhook: {e}")
            return False

# Singleton instance
telegram_service = TelegramService()
