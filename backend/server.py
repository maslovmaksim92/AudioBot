import os
import asyncio
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from loguru import logger
import sys
from pathlib import Path
from dotenv import load_dotenv

# Import services  
from ai_service import AIService
from telegram_bot import TelegramBotService
from bitrix24_service import Bitrix24Service
from dashboard_service import DashboardService

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Configuration
class Config:
    # Telegram
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_WEBHOOK_URL = os.getenv("TELEGRAM_WEBHOOK_URL", "")
    
    # Bitrix24
    BITRIX24_WEBHOOK_URL = os.getenv("BITRIX24_WEBHOOK_URL", "")
    
    # AI
    EMERGENT_LLM_KEY = os.getenv("EMERGENT_LLM_KEY", "")
    
    # Database
    MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
    DB_NAME = os.getenv("DB_NAME", "vasdom_db")
    
    # App settings
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"
    APP_ENV = os.getenv("APP_ENV", "development")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*")

config = Config()

# Initialize services
ai_service = AIService(config.EMERGENT_LLM_KEY)
bitrix24_service = Bitrix24Service(config.BITRIX24_WEBHOOK_URL)
dashboard_service = DashboardService()

# Global bot service variable
telegram_service = None

# Logging configuration
logger.remove()
logger.add(sys.stderr, level=config.LOG_LEVEL)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    global telegram_service
    
    logger.info("🚀 Starting VasDom AI Assistant...")
    
    # Initialize Telegram service
    if config.TELEGRAM_BOT_TOKEN:
        telegram_service = TelegramBotService(
            token=config.TELEGRAM_BOT_TOKEN,
            webhook_url=config.TELEGRAM_WEBHOOK_URL,
            ai_service=ai_service,
            bitrix24_service=bitrix24_service
        )
        await telegram_service.setup()
        logger.info("✅ Telegram bot initialized")
    else:
        logger.warning("⚠️ Telegram bot token not found")
    
    # Test Bitrix24 connection
    try:
        test_result = await bitrix24_service.test_connection()
        logger.info(f"✅ Bitrix24 connection: {test_result}")
    except Exception as e:
        logger.error(f"❌ Bitrix24 connection failed: {e}")
    
    yield
    
    # Cleanup
    logger.info("🛑 Shutting down VasDom AI Assistant...")
    if telegram_service:
        await telegram_service.cleanup()

# Create FastAPI app
app = FastAPI(
    title="VasDom AI Assistant",
    description="AI-powered assistant with Telegram bot and Bitrix24 integration",
    version="1.0.0",
    lifespan=lifespan
)


# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS.split(','),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root endpoint
@app.get("/")
async def root():
    """Service information endpoint"""
    return {
        "service": "VasDom AI Assistant",
        "version": "1.0.0",
        "status": "running",
        "environment": config.APP_ENV,
        "features": {
            "telegram_bot": bool(config.TELEGRAM_BOT_TOKEN),
            "bitrix24_integration": bool(config.BITRIX24_WEBHOOK_URL),
            "ai_service": bool(config.EMERGENT_LLM_KEY)
        }
    }

# Health check endpoints
@app.get("/health")
async def health_check():
    """Basic health check"""
    return {"status": "healthy", "timestamp": dashboard_service.get_current_time()}

@app.get("/healthz")
async def detailed_health_check():
    """Detailed health check with service status"""
    health_data = {
        "status": "healthy",
        "timestamp": dashboard_service.get_current_time(),
        "services": {}
    }
    
    # Check AI service
    try:
        ai_status = await ai_service.health_check()
        health_data["services"]["ai"] = {"status": "healthy", "details": ai_status}
    except Exception as e:
        health_data["services"]["ai"] = {"status": "unhealthy", "error": str(e)}
    
    # Check Bitrix24 service
    try:
        bitrix_status = await bitrix24_service.test_connection()
        health_data["services"]["bitrix24"] = {"status": "healthy", "details": bitrix_status}
    except Exception as e:
        health_data["services"]["bitrix24"] = {"status": "unhealthy", "error": str(e)}
    
    # Check Telegram service
    if telegram_service:
        try:
            telegram_status = await telegram_service.get_status()
            health_data["services"]["telegram"] = {"status": "healthy", "details": telegram_status}
        except Exception as e:
            health_data["services"]["telegram"] = {"status": "unhealthy", "error": str(e)}
    else:
        health_data["services"]["telegram"] = {"status": "not_configured"}
    
    return health_data

# Dashboard endpoints
@app.get("/dashboard")
async def get_dashboard():
    """Get dashboard data"""
    try:
        dashboard_data = await dashboard_service.get_dashboard_data()
        return dashboard_data
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/logs")
async def get_logs(lines: int = 100):
    """Get system logs"""
    try:
        logs = await dashboard_service.get_recent_logs(lines)
        return {"logs": logs}
    except Exception as e:
        logger.error(f"Logs error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Telegram webhook endpoint
@app.post("/telegram/webhook")
async def telegram_webhook(request: Request):
    """Handle Telegram webhook"""
    if not telegram_service:
        raise HTTPException(status_code=503, detail="Telegram service not initialized")
    
    try:
        update_data = await request.json()
        logger.info(f"📥 Received Telegram update: {update_data.get('update_id', 'unknown')}")
        
        await telegram_service.handle_webhook(update_data)
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"❌ Telegram webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/telegram/set-webhook")
async def set_telegram_webhook():
    """Set Telegram webhook"""
    if not telegram_service:
        raise HTTPException(status_code=503, detail="Telegram service not initialized")
    
    try:
        result = await telegram_service.set_webhook()
        return {"status": "success", "result": result}
    except Exception as e:
        logger.error(f"❌ Set webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Bitrix24 API endpoints
@app.get("/api/bitrix24/test")
async def test_bitrix24():
    """Test Bitrix24 connection"""
    try:
        result = await bitrix24_service.test_connection()
        return result
    except Exception as e:
        logger.error(f"❌ Bitrix24 test error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/bitrix24/deals")
async def get_bitrix24_deals(start: int = 0, limit: int = 50):
    """Get Bitrix24 deals with pagination"""
    try:
        deals = await bitrix24_service.get_deals(start=start, limit=limit)
        return {"deals": deals, "count": len(deals)}
    except Exception as e:
        logger.error(f"❌ Bitrix24 deals error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/bitrix24/cleaning-houses") 
async def get_cleaning_houses():
    """Get addresses from 'Уборка подъездов' pipeline"""
    try:
        houses = await bitrix24_service.get_cleaning_houses()
        return {"houses": houses, "count": len(houses)}
    except Exception as e:
        logger.error(f"❌ Cleaning houses error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# AI Testing endpoint
@app.get("/test-ai")
async def test_ai_generation():
    """Test AI response generation"""
    try:
        test_message = "Привет! Расскажи о услугах ВасДом по уборке подъездов в Калуге"
        response = await ai_service.generate_response(test_message)
        
        return {
            "status": "success",
            "test_message": test_message,
            "ai_response": response,
            "response_length": len(response),
            "model": ai_service.model,
            "provider": ai_service.provider,
            "timestamp": dashboard_service.get_current_time()
        }
    except Exception as e:
        logger.error(f"❌ AI test error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Error handlers
@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"❌ Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": str(exc)}
    )
