"""
Конфигурация базы данных - подключение к Yandex PostgreSQL с SSL
"""
import logging
import ssl
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

from .settings import settings

logger = logging.getLogger(__name__)

Base = declarative_base()

def normalize_db_url(url: str) -> str:
    """
    Нормализует URL базы данных для asyncpg
    - Меняет postgresql:// на postgresql+asyncpg://
    - Убирает sslmode из query параметров (asyncpg не поддерживает)
    """
    try:
        if not url:
            return url
            
        url = url.strip().strip("'\"")
        
        # Удаляем префикс psql если есть
        if url.lower().startswith('psql '):
            url = url[5:].strip().strip("'\"")
        
        # Находим начало URL
        for marker in ('postgresql+asyncpg://', 'postgresql://', 'postgres://'):
            idx = url.find(marker)
            if idx > 0:
                url = url[idx:]
                break
        
        # Конвертируем в asyncpg формат
        if url.startswith('postgres://'):
            url = url.replace('postgres://', 'postgresql+asyncpg://', 1)
        elif url.startswith('postgresql://') and not url.startswith('postgresql+asyncpg://'):
            url = url.replace('postgresql://', 'postgresql+asyncpg://', 1)
        elif not url.startswith('postgresql+asyncpg://'):
            url = 'postgresql+asyncpg://' + url.split('://', 1)[-1]
        
        # Убираем sslmode и другие параметры, которые asyncpg не понимает в URL
        parsed = urlparse(url)
        q = dict(parse_qsl(parsed.query, keep_blank_values=True))
        
        # Убираем параметры SSL из URL (они будут переданы через connect_args)
        q.pop('sslmode', None)
        q.pop('sslrequire', None)
        q.pop('ssl', None)
        
        new_query = urlencode(q)
        url = urlunparse((
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            new_query,
            parsed.fragment
        ))
        
        return url
    except Exception as e:
        logger.error(f"Ошибка нормализации DATABASE_URL: {e}")
        return url

# Создаем SSL context для Yandex Cloud PostgreSQL
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

# Создаем движок БД
db_url = normalize_db_url(settings.DATABASE_URL)

# Параметры подключения с SSL для asyncpg
connect_args = {
    "ssl": ssl_context,
    "server_settings": {
        "application_name": "vasdom_audiobot"
    }
}

engine = create_async_engine(
    db_url,
    echo=False,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    connect_args=connect_args
)

# Создаем фабрику сессий
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_db():
    """Dependency для получения сессии БД"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

async def init_db():
    """Инициализация базы данных - создание всех таблиц"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("✅ Database tables created successfully")

# Для работы с asyncpg напрямую (используется в миграциях и Telegram боте)
_db_pool = None

async def get_db_pool():
    """
    Получить asyncpg connection pool
    Используется для прямых SQL запросов в миграциях и Telegram боте
    """
    global _db_pool
    
    if _db_pool is None:
        try:
            import asyncpg
            from .settings import settings
            
            # Парсим DATABASE_URL
            parsed = urlparse(settings.DATABASE_URL)
            
            # Создаем pool с SSL
            _db_pool = await asyncpg.create_pool(
                host=parsed.hostname,
                port=parsed.port or 5432,
                user=parsed.username,
                password=parsed.password,
                database=parsed.path.lstrip('/'),
                ssl=ssl_context,
                min_size=2,
                max_size=10,
                command_timeout=60
            )
            
            logger.info("✅ AsyncPG pool created successfully")
        except Exception as e:
            logger.error(f"❌ Failed to create asyncpg pool: {e}")
            return None
    
    return _db_pool

async def close_db_pool():
    """Закрыть asyncpg connection pool"""
    global _db_pool
    if _db_pool:
        await _db_pool.close()
        _db_pool = None
        logger.info("✅ AsyncPG pool closed")