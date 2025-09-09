from fastapi import FastAPI, APIRouter, HTTPException, File, UploadFile, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, HTMLResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import os
import uuid
import logging
import asyncio
import json
import httpx
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, String, DateTime, Text, Integer, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from databases import Database

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Setup cloud-friendly logging
log_handlers = [logging.StreamHandler()]

# Добавляем файловое логирование только если возможно
try:
    log_file_path = os.environ.get('LOG_FILE', '/tmp/vasdom_audiobot.log')
    log_handlers.append(logging.FileHandler(log_file_path, encoding='utf-8'))
except Exception as log_error:
    # На Render может не быть прав на запись в /var/log, используем только stdout
    pass

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=log_handlers
)
logger = logging.getLogger(__name__)

# CORS settings - читаем из переменных окружения (УЛУЧШЕНИЕ 1)
CORS_ORIGINS_RAW = os.environ.get('CORS_ORIGINS', 'https://vasdom-audiobot.preview.emergentagent.com,https://audiobot-qci2.onrender.com')
CORS_ORIGINS = [origin.strip() for origin in CORS_ORIGINS_RAW.split(',') if origin.strip()]

# Безопасные дефолтные origins если переменная пустая
if not CORS_ORIGINS:
    CORS_ORIGINS = [
        "https://vasdom-audiobot.preview.emergentagent.com", 
        "https://audiobot-qci2.onrender.com"
    ]

# Frontend redirect URLs - вынос в конфигурацию (УЛУЧШЕНИЕ 7)
FRONTEND_DASHBOARD_URL = os.environ.get(
    'FRONTEND_DASHBOARD_URL', 
    'https://vasdom-audiobot.preview.emergentagent.com'
)

# Security settings (УЛУЧШЕНИЕ 3)
API_SECRET_KEY = os.environ.get('API_SECRET_KEY', 'vasdom-secret-key-change-in-production')
REQUIRE_AUTH_FOR_PUBLIC_API = os.environ.get('REQUIRE_AUTH_FOR_PUBLIC_API', 'false').lower() == 'true'

# Database configuration - PostgreSQL
DATABASE_URL = os.environ.get('DATABASE_URL')

Base = declarative_base()
database = None
engine = None

if DATABASE_URL:
    # Скрываем чувствительные данные в логах
    safe_db_url = DATABASE_URL.replace(DATABASE_URL[DATABASE_URL.find('://')+3:DATABASE_URL.find('@')+1], '://***:***@') if '@' in DATABASE_URL else DATABASE_URL[:30] + '...'
    logger.info(f"🗄️ Database URL: {safe_db_url}")
    
    # PostgreSQL setup
    if DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql+asyncpg://', 1)
    elif DATABASE_URL.startswith('postgresql://') and not DATABASE_URL.startswith('postgresql+asyncpg://'):
        DATABASE_URL = DATABASE_URL.replace('postgresql://', 'postgresql+asyncpg://', 1)
    
    try:
        database = Database(DATABASE_URL)
        logger.info("🐘 PostgreSQL async driver initialized")
        
        # Async engine for PostgreSQL
        engine = create_async_engine(
            DATABASE_URL,
            echo=False,
            future=True,
            pool_pre_ping=True
        )
    except Exception as e:
        logger.error(f"❌ PostgreSQL init error: {e}")
        database = None
        logger.warning("⚠️ Database unavailable - API will work without DB")
else:
    logger.info("📁 No DATABASE_URL - working in API-only mode")

# Database models
class VoiceLogDB(Base):
    __tablename__ = "voice_logs"
    
    id = Column(String, primary_key=True)
    user_message = Column(Text)
    ai_response = Column(Text)
    user_id = Column(String)
    context = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)

class MeetingDB(Base):
    __tablename__ = "meetings"
    
    id = Column(String, primary_key=True)
    title = Column(String)
    transcription = Column(Text)
    summary = Column(Text)
    status = Column(String, default="active")
    created_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime)

class AITaskDB(Base):
    __tablename__ = "ai_tasks"
    
    id = Column(String, primary_key=True)
    title = Column(String)
    description = Column(Text)
    scheduled_time = Column(DateTime)
    recurring = Column(Boolean, default=False)
    status = Column(String, default="pending")
    chat_messages = Column(Text)  # JSON string
    created_at = Column(DateTime, default=datetime.utcnow)

# Security helper functions (УЛУЧШЕНИЕ 3)
async def verify_api_key(authorization: str = None) -> bool:
    """Verify API key from Authorization header"""
    if not REQUIRE_AUTH_FOR_PUBLIC_API:
        return True  # Authentication disabled
    
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
        if token == API_SECRET_KEY:
            return True
    
    logger.warning("❌ Invalid API key provided")
    raise HTTPException(
        status_code=401,
        detail="Invalid API key. Provide valid Bearer token."
    )

# App initialization
app = FastAPI(
    title="VasDom AudioBot API",
    version="3.0.0",
    description="🤖 AI-система управления клининговой компанией"
)

# CORS middleware с обновленной конфигурацией (УЛУЧШЕНИЕ 1)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,  # Теперь читается из переменных окружения
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
logger.info(f"✅ CORS configured for origins: {CORS_ORIGINS}")

# Database initialization
async def init_database():
    """Initialize PostgreSQL database - миграции Alembic (УЛУЧШЕНИЕ 6)"""
    try:
        if database and engine:
            await database.connect()
            logger.info("✅ PostgreSQL connected successfully")
            
            # Tables creation is now handled by Alembic migrations
            # Use 'alembic upgrade head' to create/update tables
            logger.info("ℹ️ Database tables managed by Alembic migrations")
            
            return True
        else:
            logger.info("⚠️ No database configured - working in API-only mode")
            return False
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        return False

async def close_database():
    """Close database connection"""
    if database:
        try:
            await database.disconnect()
            logger.info("✅ Database connection closed")  
        except Exception as e:
            logger.error(f"❌ Database close error: {e}")

# Export app for entry point
__all__ = ["app"]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)