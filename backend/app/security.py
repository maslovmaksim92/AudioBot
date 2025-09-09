"""
Система безопасности и аутентификации для VasDom AudioBot
Поддерживает API ключи и JWT токены
"""
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import os
import logging

from app.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Bearer token security
security = HTTPBearer(auto_error=False)

async def verify_api_key(credentials: Optional[HTTPAuthorizationCredentials] = Security(security)) -> bool:
    """
    Проверка API ключа
    
    Args:
        credentials: HTTP Authorization credentials
        
    Returns:
        True если авторизация успешна
        
    Raises:
        HTTPException: При ошибке авторизации
    """
    # Если аутентификация отключена, разрешаем доступ
    if not settings.REQUIRE_AUTH_FOR_PUBLIC_API:
        return True
    
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Требуется авторизация",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Проверяем API ключ
    if credentials.credentials != settings.API_SECRET_KEY:
        logger.warning(f"Неверный API ключ: {credentials.credentials[:10]}...")
        raise HTTPException(
            status_code=403,
            detail="Неверный API ключ"
        )
    
    return True

async def verify_admin_access(authorized: bool = Depends(verify_api_key)) -> bool:
    """
    Проверка административного доступа
    """
    if not authorized:
        raise HTTPException(
            status_code=403,
            detail="Требуются права администратора"
        )
    
    return True

# Опциональная авторизация (не выбрасывает исключения)
async def optional_auth(credentials: Optional[HTTPAuthorizationCredentials] = Security(security)) -> bool:
    """Опциональная авторизация без исключений"""
    try:
        return await verify_api_key(credentials)
    except HTTPException:
        return False