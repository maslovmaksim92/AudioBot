import os
import logging
from pathlib import Path
from dotenv import load_dotenv
from databases import Database
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import create_async_engine

# Load environment variables
ROOT_DIR = Path(__file__).parent.parent.parent
load_dotenv(ROOT_DIR / '.env')

logger = logging.getLogger(__name__)

# Database configuration - ТОЛЬКО PostgreSQL или None
DATABASE_URL = os.environ.get('DATABASE_URL')

Base = declarative_base()
database = None
engine = None

if DATABASE_URL:
    # Скрываем чувствительные данные в логах
    safe_db_url = DATABASE_URL.replace(DATABASE_URL[DATABASE_URL.find('://')+3:DATABASE_URL.find('@')+1], '://***:***@') if '@' in DATABASE_URL else DATABASE_URL[:30] + '...'
    logger.info(f"🗄️ Database URL: {safe_db_url}")
    
    # ТОЛЬКО PostgreSQL
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

async def init_database():
    """Initialize PostgreSQL database"""
    try:
        if database and engine:
            await database.connect()
            logger.info("✅ PostgreSQL connected successfully")
            
            # Create tables
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("✅ Database tables created")
            
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