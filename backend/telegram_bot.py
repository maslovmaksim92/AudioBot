import os
import asyncio
import logging
from typing import Dict, Any
from datetime import datetime
import json

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

from ai_service import ai_assistant
from bitrix24_service import get_bitrix24_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Bot configuration
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN not found in environment variables")

# Initialize bot and dispatcher
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# States for conversation
class ConversationState(StatesGroup):
    waiting_for_feedback = State()
    waiting_for_meeting_transcript = State()
    waiting_for_deal_info = State()

# Create main menu keyboard
def get_main_menu():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📊 Дашборд"), KeyboardButton(text="🏠 Статистика домов")],
            [KeyboardButton(text="💼 Сделки Bitrix24"), KeyboardButton(text="👥 Сотрудники")],
            [KeyboardButton(text="🎙️ Анализ планерки"), KeyboardButton(text="📝 Обратная связь")],
            [KeyboardButton(text="🤖 AI Помощь"), KeyboardButton(text="⚙️ Настройки")]
        ],
        resize_keyboard=True
    )
    return keyboard

# Inline keyboard for feedback
def get_feedback_keyboard():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💡 Предложить улучшение", callback_data="suggest_improvement")],
            [InlineKeyboardButton(text="⭐ Оценить работу", callback_data="rate_work")],
            [InlineKeyboardButton(text="🐛 Сообщить о проблеме", callback_data="report_issue")]
        ]
    )
    return keyboard

# Start command handler
@dp.message(Command("start"))
async def start_handler(message: types.Message):
    user_name = message.from_user.first_name or "Пользователь"
    
    welcome_text = f"""
🤖 **Привет, {user_name}!** 

Я твой AI-ассистент для управления клининговой компанией! 

**Что я умею:**
✅ Анализировать данные из Bitrix24
✅ Управлять сделками и контактами  
✅ Анализировать планерки (голосом!)
✅ Предоставлять бизнес-аналитику
✅ Отвечать на вопросы о работе
✅ Собирать обратную связь от команды

**🎯 Выбери действие из меню ниже или просто напиши мне!**
"""
    
    await message.answer(welcome_text, reply_markup=get_main_menu(), parse_mode="Markdown")

# Dashboard handler
@dp.message(F.text == "📊 Дашборд")
async def dashboard_handler(message: types.Message):
    try:
        # Get Bitrix24 service
        bx24 = await get_bitrix24_service()
        stats = await bx24.get_cleaning_statistics()
        
        dashboard_text = f"""
📊 **ДАШБОРД КОМПАНИИ**

**Bitrix24 Статистика:**
🔸 Всего сделок: {stats.get('total_deals', 0)}
🔸 Контакты: {stats.get('total_contacts', 0)} 
🔸 Компании: {stats.get('total_companies', 0)}

**География бизнеса:**
🏠 Калуга: {stats.get('kaluga_properties', 0)} объектов
🏘️ Кемерово: {stats.get('kemerovo_properties', 0)} объектов
📍 Всего: {stats.get('kaluga_properties', 0) + stats.get('kemerovo_properties', 0)} объектов

⏰ Обновлено: {datetime.now().strftime('%H:%M %d.%m.%Y')}
"""
        
        await message.answer(dashboard_text, parse_mode="Markdown")
    except Exception as e:
        await message.answer(f"❌ Ошибка получения данных: {str(e)}")

# Houses statistics handler
@dp.message(F.text == "🏠 Статистика домов")
async def houses_stats_handler(message: types.Message):
    try:
        bx24 = await get_bitrix24_service()
        
        # Get companies (buildings)
        companies = await bx24.get_companies()
        contacts = await bx24.get_contacts()
        
        kaluga_count = 0
        kemerovo_count = 0
        
        # Count by city from companies
        for company in companies:
            address = company.get("ADDRESS", "").lower()
            if "калуга" in address:
                kaluga_count += 1
            elif "кемерово" in address:
                kemerovo_count += 1
        
        # Count by city from contacts
        for contact in contacts:
            address = contact.get("ADDRESS", "").lower()
            if "калуга" in address:
                kaluga_count += 1
            elif "кемерово" in address:
                kemerovo_count += 1
        
        houses_text = f"""
🏠 **СТАТИСТИКА ДОМОВ**

**По городам:**
🔸 Калуга: {kaluga_count} домов
🔸 Кемерово: {kemerovo_count} домов
📊 **Всего под обслуживанием: {kaluga_count + kemerovo_count} домов**

**Источники данных:**
• Компании в Bitrix24: {len(companies)}
• Контакты в Bitrix24: {len(contacts)}

💡 *Для добавления новых домов используйте воронку "Уборка подъездов" в Bitrix24*
"""
        
        await message.answer(houses_text, parse_mode="Markdown")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")

# Bitrix24 deals handler
@dp.message(F.text == "💼 Сделки Bitrix24")
async def deals_handler(message: types.Message):
    try:
        bx24 = await get_bitrix24_service()
        deals = await bx24.get_deals()
        
        if not deals:
            await message.answer("📋 Сделок пока нет. Создайте первую сделку в Bitrix24!")
            return
        
        deals_text = f"💼 **ПОСЛЕДНИЕ СДЕЛКИ** (всего: {len(deals)})\n\n"
        
        # Show last 5 deals
        for i, deal in enumerate(deals[:5]):
            title = deal.get("TITLE", "Без названия")[:50]
            deal_id = deal.get("ID")
            stage = deal.get("STAGE_ID", "")
            
            deals_text += f"🔸 **#{deal_id}**: {title}\n"
            if len(title) > 47:
                deals_text += "...\n"
        
        if len(deals) > 5:
            deals_text += f"\n➕ И ещё {len(deals) - 5} сделок в Bitrix24"
        
        await message.answer(deals_text, parse_mode="Markdown")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")

# Meeting analysis handler
@dp.message(F.text == "🎙️ Анализ планерки")
async def meeting_analysis_handler(message: types.Message, state: FSMContext):
    await state.set_state(ConversationState.waiting_for_meeting_transcript)
    
    instruction_text = """
🎙️ **АНАЛИЗ ПЛАНЕРКИ**

Отправьте мне:
🗣️ **Голосовое сообщение** с записью планерки
📝 **Текст** с транскриптом встречи

Я проанализирую и выделю:
✅ Ключевые решения
✅ Поставленные задачи  
✅ Важные проблемы
✅ Следующие шаги

**Отправляйте запись!** 🎯
"""
    
    await message.answer(instruction_text, parse_mode="Markdown")

# Handle meeting transcript (voice or text)
@dp.message(StateFilter(ConversationState.waiting_for_meeting_transcript))
async def process_meeting_transcript(message: types.Message, state: FSMContext):
    try:
        transcript_text = ""
        
        if message.voice:
            # TODO: Implement voice to text conversion
            await message.answer("🎙️ Получил голосовое сообщение! (Функция распознавания речи в разработке)")
            transcript_text = "Голосовая запись планерки получена. Анализирую содержание..."
        elif message.text:
            transcript_text = message.text
        else:
            await message.answer("❌ Пожалуйста, отправьте текст или голосовое сообщение")
            return
        
        await message.answer("🔄 Анализирую планерку с помощью AI...")
        
        # Analyze with AI
        analysis = await ai_assistant.analyze_meeting_transcript(transcript_text)
        
        result_text = f"""
📝 **АНАЛИЗ ПЛАНЕРКИ**

{analysis.get('summary', 'Анализ выполнен')}

⏰ Время анализа: {datetime.now().strftime('%H:%M %d.%m.%Y')}
"""
        
        await message.answer(result_text, parse_mode="Markdown")
        await state.clear()
        
    except Exception as e:
        await message.answer(f"❌ Ошибка анализа: {str(e)}")
        await state.clear()

# Feedback handler
@dp.message(F.text == "📝 Обратная связь")
async def feedback_handler(message: types.Message):
    feedback_text = """
📝 **ОБРАТНАЯ СВЯЗЬ**

Ваше мнение важно для улучшения работы! 

Выберите тип обратной связи:
"""
    
    await message.answer(feedback_text, reply_markup=get_feedback_keyboard(), parse_mode="Markdown")

# Feedback callback handlers
@dp.callback_query(F.data == "suggest_improvement")
async def suggest_improvement_handler(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(ConversationState.waiting_for_feedback)
    await callback.message.answer("💡 Напишите ваше предложение по улучшению работы:")

@dp.callback_query(F.data == "rate_work")
async def rate_work_handler(callback: types.CallbackQuery):
    rating_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⭐", callback_data="rate_1"),
             InlineKeyboardButton(text="⭐⭐", callback_data="rate_2"),
             InlineKeyboardButton(text="⭐⭐⭐", callback_data="rate_3")],
            [InlineKeyboardButton(text="⭐⭐⭐⭐", callback_data="rate_4"),
             InlineKeyboardButton(text="⭐⭐⭐⭐⭐", callback_data="rate_5")]
        ]
    )
    await callback.message.answer("⭐ Оцените качество работы:", reply_markup=rating_keyboard)

# Rating handlers
@dp.callback_query(F.data.startswith("rate_"))
async def rating_handler(callback: types.CallbackQuery):
    rating = callback.data.split("_")[1]
    await callback.message.answer(f"✅ Спасибо за оценку {rating}/5! Ваш отзыв учтен.")

# AI Help handler
@dp.message(F.text == "🤖 AI Помощь")
async def ai_help_handler(message: types.Message):
    help_text = """
🤖 **AI ПОМОЩЬ**

Просто напишите мне любой вопрос! Я могу:

🔸 Проанализировать бизнес-ситуацию
🔸 Дать рекомендации по развитию
🔸 Помочь с планированием работ
🔸 Объяснить данные из Bitrix24
🔸 Предложить оптимизацию процессов

**Примеры вопросов:**
• "Как увеличить прибыль?"
• "Проанализируй загрузку сотрудников"
• "Какие дома нужно убирать на этой неделе?"

**Пишите что угодно - я умный! 🧠**
"""
    
    await message.answer(help_text, parse_mode="Markdown")

# Handle any text message as AI chat
@dp.message(F.text & ~F.text.in_(["📊 Дашборд", "🏠 Статистика домов", "💼 Сделки Bitrix24", 
                                 "👥 Сотрудники", "🎙️ Анализ планерки", "📝 Обратная связь", 
                                 "🤖 AI Помощь", "⚙️ Настройки"]))
async def ai_chat_handler(message: types.Message):
    try:
        user_message = message.text
        user_name = message.from_user.first_name or "Пользователь"
        
        # Add context about user
        contextual_message = f"Пользователь {user_name} спрашивает: {user_message}"
        
        await message.answer("🤖 Думаю...")
        
        # Get AI response
        response = await ai_assistant.chat(contextual_message, f"telegram_{message.from_user.id}")
        
        ai_text = response.get("response", "Извините, не могу ответить прямо сейчас")
        
        # Add improvement suggestion button to every AI response
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="💡 Предложить улучшения", callback_data="suggest_improvement")]
            ]
        )
        
        await message.answer(f"🤖 {ai_text}", reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"AI chat error: {e}")
        await message.answer("❌ Извините, произошла ошибка при обработке запроса")

# Handle feedback input
@dp.message(StateFilter(ConversationState.waiting_for_feedback))
async def process_feedback(message: types.Message, state: FSMContext):
    feedback_text = message.text
    user_name = message.from_user.first_name or "Пользователь"
    
    # Here you would typically save feedback to database
    logger.info(f"Feedback from {user_name}: {feedback_text}")
    
    await message.answer("✅ Спасибо за обратную связь! Ваше предложение учтено и будет рассмотрено.")
    await state.clear()

# Error handler
@dp.error()
async def error_handler(update: types.Update, exception: Exception):
    logger.error(f"Update {update} caused error {exception}")
    return True

# Start bot function
async def start_bot():
    logger.info("🚀 Starting Telegram bot...")
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Bot error: {e}")
    finally:
        await bot.session.close()

# Function to run bot in background
def run_bot_background():
    """Run bot in background thread"""
    asyncio.create_task(start_bot())

if __name__ == "__main__":
    asyncio.run(start_bot())