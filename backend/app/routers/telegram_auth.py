"""
API роутер для аутентификации через Telegram с QR-кодом
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional, Dict
from datetime import datetime, timedelta, timezone
from uuid import uuid4
import logging
import qrcode
import io
import base64

from backend.app.config.database import get_db
from backend.app.models.user import User
from backend.app.utils.security import create_access_token

router = APIRouter(prefix="/telegram-auth", tags=["Telegram Authentication"])
logger = logging.getLogger(__name__)

# Временное хранилище auth кодов (в production использовать Redis)
auth_codes: Dict[str, dict] = {}
# Формат: {
#   "auth_code": {
#       "username": "user123",
#       "telegram_chat_id": None,
#       "confirmed": False,
#       "created_at": datetime,
#       "expires_at": datetime
#   }
# }

class InitAuthRequest(BaseModel):
    username: str  # или email

class InitAuthResponse(BaseModel):
    auth_code: str
    qr_code: str  # base64 изображение QR-кода
    bot_link: str
    expires_in: int  # секунды

class CheckAuthStatusResponse(BaseModel):
    status: str  # "pending", "confirmed", "expired", "invalid"
    access_token: Optional[str] = None
    token_type: Optional[str] = None
    user: Optional[dict] = None

@router.post("/init", response_model=InitAuthResponse)
async def init_telegram_auth(
    request: InitAuthRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Шаг 1: Инициализация входа через Telegram
    - Проверяет существование пользователя
    - Генерирует auth_code
    - Создает QR-код со ссылкой на бота
    """
    try:
        # Проверяем существование пользователя (по username или email)
        result = await db.execute(
            select(User).where(
                (User.email == request.username) | (User.full_name == request.username)
            )
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Пользователь не найден"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Пользователь деактивирован"
            )
        
        # Генерируем уникальный код
        auth_code = str(uuid4())
        
        # Сохраняем в хранилище
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)
        auth_codes[auth_code] = {
            "username": request.username,
            "user_id": user.id,
            "telegram_chat_id": None,
            "confirmed": False,
            "created_at": datetime.now(timezone.utc),
            "expires_at": expires_at
        }
        
        # Получаем имя бота из переменной окружения
        import os
        BOT_USERNAME = os.getenv("TELEGRAM_BOT_USERNAME")
        
        if not BOT_USERNAME:
            logger.error("❌ TELEGRAM_BOT_USERNAME not set in environment variables!")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Telegram bot username not configured. Please contact administrator."
            )
        
        logger.info(f"✅ Using bot: @{BOT_USERNAME}")
        
        # Создаем deep link для бота
        bot_link = f"https://t.me/{BOT_USERNAME}?start=AUTH_{auth_code}"
        
        # Генерируем QR-код
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(bot_link)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Конвертируем в base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        qr_code_base64 = base64.b64encode(buffer.read()).decode('utf-8')
        
        logger.info(f"Auth initiated for user: {request.username}, code: {auth_code}")
        
        return InitAuthResponse(
            auth_code=auth_code,
            qr_code=f"data:image/png;base64,{qr_code_base64}",
            bot_link=bot_link,
            expires_in=300  # 5 минут
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error initiating Telegram auth: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка инициализации входа: {str(e)}"
        )

@router.get("/status/{auth_code}", response_model=CheckAuthStatusResponse)
async def check_auth_status(
    auth_code: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Шаг 3: Проверка статуса подтверждения
    - Frontend опрашивает этот endpoint
    - Возвращает токен после подтверждения
    """
    try:
        # Проверяем существование кода
        if auth_code not in auth_codes:
            return CheckAuthStatusResponse(status="invalid")
        
        auth_data = auth_codes[auth_code]
        
        # Проверяем срок действия
        if datetime.now(timezone.utc) > auth_data["expires_at"]:
            del auth_codes[auth_code]
            return CheckAuthStatusResponse(status="expired")
        
        # Проверяем подтверждение
        if not auth_data["confirmed"]:
            return CheckAuthStatusResponse(status="pending")
        
        # Подтверждено! Создаем токен
        user_id = auth_data["user_id"]
        
        # Загружаем пользователя
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            return CheckAuthStatusResponse(status="invalid")
        
        # Получение ролей
        roles = [role.name.value for role in user.roles]
        
        # Создание токена
        access_token = create_access_token(
            data={
                "sub": user.email,
                "user_id": user.id,
                "roles": roles
            }
        )
        
        # Удаляем использованный код
        del auth_codes[auth_code]
        
        logger.info(f"Auth confirmed for user: {user.email}")
        
        return CheckAuthStatusResponse(
            status="confirmed",
            access_token=access_token,
            token_type="bearer",
            user={
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "phone": user.phone,
                "roles": roles,
                "brigade_number": user.brigade_number
            }
        )
        
    except Exception as e:
        logger.error(f"Error checking auth status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка проверки статуса: {str(e)}"
        )

@router.post("/confirm/{auth_code}")
async def confirm_auth(
    auth_code: str,
    telegram_chat_id: int
):
    """
    Шаг 2: Подтверждение входа (вызывается Telegram ботом)
    """
    try:
        if auth_code not in auth_codes:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Код не найден"
            )
        
        auth_data = auth_codes[auth_code]
        
        # Проверяем срок действия
        if datetime.now(timezone.utc) > auth_data["expires_at"]:
            del auth_codes[auth_code]
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail="Код истёк"
            )
        
        # Подтверждаем
        auth_data["confirmed"] = True
        auth_data["telegram_chat_id"] = telegram_chat_id
        
        logger.info(f"Auth confirmed: {auth_code} by Telegram chat {telegram_chat_id}")
        
        return {"success": True, "message": "Вход подтверждён"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error confirming auth: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка подтверждения: {str(e)}"
        )

@router.post("/cancel/{auth_code}")
async def cancel_auth(auth_code: str):
    """
    Отмена входа (вызывается Telegram ботом при отказе)
    """
    if auth_code in auth_codes:
        del auth_codes[auth_code]
        logger.info(f"Auth cancelled: {auth_code}")
    
    return {"success": True, "message": "Вход отменён"}
