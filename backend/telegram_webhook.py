"""
Telegram Webhook Handler for Production Deployment
"""
import os
import asyncio
import logging
from fastapi import APIRouter, Request, HTTPException
import json

logger = logging.getLogger(__name__)

# Create router for webhook
webhook_router = APIRouter()

@webhook_router.post("/telegram/webhook")
async def telegram_webhook_handler(request: Request):
    """Handle incoming Telegram webhook updates"""
    try:
        # Get webhook secret for security
        webhook_secret = os.getenv("TELEGRAM_WEBHOOK_SECRET", "")
        
        # Verify webhook secret if provided
        if webhook_secret:
            secret_header = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
            if secret_header != webhook_secret:
                raise HTTPException(status_code=403, detail="Invalid webhook secret")
        
        # Parse webhook data
        update_data = await request.json()
        
        # Process the update using aiogram dispatcher
        await process_telegram_update(update_data)
        
        return {"status": "ok"}
        
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        raise HTTPException(status_code=500, detail="Webhook processing failed")

@webhook_router.get("/telegram/set-webhook")
async def set_telegram_webhook():
    """Set up Telegram webhook URL (call this once after deployment)"""
    try:
        # Import bot here to avoid circular imports
        from telegram_bot import bot
        
        # Get webhook URL from environment
        webhook_url = os.getenv("TELEGRAM_WEBHOOK_URL")
        if not webhook_url:
            return {
                "error": "TELEGRAM_WEBHOOK_URL not configured", 
                "required": "https://your-app.onrender.com/api/telegram/webhook"
            }
        
        # Set webhook with secret token
        webhook_secret = os.getenv("TELEGRAM_WEBHOOK_SECRET", "")
        
        await bot.set_webhook(
            url=webhook_url,
            secret_token=webhook_secret if webhook_secret else None,
            drop_pending_updates=True  # Clear old updates
        )
        
        return {
            "status": "success",
            "webhook_url": webhook_url,
            "message": "Webhook set successfully"
        }
        
    except Exception as e:
        logger.error(f"Set webhook error: {e}")
        return {
            "error": str(e),
            "status": "failed"
        }

@webhook_router.get("/telegram/webhook-info")
async def get_webhook_info():
    """Get current webhook information"""
    try:
        from telegram_bot import bot
        
        webhook_info = await bot.get_webhook_info()
        
        return {
            "url": webhook_info.url,
            "has_custom_certificate": webhook_info.has_custom_certificate,
            "pending_update_count": webhook_info.pending_update_count,
            "last_error_date": webhook_info.last_error_date,
            "last_error_message": webhook_info.last_error_message,
            "max_connections": webhook_info.max_connections,
            "allowed_updates": webhook_info.allowed_updates
        }
        
    except Exception as e:
        logger.error(f"Get webhook info error: {e}")
        return {"error": str(e)}

async def process_telegram_update(update_data: dict):
    """Process incoming Telegram update"""
    try:
        from telegram_bot import dp, bot
        from aiogram.types import Update
        
        # Convert dict to Telegram Update object
        update = Update.model_validate(update_data)
        
        # Process update through dispatcher
        await dp.feed_update(bot=bot, update=update)
        
    except Exception as e:
        logger.error(f"Error processing Telegram update: {e}")
        raise