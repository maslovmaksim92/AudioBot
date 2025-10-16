"""
Debug endpoint для просмотра пользователей (только для разработки)
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import logging

from backend.app.config.database import get_db

router = APIRouter(prefix="/debug", tags=["Debug"])
logger = logging.getLogger(__name__)

@router.get("/users")
async def list_all_users(db: AsyncSession = Depends(get_db)):
    """
    Получить список всех пользователей для отладки
    """
    try:
        result = await db.execute(
            text("""
                SELECT id, email, full_name, phone, is_active, brigade_number
                FROM users
                ORDER BY full_name
                LIMIT 50
            """)
        )
        
        users = result.fetchall()
        
        users_list = []
        for row in users:
            users_list.append({
                "id": row[0],
                "email": row[1],
                "full_name": row[2],
                "phone": row[3],
                "is_active": row[4],
                "brigade_number": row[5]
            })
        
        return {
            "total": len(users_list),
            "users": users_list,
            "message": "Попробуйте войти используя email или full_name"
        }
        
    except Exception as e:
        logger.error(f"Error fetching users: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            "error": str(e),
            "message": "Check backend logs for details"
        }
