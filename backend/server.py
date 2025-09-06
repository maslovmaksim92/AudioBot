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


# Define Models
class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class StatusCheckCreate(BaseModel):
    client_name: str

# Add your routes to the router instead of directly to app
@api_router.get("/")
async def root():
    return {"message": "Hello World"}

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.dict()
    status_obj = StatusCheck(**status_dict)
    _ = await db.status_checks.insert_one(status_obj.dict())
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find().to_list(1000)
    return [StatusCheck(**status_check) for status_check in status_checks]

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
