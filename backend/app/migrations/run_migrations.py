"""
Автоматический запуск миграций при старте приложения
"""
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

async def run_migrations(db_pool):
    """
    Выполняет SQL миграции из папки migrations
    
    Args:
        db_pool: asyncpg connection pool
    """
    migrations_dir = Path(__file__).parent
    
    # Список миграций в порядке выполнения
    migrations = [
        "create_cleaning_photos_table.sql",
        "create_house_acts_table.sql",
        "add_telegram_links_to_cleaning_photos.sql",
        "create_plannerka_table.sql",
        "add_meeting_id_to_tasks.sql",
        "add_admin_user.sql",
        "create_call_summaries_table.sql"
    ]
    
    for migration_file in migrations:
        migration_path = migrations_dir / migration_file
        
        if not migration_path.exists():
            logger.warning(f"[migrations] Migration file not found: {migration_file}")
            continue
        
        try:
            # Читаем SQL
            with open(migration_path, 'r', encoding='utf-8') as f:
                sql = f.read()
            
            # Выполняем
            async with db_pool.acquire() as conn:
                await conn.execute(sql)
            
            logger.info(f"[migrations] ✅ Migration executed: {migration_file}")
            
        except Exception as e:
            # Если таблица уже существует - это нормально
            if "already exists" in str(e).lower():
                logger.info(f"[migrations] ⏭️  Migration skipped (already applied): {migration_file}")
            else:
                logger.error(f"[migrations] ❌ Migration failed: {migration_file}, error: {e}")
                raise

    logger.info("[migrations] ✅ All migrations completed")
