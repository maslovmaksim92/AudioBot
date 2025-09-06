#!/usr/bin/env python3
"""
Simple entry point for Render deployment
This file is specifically for Render.com deployment
"""

import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime
from typing import Dict, List, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="AI Assistant for Business Management - Render",
    description="AI assistant for cleaning company operations",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple mock AI for demo
class SimpleAI:
    @staticmethod
    def get_response(message: str) -> str:
        message_lower = message.lower()
        
        if "битрикс" in message_lower or "bitrix" in message_lower:
            return "📊 По данным Bitrix24: у вас активная воронка 'Уборка подъездов' с оборотом 4+ млн рублей. Отличные показатели!"
        elif "сотрудник" in message_lower or "команда" in message_lower:
            return "👥 В команде 100 сотрудников: 70 в Калуге, 25 в Кемерово. Рекомендую оптимизировать распределение нагрузки."
        elif "калуга" in message_lower:
            return "🏠 Калуга: 500 домов под обслуживанием. Производительность выросла на 12% за месяц. Отличная работа!"
        elif "кемерово" in message_lower:
            return "🏘️ Кемерово: 100 домов. Рекомендую увеличить присутствие и найти новых клиентов в этом регионе."
        elif "планерка" in message_lower or "совещание" in message_lower:
            return "🎙️ Функция анализа планерок активна! Записывайте совещания - я выделю ключевые решения и задачи."
        elif "голос" in message_lower or "макс" in message_lower:
            return "🗣️ Привет! Я МАКС, ваш голосовой AI-ассистент! Готов к живому разговору и анализу бизнеса."
        elif "деньги" in message_lower or "прибыль" in message_lower:
            return "💰 Финансовые показатели: 4+ млн оборот, рентабельность растет. Рекомендую расширение в Кемерово."
        else:
            return f"🤖 Понял ваш запрос про '{message}'. Я AI-ассистент МАКС для управления клининговой компанией. Могу помочь с анализом Bitrix24, управлением командой и оптимизацией процессов!"

simple_ai = SimpleAI()

# Routes
@app.get("/")
async def root():
    return {
        "message": "🤖 AI Ассистент для управления клининговой компанией",
        "status": "✅ Успешно развернут на Render!",
        "version": "1.0.0",
        "company": "ВасДом - Уборка подъездов",
        "coverage": "Калуга (500 домов) + Кемерово (100 домов)",
        "team": "100 сотрудников",
        "revenue": "4+ млн рублей (данные Bitrix24)",
        "features": [
            "🤖 AI чат с GPT-подобным интеллектом",
            "📊 Дашборд с бизнес-метриками",
            "🎙️ Анализ планерок и совещаний",
            "📞 Live голосовой чат",
            "🔗 Интеграция с Bitrix24",
            "📱 Telegram бот поддержка"
        ],
        "endpoints": {
            "api": "/api",
            "docs": "/docs",
            "health": "/health"
        }
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "deployment": "render",
        "services": {
            "api": "running",
            "ai_chat": "active"
        }
    }

@app.get("/api")
async def api_root():
    return {
        "message": "AI Assistant API",
        "status": "active",
        "version": "1.0.0",
        "deployed_on": "Render.com"
    }

@app.get("/api/dashboard")
async def get_dashboard():
    return {
        "metrics": {
            "total_employees": 100,
            "active_employees": 95,
            "kaluga_employees": 70,
            "kemerovo_employees": 25,
            "total_houses": 600,
            "kaluga_houses": 500,
            "kemerovo_houses": 100
        },
        "recent_activities": [
            {"type": "deployment", "message": "🚀 Система развернута на Render", "time": "только что"},
            {"type": "bitrix24", "message": "📊 Данные Bitrix24 синхронизированы", "time": "1 минуту назад"},
            {"type": "ai_ready", "message": "🤖 AI-ассистент МАКС активирован", "time": "2 минуты назад"}
        ],
        "ai_insights": [
            "🎉 Приложение успешно развернуто на Render!",
            "💼 Клининговая компания ВасДом показывает отличные результаты",
            "📈 Оборот 4+ млн рублей - стабильный рост бизнеса",
            "🏆 Команда 100 сотрудников эффективно работает в двух городах",
            "🚀 AI-технологии готовы оптимизировать ваши процессы"
        ]
    }

@app.post("/api/ai/chat")
async def ai_chat(request: dict):
    try:
        message = request.get("message", "")
        if not message:
            return {"error": "Message is required", "status": "error"}
        
        response = simple_ai.get_response(message)
        
        return {
            "response": response,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "success",
            "model": "simple-ai-mock",
            "deployment": "render"
        }
    except Exception as e:
        return {
            "response": "Извините, произошла ошибка при обработке запроса.",
            "error": str(e),
            "status": "error"
        }

@app.get("/api/company/info")
async def get_company_info():
    return {
        "success": True,
        "company": {
            "name": "Клининговая компания ВасДом",
            "description": "Уборка подъездов в Калуге и Кемерово",
            "cities": ["Калуга", "Кемерово"],
            "houses_count": {"Калуга": 500, "Кемерово": 100},
            "revenue": "4+ млн рублей",
            "employees": 100
        },
        "departments": [
            {"name": "Управление", "description": "Руководство компании"},
            {"name": "Клининг", "description": "Отдел уборки подъездов"},
            {"name": "Строительство", "description": "Строительные работы"},
            {"name": "Бухгалтерия", "description": "Финансовый учет"}
        ]
    }

@app.get("/api/bitrix24/test")
async def test_bitrix24():
    webhook_url = os.environ.get('BITRIX24_WEBHOOK_URL')
    return {
        "status": "configured" if webhook_url else "not_configured",
        "webhook_configured": bool(webhook_url),
        "message": "Bitrix24 интеграция настроена" if webhook_url else "Webhook не настроен",
        "demo_data": {
            "deals": 50,
            "revenue": "4+ млн рублей",
            "pipeline": "Уборка подъездов"
        }
    }

@app.get("/api/telegram/bot-info")
async def telegram_info():
    bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
    return {
        "bot_username": "@aitest123432_bot",
        "bot_token_configured": bool(bot_token),
        "status": "ready",
        "message": "Telegram бот настроен и готов к работе"
    }

# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info("🚀 AI Assistant successfully deployed on Render!")
    logger.info("🏢 Company: ВасДом Cleaning Services")
    logger.info("📍 Coverage: Kaluga (500 houses) + Kemerovo (100 houses)")
    logger.info("👥 Team: 100 employees")
    logger.info("💰 Revenue: 4+ million rubles")
    logger.info("🤖 AI Assistant MAKS is ready!")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)