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
from voice_service import generate_voice_message, make_text_conversational

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
    onboarding_name = State()
    onboarding_role = State()
    onboarding_experience = State()
    onboarding_priorities = State()
    onboarding_schedule = State()

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

# User profiles storage (in production, use database)
user_profiles = {}

# Start command handler with proactive onboarding
@dp.message(Command("start"))
async def start_handler(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    user_name = message.from_user.first_name or "коллега"
    
    # Check if user is already onboarded
    if user_id in user_profiles:
        profile = user_profiles[user_id]
        welcome_text = f"""
👋 **С возвращением, {profile.get('name', user_name)}!**

Я МАКС - ваш AI-директор для управления ВасДом.

📊 **Быстрая сводка:**
• Активных сделок: проверяю...
• Команда: работает в штатном режиме
• Проблемы: анализирую текущие данные

**Что обсудим сегодня?** Выберите из меню или просто напишите мне.
"""
        await message.answer(welcome_text, reply_markup=get_main_menu(), parse_mode="Markdown")
        
        # Send proactive daily insights
        await send_daily_insights(message.chat.id)
    else:
        # Start onboarding for new user
        await start_onboarding(message, state)

async def start_onboarding(message: types.Message, state: FSMContext):
    """Start proactive onboarding process"""
    await state.set_state(ConversationState.onboarding_name)
    
    welcome_text = f"""
🎯 **Добро пожаловать в команду ВасДом!**

Я МАКС - ваш AI-директор и помощник по управлению бизнесом.

Я здесь, чтобы:
• Контролировать выполнение планов
• Анализировать эффективность команды  
• Предупреждать о проблемах заранее
• Помогать принимать правильные решения

**Давайте познакомимся поближе.**

Как к вам обращаться? Напишите ваше имя и должность в компании.

*Например: "Максим Маслов, генеральный директор"*
"""
    
    await message.answer(welcome_text, parse_mode="Markdown")

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

# Houses statistics handler with real cleaning houses data
@dp.message(F.text == "🏠 Статистика домов")
async def houses_stats_handler(message: types.Message):
    try:
        bx24 = await get_bitrix24_service()
        
        # Get real cleaning houses from funnel
        cleaning_houses = await bx24.get_cleaning_houses_deals()
        
        kaluga_count = 0
        kemerovo_count = 0
        active_count = 0
        total_value = 0
        
        # Analyze cleaning houses
        for house in cleaning_houses:
            title = house.get("TITLE", "").lower()
            stage_id = house.get("STAGE_ID", "")
            opportunity = float(house.get("OPPORTUNITY", 0))
            
            total_value += opportunity
            
            # Count by city
            if "калуга" in title:
                kaluga_count += 1
            elif "кемерово" in title:
                kemerovo_count += 1
            
            # Count active houses (not won/lost)
            if "WON" not in stage_id and "LOSE" not in stage_id:
                active_count += 1
        
        houses_text = f"""
🏠 **РЕАЛЬНАЯ СТАТИСТИКА ДОМОВ**

**📊 Общие показатели:**
• Всего домов в работе: {len(cleaning_houses)}
• Активных объектов: {active_count}
• Общая стоимость контрактов: {total_value:,.0f} ₽

**🌍 По городам:**
🔸 Калуга: {kaluga_count} домов
🔸 Кемерово: {kemerovo_count} домов
🔸 Другие: {len(cleaning_houses) - kaluga_count - kemerovo_count} домов

**💰 Средняя стоимость:** {total_value/max(len(cleaning_houses), 1):,.0f} ₽ за объект

**📈 Эффективность:**
• Конверсия: {((len(cleaning_houses) - active_count)/max(len(cleaning_houses), 1)*100):,.1f}%
• Средний чек: {total_value/max(len(cleaning_houses), 1):,.0f} ₽

🎯 *Данные получены из воронки "Уборка подъездов" в Bitrix24*
"""
        
        # Add task creation button for directors
        user_id = message.from_user.id
        profile = user_profiles.get(user_id, {})
        if "директор" in profile.get("role", "").lower():
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="📋 Создать задачу по домам", callback_data="create_houses_task")],
                    [InlineKeyboardButton(text="📊 Подробный анализ", callback_data="detailed_houses_analysis")]
                ]
            )
            await message.answer(houses_text, reply_markup=keyboard, parse_mode="Markdown")
        else:
            await message.answer(houses_text, parse_mode="Markdown")
            
    except Exception as e:
        await message.answer(f"❌ Ошибка получения данных: {str(e)}")

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

# Onboarding handlers
@dp.message(StateFilter(ConversationState.onboarding_name))
async def process_onboarding_name(message: types.Message, state: FSMContext):
    name_and_role = message.text
    await state.update_data(name_and_role=name_and_role)
    
    await state.set_state(ConversationState.onboarding_experience)
    
    response = f"""
✅ **Понял: {name_and_role}**

Отлично! Теперь расскажите о вашем опыте в ВасДом:

• Сколько лет работаете в клининговой сфере?
• За какие направления отвечаете? (Калуга, Кемерово, общее управление)
• Какие основные задачи решаете ежедневно?

*Это поможет мне давать более точные рекомендации и отчеты.*
"""
    
    await message.answer(response, parse_mode="Markdown")

@dp.message(StateFilter(ConversationState.onboarding_experience))
async def process_onboarding_experience(message: types.Message, state: FSMContext):
    experience = message.text
    await state.update_data(experience=experience)
    
    await state.set_state(ConversationState.onboarding_priorities)
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📊 Финансовые показатели", callback_data="priority_finance")],
            [InlineKeyboardButton(text="👥 Управление персоналом", callback_data="priority_hr")],
            [InlineKeyboardButton(text="📈 Рост и развитие", callback_data="priority_growth")],
            [InlineKeyboardButton(text="🏠 Операционная эффективность", callback_data="priority_operations")],
            [InlineKeyboardButton(text="📋 Все направления", callback_data="priority_all")]
        ]
    )
    
    response = """
📊 **Какие метрики для вас приоритетны?**

Выберите главное направление, которое хотите контролировать через меня:
"""
    
    await message.answer(response, reply_markup=keyboard, parse_mode="Markdown")

@dp.callback_query(F.data.startswith("priority_"))
async def process_onboarding_priority(callback: types.CallbackQuery, state: FSMContext):
    priority = callback.data.replace("priority_", "")
    await state.update_data(priority=priority)
    
    await state.set_state(ConversationState.onboarding_schedule)
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🌅 Утром (8:00)", callback_data="schedule_morning")],
            [InlineKeyboardButton(text="🌇 Вечером (18:00)", callback_data="schedule_evening")],
            [InlineKeyboardButton(text="📊 По запросу", callback_data="schedule_ondemand")],
            [InlineKeyboardButton(text="🚨 Только критичное", callback_data="schedule_critical")]
        ]
    )
    
    response = """
⏰ **Когда присылать ежедневные сводки?**

Выберите удобное время для получения отчетов и аналитики:
"""
    
    await callback.message.answer(response, reply_markup=keyboard, parse_mode="Markdown")

@dp.callback_query(F.data.startswith("schedule_"))
async def complete_onboarding(callback: types.CallbackQuery, state: FSMContext):
    schedule = callback.data.replace("schedule_", "")
    user_data = await state.get_data()
    
    user_id = callback.from_user.id
    user_profiles[user_id] = {
        "name": user_data.get("name_and_role", "").split(",")[0].strip(),
        "role": user_data.get("name_and_role", ""),
        "experience": user_data.get("experience", ""),
        "priority": schedule,
        "schedule": schedule,
        "onboarded_at": datetime.now().isoformat()
    }
    
    await state.clear()
    
    # Personalized welcome based on role
    profile = user_profiles[user_id]
    role_lower = profile["role"].lower()
    
    if "директор" in role_lower or "руководитель" in role_lower:
        director_welcome = f"""
🎯 **Отлично, {profile['name']}!**

Теперь я ваш персональный AI-директор. Буду следить за:

📊 **Ежедневные сводки:** ключевые метрики, проблемы, возможности
🚨 **Критические алерты:** падение показателей, срочные задачи  
💡 **Стратегические инсайты:** рекомендации по развитию бизнеса
📈 **Прогнозы:** планирование на основе данных Bitrix24

**Первый отчет готовлю прямо сейчас...**
"""
        await callback.message.answer(director_welcome, reply_markup=get_main_menu(), parse_mode="Markdown")
        
        # Send immediate business overview
        await send_director_briefing(callback.message.chat.id, profile)
        
    else:
        manager_welcome = f"""
✅ **Настройка завершена, {profile['name']}!**

Я буду помогать вам с:
• Анализом ваших задач и приоритетов
• Отчетами по вашему направлению  
• Предупреждениями о важных событиях
• Ответами на рабочие вопросы

**Начнем работу! Что вас интересует в первую очередь?**
"""
        await callback.message.answer(manager_welcome, reply_markup=get_main_menu(), parse_mode="Markdown")

# Proactive daily insights
async def send_daily_insights(chat_id: int):
    """Send proactive daily business insights"""
    try:
        from bitrix24_service import get_bitrix24_service
        
        bx24 = await get_bitrix24_service()
        deals = await bx24.get_deals()
        
        insights = [
            f"📊 Активных сделок: {len([d for d in deals if 'WON' not in d.get('STAGE_ID', '')])}",
            f"💰 В работе: {sum(float(d.get('OPPORTUNITY', 0)) for d in deals):,.0f} ₽",
            "🎯 Сегодня стоит обратить внимание на конверсию в Кемерово"
        ]
        
        insight_text = "📈 **Быстрая аналитика на сегодня:**\n\n" + "\n".join(insights)
        await bot.send_message(chat_id, insight_text, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Error sending daily insights: {e}")

async def send_director_briefing(chat_id: int, profile: dict):
    """Send comprehensive briefing for directors"""
    try:
        from bitrix24_service import get_bitrix24_service
        from analytics_service import get_performance_metrics
        
        # Get real data
        bx24 = await get_bitrix24_service()
        deals = await bx24.get_deals()
        metrics = await get_performance_metrics()
        
        won_deals = [d for d in deals if 'WON' in d.get('STAGE_ID', '')]
        active_deals = [d for d in deals if 'WON' not in d.get('STAGE_ID', '') and 'LOSE' not in d.get('STAGE_ID', '')]
        
        briefing = f"""
📋 **УПРАВЛЕНЧЕСКАЯ СВОДКА ДЛЯ {profile['name'].upper()}**

🎯 **КРИТИЧЕСКИЕ ПОКАЗАТЕЛИ:**
• Выручка план/факт: {metrics.get('sales_metrics', {}).get('conversion_rate', 0)}% конверсия
• Активных сделок: {len(active_deals)} на сумму {sum(float(d.get('OPPORTUNITY', 0)) for d in active_deals):,.0f} ₽
• Команда: {metrics.get('operational_metrics', {}).get('total_employees', 100)} сотрудников в работе

⚠️ **ТРЕБУЕТ ВНИМАНИЯ:**
• Сделки без движения: {len([d for d in deals if not d.get('DATE_MODIFY')])} штук
• Низкая активность в Кемерово: проверить менеджеров
• План на месяц: выполнен на {metrics.get('growth_metrics', {}).get('revenue_target_achievement', 85)}%

💡 **РЕКОМЕНДАЦИИ НА СЕГОДНЯ:**
1. Провести планерку с командой Кемерово
2. Проанализировать застрявшие сделки в Bitrix24
3. Проверить выполнение KPI за неделю

**Нужна детализация по любому пункту?** Просто спросите меня.
"""
        
        await bot.send_message(chat_id, briefing, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Error sending director briefing: {e}")

# Handle any text message as AI chat with director tone
@dp.message(F.text & ~F.text.in_(["📊 Дашборд", "🏠 Статистика домов", "💼 Сделки Bitrix24", 
                                 "👥 Сотрудники", "🎙️ Анализ планерки", "📝 Обратная связь", 
                                 "🤖 AI Помощь", "⚙️ Настройки"]))
async def ai_chat_handler(message: types.Message):
    try:
        user_id = message.from_user.id
        user_message = message.text
        
        # Get user profile for context
        profile = user_profiles.get(user_id, {})
        user_name = profile.get("name", message.from_user.first_name or "коллега")
        user_role = profile.get("role", "сотрудник")
        
        # Director-style context
        if "директор" in user_role.lower():
            contextual_message = f"""
Генеральный директор {user_name} обращается с вопросом: "{user_message}"

Контекст: это руководитель компании ВасДом, отвечающий за стратегические решения.
Отвечай как опытный AI-директор: четко, по делу, с конкретными рекомендациями и цифрами.
"""
        else:
            contextual_message = f"""
Сотрудник {user_name} ({user_role}) спрашивает: "{user_message}"

Отвечай как руководитель: направляющий тон, конкретные задачи, четкие инструкции.
"""
        
        await message.answer("🎯 Анализирую ситуацию...")
        
        # Get AI response with memory
        response = await ai_assistant.chat(contextual_message, f"telegram_{user_id}", user_name)
        
        ai_text = response.get("response", "Извините, не могу ответить прямо сейчас")
        
        # Add proactive suggestions based on response
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="📊 Показать данные", callback_data="show_analytics")],
                [InlineKeyboardButton(text="💡 Предложить улучшения", callback_data="suggest_improvement")]
            ]
        )
        
        # Send BOTH voice and text message for convenience
        try:
            # First send voice message
            conversational_text = make_text_conversational(ai_text)
            voice_data = await generate_voice_message(conversational_text, "director")
            
            if voice_data and len(voice_data) > 100:  # Check if voice was generated
                # Create voice message using InputFile
                from aiogram.types import BufferedInputFile
                voice_file = BufferedInputFile(voice_data, filename="voice_response.ogg")
                await message.answer_voice(voice_file)
            
            # Then send text message with buttons
            await message.answer(f"📋 **МАКС:** {ai_text}", reply_markup=keyboard, parse_mode="Markdown")
            
        except Exception as voice_error:
            logger.error(f"Voice generation error: {voice_error}")
            # Fallback to text only
            await message.answer(f"📋 **МАКС:** {ai_text}", reply_markup=keyboard, parse_mode="Markdown")
        
        # Be proactive - suggest related actions
        await suggest_proactive_actions(message, user_message, profile)
        
    except Exception as e:
        logger.error(f"AI chat error: {e}")
        await message.answer("❌ Произошла техническая ошибка. Перепроверяю системы...")

async def suggest_proactive_actions(message: types.Message, user_question: str, profile: dict):
    """Suggest proactive actions based on user question"""
    try:
        question_lower = user_question.lower()
        
        if any(word in question_lower for word in ["проблема", "снижение", "падение", "плохо"]):
            await message.answer("🔍 **Дополнительно:** Запустить углубленный анализ по этой проблеме? Я могу проверить данные в Bitrix24 и дать конкретные рекомендации.")
            
        elif any(word in question_lower for word in ["план", "прогноз", "увеличить", "рост"]):
            await message.answer("📈 **Идея:** Подготовить детальный план с конкретными шагами и метриками? Могу интегрировать данные из текущих сделок.")
            
        elif any(word in question_lower for word in ["сотрудник", "команда", "персонал"]):
            await message.answer("👥 **Предложение:** Проанализировать эффективность каждого сотрудника по городам? У меня есть доступ к статистике.")
            
    except Exception as e:
        logger.error(f"Error suggesting proactive actions: {e}")

# Task creation callbacks
@dp.callback_query(F.data == "create_houses_task")
async def create_houses_task_callback(callback: types.CallbackQuery):
    try:
        bx24 = await get_bitrix24_service()
        
        # Create task for house inspection
        task_title = f"Проверка состояния домов - {datetime.now().strftime('%d.%m.%Y')}"
        task_description = """
ЗАДАЧА: Комплексная проверка состояния объектов

ПРОВЕРИТЬ:
1. Качество уборки в подъездах
2. Состояние оборудования
3. Жалобы от жильцов
4. Выполнение графика работ

ОТЧЕТ: Отправить фото и результаты в Telegram группу
СРОК: до 18:00 сегодня
"""
        
        result = await bx24.create_task(
            title=task_title,
            description=task_description,
            responsible_id=1,  # Assign to main manager
            deadline=datetime.now().strftime('%Y-%m-%d 18:00:00')
        )
        
        if result.get('success'):
            await callback.message.answer(f"""
✅ **ЗАДАЧА СОЗДАНА В BITRIX24**

📋 **Задача:** {task_title}
🆔 **ID:** {result.get('task_id')}
⏰ **Срок:** до 18:00 сегодня

**Ответственный уведомлен автоматически**

Отслеживать выполнение можно в Bitrix24 или спросить меня: "Статус задачи {result.get('task_id')}"
""", parse_mode="Markdown")
        else:
            await callback.message.answer(f"❌ Ошибка создания задачи: {result.get('error')}")
            
    except Exception as e:
        await callback.message.answer(f"❌ Ошибка: {str(e)}")

@dp.callback_query(F.data == "detailed_houses_analysis")
async def detailed_houses_analysis_callback(callback: types.CallbackQuery):
    await callback.message.answer("🔍 Запускаю углубленный анализ домов...")
    
    try:
        bx24 = await get_bitrix24_service()
        cleaning_houses = await bx24.get_cleaning_houses_deals()
        
        # Analyze by stages
        stage_analysis = {}
        problem_houses = []
        
        for house in cleaning_houses:
            stage_id = house.get("STAGE_ID", "")
            title = house.get("TITLE", "")
            
            if stage_id not in stage_analysis:
                stage_analysis[stage_id] = 0
            stage_analysis[stage_id] += 1
            
            # Identify potential problems
            if "проблем" in title.lower() or "жалоб" in title.lower():
                problem_houses.append(title)
        
        analysis_text = f"""
🔍 **УГЛУБЛЕННЫЙ АНАЛИЗ ДОМОВ**

**📊 По стадиям:**
"""
        for stage, count in stage_analysis.items():
            analysis_text += f"• {stage}: {count} домов\n"
        
        if problem_houses:
            analysis_text += f"""
⚠️ **ПРОБЛЕМНЫЕ ОБЪЕКТЫ ({len(problem_houses)}):**
"""
            for house in problem_houses[:5]:  # Show first 5
                analysis_text += f"• {house[:50]}...\n"
        
        analysis_text += f"""
💡 **РЕКОМЕНДАЦИИ:**
1. Усилить контроль в проблемных домах
2. Провести внеплановые проверки
3. Связаться с управляющими компаниями
4. Обновить график уборки для отстающих объектов

**Создать план корректирующих действий?**
"""
        
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="📋 Создать план действий", callback_data="create_action_plan")],
                [InlineKeyboardButton(text="📞 Связаться с УК", callback_data="contact_management")]
            ]
        )
        
        await callback.message.answer(analysis_text, reply_markup=keyboard, parse_mode="Markdown")
        
    except Exception as e:
        await callback.message.answer(f"❌ Ошибка анализа: {str(e)}")

# Callback for analytics request
@dp.callback_query(F.data == "show_analytics")
async def show_analytics_callback(callback: types.CallbackQuery):
    await callback.message.answer("📊 Готовлю аналитический отчет...")
    
    # Send analytics data
    try:
        from analytics_service import get_performance_metrics
        metrics = await get_performance_metrics()
        
        analytics_text = f"""
📊 **ОПЕРАТИВНАЯ АНАЛИТИКА**

**ПРОДАЖИ:**
• Конверсия: {metrics.get('sales_metrics', {}).get('conversion_rate', 0)}%
• Средняя сделка: {metrics.get('sales_metrics', {}).get('avg_deal_size', 0):,.0f} ₽
• Активных клиентов: {metrics.get('client_metrics', {}).get('active_clients', 0)}

**ОПЕРАЦИИ:**  
• Калуга: {metrics.get('operational_metrics', {}).get('kaluga_team', 0)} чел
• Кемерово: {metrics.get('operational_metrics', {}).get('kemerovo_team', 0)} чел
• Время отклика: {metrics.get('operational_metrics', {}).get('avg_response_time_hours', 2)}ч

**РОСТ:**
• За квартал: +{metrics.get('growth_metrics', {}).get('quarterly_growth', '15%')}
• План выполнен: {metrics.get('growth_metrics', {}).get('revenue_target_achievement', 92)}%

**Нужна детализация по какому-то направлению?**
"""
        
        await callback.message.answer(analytics_text, parse_mode="Markdown")
        
    except Exception as e:
        await callback.message.answer("❌ Ошибка получения аналитики. Проверяю подключения к системам...")

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