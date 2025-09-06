import asyncio
import json
from typing import Dict, Any, Optional
from loguru import logger
import httpx
from aiogram import Bot, Dispatcher, types
from aiogram.types import Update, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramAPIError

class TelegramBotService:
    """Telegram Bot Service with AI integration"""
    
    def __init__(self, token: str, webhook_url: str, ai_service, bitrix24_service):
        self.token = token
        self.webhook_url = webhook_url
        self.ai_service = ai_service
        self.bitrix24_service = bitrix24_service
        
        self.bot = Bot(token=token) if token else None
        self.dp = Dispatcher() if token else None
        
        # User sessions storage (in production use Redis/DB)
        self.user_sessions = {}
        
        if not token:
            logger.warning("⚠️ Telegram bot token not provided")
        else:
            logger.info("✅ Telegram bot service initialized")
    
    async def setup(self):
        """Setup bot and webhook"""
        if not self.bot:
            return
        
        try:
            # Get bot info
            bot_info = await self.bot.get_me()
            logger.info(f"🤖 Bot info: @{bot_info.username} ({bot_info.first_name})")
            
            # Set webhook if URL provided
            if self.webhook_url:
                await self.set_webhook()
            
        except Exception as e:
            logger.error(f"❌ Bot setup error: {e}")
    
    async def set_webhook(self) -> Dict[str, Any]:
        """Set Telegram webhook"""
        if not self.bot or not self.webhook_url:
            return {"error": "Bot or webhook URL not configured"}
        
        try:
            webhook_info = await self.bot.get_webhook_info()
            logger.info(f"Current webhook: {webhook_info.url}")
            
            if webhook_info.url != self.webhook_url:
                success = await self.bot.set_webhook(url=self.webhook_url)
                logger.info(f"✅ Webhook set to: {self.webhook_url}")
                return {"status": "webhook_set", "url": self.webhook_url}
            else:
                return {"status": "webhook_already_set", "url": self.webhook_url}
                
        except Exception as e:
            logger.error(f"❌ Webhook setup error: {e}")
            return {"error": str(e)}
    
    async def handle_webhook(self, update_data: Dict[str, Any]):
        """Handle incoming webhook update"""
        if not self.bot:
            return
        
        try:
            # Create Update object
            update = Update(**update_data)
            
            # Process the update
            if update.message:
                await self.handle_message(update.message)
            elif update.callback_query:
                await self.handle_callback_query(update.callback_query)
            else:
                logger.info(f"📨 Unhandled update type: {type(update)}")
                
        except Exception as e:
            logger.error(f"❌ Webhook handling error: {e}")
    
    async def handle_message(self, message: Message):
        """Handle incoming message"""
        user_id = message.from_user.id
        user_name = message.from_user.first_name or "Пользователь"
        text = message.text or ""
        
        logger.info(f"📥 Message from {user_name} (ID: {user_id}): {text}")
        
        # Update user session
        self.user_sessions[user_id] = {
            "name": user_name,
            "username": message.from_user.username,
            "last_message": text,
            "message_count": self.user_sessions.get(user_id, {}).get("message_count", 0) + 1
        }
        
        try:
            # Handle special commands
            if text.startswith("/start"):
                await self.send_welcome_message(message)
                return
            elif text.startswith("/help"):
                await self.send_help_message(message)
                return
            elif text.startswith("/menu"):
                await self.send_menu(message)
                return
            
            # Generate AI response
            user_data = self.user_sessions.get(user_id, {})
            response = await self.ai_service.generate_smart_reply(text, user_data)
            
            # Analyze user intent
            intent_data = await self.ai_service.analyze_user_intent(text)
            
            # Send response with appropriate keyboard
            keyboard = self.get_response_keyboard(intent_data.get("intent", "other"))
            
            await self.bot.send_message(
                chat_id=user_id,
                text=response,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
            
            # Log interaction
            logger.info(f"📤 Response sent to {user_name}: {len(response)} chars")
            
        except Exception as e:
            logger.error(f"❌ Message handling error: {e}")
            await self.bot.send_message(
                chat_id=user_id,
                text="🤖 Извините, произошла ошибка. Попробуйте еще раз или обратитесь к менеджеру."
            )
    
    async def send_welcome_message(self, message: Message):
        """Send welcome message"""
        user_name = message.from_user.first_name or "Пользователь"
        
        welcome_text = f"""🏠 Добро пожаловать в ВасДом, {user_name}!

Я ваш AI-помощник. Могу помочь с:
• 🧹 Заказом уборки подъездов
• 💰 Информацией о ценах
• 📋 Вопросами об услугах
• 🏢 Управлением недвижимостью

Просто напишите ваш вопрос, и я постараюсь помочь!"""
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🧹 Заказать уборку", callback_data="order_cleaning")],
            [InlineKeyboardButton(text="💰 Узнать цены", callback_data="get_prices")],
            [InlineKeyboardButton(text="📞 Связаться с менеджером", callback_data="contact_manager")]
        ])
        
        await self.bot.send_message(
            chat_id=message.chat.id,
            text=welcome_text,
            reply_markup=keyboard
        )
    
    async def send_help_message(self, message: Message):
        """Send help message"""
        help_text = """ℹ️ <b>Справка по командам:</b>

/start - Приветствие и меню
/help - Эта справка
/menu - Показать главное меню

<b>Что я умею:</b>
• Отвечать на вопросы об услугах ВасДом
• Помогать с заказом уборки
• Предоставлять информацию о ценах
• Связывать с менеджерами

<b>Просто напишите мне!</b> 🤖"""
        
        await self.bot.send_message(
            chat_id=message.chat.id,
            text=help_text,
            parse_mode="HTML"
        )
    
    async def send_menu(self, message: Message):
        """Send main menu"""
        menu_text = "📋 <b>Главное меню ВасДом</b>\n\nВыберите интересующую услугу:"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🧹 Уборка подъездов", callback_data="cleaning_service")],
            [InlineKeyboardButton(text="🏢 Управление недвижимостью", callback_data="property_management")],
            [InlineKeyboardButton(text="💰 Цены и тарифы", callback_data="pricing")],
            [InlineKeyboardButton(text="📞 Контакты", callback_data="contacts")],
            [InlineKeyboardButton(text="ℹ️ О компании", callback_data="about")]
        ])
        
        await self.bot.send_message(
            chat_id=message.chat.id,
            text=menu_text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    
    def get_response_keyboard(self, intent: str) -> Optional[InlineKeyboardMarkup]:
        """Get appropriate keyboard based on user intent"""
        keyboards = {
            "cleaning_request": InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📞 Связаться с менеджером", callback_data="contact_manager")],
                [InlineKeyboardButton(text="📋 Главное меню", callback_data="main_menu")]
            ]),
            "price_inquiry": InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🧹 Заказать уборку", callback_data="order_cleaning")],
                [InlineKeyboardButton(text="📋 Главное меню", callback_data="main_menu")]
            ]),
            "support_request": InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📞 Связаться с менеджером", callback_data="contact_manager")]
            ])
        }
        
        return keyboards.get(intent)
    
    async def handle_callback_query(self, callback_query: types.CallbackQuery):
        """Handle callback query from inline keyboard"""
        user_id = callback_query.from_user.id
        data = callback_query.data
        
        logger.info(f"📱 Callback from user {user_id}: {data}")
        
        try:
            await callback_query.answer()  # Acknowledge the callback
            
            # Handle different callback actions
            if data == "order_cleaning":
                await self.handle_order_cleaning(callback_query)
            elif data == "get_prices":
                await self.handle_get_prices(callback_query)
            elif data == "contact_manager":
                await self.handle_contact_manager(callback_query)
            elif data == "main_menu":
                await self.send_menu_from_callback(callback_query)
            else:
                # Generate AI response for other callbacks
                response = await self.ai_service.generate_response(f"Пользователь нажал кнопку: {data}")
                await self.bot.edit_message_text(
                    chat_id=callback_query.message.chat.id,
                    message_id=callback_query.message.message_id,
                    text=response
                )
                
        except Exception as e:
            logger.error(f"❌ Callback handling error: {e}")
    
    async def handle_order_cleaning(self, callback_query: types.CallbackQuery):
        """Handle cleaning order callback"""
        text = """🧹 <b>Заказ уборки подъездов</b>

Для заказа уборки мне понадобится:
• 📍 Адрес подъезда
• 📅 Желаемая дата
• 📞 Контактный телефон

Напишите эту информацию, и я свяжу вас с менеджером для оформления заказа!"""
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📞 Связаться с менеджером", callback_data="contact_manager")]
        ])
        
        await self.bot.edit_message_text(
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id,
            text=text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    
    async def handle_get_prices(self, callback_query: types.CallbackQuery):
        """Handle price inquiry callback"""
        text = """💰 <b>Цены на услуги ВасДом</b>

<b>Уборка подъездов:</b>
• Разовая уборка: от 2000₽
• Ежемесячное обслуживание: от 1500₽/мес
• Генеральная уборка: от 3000₽

<b>Управление недвижимостью:</b>
• Консультации: от 1000₽
• Полное сопровождение: от 5000₽/мес

<i>Точная стоимость зависит от объема работ и регулярности.</i>"""
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🧹 Заказать уборку", callback_data="order_cleaning")],
            [InlineKeyboardButton(text="📞 Уточнить у менеджера", callback_data="contact_manager")]
        ])
        
        await self.bot.edit_message_text(
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id,
            text=text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    
    async def handle_contact_manager(self, callback_query: types.CallbackQuery):
        """Handle contact manager callback"""
        text = """📞 <b>Контакты менеджеров ВасДом</b>

<b>Максим Маслов</b>
📞 Телефон: +7 (XXX) XXX-XX-XX
📧 Email: info@vas-dom.ru

<b>График работы:</b>
Пн-Пт: 9:00 - 18:00
Сб: 10:00 - 16:00
Вс: выходной

Менеджер свяжется с вами в ближайшее время для уточнения деталей заказа."""
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📋 Главное меню", callback_data="main_menu")]
        ])
        
        await self.bot.edit_message_text(
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id,
            text=text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    
    async def send_menu_from_callback(self, callback_query: types.CallbackQuery):
        """Send main menu from callback"""
        menu_text = "📋 <b>Главное меню ВасДом</b>\n\nВыберите интересующую услугу:"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🧹 Уборка подъездов", callback_data="cleaning_service")],
            [InlineKeyboardButton(text="🏢 Управление недвижимостью", callback_data="property_management")],
            [InlineKeyboardButton(text="💰 Цены и тарифы", callback_data="pricing")],
            [InlineKeyboardButton(text="📞 Контакты", callback_data="contacts")]
        ])
        
        await self.bot.edit_message_text(
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id,
            text=menu_text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    
    async def get_status(self) -> Dict[str, Any]:
        """Get bot status"""
        if not self.bot:
            return {"status": "not_configured"}
        
        try:
            bot_info = await self.bot.get_me()
            webhook_info = await self.bot.get_webhook_info()
            
            return {
                "status": "active",
                "bot_username": bot_info.username,
                "bot_name": bot_info.first_name,
                "webhook_url": webhook_info.url,
                "pending_updates": webhook_info.pending_update_count,
                "active_sessions": len(self.user_sessions)
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.bot:
            await self.bot.session.close()
            logger.info("🛑 Telegram bot session closed")