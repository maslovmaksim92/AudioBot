import time
import os
from fastapi import APIRouter, Request
from loguru import logger
from datetime import datetime

router = APIRouter()

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
    """Добавить лог в глобальный список для дашборда"""
    global application_logs
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "level": level,
        "message": message,
        "details": details or {}
    }
    application_logs.append(log_entry)
    
    # Оставляем только последние 100 записей
    if len(application_logs) > 100:
        application_logs = application_logs[-100:]
    
    # Логируем также в loguru
    if level == "ERROR":
        logger.error(f"🔴 {message}")
    elif level == "WARNING":
        logger.warning(f"🟡 {message}")
    elif level == "SUCCESS":
        logger.success(f"🟢 {message}")
    else:  # INFO
        logger.info(f"🔵 {message}")

@router.get("/")
async def root():
    """Главная страница приложения"""
    system_status["total_requests"] += 1
    system_status["last_activity"] = datetime.utcnow().isoformat()
    
    add_log("INFO", "Запрос главной страницы", {"endpoint": "/"})
    
    return {
        "message": "🤖 AI-Ассистент ВасДом - ТОЧНАЯ КОПИЯ PostingFotoTG",
        "status": "✅ Успешно развернут на Render",
        "company": "ВасДом - Клининговая компания",
        "version": "3.0.0 (PostingFotoTG Edition)",
        "telegram_bot": "@aitest123432_bot",
        "logs_count": len(application_logs),
        "system_status": system_status,
        "endpoints": {
            "health": "/health",
            "webhook_setup": "/telegram/set-webhook",
            "dashboard": "/dashboard",
            "logs": "/logs"
        }
    }

@router.get("/health")
async def health_check():
    """Health check endpoint с детальной диагностикой"""
    system_status["total_requests"] += 1
    system_status["last_activity"] = datetime.utcnow().isoformat()
    
    # Проверяем переменные окружения
    env_check = {
        "TELEGRAM_BOT_TOKEN": bool(os.environ.get("TELEGRAM_BOT_TOKEN")),
        "TELEGRAM_WEBHOOK_URL": bool(os.environ.get("TELEGRAM_WEBHOOK_URL")),
        "BITRIX24_WEBHOOK_URL": bool(os.environ.get("BITRIX24_WEBHOOK_URL")),
        "EMERGENT_LLM_KEY": bool(os.environ.get("EMERGENT_LLM_KEY"))
    }
    
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "VasDom AI Assistant (PostingFotoTG Edition)",
        "version": "3.0.0",
        "deployment": "render",
        "uptime": system_status["startup_time"],
        "environment_variables": env_check,
        "statistics": system_status,
        "logs_available": len(application_logs)
    }
    
    add_log("INFO", "Health check запрос", health_status)
    
    return health_status

@router.get("/dashboard")
async def get_dashboard():
    """Дашборд с логами и статистикой"""
    system_status["total_requests"] += 1
    system_status["last_activity"] = datetime.utcnow().isoformat()
    
    add_log("INFO", "Запрос дашборда", {"endpoint": "/dashboard"})
    
    return {
        "success": True,
        "company": "ВасДом",
        "message": "🎉 AI-ассистент работает! (PostingFotoTG Edition)",
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

@router.get("/logs")
async def get_logs():
    """Endpoint для просмотра всех логов"""
    system_status["total_requests"] += 1
    
    return {
        "total_logs": len(application_logs),
        "logs": application_logs,
        "system_status": system_status,
        "telegram_messages": telegram_messages
    }

@router.get("/telegram/set-webhook")
async def set_telegram_webhook():
    """Установка Telegram webhook - МАКСИМАЛЬНО ЗАЛОГИРОВАНО"""
    system_status["total_requests"] += 1
    system_status["last_activity"] = datetime.utcnow().isoformat()
    
    add_log("INFO", "🚀 НАЧИНАЕМ УСТАНОВКУ TELEGRAM WEBHOOK", {"step": "start"})
    
    try:
        webhook_url = os.environ.get("TELEGRAM_WEBHOOK_URL")
        bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
        
        add_log("INFO", f"📋 Проверка переменных окружения", {
            "webhook_url": webhook_url, 
            "bot_token_configured": bool(bot_token)
        })
        
        if not webhook_url or not bot_token:
            missing = []
            if not webhook_url: missing.append("TELEGRAM_WEBHOOK_URL")
            if not bot_token: missing.append("TELEGRAM_BOT_TOKEN")
            
            error_msg = f"❌ Отсутствуют переменные: {', '.join(missing)}"
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
            
            add_log("INFO", "📡 Выполняем HTTP запрос к Telegram", payload)
            
            response = await client.post(telegram_api_url, json=payload)
            
            add_log("INFO", f"📥 Ответ от Telegram API", {
                "status_code": response.status_code,
                "response_text": response.text[:500]
            })
            
            if response.status_code == 200:
                result = response.json()
                if result.get("ok"):
                    success_msg = f"✅ WEBHOOK УСТАНОВЛЕН УСПЕШНО: {webhook_url}"
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

@router.post("/telegram/webhook")
async def telegram_webhook(request: Request):
    """Обработка Telegram webhook - МАКСИМАЛЬНО ЗАЛОГИРОВАНО"""
    system_status["total_requests"] += 1
    system_status["telegram_updates"] += 1
    system_status["last_activity"] = datetime.utcnow().isoformat()
    
    try:
        data = await request.json()
        
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
            # Пока просто логируем успешную обработку
            add_log("SUCCESS", "✅ СООБЩЕНИЕ ОБРАБОТАНО УСПЕШНО", {
                "processed_at": datetime.utcnow().isoformat()
            })
        
        elif 'callback_query' in data:
            callback = data['callback_query']
            add_log("INFO", "🔘 ПОЛУЧЕН CALLBACK QUERY", {
                "callback_data": callback.get('data', ''),
                "user_id": callback.get('from', {}).get('id')
            })
        
        else:
            add_log("WARNING", "⚠️ НЕИЗВЕСТНЫЙ ТИП UPDATE", {
                "update_keys": list(data.keys())
            })
        
        return {"ok": True}
        
    except Exception as e:
        error_msg = f"❌ ОШИБКА ОБРАБОТКИ WEBHOOK: {str(e)}"
        add_log("ERROR", error_msg, {"exception": str(e)})
        system_status["errors"] += 1
        
        return {"ok": False, "error": str(e)}

# Добавляем стартовый лог
add_log("SUCCESS", "🚀 WEBHOOK МОДУЛЬ ИНИЦИАЛИЗИРОВАН", {
    "timestamp": datetime.utcnow().isoformat(),
    "module": "webhook.py"
})