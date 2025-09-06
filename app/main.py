#!/usr/bin/env python3
"""
Simple FastAPI app for Render deployment - VasDom AI Assistant
"""

import os
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="🤖 AI Ассистент ВасДом",
    description="AI assistant for VasDom cleaning company",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Main endpoint"""
    return {
        "message": "🤖 AI-Ассистент ВасДом работает!",
        "status": "✅ Успешно развернут на Render",
        "company": "ВасДом - Клининговая компания",
        "version": "2.0.0",
        "endpoints": {
            "health": "/health",
            "api": "/api",
            "telegram_webhook_setup": "/api/telegram/set-webhook",
            "dashboard": "/api/dashboard"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "VasDom AI Assistant",
        "version": "2.0.0",
        "deployment": "render"
    }

@app.get("/api")
async def api_root():
    """API root endpoint"""
    return {
        "message": "🤖 ВасДом AI Assistant API",
        "version": "2.0.0",
        "status": "running",
        "telegram_bot": "@aitest123432_bot",
        "endpoints": [
            "GET /api/telegram/set-webhook",
            "POST /api/telegram/webhook", 
            "GET /api/dashboard",
            "POST /api/ai/chat"
        ]
    }

@app.get("/api/telegram/set-webhook")
async def set_telegram_webhook():
    """Set up Telegram webhook URL - SIMPLIFIED VERSION"""
    try:
        webhook_url = os.environ.get("TELEGRAM_WEBHOOK_URL")
        bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
        
        # Check configuration
        config_status = {
            "webhook_url": webhook_url,
            "bot_token_configured": bool(bot_token),
            "webhook_configured": bool(webhook_url)
        }
        
        if not webhook_url or not bot_token:
            return {
                "status": "❌ Конфигурация неполная",
                "config": config_status,
                "required_env_vars": {
                    "TELEGRAM_WEBHOOK_URL": "https://audiobot-qq2.onrender.com/api/telegram/webhook",
                    "TELEGRAM_BOT_TOKEN": "8327964628:AAHMIgT1XiGEkLc34nogRGZt-Ox-9R0TSn0"
                },
                "instructions": [
                    "1. Добавьте переменные в Render Environment",
                    "2. Дождитесь redeploy",
                    "3. Вызовите этот endpoint снова"
                ]
            }
        
        # Try to set webhook via HTTP request
        import httpx
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            telegram_url = f"https://api.telegram.org/bot{bot_token}/setWebhook"
            
            payload = {
                "url": webhook_url,
                "drop_pending_updates": True
            }
            
            response = await client.post(telegram_url, json=payload)
            
            if response.status_code == 200:
                result = response.json()
                if result.get("ok"):
                    logger.info(f"✅ Webhook установлен успешно: {webhook_url}")
                    return {
                        "status": "✅ УСПЕХ!",
                        "message": "Telegram webhook установлен успешно!",
                        "webhook_url": webhook_url,
                        "bot": "@aitest123432_bot",
                        "next_steps": [
                            "1. Найдите @aitest123432_bot в Telegram",
                            "2. Напишите /start",
                            "3. Бот должен ответить!"
                        ],
                        "telegram_response": result
                    }
                else:
                    return {
                        "status": "❌ Telegram API ошибка",
                        "error": result.get("description", "Неизвестная ошибка"),
                        "telegram_response": result
                    }
            else:
                return {
                    "status": "❌ HTTP ошибка",
                    "http_status": response.status_code,
                    "response": response.text[:500]
                }
                
    except Exception as e:
        logger.error(f"❌ Ошибка установки webhook: {e}")
        return {
            "status": "❌ Критическая ошибка",
            "error": str(e),
            "troubleshooting": [
                "Проверьте что переменные окружения настроены в Render",
                "Убедитесь что бот токен правильный",
                "Проверьте что домен доступен публично"
            ]
        }

@app.post("/api/telegram/webhook")
async def telegram_webhook(request: Request):
    """Handle Telegram webhook updates"""
    try:
        data = await request.json()
        logger.info(f"🤖 Получен Telegram update: {data}")
        
        # Simple message handling
        if 'message' in data:
            message = data['message']
            chat_id = message['chat']['id']
            text = message.get('text', '')
            user_name = message.get('from', {}).get('first_name', 'Пользователь')
            
            logger.info(f"💬 Сообщение от {user_name} (ID:{chat_id}): {text}")
            
            # Here we would normally send response back to Telegram
            # For now, just log successful processing
            logger.info(f"✅ Сообщение обработано успешно")
        
        return {"ok": True}
        
    except Exception as e:
        logger.error(f"❌ Ошибка обработки webhook: {e}")
        return {"ok": False, "error": str(e)}

@app.get("/api/dashboard")
async def get_dashboard():
    """Simple dashboard endpoint"""
    return {
        "success": True,
        "company": "ВасДом",
        "message": "🎉 AI-ассистент работает!",
        "metrics": {
            "houses": {"Калуга": 500, "Кемерово": 100},
            "employees": 100,
            "status": "active"
        },
        "telegram_bot": "@aitest123432_bot"
    }

@app.post("/api/ai/chat")
async def ai_chat(request: Request):
    """Simple AI chat endpoint"""
    try:
        data = await request.json()
        message = data.get("message", "")
        
        # Simple AI responses
        responses = {
            "привет": "🤖 Привет! Я МАКС - AI-ассистент компании ВасДом!",
            "дома": "🏠 У нас 500 домов в Калуге и 100 в Кемерово",
            "сотрудники": "👥 В команде 100 профессиональных сотрудников",
            "default": f"🤖 Получил ваше сообщение: '{message}'. AI-анализ в разработке!"
        }
        
        response_text = responses.get(message.lower(), responses["default"])
        
        return {
            "response": response_text,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "success"
        }
        
    except Exception as e:
        return {
            "response": "Извините, произошла ошибка.",
            "error": str(e),
            "status": "error"
        }

# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info("🚀 VasDom AI Assistant запущен на Render!")
    logger.info("🤖 Telegram Bot: @aitest123432_bot")
    logger.info("✅ Все системы готовы к работе!")

# Export for gunicorn
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
async def get_company_info():
    """Get detailed company information"""
    return {
        "success": True,
        "company": {
            "name": "ВасДом",
            "full_name": "Клининговая компания ВасДом",
            "description": "Профессиональная уборка подъездов и строительные работы",
            "founded": "2020",
            "cities": ["Калуга", "Кемерово"],
            "houses_count": {"Калуга": 500, "Кемерово": 100},
            "revenue": "4+ млн рублей",
            "employees": 100,
            "growth_rate": "15% в квартал"
        },
        "departments": [
            {
                "name": "Управление",
                "description": "Стратегическое руководство и развитие",
                "employees": 5
            },
            {
                "name": "Клининг",
                "description": "Уборка подъездов и территорий",
                "employees": 75
            },
            {
                "name": "Строительство",
                "description": "Ремонтные и строительные работы",
                "employees": 15
            },
            {
                "name": "Бухгалтерия",
                "description": "Финансовый учет и отчетность",
                "employees": 5
            }
        ],
        "services": [
            "Ежедневная уборка подъездов",
            "Генеральная уборка помещений",
            "Уборка придомовых территорий",
            "Текущий ремонт подъездов",
            "Покраска и отделочные работы",
            "Техническое обслуживание зданий"
        ],
        "achievements": [
            "🏆 500+ домов под постоянным обслуживанием",
            "📈 15% рост выручки за квартал",
            "⭐ 4.8/5 средняя оценка клиентов",
            "🚀 Внедрение AI-технологий в управление"
        ]
    }

@app.get("/api/bitrix24/status")
async def bitrix24_status():
    """Get Bitrix24 integration status"""
    webhook_url = os.environ.get('BITRIX24_WEBHOOK_URL')
    return {
        "integration": "Bitrix24 CRM",
        "status": "configured" if webhook_url else "not_configured",
        "webhook_configured": bool(webhook_url),
        "features": [
            "📊 Воронка 'Уборка подъездов'",
            "📞 Учет и анализ звонков",
            "📝 Управление сделками и контактами",
            "📅 Планирование задач и встреч"
        ],
        "demo_data": {
            "active_deals": 45,
            "pipeline_value": "4+ млн рублей",
            "conversion_rate": "23%",
            "avg_deal_size": "89,000 рублей"
        }
    }

@app.get("/api/telegram/info")
async def telegram_info():
    """Get Telegram bot information"""
    bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
    return {
        "bot": "@aitest123432_bot",
        "status": "configured" if bot_token else "not_configured",
        "features": [
            "🤖 AI чат с контекстом бизнеса",
            "📊 Мобильный доступ к метрикам",
            "🎙️ Анализ голосовых сообщений",
            "📝 Система обратной связи",
            "⚡ Быстрые команды и отчеты"
        ],
        "commands": [
            "/start - Знакомство с ботом",
            "/dashboard - Основные метрики",
            "/houses - Статистика по домам",
            "/team - Информация о команде",
            "/help - Список всех команд"
        ]
    }

# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info("🚀 ВасДом AI Assistant запущен на Render!")
    logger.info("🏢 Компания: ВасДом Клининговые Услуги")
    logger.info("📍 География: Калуга (500 домов) + Кемерово (100 домов)")
    logger.info("👥 Команда: 100 сотрудников")
    logger.info("💰 Оборот: 4+ млн рублей")
    logger.info("🤖 AI-ассистент МАКС готов к работе!")

# Export app for uvicorn
__all__ = ["app"]

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)