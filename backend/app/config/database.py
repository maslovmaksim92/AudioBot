from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from databases import Database
import os
import logging

logger = logging.getLogger(__name__)

# PostgreSQL для самообучения
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost:5432/vasdom_audio")
ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

# Try to initialize database components
try:
    # Async database
    database = Database(ASYNC_DATABASE_URL)
    
    # SQLAlchemy
    engine = create_async_engine(ASYNC_DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)
    
    DATABASE_AVAILABLE = True
    logger.info("PostgreSQL database components initialized")
except Exception as e:
    logger.warning(f"PostgreSQL not available: {e}")
    database = None
    engine = None
    SessionLocal = None
    DATABASE_AVAILABLE = False

Base = declarative_base()

# Dependency
async def get_database():
    if database is None:
        raise RuntimeError("PostgreSQL database not available")
    return database

async def get_db():
    if SessionLocal is None:
        raise RuntimeError("PostgreSQL database not available")
    async with SessionLocal() as session:
        yield session