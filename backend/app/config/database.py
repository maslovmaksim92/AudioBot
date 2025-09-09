from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from databases import Database
import os

# PostgreSQL для самообучения
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost:5432/vasdom_audio")
ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

# Async database
database = Database(ASYNC_DATABASE_URL)

# SQLAlchemy
engine = create_async_engine(ASYNC_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)

Base = declarative_base()

# Dependency
async def get_database():
    return database

async def get_db():
    async with SessionLocal() as session:
        yield session