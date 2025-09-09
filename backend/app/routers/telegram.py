import logging
from fastapi import APIRouter, HTTPException, Depends
from ..models.telegram import TelegramUpdate
from ..services.telegram_service import TelegramService
from ..services.ai_service import AIService
from ..services.bitrix_service import BitrixService
from ..security import telegram_security_check, optional_auth
from ..config.settings import TELEGRAM_BOT_TOKEN, TELEGRAM_WEBHOOK_URL, BITRIX24_WEBHOOK_URL

logger = logging.getLogger(__name__)
router = APIRouter(tags=["telegram"])

# Initialize services
telegram_service = TelegramService()
ai_service = AIService()
bitrix_service = BitrixService(BITRIX24_WEBHOOK_URL)

@router.post("/telegram/webhook")
@router.post("/api/telegram/webhook")
async def telegram_webhook(
    update: TelegramUpdate,  # Заменил dict на TelegramUpdate модель
    _security: bool = Depends(telegram_security_check)
):
    """Telegram webhook endpoint с валидацией и обработкой задач для Bitrix24"""
    try:
        logger.info(f"📱 Telegram webhook received: {update.update_id}")
        
        # Валидация обязательных полей
        if not update.has_text_message():
            raise HTTPException(
                status_code=400, 
                detail="Invalid update: missing message or text content"
            )
        
        # Извлекаем данные сообщения
        message_data = update.extract_message_data()
        if not message_data:
            raise HTTPException(
                status_code=400,
                detail="Invalid update: cannot extract message data"
            )
        
        chat_id = message_data["chat_id"]
        text = message_data["text"]
        user_name = message_data["user_name"]
        
        logger.info(f"💬 Message from {user_name} (chat {chat_id}): {text}")
        
        # Проверяем команды для создания задач в Bitrix24
        if text.lower().startswith('/задача ') or text.lower().startswith('/task '):
            return await handle_bitrix_task_creation(text, chat_id, user_name)
        
        # Обычный AI ответ
        ai_response = await ai_service.process_message(text, f"telegram_{chat_id}")
        
        # Отправляем ответ обратно в Telegram
        if chat_id:
            success = await telegram_service.send_message(chat_id, ai_response)
            if not success:
                logger.error(f"❌ Failed to send response to Telegram chat {chat_id}")
                return {
                    "status": "failed",
                    "message": "Message processed but failed to send response",
                    "error": "Telegram API error",
                    "chat_id": chat_id
                }
            
            logger.info(f"✅ Response sent to Telegram chat {chat_id}")
                
        return {
            "status": "processed",
            "message": "Message processed and response sent",
            "chat_id": chat_id,
            "user_message": text,
            "ai_response": ai_response[:100] + "..." if len(ai_response) > 100 else ai_response
        }
        
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        logger.error(f"❌ Telegram webhook error: {e}")
        return {
            "status": "failed", 
            "message": "Internal server error",
            "error": str(e)
        }

async def handle_bitrix_task_creation(text: str, chat_id: int, user_name: str) -> dict:
    """Обработка создания задач в Bitrix24 через Telegram"""
    try:
        # Извлекаем текст задачи
        if text.lower().startswith('/задача '):
            task_text = text[8:].strip()  # Убираем '/задача '
        elif text.lower().startswith('/task '):
            task_text = text[6:].strip()  # Убираем '/task '
        else:
            task_text = text.strip()
        
        if not task_text:
            await telegram_service.send_message(
                chat_id, 
                "❌ Укажите текст задачи.\nПример: /задача Проверить уборку в доме Пролетарская 112"
            )
            return {"status": "failed", "message": "Empty task text"}
        
        # Создаем задачу в Bitrix24
        success = await create_bitrix_task(task_text, user_name)
        
        if success:
            response_text = f"✅ Задача создана в Bitrix24!\n\n📝 Текст: {task_text}\n👤 Автор: {user_name}"
            await telegram_service.send_message(chat_id, response_text)
            
            return {
                "status": "processed",
                "message": "Bitrix24 task created successfully",
                "task_text": task_text,
                "chat_id": chat_id
            }
        else:
            await telegram_service.send_message(
                chat_id, 
                "❌ Ошибка при создании задачи в Bitrix24. Попробуйте позже."
            )
            return {"status": "failed", "message": "Failed to create Bitrix24 task"}
            
    except Exception as e:
        logger.error(f"❌ Bitrix task creation error: {e}")
        await telegram_service.send_message(
            chat_id,
            "❌ Произошла ошибка при создании задачи. Проверьте подключение к Bitrix24."
        )
        return {"status": "failed", "message": str(e)}

async def create_bitrix_task(task_text: str, user_name: str) -> bool:
    """Создать задачу в Bitrix24 из Telegram"""
    try:
        # Определяем ответственного по тексту задачи
        responsible_id = 1  # По умолчанию - администратор
        
        # Можно добавить логику определения ответственного по адресу
        if "пролетарская" in task_text.lower() or "центр" in task_text.lower():
            responsible_id = 1  # 1 бригада
        elif "чижевского" in task_text.lower() or "никитинский" in task_text.lower():
            responsible_id = 2  # 2 бригада
        # и т.д.
        
        # Создаем задачу
        title = f"Telegram: {task_text[:50]}{'...' if len(task_text) > 50 else ''}"
        description = f"Задача от {user_name} через Telegram:\n\n{task_text}"
        
        result = await bitrix_service.create_task(
            title=title,
            description=description,
            responsible_id=responsible_id
        )
        
        return result.get("status") == "success"
        
    except Exception as e:
        logger.error(f"❌ Create Bitrix task error: {e}")
        return False

@router.get("/api/telegram/status")
async def telegram_status():
    """Telegram bot status с тестированием"""
    status = {
        "status": "configured" if TELEGRAM_BOT_TOKEN else "missing_token",
        "bot_token": "present" if TELEGRAM_BOT_TOKEN else "missing",
        "webhook_url": TELEGRAM_WEBHOOK_URL or 'not_configured',
        "message": "Telegram bot готов для интеграции",
        "features": {
            "ai_chat": True,
            "bitrix_tasks": True if BITRIX24_WEBHOOK_URL else False
        }
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