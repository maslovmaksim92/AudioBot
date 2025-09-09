import logging
from fastapi import APIRouter, HTTPException
from ..models.schemas import TelegramUpdate
from ..services.telegram_service import TelegramService
from ..services.ai_service import AIService
from ..config.settings import TELEGRAM_BOT_TOKEN, TELEGRAM_WEBHOOK_URL

logger = logging.getLogger(__name__)
router = APIRouter(tags=["telegram"])

# Initialize services
telegram_service = TelegramService()
ai_service = AIService()

@router.post("/telegram/webhook")
@router.post("/api/telegram/webhook")
async def telegram_webhook(update: dict):
    """Telegram webhook endpoint с ответами"""
    try:
        logger.info(f"📱 Telegram webhook received: {update.get('update_id', 'unknown')}")
        
        # Извлекаем данные сообщения
        message_data = telegram_service.extract_message_data(update)
        
        if message_data and message_data["text"]:
            chat_id = message_data["chat_id"]
            text = message_data["text"]
            user_name = message_data["user_name"]
            
            logger.info(f"💬 Message from {user_name} (chat {chat_id}): {text}")
            
            # Генерируем ответ через AI
            ai_response = await ai_service.process_message(text, f"telegram_{chat_id}")
            
            # Отправляем ответ обратно в Telegram
            if chat_id:
                success = await telegram_service.send_message(chat_id, ai_response)
                if success:
                    logger.info(f"✅ Response sent to Telegram chat {chat_id}")
                
                return {
                    "status": "processed",
                    "message": "Message processed and response sent",
                    "chat_id": chat_id,
                    "user_message": text,
                    "ai_response": ai_response[:100] + "..." if len(ai_response) > 100 else ai_response
                }
        
        return {
            "status": "received",
            "message": "Webhook received but no message to process",
            "update_id": update.get("update_id")
        }
        
    except Exception as e:
        logger.error(f"❌ Telegram webhook error: {e}")
        return {"status": "error", "message": str(e)}

@router.get("/api/telegram/status")
async def telegram_status():
    """Telegram bot status с тестированием"""
    status = {
        "status": "configured" if TELEGRAM_BOT_TOKEN else "missing_token",
        "bot_token": "present" if TELEGRAM_BOT_TOKEN else "missing",
        "webhook_url": TELEGRAM_WEBHOOK_URL or 'not_configured',
        "message": "Telegram bot готов для интеграции"
    }
    
    # Проверяем соединение с Telegram API если есть токен
    if TELEGRAM_BOT_TOKEN:
        bot_info = await telegram_service.get_bot_info()
        if bot_info:
            status["bot_info"] = bot_info
            status["connection"] = "✅ Connected to Telegram API"
            logger.info(f"✅ Telegram bot connected: @{bot_info.get('username')}")
        else:
            status["connection"] = "❌ Connection failed"
    
    return status