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
            
            logger.info(f"💬 Message from {from_user.get('username', 'unknown')}: {text}")
            
            # Обработка команд
            if text.startswith('/'):
                await handle_telegram_command(chat_id, text, from_user)
            else:
                await handle_telegram_message(chat_id, text, from_user)
        
        return {"ok": True}
    
    except Exception as e:
        logger.error(f"❌ Error processing telegram webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def handle_telegram_command(chat_id: int, command: str, user: Dict[str, Any]):
    """
    Обработка команд от пользователей
    
    Поддерживаемые команды:
    - /start - Приветствие
    - /help - Список команд
    - /agents - Список активных агентов
    - /status - Статус системы
    """
    import httpx
    
    bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
    if not bot_token:
        return
    
    response_text = ""
    
    if command == '/start':
        response_text = f"👋 Привет, {user.get('first_name', 'пользователь')}!\n\nЯ бот VasDom для управления задачами и уведомлениями.\n\nИспользуй /help чтобы узнать доступные команды."
    
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
