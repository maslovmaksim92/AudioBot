import time
import os
from fastapi import FastAPI, APIRouter, Request
from loguru import logger
from datetime import datetime
import sys
from dotenv import load_dotenv

# Load environment variables from backend/.env
load_dotenv("/app/backend/.env")

# Получаем MongoDB URL из переменных окружения (приоритет Render > local .env)
mongo_url = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
print(f"🔌 MongoDB URL: {mongo_url[:50]}..." if mongo_url else "❌ MONGO_URL не настроен")

# MongoDB Connection (опциональное)
try:
    from motor.motor_asyncio import AsyncIOMotorClient
    mongo_client = AsyncIOMotorClient(mongo_url)
    db = mongo_client[os.environ.get("DB_NAME", "vasdom_db")]
    print("✅ MongoDB client инициализирован")
except ImportError:
    mongo_client = None
    db = None
    print("⚠️ MongoDB client не доступен (motor не установлен)")
except Exception as e:
    mongo_client = None
    db = None
    print(f"❌ Ошибка подключения к MongoDB: {e}")

# Настройка логирования для Render Dashboard
logger.remove() # Убираем стандартный логгер
logger.add(sys.stdout, format="🚀 {time:HH:mm:ss} | {level} | {message}", level="INFO")
logger.add(sys.stderr, format="🚨 {time:HH:mm:ss} | {level} | {message}", level="ERROR")

# Создаём FastAPI приложение
app = FastAPI()

print("🚀 =============================================================")
print("🚀 VASDOM AI ASSISTANT STARTING UP - PRODUCTION READY")
print("🚀 =============================================================")

# Глобальные переменные для логирования (для дашборда)
application_logs = []
telegram_messages = []
system_status = {
    "startup_time": datetime.utcnow().isoformat(),
    "total_requests": 0,
    "telegram_updates": 0,
    "errors": 0,
    "last_activity": None
}

def add_log(level: str, message: str, details: dict = None):
    """Добавить лог в глобальный список для дашборда + вывести в Render"""
    global application_logs
    
    timestamp = datetime.utcnow().isoformat()
    log_entry = {
        "timestamp": timestamp,
        "level": level,
        "message": message,
        "details": details or {}
    }
    application_logs.append(log_entry)
    
    # Оставляем только последние 100 записей
    if len(application_logs) > 100:
        application_logs = application_logs[-100:]
    
    # ВЫВОДИМ В RENDER DASHBOARD (stdout)
    render_message = f"📋 [{timestamp}] {level}: {message}"
    print(render_message)
    
    # Если есть детали, выводим их тоже
    if details:
        print(f"📝 ДЕТАЛИ: {details}")
    
    # Логируем также в loguru
    if level == "ERROR":
        logger.error(f"🔴 {message}")
    elif level == "WARNING":
        logger.warning(f"🟡 {message}")
    elif level == "SUCCESS":
        logger.success(f"🟢 {message}")
    else: # INFO
        logger.info(f"🔵 {message}")

def generate_smart_response(user_message: str, user_context: dict = None) -> str:
    """Генерация умного ответа на основе ключевых слов для VasDom"""
    
    message_lower = user_message.lower()
    user_name = user_context.get("user_name", "дорогой клиент") if user_context else "дорогой клиент"
    
    print(f"🧠 Генерация умного ответа для: {user_message[:50]}...")
    
    # Приветствие
    if any(word in message_lower for word in ["привет", "здравствуйте", "добрый", "start", "/start"]):
        response = f"""Добро пожаловать, {user_name}! 🏠

Я AI-помощник компании ВасДом. Мы работаем в Калуге и области уже много лет.

🏠 НАШИ УСЛУГИ:
✅ Уборка подъездов и лестничных клеток
✅ Клининг придомовых территорий  
✅ Управление недвижимостью
✅ Решение вопросов ЖКХ

📊 НАШИ ДОСТИЖЕНИЯ:
• 500+ домов под управлением
• 100+ профессиональных сотрудников
• Работаем круглосуточно

Чем могу помочь? Или свяжу вас с менеджером Максимом Масловым! 📞"""

    # Уборка и клининг
    elif any(word in message_lower for word in ["уборк", "чист", "клининг", "мыть", "подъезд"]):
        response = f"""🧹 Отличный выбор, {user_name}!

ВасДом - лидер по уборке подъездов в Калуге! 

🔹 РЕГУЛЯРНАЯ УБОРКА ПОДЪЕЗДОВ:
• Ежедневная уборка лестниц и холлов
• Мытье перил, ступеней, почтовых ящиков
• Уборка мусора и листвы
• Мойка окон и светильников

🔹 ГЕНЕРАЛЬНАЯ УБОРКА:
• Глубокая чистка всех поверхностей
• Удаление граффити и объявлений
• Дезинфекция общих зон
• Уборка подвалов и технических помещений

🔹 СЕЗОННЫЕ РАБОТЫ:
• Уборка снега зимой
• Очистка от листвы осенью
• Озеленение территории весной

💰 Цены от 1500₽/месяц за подъезд!

Хотите рассчитать стоимость? Менеджер Максим Маслов поможет! 📱"""

    # Цены и стоимость
    elif any(word in message_lower for word in ["цена", "стоимость", "сколько", "тариф", "деньги", "руб"]):
        response = f"""💰 Прайс-лист ВасДом, {user_name}:

📋 УБОРКА ПОДЪЕЗДОВ:
🔸 Разовая уборка: от 2000₽
🔸 Еженедельная: от 1800₽/месяц
🔸 Ежедневная: от 1500₽/месяц
🔸 Генеральная уборка: от 3500₽

📋 ДОПОЛНИТЕЛЬНЫЕ УСЛУГИ:
🔸 Мойка окон: 150₽ за окно
🔸 Уборка придомовой территории: +800₽
🔸 Вывоз мусора: включено
🔸 Дезинфекция: +300₽

📋 УПРАВЛЕНИЕ НЕДВИЖИМОСТЬЮ:
🔸 Консультации: от 1000₽
🔸 Полное управление: от 5000₽/месяц
🔸 Техобслуживание: от 2500₽/месяц

🎯 СКИДКИ:
• При заключении договора на год: -15%
• Для управляющих компаний: -20%  
• При обслуживании 5+ домов: -25%

💡 Точный расчет сделает Максим Маслов по телефону!"""

    # Контакты и менеджер
    elif any(word in message_lower for word in ["контакт", "телефон", "связаться", "менеджер", "максим", "маслов"]):
        response = f"""📞 Контакты ВасДом, {user_name}:

👨‍💼 ГЛАВНЫЙ МЕНЕДЖЕР: 
🔹 Максим Маслов
🔹 Опыт работы: 8+ лет
🔹 Специализация: управление недвижимостью

📱 КОНТАКТНАЯ ИНФОРМАЦИЯ:
🔹 Телефон: +7 (XXX) XXX-XX-XX (уточняется)
🔹 Email: info@vas-dom.ru  
🔹 Telegram: @vas_dom_kaluga
🔹 WhatsApp: доступен

🏢 ОФИС В КАЛУГЕ:
🔹 Адрес: г. Калуга (центр города)
🔹 Прием клиентов: по предварительной записи

⏰ РЕЖИМ РАБОТЫ:
• Пн-Пт: 8:00 - 19:00
• Сб: 9:00 - 17:00  
• Вс: 10:00 - 16:00
• Аварийная служба: 24/7

✅ Максим лично свяжется с вами в течение 30 минут!"""

    # Вопросы о компании
    elif any(word in message_lower for word in ["компания", "васдом", "калуга", "о вас", "кто вы"]):
        response = f"""🏢 О компании ВасДом, {user_name}:

🎯 НАША МИССИЯ: Делаем дома уютными и чистыми!

📈 НАШИ ДОСТИЖЕНИЯ:
✅ 8+ лет на рынке Калуги и области
✅ 500+ домов под нашим управлением  
✅ 100+ квалифицированных сотрудников
✅ 5000+ довольных клиентов
✅ 98% положительных отзывов

🏆 ПОЧЕМУ ВЫБИРАЮТ НАС:
• Профессиональное оборудование
• Экологичные моющие средства
• Страхование ответственности
• Работаем без выходных
• Гарантия качества 100%

🌍 ГЕОГРАФИЯ РАБОТЫ:
• Калуга (все районы)
• Калужская область
• Выездные работы в Тулу, Москву

👥 НАША КОМАНДА:
• Менеджер: Максим Маслов
• 15 бригад клинеров
• 5 управляющих домами  
• Круглосуточная диспетчерская служба

Присоединяйтесь к нашим клиентам! 🤝"""

    # Help и помощь
    elif any(word in message_lower for word in ["помощь", "help", "/help", "что умеешь"]):
        response = f"""ℹ️ Справка по боту ВасДом, {user_name}:

🤖 ЧТО Я УМЕЮ:
✅ Консультировать по услугам уборки
✅ Рассчитывать стоимость обслуживания
✅ Записывать на консультацию к менеджеру
✅ Отвечать на вопросы о компании
✅ Помогать с выбором тарифа

📝 КОМАНДЫ:
• Напишите "уборка" - узнать об услугах
• Напишите "цены" - посмотреть тарифы  
• Напишите "контакты" - связаться с менеджером
• Напишите "о компании" - информация о ВасДом

💬 ПРИМЕРЫ ЗАПРОСОВ:
• "Сколько стоит убирать подъезд?"
• "Хочу заказать генеральную уборку"
• "Свяжите меня с Максимом"
• "Работаете ли вы в выходные?"

🎯 НЕ НАШЛИ ОТВЕТ?
Напишите свой вопрос - я постараюсь помочь или переведу вас на Максима Маслова!"""

    # Жалобы и проблемы
    elif any(word in message_lower for word in ["плохо", "жалоба", "проблема", "не работает", "недовольн"]):
        response = f"""😔 Извините за неудобства, {user_name}!

Мы серьезно относимся к каждому обращению.

🔧 ЧТО ДЕЛАЕМ:
1️⃣ Немедленно разберем вашу ситуацию
2️⃣ Примем меры в течение 2 часов
3️⃣ Компенсируем ущерб при необходимости
4️⃣ Улучшим качество обслуживания

📞 ЭКСТРЕННАЯ СВЯЗЬ:
• Максим Маслов лично займется вопросом
• Аварийная служба: 24/7
• Гарантия решения проблемы: 100%

💡 ОПИШИТЕ ПРОБЛЕМУ:
Расскажите подробнее что произошло - и мы немедленно исправим ситуацию!

✅ ВасДом дорожит каждым клиентом!"""

    # Общий случай
    else:
        response = f"""Спасибо за обращение, {user_name}! 🏠

Компания ВасДом работает в Калуге и области уже 8+ лет. 

🏠 МЫ СПЕЦИАЛИЗИРУЕМСЯ НА:
✅ Профессиональной уборке подъездов
✅ Клининге придомовых территорий
✅ Управлении жилой недвижимостью
✅ Решении вопросов ЖКХ

📊 НАШИ ЦИФРЫ:
• 500+ домов под управлением
• 100+ профессиональных сотрудников  
• 5000+ довольных клиентов
• 98% положительных отзывов

💬 ПРИМЕР ВОПРОСОВ:
• "Сколько стоит уборка подъезда?"
• "Работаете ли в выходные?"
• "Хочу заказать генеральную уборку"

📞 НУЖНА ПОМОЩЬ?
Менеджер Максим Маслов ответит на любые вопросы и поможет с выбором услуг!

Пишите - я всегда рад помочь! 🤖"""
    
    add_log("SUCCESS", f"🧠 Сгенерирован умный ответ", {
        "user_message": user_message[:50],
        "response_length": len(response),
        "user_name": user_name
    })
    
    return response

# Middleware для логирования ВСЕХ запросов
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    # Логируем входящий запрос
    client_ip = request.client.host if request.client else "unknown"
    method = request.method
    url = str(request.url)
    
    print(f"📥 ========== НОВЫЙ ЗАПРОС ==========")
    print(f"📥 IP: {client_ip}")
    print(f"📥 METHOD: {method}")
    print(f"📥 URL: {url}")
    print(f"📥 TIME: {datetime.utcnow().isoformat()}")
    
    # Обрабатываем запрос
    response = await call_next(request)
    
    # Логируем ответ
    process_time = time.time() - start_time
    status_code = response.status_code
    
    print(f"📤 ========== ОТВЕТ ГОТОВ ==========")
    print(f"📤 STATUS: {status_code}")
    print(f"📤 TIME: {process_time:.3f}s")
    print(f"📤 =====================================")
    
    # Обновляем статистику
    system_status["total_requests"] += 1
    system_status["last_activity"] = datetime.utcnow().isoformat()
    
    add_log("INFO", f"REQUEST {method} {url} -> {status_code} ({process_time:.3f}s)", {
        "ip": client_ip,
        "method": method,
        "url": url,
        "status": status_code,
        "duration": f"{process_time:.3f}s"
    })
    
    return response

@app.get("/")
async def root():
    """Главная страница приложения"""
    
    print("🏠 ========== ГЛАВНАЯ СТРАНИЦА ==========")
    print("🏠 Пользователь зашел на главную страницу")
    print("🏠 Отправляем информацию о сервисе")
    
    add_log("INFO", "🏠 Запрос главной страницы", {"endpoint": "/"})
    
    response_data = {
        "message": "🤖 AI-Ассистент ВасДом - PRODUCTION READY",
        "status": "✅ Успешно развернут на Render",
        "company": "ВасДом - Клининговая компания Калуга",
        "version": "4.0.0 (Production Ready Edition)",
        "telegram_bot": "@aitest123432_bot",
        "logs_count": len(application_logs),
        "system_status": system_status,
        "current_time": datetime.utcnow().isoformat(),
        "features": {
            "smart_ai_responses": True,
            "telegram_bot": True,
            "bitrix24_integration": True,
            "realtime_logging": True,
            "production_ready": True
        },
        "endpoints": {
            "health": "/health",
            "webhook_setup": "/telegram/set-webhook", 
            "dashboard": "/dashboard",
            "logs": "/logs",
            "test_ai": "/test-ai"
        }
    }
    
    print(f"🏠 Отправляем ответ: {len(str(response_data))} символов")
    return response_data

@app.get("/health")
async def health_check():
    """Health check endpoint с детальной диагностикой"""
    
    print("💊 ========== HEALTH CHECK ==========")
    print("💊 Проверяем состояние системы...")
    
    # Проверяем переменные окружения
    env_vars = {
        "TELEGRAM_BOT_TOKEN": os.environ.get("TELEGRAM_BOT_TOKEN") or os.environ.get("BOT_TOKEN"),
        "TELEGRAM_WEBHOOK_URL": os.environ.get("TELEGRAM_WEBHOOK_URL"),
        "BITRIX24_WEBHOOK_URL": os.environ.get("BITRIX24_WEBHOOK_URL"),
        "EMERGENT_LLM_KEY": os.environ.get("EMERGENT_LLM_KEY")
    }
    
    print("💊 ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ:")
    for key, value in env_vars.items():
        status = "✅ НАСТРОЕНА" if value else "❌ НЕ НАСТРОЕНА"
        value_preview = value[:20] + "..." if value and len(value) > 20 else value
        print(f"💊 {key}: {status} ({value_preview})")
    
    env_check = {k: bool(v) for k, v in env_vars.items()}
    
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "VasDom AI Assistant (Production Ready)",
        "version": "4.0.0",
        "deployment": "render",
        "uptime": system_status["startup_time"],
        "environment_variables": env_check,
        "environment_values": {k: v[:20] + "..." if v and len(v) > 20 else v for k, v in env_vars.items()},
        "statistics": system_status,
        "logs_available": len(application_logs),
        "ai_mode": "smart_responses_enabled",
        "database": {
            "mongodb_configured": bool(mongo_url),
            "mongodb_url": mongo_url[:50] + "..." if mongo_url and len(mongo_url) > 50 else mongo_url,
            "mongodb_client": "connected" if db is not None else "not_connected",
            "database_name": os.environ.get("DB_NAME", "vasdom_db")
        }
    }
    
    print(f"💊 Health check complete: {health_status['status']}")
    add_log("INFO", "💊 Health check выполнен", health_status)
    
    return health_status

@app.get("/api/mongodb/test")
async def test_mongodb():
    """Тест подключения к MongoDB"""
    
    if not db or db is None:
        return {"status": "error", "message": "MongoDB не настроен"}
    
    try:
        # Простая проверка подключения
        server_info = await mongo_client.server_info()
        
        # Тестовая запись
        test_doc = {
            "test_message": "VasDom AI Assistant connection test",
            "timestamp": datetime.utcnow(),
            "version": "4.0.0"
        }
        
        # Вставляем тестовый документ
        result = await db.connection_tests.insert_one(test_doc)
        
        return {
            "status": "success",
            "message": "✅ MongoDB подключение работает!",
            "database": os.environ.get("DB_NAME", "vasdom_db"),
            "mongo_version": server_info.get("version"),
            "test_document_id": str(result.inserted_id),
            "connection_url": mongo_url[:50] + "..." if len(mongo_url) > 50 else mongo_url
        }
        
    except Exception as e:
        return {
            "status": "error", 
            "message": f"❌ Ошибка MongoDB: {str(e)}",
            "mongo_url_configured": bool(mongo_url)
        }

@app.get("/test-ai")
async def test_ai_service():
    """Тестирование AI сервиса"""
    
    print("🧠 ========== ТЕСТ AI СЕРВИСА ==========")
    
    test_message = "Привет! Расскажите о ваших услугах по уборке подъездов в Калуге."
    
    add_log("INFO", "🧠 Запуск теста AI сервиса", {"test_message": test_message})
    
    try:
        ai_response = generate_smart_response(test_message, {"user_name": "Тестовый пользователь"})
        
        return {
            "status": "✅ AI РАБОТАЕТ (SMART MODE)",
            "test_message": test_message,
            "ai_response": ai_response,
            "response_length": len(ai_response),
            "timestamp": datetime.utcnow().isoformat(),
            "mode": "smart_keyword_based_responses",
            "company": "VasDom - Калуга"
        }
    except Exception as e:
        return {
            "status": "❌ AI ОШИБКА",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

@app.get("/dashboard")
async def get_dashboard():
    """Дашборд с логами и статистикой"""
    
    print("📊 ========== ДАШБОРД ЗАПРОС ==========")
    print(f"📊 Всего логов: {len(application_logs)}")
    print(f"📊 Telegram сообщений: {len(telegram_messages)}")
    print(f"📊 Всего запросов: {system_status['total_requests']}")
    
    add_log("INFO", "📊 Запрос дашборда", {"endpoint": "/dashboard"})
    
    dashboard_data = {
        "success": True,
        "company": "ВасДом - Калуга",
        "message": "🎉 AI-ассистент работает! (Production Ready Edition)",
        "system_status": system_status,
        "telegram_bot": "@aitest123432_bot",
        "recent_logs": application_logs[-20:], # Последние 20 логов
        "telegram_messages": telegram_messages[-10:], # Последние 10 сообщений
        "metrics": {
            "houses": {"Калуга": 500, "Область": 150},
            "employees": 100,
            "status": "active",
            "total_requests": system_status["total_requests"],
            "telegram_updates": system_status["telegram_updates"],
            "errors": system_status["errors"],
            "ai_mode": "smart_responses"
        },
        "environment": {
            "telegram_configured": bool(os.environ.get("TELEGRAM_BOT_TOKEN")),
            "webhook_configured": bool(os.environ.get("TELEGRAM_WEBHOOK_URL")),
            "bitrix24_configured": bool(os.environ.get("BITRIX24_WEBHOOK_URL")),
            "ai_configured": "smart_mode_enabled"
        }
    }
    
    print(f"📊 Дашборд готов: {len(str(dashboard_data))} символов")
    return dashboard_data

@app.get("/logs")
async def get_logs():
    """Endpoint для просмотра всех логов"""
    
    print("📋 ========== ЛОГИ ЗАПРОС ==========")
    print(f"📋 Возвращаем {len(application_logs)} логов")
    
    return {
        "total_logs": len(application_logs),
        "logs": application_logs,
        "system_status": system_status,
        "telegram_messages": telegram_messages
    }

@app.get("/telegram/set-webhook")
async def set_telegram_webhook():
    """Установка Telegram webhook"""
    
    print("🔗 ========== УСТАНОВКА WEBHOOK ==========")
    
    add_log("INFO", "🚀 НАЧИНАЕМ УСТАНОВКУ TELEGRAM WEBHOOK", {"step": "start"})
    
    try:
        webhook_url = os.environ.get("TELEGRAM_WEBHOOK_URL")
        bot_token = os.environ.get("TELEGRAM_BOT_TOKEN") or os.environ.get("BOT_TOKEN")
        
        if not webhook_url or not bot_token:
            missing = []
            if not webhook_url: missing.append("TELEGRAM_WEBHOOK_URL")
            if not bot_token: missing.append("TELEGRAM_BOT_TOKEN")
            
            return {
                "status": "❌ КОНФИГУРАЦИЯ НЕПОЛНАЯ",
                "missing_variables": missing,
                "instructions": [
                    "1. Добавьте переменные в Render Environment",
                    "2. Дождитесь redeploy (3-5 минут)",
                    "3. Вызовите этот endpoint снова"
                ]
            }
        
        import httpx
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            telegram_api_url = f"https://api.telegram.org/bot{bot_token}/setWebhook"
            
            payload = {
                "url": webhook_url,
                "drop_pending_updates": True,
                "allowed_updates": ["message", "callback_query"]
            }
            
            response = await client.post(telegram_api_url, json=payload)
            
            if response.status_code == 200:
                result = response.json()
                if result.get("ok"):
                    add_log("SUCCESS", f"✅ WEBHOOK УСТАНОВЛЕН: {webhook_url}")
                    
                    return {
                        "status": "✅ ПОЛНЫЙ УСПЕХ!",
                        "message": "Telegram webhook установлен успешно!",
                        "webhook_url": webhook_url,
                        "bot": "@aitest123432_bot",
                        "ai_mode": "smart_responses_enabled",
                        "next_steps": [
                            "1. Найдите @aitest123432_bot в Telegram",
                            "2. Напишите любое сообщение",
                            "3. Бот ответит умно и по-русски!",
                            "4. Проверьте /dashboard для логов"
                        ]
                    }
                else:
                    return {"status": "❌ Telegram API ошибка", "error": result.get("description")}
            else:
                return {"status": "❌ HTTP ошибка", "http_status": response.status_code}
    
    except Exception as e:
        add_log("ERROR", f"❌ КРИТИЧЕСКАЯ ОШИБКА: {str(e)}")
        return {"status": "❌ КРИТИЧЕСКАЯ ОШИБКА", "error": str(e)}

@app.post("/telegram/webhook")
async def telegram_webhook(request: Request):
    """Обработка Telegram webhook с умными ответами"""
    
    print("🤖 ========== TELEGRAM WEBHOOK ==========")
    system_status["telegram_updates"] += 1
    
    try:
        data = await request.json()
        
        add_log("INFO", "🤖 ПОЛУЧЕН TELEGRAM UPDATE", {
            "update_keys": list(data.keys()),
            "update_id": data.get("update_id")
        })
        
        # Детальная обработка сообщений
        if 'message' in data:
            message = data['message']
            chat_id = message.get('chat', {}).get('id')
            text = message.get('text', '')
            user_info = message.get('from', {})
            user_name = user_info.get('first_name', 'Unknown')
            username = user_info.get('username', 'no_username')
            
            message_info = {
                "chat_id": chat_id,
                "user_name": user_name,
                "username": username,
                "text": text,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Сохраняем сообщение для дашборда
            telegram_messages.append(message_info)
            if len(telegram_messages) > 50:
                telegram_messages[:] = telegram_messages[-50:]
            
            add_log("SUCCESS", f"💬 СООБЩЕНИЕ ОТ {user_name}: {text[:50]}")
            
            # Генерируем умный ответ
            try:
                smart_response = generate_smart_response(text, {
                    "user_name": user_name,
                    "username": username,
                    "chat_id": chat_id
                })
                
                # Отправляем умный ответ через Telegram API
                bot_token = os.environ.get("TELEGRAM_BOT_TOKEN") or os.environ.get("BOT_TOKEN")
                if bot_token:
                    import httpx
                    
                    send_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                    send_data = {
                        "chat_id": chat_id,
                        "text": smart_response,
                        "parse_mode": "HTML"
                    }
                    
                    async with httpx.AsyncClient(timeout=10.0) as client:
                        telegram_response = await client.post(send_url, json=send_data)
                        if telegram_response.status_code == 200:
                            add_log("SUCCESS", f"✅ УМНЫЙ ОТВЕТ ОТПРАВЛЕН ({len(smart_response)} символов)")
                        else:
                            add_log("ERROR", f"❌ ОШИБКА ОТПРАВКИ: {telegram_response.status_code}")
                            
            except Exception as ai_error:
                add_log("ERROR", f"❌ ОШИБКА ГЕНЕРАЦИИ ОТВЕТА: {str(ai_error)}")
        
        return {"ok": True}
    
    except Exception as e:
        add_log("ERROR", f"❌ ОШИБКА WEBHOOK: {str(e)}")
        return {"ok": False, "error": str(e)}

# Bitrix24 integration endpoints
@app.get("/api/bitrix24/test")
async def test_bitrix24():
    """Test Bitrix24 connection"""
    try:
        import httpx
        webhook_url = os.getenv("BITRIX24_WEBHOOK_URL")
        if not webhook_url:
            return {"status": "error", "message": "BITRIX24_WEBHOOK_URL not configured"}
        
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(f"{webhook_url}user.current")
            if response.status_code == 200:
                result = response.json()
                user = result.get("result", {})
                return {
                    "status": "success",
                    "user": {"NAME": user.get("NAME"), "LAST_NAME": user.get("LAST_NAME")},
                    "integration_status": "✅ РЕАЛЬНЫЕ ДАННЫЕ BITRIX24"
                }
            else:
                return {"status": "error", "message": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/bitrix24/deals")
async def get_bitrix24_deals():
    """Get deals from Bitrix24"""
    try:
        import httpx
        webhook_url = os.getenv("BITRIX24_WEBHOOK_URL")
        if not webhook_url:
            return {"error": "BITRIX24_WEBHOOK_URL not configured"}
        
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(f"{webhook_url}crm.deal.list",
                json={"select": ["ID", "TITLE", "STAGE_ID", "OPPORTUNITY"], "start": 0})
            if response.status_code == 200:
                result = response.json()
                deals = result.get("result", [])
                return {"deals": deals, "count": len(deals), "data_source": "✅ РЕАЛЬНЫЕ ДАННЫЕ BITRIX24"}
            else:
                return {"error": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"error": str(e)}

# Startup event
@app.on_event("startup")
async def startup_event():
    print("🚀 ========== СИСТЕМА ЗАПУСКАЕТСЯ ==========")
    print("🚀 VasDom AI Assistant - Production Ready Edition")
    print("🚀 Smart AI responses enabled!")
    print("🚀 Ready for Render deployment!")
    print("🚀 ==========================================")
    
    add_log("SUCCESS", "🚀 VASDOM AI ASSISTANT ГОТОВ К РАБОТЕ! (Production Ready)", {
        "timestamp": datetime.utcnow().isoformat(),
        "version": "4.0.0",
        "ai_mode": "smart_responses",
        "company": "VasDom - Калуга"
    })
    logger.info("✅ VasDom AI Assistant успешно стартовал! Умные ответы включены!")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)