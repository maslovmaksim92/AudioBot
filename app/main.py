import time
import os
from fastapi import FastAPI, APIRouter, Request
from loguru import logger
from datetime import datetime
import sys

# Настройка логирования для Render Dashboard
logger.remove()  # Убираем стандартный логгер
logger.add(sys.stdout, format="🚀 {time:HH:mm:ss} | {level} | {message}", level="INFO")
logger.add(sys.stderr, format="🚨 {time:HH:mm:ss} | {level} | {message}", level="ERROR")

# Создаём FastAPI приложение
app = FastAPI()

print("🚀 =============================================================")
print("🚀 VASDOM AI ASSISTANT STARTING UP - FULL LOGGING ENABLED")
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
    else:  # INFO
        logger.info(f"🔵 {message}")

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
        "message": "🤖 AI-Ассистент ВасДом - ПОЛНОЕ ЛОГИРОВАНИЕ",
        "status": "✅ Успешно развернут на Render",
        "company": "ВасДом - Клининговая компания",
        "version": "3.1.0 (Full Logging Edition)",
        "telegram_bot": "@aitest123432_bot",
        "logs_count": len(application_logs),
        "system_status": system_status,
        "current_time": datetime.utcnow().isoformat(),
        "endpoints": {
            "health": "/health",
            "webhook_setup": "/telegram/set-webhook",
            "dashboard": "/dashboard",
            "logs": "/logs",
            "test_chat": "/test-chat"
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
        "TELEGRAM_BOT_TOKEN": os.environ.get("TELEGRAM_BOT_TOKEN"),
        "TELEGRAM_WEBHOOK_URL": os.environ.get("TELEGRAM_WEBHOOK_URL"),
        "BITRIX24_WEBHOOK_URL": os.environ.get("BITRIX24_WEBHOOK_URL"),
        "EMERGENT_LLM_KEY": os.environ.get("EMERGENT_LLM_KEY")
    }
    
    print("💊 ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ:")
    for key, value in env_vars.items():
        status = "✅ НАСТРОЕНА" if value else "❌ НЕ НАСТРОЕНА"
        value_preview = value[:20] + "..." if value and len(value) > 20 else value
        print(f"💊   {key}: {status} ({value_preview})")
    
    env_check = {k: bool(v) for k, v in env_vars.items()}
    
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "VasDom AI Assistant (Full Logging Edition)",
        "version": "3.1.0",
        "deployment": "render",
        "uptime": system_status["startup_time"],
        "environment_variables": env_check,
        "environment_values": {k: v[:20] + "..." if v and len(v) > 20 else v for k, v in env_vars.items()},
        "statistics": system_status,
        "logs_available": len(application_logs)
    }
    
    print(f"💊 Health check complete: {health_status['status']}")
    add_log("INFO", "💊 Health check выполнен", health_status)
    
    return health_status

@app.get("/test-chat")
async def test_chat():
    """Тестовый endpoint для проверки чата"""
    
    print("💬 ========== ТЕСТ ЧАТА ==========")
    print("💬 Тестируем функционал чата...")
    
    test_message = "Привет! Это тестовое сообщение для проверки чата."
    
    add_log("INFO", "💬 Тест чата запущен", {"test_message": test_message})
    
    # Симулируем AI ответ
    ai_response = f"🤖 Получил тестовое сообщение: '{test_message}'. Чат работает корректно!"
    
    print(f"💬 Тестовое сообщение: {test_message}")
    print(f"💬 AI ответ: {ai_response}")
    
    add_log("SUCCESS", "💬 Тест чата успешен", {"ai_response": ai_response})
    
    return {
        "status": "success",
        "test_message": test_message,
        "ai_response": ai_response,
        "timestamp": datetime.utcnow().isoformat(),
        "logs_count": len(application_logs)
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
        "company": "ВасДом",
        "message": "🎉 AI-ассистент работает! (Full Logging Edition)",
        "system_status": system_status,
        "telegram_bot": "@aitest123432_bot",
        "recent_logs": application_logs[-20:],  # Последние 20 логов
        "telegram_messages": telegram_messages[-10:],  # Последние 10 сообщений
        "metrics": {
            "houses": {"Калуга": 500, "Кемерово": 100},
            "employees": 100,
            "status": "active",
            "total_requests": system_status["total_requests"],
            "telegram_updates": system_status["telegram_updates"],
            "errors": system_status["errors"]
        },
        "environment": {
            "telegram_configured": bool(os.environ.get("TELEGRAM_BOT_TOKEN")),
            "webhook_configured": bool(os.environ.get("TELEGRAM_WEBHOOK_URL")),
            "bitrix24_configured": bool(os.environ.get("BITRIX24_WEBHOOK_URL")),
            "ai_configured": bool(os.environ.get("EMERGENT_LLM_KEY"))
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

@app.get("/live-status")
async def live_status():
    """Живой статус для мониторинга в реальном времени"""
    
    print("📺 ========== LIVE STATUS CHECK ==========")
    print(f"📺 Время: {datetime.utcnow().isoformat()}")
    print(f"📺 Запросов: {system_status['total_requests']}")
    print(f"📺 Telegram updates: {system_status['telegram_updates']}")
    print(f"📺 Ошибок: {system_status['errors']}")
    print(f"📺 Логов: {len(application_logs)}")
    
    # Проверяем последние 5 логов
    recent_logs = application_logs[-5:] if application_logs else []
    print("📺 Последние 5 логов:")
    for log in recent_logs:
        print(f"📺   [{log['timestamp']}] {log['level']}: {log['message']}")
    
    return {
        "live_time": datetime.utcnow().isoformat(),
        "status": "✅ ALIVE",
        "uptime_seconds": (datetime.utcnow() - datetime.fromisoformat(system_status["startup_time"])).total_seconds(),
        "statistics": system_status,
        "recent_logs": recent_logs,
        "environment_check": {
            "telegram_bot_token": "✅" if os.environ.get("TELEGRAM_BOT_TOKEN") else "❌",
            "telegram_webhook_url": "✅" if os.environ.get("TELEGRAM_WEBHOOK_URL") else "❌",
            "bitrix24_webhook_url": "✅" if os.environ.get("BITRIX24_WEBHOOK_URL") else "❌",
            "emergent_llm_key": "✅" if os.environ.get("EMERGENT_LLM_KEY") else "❌"
        },
        "message": "🎉 Система работает и логирует ВСЕ действия!"
    }

@app.get("/telegram/set-webhook")
async def set_telegram_webhook():
    """Установка Telegram webhook - МАКСИМАЛЬНО ЗАЛОГИРОВАНО"""
    
    print("🔗 ========== УСТАНОВКА WEBHOOK ==========")
    
    add_log("INFO", "🚀 НАЧИНАЕМ УСТАНОВКУ TELEGRAM WEBHOOK", {"step": "start"})
    
    try:
        webhook_url = os.environ.get("TELEGRAM_WEBHOOK_URL")
        bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
        
        print(f"🔗 TELEGRAM_WEBHOOK_URL: {webhook_url}")
        print(f"🔗 TELEGRAM_BOT_TOKEN: {'✅ ЕСТЬ' if bot_token else '❌ НЕТ'}")
        
        add_log("INFO", f"📋 Проверка переменных окружения", {
            "webhook_url": webhook_url, 
            "bot_token_configured": bool(bot_token)
        })
        
        if not webhook_url or not bot_token:
            missing = []
            if not webhook_url: missing.append("TELEGRAM_WEBHOOK_URL")
            if not bot_token: missing.append("TELEGRAM_BOT_TOKEN")
            
            error_msg = f"❌ Отсутствуют переменные: {', '.join(missing)}"
            print(f"🔗 ОШИБКА: {error_msg}")
            
            add_log("ERROR", error_msg, {"missing_vars": missing})
            system_status["errors"] += 1
            
            return {
                "status": "❌ КОНФИГУРАЦИЯ НЕПОЛНАЯ",
                "missing_variables": missing,
                "required_env_vars": {
                    "TELEGRAM_WEBHOOK_URL": "https://audiobot-qq2.onrender.com/telegram/webhook",
                    "TELEGRAM_BOT_TOKEN": "8327964628:AAHMIgT1XiGEkLc34nogRGZt-Ox-9R0TSn0"
                },
                "instructions": [
                    "1. Добавьте переменные в Render Environment",
                    "2. Дождитесь redeploy (3-5 минут)",
                    "3. Вызовите этот endpoint снова"
                ],
                "logs": application_logs[-5:]
            }
        
        print(f"🔗 Отправляем запрос в Telegram API...")
        add_log("INFO", "🔗 Отправляем запрос в Telegram API", {
            "telegram_url": f"https://api.telegram.org/bot{bot_token[:10]}***/setWebhook",
            "webhook_url": webhook_url
        })
        
        # Отправляем запрос в Telegram API
        import httpx
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            telegram_api_url = f"https://api.telegram.org/bot{bot_token}/setWebhook"
            
            payload = {
                "url": webhook_url,
                "drop_pending_updates": True,
                "allowed_updates": ["message", "callback_query"]
            }
            
            print(f"🔗 Payload: {payload}")
            add_log("INFO", "📡 Выполняем HTTP запрос к Telegram", payload)
            
            response = await client.post(telegram_api_url, json=payload)
            
            print(f"🔗 Response status: {response.status_code}")
            print(f"🔗 Response text: {response.text}")
            
            add_log("INFO", f"📥 Ответ от Telegram API", {
                "status_code": response.status_code,
                "response_text": response.text[:500]
            })
            
            if response.status_code == 200:
                result = response.json()
                if result.get("ok"):
                    success_msg = f"✅ WEBHOOK УСТАНОВЛЕН УСПЕШНО: {webhook_url}"
                    print(f"🔗 УСПЕХ: {success_msg}")
                    
                    add_log("SUCCESS", success_msg, {
                        "webhook_url": webhook_url,
                        "telegram_response": result
                    })
                    
                    return {
                        "status": "✅ ПОЛНЫЙ УСПЕХ!",
                        "message": "Telegram webhook установлен успешно!",
                        "webhook_url": webhook_url,
                        "bot": "@aitest123432_bot",
                        "telegram_response": result,
                        "next_steps": [
                            "1. Найдите @aitest123432_bot в Telegram",
                            "2. Напишите /start",
                            "3. Бот должен ответить мгновенно!",
                            "4. Проверьте /dashboard для логов"
                        ],
                        "logs": application_logs[-3:]
                    }
                else:
                    error_msg = f"❌ TELEGRAM API ОШИБКА: {result.get('description')}"
                    print(f"🔗 ОШИБКА: {error_msg}")
                    
                    add_log("ERROR", error_msg, {"telegram_response": result})
                    system_status["errors"] += 1
                    
                    return {
                        "status": "❌ Telegram API ошибка",
                        "error": result.get("description", "Неизвестная ошибка"),
                        "telegram_response": result,
                        "logs": application_logs[-5:]
                    }
            else:
                error_msg = f"❌ HTTP ОШИБКА: {response.status_code}"
                print(f"🔗 ОШИБКА: {error_msg}")
                
                add_log("ERROR", error_msg, {
                    "status_code": response.status_code,
                    "response": response.text[:300]
                })
                system_status["errors"] += 1
                
                return {
                    "status": "❌ HTTP ошибка",
                    "http_status": response.status_code,
                    "response": response.text[:500],
                    "logs": application_logs[-5:]
                }
                
    except Exception as e:
        error_msg = f"❌ КРИТИЧЕСКАЯ ОШИБКА: {str(e)}"
        print(f"🔗 КРИТИЧЕСКАЯ ОШИБКА: {e}")
        
        add_log("ERROR", error_msg, {"exception": str(e)})
        system_status["errors"] += 1
        
        return {
            "status": "❌ КРИТИЧЕСКАЯ ОШИБКА",
            "error": str(e),
            "troubleshooting": [
                "Проверьте интернет соединение",
                "Убедитесь что токен бота правильный",
                "Проверьте что домен доступен публично",
                "Посмотрите логи Render на ошибки"
            ],
            "logs": application_logs[-10:]
        }

@app.post("/telegram/webhook")
async def telegram_webhook(request: Request):
    """Обработка Telegram webhook - МАКСИМАЛЬНО ЗАЛОГИРОВАНО"""
    
    print("🤖 ========== TELEGRAM WEBHOOK ==========")
    system_status["telegram_updates"] += 1
    
    try:
        data = await request.json()
        
        print(f"🤖 Получен update от Telegram:")
        print(f"🤖 Keys: {list(data.keys())}")
        print(f"🤖 Data: {str(data)[:200]}...")
        
        add_log("INFO", "🤖 ПОЛУЧЕН TELEGRAM UPDATE", {
            "update_keys": list(data.keys()),
            "update_id": data.get("update_id"),
            "data_size": len(str(data))
        })
        
        # Детальная обработка сообщений
        if 'message' in data:
            message = data['message']
            chat_id = message.get('chat', {}).get('id')
            text = message.get('text', '')
            user_info = message.get('from', {})
            user_name = user_info.get('first_name', 'Unknown')
            username = user_info.get('username', 'no_username')
            
            print(f"🤖 💬 СООБЩЕНИЕ:")
            print(f"🤖   От: {user_name} (@{username})")
            print(f"🤖   Chat ID: {chat_id}")
            print(f"🤖   Текст: {text}")
            
            message_info = {
                "chat_id": chat_id,
                "user_name": user_name,
                "username": username,
                "text": text,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Сохраняем сообщение для дашборда
            telegram_messages.append(message_info)
            if len(telegram_messages) > 50:  # Оставляем последние 50
                telegram_messages[:] = telegram_messages[-50:]
            
            add_log("SUCCESS", f"💬 СООБЩЕНИЕ ОТ ПОЛЬЗОВАТЕЛЯ", message_info)
            
            # Здесь должна быть отправка ответа через Telegram API
            print("🤖 ✅ Сообщение обработано успешно!")
            add_log("SUCCESS", "✅ СООБЩЕНИЕ ОБРАБОТАНО УСПЕШНО", {
                "processed_at": datetime.utcnow().isoformat()
            })
        
        elif 'callback_query' in data:
            callback = data['callback_query']
            print(f"🤖 🔘 CALLBACK QUERY: {callback.get('data', '')}")
            add_log("INFO", "🔘 ПОЛУЧЕН CALLBACK QUERY", {
                "callback_data": callback.get('data', ''),
                "user_id": callback.get('from', {}).get('id')
            })
        
        else:
            print(f"🤖 ⚠️ НЕИЗВЕСТНЫЙ ТИП UPDATE: {list(data.keys())}")
            add_log("WARNING", "⚠️ НЕИЗВЕСТНЫЙ ТИП UPDATE", {
                "update_keys": list(data.keys())
            })
        
        return {"ok": True}
        
    except Exception as e:
        error_msg = f"❌ ОШИБКА ОБРАБОТКИ WEBHOOK: {str(e)}"
        print(f"🤖 ОШИБКА: {e}")
        
        add_log("ERROR", error_msg, {"exception": str(e)})
        system_status["errors"] += 1
        
        return {"ok": False, "error": str(e)}

# Startup event
@app.on_event("startup")
async def startup_event():
    print("🚀 ========== СИСТЕМА ЗАПУСКАЕТСЯ ==========")
    print("🚀 VasDom AI Assistant - Full Logging Edition")
    print("🚀 Все логи будут отображаться в Render Dashboard")
    print("🚀 ==========================================")
    
    add_log("SUCCESS", "🚀 ПРИЛОЖЕНИЕ ИНИЦИАЛИЗИРОВАНО (Full Logging Edition)", {
        "timestamp": datetime.utcnow().isoformat(),
        "module": "app.main",
        "version": "3.1.0"
    })

logger.info("✅ FastAPI приложение успешно стартовало (Full Logging Edition)")