from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
import os
import ssl
import logging
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse

logger = logging.getLogger(__name__)

Base = declarative_base()

def _normalize_db_url(url: str) -> str:
    """Normalize database URL for asyncpg"""
    try:
        if not url:
            return url
        url = url.strip().strip("'\"")
        
        # Remove psql prefix if present
        if url.lower().startswith('psql '):
            url = url[5:].strip().strip("'\"")
        
        # Find the actual URL start
        for marker in ('postgresql+asyncpg://', 'postgresql://', 'postgres://'):
            idx = url.find(marker)
            if idx > 0:
                url = url[idx:]
                break
        
        # Convert to asyncpg
        if url.startswith('postgres://'):
            url = url.replace('postgres://', 'postgresql+asyncpg://', 1)
        elif url.startswith('postgresql://') and not url.startswith('postgresql+asyncpg://'):
            url = url.replace('postgresql://', 'postgresql+asyncpg://', 1)
        elif not url.startswith('postgresql+asyncpg://'):
            url = 'postgresql+asyncpg://' + url.split('://',1)[-1]
        
        # Remove sslmode from URL query params (we handle it in connect_args)
        parsed = urlparse(url)
        q = dict(parse_qsl(parsed.query, keep_blank_values=True))
        q.pop('sslmode', None)
        q.pop('sslrequire', None)
        new_query = urlencode(q)
        url = urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, new_query, parsed.fragment))
        
        return url
    except Exception as e:
        logger.error(f"Error normalizing DB URL: {e}")
        return url

# Get DATABASE_URL from environment
DATABASE_URL = _normalize_db_url(
    os.environ.get('NEON_DATABASE_URL') or 
    os.environ.get('DATABASE_URL') or 
    ''
)

engine = None
AsyncSessionLocal = None

if DATABASE_URL:
    # Create SSL context
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    connect_args = {'ssl': ssl_context}
    
    engine = create_async_engine(
        DATABASE_URL,
        future=True,
        echo=False,
        connect_args=connect_args
    )
    
    AsyncSessionLocal = async_sessionmaker(
        engine,
        expire_on_commit=False,
        class_=AsyncSession
    )
    
    logger.info(f"✅ Database engine created successfully")
else:
    logger.warning("⚠️ DATABASE_URL not set - database features will not work")

async def get_db() -> AsyncSession:
    """Dependency for getting database session"""
    if not AsyncSessionLocal:
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail='Database is not initialized')
    
    async with AsyncSessionLocal() as session:
        yield session

async def init_db():
    """Initialize database tables"""
    if engine:
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("✅ Database tables initialized")
        except Exception as e:
            logger.error(f"❌ Database initialization error: {e}")
            raise
    else:
        logger.warning("⚠️ Database engine not available - skipping initialization")