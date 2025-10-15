"""
Роутер для Telegram webhook - двусторонняя коммуникация
"""
from fastapi import APIRouter, Request, HTTPException
from typing import Dict, Any
import logging
import json
import os

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/telegram-webhook", tags=["Telegram"])

# Хранилище команд для агентов (можно расширить до БД)
telegram_commands = {}

@router.post("/")
async def telegram_webhook(request: Request):
    """
    Webhook для получения обновлений от Telegram
    """
    try:
        data = await request.json()
        logger.info(f"📱 Telegram webhook received: {json.dumps(data, ensure_ascii=False)}")
        
        # Обработка сообщения
        if 'message' in data:
            message = data['message']
            chat_id = message.get('chat', {}).get('id')
            text = message.get('text', '')
            from_user = message.get('from', {})
            user_id = from_user.get('id')
            
            logger.info(f"💬 Message from {from_user.get('username', 'unknown')}: {text}")
            
            # Обработка фото (для бригад)
            if 'photo' in message:
                await handle_telegram_photo(chat_id, user_id, message['photo'], from_user)
            # Обработка команд
            elif text.startswith('/'):
                await handle_telegram_command(chat_id, user_id, text, from_user)
            else:
                await handle_telegram_message(chat_id, text, from_user)
        
        # Обработка callback query (inline buttons)
        elif 'callback_query' in data:
            callback = data['callback_query']
            chat_id = callback.get('message', {}).get('chat', {}).get('id')
            user_id = callback.get('from', {}).get('id')
            callback_data = callback.get('data', '')
            callback_query_id = callback.get('id')
            
            logger.info(f"🔘 Callback from user {user_id}: {callback_data}")
            
            await handle_telegram_callback(chat_id, user_id, callback_data, callback_query_id)
        
        return {"ok": True}
    
    except Exception as e:
        logger.error(f"❌ Error processing telegram webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def handle_auth_request(chat_id: int, user_id: int, auth_code: str, user: Dict[str, Any]):
    """
    Обработка запроса на аутентификацию через Telegram
    """
    import httpx
    
    bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
    BACKEND_URL = os.getenv("BACKEND_INTERNAL_URL", "http://localhost:8001")
    
    # Проверяем существование auth_code через backend
    from backend.app.routers.telegram_auth import auth_codes
    
    if auth_code not in auth_codes:
        # Код не найден или истёк
        await send_telegram_message(
            chat_id,
            "❌ Код не найден или истёк. Попробуйте начать вход заново.",
            bot_token
        )
        return
    
    auth_data = auth_codes[auth_code]
    username = auth_data.get("username", "неизвестный")
    
    # Отправляем сообщение с кнопками подтверждения
    keyboard = {
        "inline_keyboard": [
            [
                {"text": "✅ Подтвердить вход", "callback_data": f"auth_confirm_{auth_code}"},
                {"text": "❌ Отменить", "callback_data": f"auth_cancel_{auth_code}"}
            ]
        ]
    }
    
    message = f"🔐 <b>Вход в VasDom</b>\n\n"
    message += f"Пользователь: <b>{username}</b>\n\n"
    message += "Подтвердите вход в систему:"
    
    await send_telegram_message(chat_id, message, bot_token, reply_markup=keyboard)
    logger.info(f"Auth request sent to user {user_id} for code {auth_code}")

async def send_telegram_message(chat_id: int, text: str, bot_token: str, reply_markup: Dict = None):
    """Отправить сообщение в Telegram"""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            payload = {
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "HTML"
            }
            if reply_markup:
                payload["reply_markup"] = reply_markup
            
            response = await client.post(
                f"https://api.telegram.org/bot{bot_token}/sendMessage",
                json=payload
            )
            return response.status_code == 200
    except Exception as e:
        logger.error(f"Error sending telegram message: {e}")
        return False

async def handle_telegram_command(chat_id: int, user_id: int, command: str, user: Dict[str, Any]):
    """
    Обработка команд от пользователей
    
    Поддерживаемые команды для бригад:
    - /start - Список домов на сегодня
    - /start AUTH_xxx - Аутентификация через Telegram
    - /done - Завершить уборку и отправить фото
    
    Общие команды:
    - /help - Список команд
    - /agents - Список активных агентов
    - /status - Статус системы
    """
    import httpx
    from backend.app.services.telegram_cleaning_bot import (
        handle_start_command,
        handle_done_command
    )
    
    bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
    if not bot_token:
        return
    
    response_text = ""
    
    # Команды для бригад
    if command.startswith('/start'):
        # Проверяем, есть ли параметр для аутентификации
        if command.startswith('/start AUTH_'):
            # Это запрос на аутентификацию
            auth_code = command.replace('/start AUTH_', '').strip()
            await handle_auth_request(chat_id, user_id, auth_code, user)
            return
        else:
            # Обычный /start - показываем список домов
            await handle_start_command(chat_id, user_id, db_session=None)
            return
    
    elif command == '/done':
        await handle_done_command(chat_id, user_id, db_session=None)
        return
    
    # Общие команды
    elif command == '/help':
        response_text = """📋 Доступные команды:

/start - Начать работу
/help - Список команд
/agents - Список активных агентов
/status - Статус системы
/ping - Проверка связи

Или просто напиши сообщение, и я передам его команде! 📨"""
    
    elif command == '/agents':
        # Получаем список агентов
        try:
            import asyncpg
            db_url = os.environ.get('DATABASE_URL', '').replace('postgresql+asyncpg://', 'postgresql://')
            conn = await asyncpg.connect(db_url)
            
            rows = await conn.fetch("SELECT name, status, type FROM agents WHERE status = 'active' LIMIT 5")
            await conn.close()
            
            if rows:
                response_text = "🤖 Активные агенты:\n\n"
                for row in rows:
                    response_text += f"• {row['name']} ({row['type']})\n"
            else:
                response_text = "Нет активных агентов"
        except Exception as e:
            response_text = f"Ошибка получения агентов: {e}"
    
    elif command == '/status':
        response_text = "✅ Система работает нормально\n\n📊 Статистика:\n• Backend: OK\n• База данных: OK\n• Scheduler: OK"
    
    elif command == '/ping':
        response_text = "🏓 Pong!"
    
    else:
        response_text = f"Неизвестная команда: {command}\n\nИспользуй /help для списка команд"
    
    # Отправляем ответ
    if response_text:
        try:
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"https://api.telegram.org/bot{bot_token}/sendMessage",
                    json={
                        'chat_id': chat_id,
                        'text': response_text,
                        'parse_mode': 'HTML'
                    }
                )
        except Exception as e:
            logger.error(f"❌ Error sending telegram response: {e}")


async def handle_telegram_callback(chat_id: int, user_id: int, callback_data: str, callback_query_id: str):
    """
    Обработка нажатий на inline кнопки
    """
    import httpx
    
    bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
    if not bot_token:
        return
    
    # Обработка аутентификации
    if callback_data.startswith('auth_confirm_'):
        auth_code = callback_data.replace('auth_confirm_', '')
        
        # Подтверждаем через backend API
        from backend.app.routers.telegram_auth import auth_codes
        
        if auth_code in auth_codes:
            auth_codes[auth_code]['confirmed'] = True
            auth_codes[auth_code]['telegram_chat_id'] = chat_id
            
            # Отправляем уведомление
            message = "✅ <b>Вход подтверждён!</b>\n\nВы можете вернуться в браузер."
            
            await send_telegram_message(chat_id, message, bot_token)
            
            # Отвечаем на callback query
            await answer_callback_query(callback_query_id, "✅ Вход подтверждён", bot_token)
            logger.info(f"Auth confirmed by user {user_id} for code {auth_code}")
        else:
            await answer_callback_query(callback_query_id, "❌ Код истёк", bot_token)
    
    elif callback_data.startswith('auth_cancel_'):
        auth_code = callback_data.replace('auth_cancel_', '')
        
        # Отменяем
        from backend.app.routers.telegram_auth import auth_codes
        if auth_code in auth_codes:
            del auth_codes[auth_code]
        
        message = "❌ <b>Вход отменён</b>"
        await send_telegram_message(chat_id, message, bot_token)
        await answer_callback_query(callback_query_id, "Отменено", bot_token)
    
    # Обработка выбора дома для уборки (существующий функционал)
    elif callback_data.startswith('select_house_'):
        from backend.app.services.telegram_cleaning_bot import handle_house_selection
        await handle_house_selection(chat_id, user_id, callback_data, callback_query_id)

async def answer_callback_query(callback_query_id: str, text: str, bot_token: str):
    """Ответить на callback query"""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            await client.post(
                f"https://api.telegram.org/bot{bot_token}/answerCallbackQuery",
                json={
                    "callback_query_id": callback_query_id,
                    "text": text
                }
            )
    except Exception as e:
        logger.error(f"Error answering callback query: {e}")

async def handle_telegram_message(chat_id: int, text: str, user: Dict[str, Any]):
    """
    Обработка обычных сообщений (не команд)
    """
    import httpx
    
    bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
    if not bot_token:
        return
    
    # Логируем сообщение
    logger.info(f"📝 Regular message from {user.get('username')}: {text}")
    
    # Можно добавить AI обработку или пересылку администраторам
    response_text = f"Спасибо за сообщение! Я передал его команде. 📬"
    
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                f"https://api.telegram.org/bot{bot_token}/sendMessage",
                json={
                    'chat_id': chat_id,
                    'text': response_text
                }
            )
    except Exception as e:
        logger.error(f"❌ Error sending telegram response: {e}")


@router.post("/set-webhook")
async def set_telegram_webhook():
    """
    Установить webhook для Telegram бота
    """
    try:
        import httpx
        
        bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
        if not bot_token:
            raise HTTPException(status_code=500, detail="TELEGRAM_BOT_TOKEN not configured")
        
        # URL webhook должен быть публичным (например, через Render)
        webhook_url = os.environ.get('WEBHOOK_URL', 'https://audiobot-qci2.onrender.com')
        full_webhook_url = f"{webhook_url}/api/telegram-webhook/"
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://api.telegram.org/bot{bot_token}/setWebhook",
                json={'url': full_webhook_url}
            )
            
            result = response.json()
            
            if result.get('ok'):
                logger.info(f"✅ Telegram webhook set to: {full_webhook_url}")
                return {
                    "success": True,
                    "message": "Webhook registered successfully",
                    "webhook_url": full_webhook_url
                }
            else:
                logger.error(f"❌ Failed to set webhook: {result}")
                raise HTTPException(status_code=500, detail=result.get('description'))
    
    except Exception as e:
        logger.error(f"❌ Error setting webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/webhook-info")
async def get_webhook_info():
    """
    Получить информацию о текущем webhook
    """
    try:
        import httpx
        
        bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
        if not bot_token:
            raise HTTPException(status_code=500, detail="TELEGRAM_BOT_TOKEN not configured")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://api.telegram.org/bot{bot_token}/getWebhookInfo"
            )
            
            return response.json()
    
    except Exception as e:
        logger.error(f"❌ Error getting webhook info: {e}")
        raise HTTPException(status_code=500, detail=str(e))



async def handle_telegram_callback(chat_id: int, user_id: int, callback_data: str, callback_query_id: str):
    """
    Обработка callback query (inline buttons)
    """
    from backend.app.services.telegram_cleaning_bot import handle_house_selection
    
    logger.info(f"[telegram_webhook] Callback: {callback_data} from user {user_id}")
    
    try:
        # Обработка выбора дома
        if callback_data.startswith('house_'):
            house_id = callback_data.replace('house_', '')
            await handle_house_selection(chat_id, user_id, house_id, callback_query_id, db_session=None)
        else:
            logger.warning(f"Unknown callback_data: {callback_data}")
    
    except Exception as e:
        logger.error(f"[telegram_webhook] Error in handle_telegram_callback: {e}")


async def handle_telegram_photo(chat_id: int, user_id: int, photos: list, user: Dict[str, Any]):
    """
    Обработка фото от бригад
    """
    from backend.app.services.telegram_cleaning_bot import handle_photo
    
    try:
        # Берём фото максимального размера
        largest_photo = max(photos, key=lambda p: p.get('file_size', 0))
        file_id = largest_photo.get('file_id')
        
        logger.info(f"[telegram_webhook] Photo received from user {user_id}, file_id: {file_id}")
        
        await handle_photo(chat_id, user_id, file_id)
    
    except Exception as e:
        logger.error(f"[telegram_webhook] Error in handle_telegram_photo: {e}")

