"""
API роутер для Telegram Bot - webhook и обработка сообщений с Brain integration
"""
from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional, Dict, Any
import logging

from backend.app.config.database import get_db
from backend.app.services.telegram_service import telegram_service
from backend.app.services.brain_router import try_fast_answer
from backend.app.models.log import Log, LogLevel, LogCategory
from uuid import uuid4
from datetime import datetime

logger = logging.getLogger(__name__)


import os
import httpx


router = APIRouter(prefix="/telegram", tags=["Telegram"])


# ============= Webhook Management =============

@router.get("/webhook/info")
async def get_webhook_info():
    """Получить информацию о текущем webhook"""
    try:
        bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not bot_token:
            return {"error": "TELEGRAM_BOT_TOKEN not configured"}
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://api.telegram.org/bot{bot_token}/getWebhookInfo"
            )
            data = response.json()
            logger.info(f"🔍 Webhook info: {data}")
            return data
    except Exception as e:
        logger.error(f"Error getting webhook info: {e}")
        return {"error": str(e)}

@router.post("/webhook/set")
async def set_webhook():
    """Установить webhook для бота"""
    try:
        bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        webhook_url = os.getenv('TELEGRAM_WEBHOOK_URL')
        
        if not bot_token or not webhook_url:
            return {"error": "TELEGRAM_BOT_TOKEN or TELEGRAM_WEBHOOK_URL not configured"}
        
        logger.info(f"🔧 Setting webhook to: {webhook_url}")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://api.telegram.org/bot{bot_token}/setWebhook",
                json={
                    "url": webhook_url,
                    "drop_pending_updates": True
                }
            )
            data = response.json()
            logger.info(f"✅ Webhook set result: {data}")
            return data
    except Exception as e:
        logger.error(f"Error setting webhook: {e}")
        return {"error": str(e)}

@router.post("/webhook/delete")
async def delete_webhook():
    """Удалить webhook"""
    try:
        bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not bot_token:
            return {"error": "TELEGRAM_BOT_TOKEN not configured"}
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://api.telegram.org/bot{bot_token}/deleteWebhook",
                json={"drop_pending_updates": True}
            )
            data = response.json()
            logger.info(f"🗑️ Webhook deleted: {data}")
            return data
    except Exception as e:
        logger.error(f"Error deleting webhook: {e}")
        return {"error": str(e)}

@router.get("/test/send")
async def test_send_message(chat_id: str, text: str = "Test message"):
    """Тестовая отправка сообщения"""
    try:
        logger.info(f"🧪 Testing message send to {chat_id}: {text}")
        success = await telegram_service.send_message(chat_id=chat_id, text=text)
        return {"success": success, "chat_id": chat_id, "text": text}
    except Exception as e:
        logger.error(f"Error in test send: {e}")
        return {"error": str(e)}

# ============= Webhook Handler =============



class TelegramUpdate(BaseModel):
    """Модель обновления от Telegram"""
    update_id: int
    message: Optional[Dict[str, Any]] = None
    callback_query: Optional[Dict[str, Any]] = None

@router.post("/webhook")
async def telegram_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Webhook для приема обновлений от Telegram
    Обрабатывает:
    - Фото от бригад
    - Текстовые сообщения
    - Callback query от кнопок
    """
    
    try:
        # Получаем RAW body для логирования
        body = await request.body()
        logger.info(f"📥 TELEGRAM WEBHOOK RECEIVED")
        logger.info(f"📋 Raw body: {body.decode('utf-8')}")
        
        # Парсим JSON
        import json
        data = json.loads(body)
        logger.info(f"📦 Parsed data: {json.dumps(data, indent=2, ensure_ascii=False)}")
        
        # Создаем update object
        update = TelegramUpdate(**data)
        logger.info(f"✅ Update parsed successfully. Update ID: {update.update_id}")
        
        # Обработка сообщения
        if update.message:
            logger.info(f"💬 Processing message from update {update.update_id}")
            logger.info(f"📝 Message data: {update.message}")
            await handle_message(update.message, db)
        else:
            logger.warning(f"⚠️ No message in update {update.update_id}")
        
        # Обработка callback query
        if update.callback_query:
            logger.info(f"🔘 Processing callback query from update {update.update_id}")
            await handle_callback_query(update.callback_query, db)
        
        logger.info(f"✅ Webhook processed successfully for update {update.update_id}")
        return {"status": "ok"}
        
    except Exception as e:
        logger.error(f"❌ ERROR in webhook handler: {e}")
        import traceback
        logger.error(f"📍 Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

async def handle_message(message: Dict[str, Any], db: AsyncSession):
    """Обработка входящего сообщения"""
    
    chat_id = message.get("chat", {}).get("id")
    message_id = message.get("message_id")
    from_user = message.get("from", {})
    user_name = from_user.get("first_name", "Unknown")
    user_username = from_user.get("username", "")
    
    # Обработка фото
    if "photo" in message:
        await handle_photo(message, chat_id, user_name, user_username, db)
    
    # Обработка текста
    elif "text" in message:
        await handle_text(message, chat_id, user_name, user_username, db)
    
    # Логирование
    log = Log(
        id=str(uuid4()),
        level=LogLevel.INFO,
        category=LogCategory.INTEGRATION,
        message=f"Telegram message from {user_name} (@{user_username})",
        extra_data={
            "chat_id": chat_id,
            "message_id": message_id,
            "user_id": from_user.get("id")
        },
        created_at=datetime.now(timezone.utc)
    )
    
    db.add(log)
    await db.commit()

async def handle_photo(
    message: Dict[str, Any],
    chat_id: int,
    user_name: str,
    user_username: str,
    db: AsyncSession
):
    """Обработка фото от бригад"""
    
    logger.info(f"📸 Получено фото от {user_name} (@{user_username})")
    
    # Получаем file_id самого большого фото (последний элемент)
    photos = message.get("photo", [])
    if not photos:
        return
    
    largest_photo = photos[-1]
    file_id = largest_photo.get("file_id")
    
    # Описание к фото (если есть)
    caption = message.get("caption", "")
    
    # Информация об отправителе
    sender_info = f"Бригада: {user_name}"
    if user_username:
        sender_info += f" (@{user_username})"
    
    # Пересылка фото в канал/группу
    success = await telegram_service.forward_photo_to_channel(
        photo_file_id=file_id,
        caption=caption,
        sender_info=sender_info
    )
    
    # Отправка подтверждения отправителю
    if success:
        await telegram_service.send_message(
            chat_id=str(chat_id),
            text="✅ Фото принято и опубликовано в группе!"
        )
    else:
        await telegram_service.send_message(
            chat_id=str(chat_id),
            text="⚠️ Фото принято, но не удалось опубликовать в группе"
        )
    
    # TODO: Сохранить фото в базе данных (привязать к дому)
    # Можно добавить логику определения дома по контексту или комментарию

async def handle_text(
    message: Dict[str, Any],
    chat_id: int,
    user_name: str,
    user_username: str,
    db: AsyncSession
):
    """Обработка текстовых сообщений"""
    
    text = message.get("text", "").strip()
    from_user = message.get("from", {})
    user_id = from_user.get("id")
    
    logger.info(f"💬 Получено сообщение от {user_name}: {text[:50]}...")
    
    # Команда /start - регистрация пользователя
    if text == "/start":
        logger.info(f"👤 Пользователь {user_name} (@{user_username}) запустил бота. Chat ID: {chat_id}")
        
        # Сохраняем в .env для владельца
        phone = from_user.get("phone_number")
        
        welcome_msg = f"""👋 Привет, {user_name}!

Я бот VasDom AudioBot.

📋 Ваши данные:
• Chat ID: <code>{chat_id}</code>
• User ID: {user_id}
• Username: @{user_username if user_username else 'не указан'}

✅ Теперь я могу отправлять вам уведомления!

⏰ Расписание:
• 8:25 - напоминание о планерке
• 16:55 - AI звонок для сбора отчётности"""
        
        await telegram_service.send_message(
            chat_id=str(chat_id),
            text=welcome_msg
        )
        
        # Логируем chat_id для настройки
        logger.warning(f"🔑 IMPORTANT: Chat ID for @{user_username}: {chat_id}")
        return
    
    # Команды
    if text.startswith("/"):
        await handle_command(text, chat_id, user_name, user_username, db)
    else:
        # Обычное сообщение - можно добавить AI обработку
        pass

async def handle_command(
    command: str,
    chat_id: int,
    user_name: str,
    user_username: str,
    db: AsyncSession
):
    """Обработка команд"""
    
    cmd = command.lower().split()[0]
    
    if cmd == "/start":
        welcome_text = f"""
👋 Привет, {user_name}!

Я бот VasDom AudioBot.

📸 Отправляй мне фото с объектов - я автоматически опубликую их в группе.

📋 Доступные команды:
/help - помощь
/status - статус бота
        """
        await telegram_service.send_message(str(chat_id), welcome_text)
    
    elif cmd == "/help":
        help_text = """
📖 <b>Помощь по боту</b>

<b>Отправка фото:</b>
Просто отправь фото с подписью (адрес дома или комментарий)

<b>Команды:</b>
/start - начало работы
/help - эта справка
/status - статус бота и синхронизации
        """
        await telegram_service.send_message(str(chat_id), help_text)
    
    elif cmd == "/status":
        # TODO: Получить реальную статистику
        status_text = """
✅ <b>Статус бота</b>

🟢 Бот работает
📸 Фото принимаются
🔄 Синхронизация активна

📊 За сегодня:
• Фото получено: ~0
• Фото опубликовано: ~0
        """
        await telegram_service.send_message(str(chat_id), status_text)

async def handle_callback_query(callback: Dict[str, Any], db: AsyncSession):
    """Обработка нажатий на кнопки"""
    
    query_id = callback.get("id")
    data = callback.get("data", "")
    chat_id = callback.get("message", {}).get("chat", {}).get("id")
    
    logger.info(f"🔘 Callback query: {data}")
    
    # TODO: Обработка действий по кнопкам
    # Например: подтверждение задач, выбор дома и т.д.

@router.get("/webhook-info")
async def get_webhook_info():
    """Получение информации о webhook"""
    
    info = await telegram_service.get_webhook_info()
    return info

@router.post("/set-webhook")
async def set_webhook(webhook_url: str):
    """Установка webhook для бота"""
    
    success = await telegram_service.set_webhook(webhook_url)
    
    if success:
        return {"message": "Webhook установлен", "url": webhook_url}
    else:
        raise HTTPException(status_code=500, detail="Ошибка установки webhook")

@router.post("/send-notification")
async def send_notification(
    chat_id: str,
    text: str,
    parse_mode: str = "HTML"
):
    """Отправка уведомления (для тестирования)"""
    
    success = await telegram_service.send_message(chat_id, text, parse_mode)
    
    if success:
        return {"message": "Уведомление отправлено"}
    else:
        raise HTTPException(status_code=500, detail="Ошибка отправки")
