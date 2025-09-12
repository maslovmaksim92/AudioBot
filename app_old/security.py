from fastapi import HTTPException, Depends, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import logging
from .config.settings import API_SECRET_KEY, REQUIRE_AUTH_FOR_PUBLIC_API

logger = logging.getLogger(__name__)
security = HTTPBearer(auto_error=False)

async def verify_api_key(
    authorization: Optional[str] = Header(None),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> bool:
    """Verify API key from Authorization header"""
    if not REQUIRE_AUTH_FOR_PUBLIC_API:
        return True  # Authentication disabled
    
    # Check Bearer token
    if credentials:
        if credentials.credentials == API_SECRET_KEY:
            return True
    
    # Check X-API-Key header
    if authorization and authorization == f"Bearer {API_SECRET_KEY}":
        return True
    
    # Check direct API key in custom header
    api_key = Header(None, alias="X-API-Key")
    if api_key == API_SECRET_KEY:
        return True
    
    logger.warning("❌ Invalid API key provided")
    raise HTTPException(
        status_code=401,
        detail="Invalid API key. Provide valid Bearer token or X-API-Key header."
    )

async def telegram_security_check(
    x_telegram_bot_api_secret_token: Optional[str] = Header(None)
) -> bool:
    """Security check for Telegram webhook"""
    # В продакшене можно добавить проверку секретного токена Telegram
    # if x_telegram_bot_api_secret_token != TELEGRAM_SECRET_TOKEN:
    #     raise HTTPException(status_code=403, detail="Invalid Telegram secret token")
    return True

# Dependencies для использования в роутерах
async def require_auth():
    """Dependency для endpoints требующих аутентификации"""
    return await verify_api_key()

async def optional_auth():
    """Dependency для endpoints с опциональной аутентификацией"""
    try:
        return await verify_api_key()
    except HTTPException:
        return False  # Не требуем аутентификацию, просто возвращаем False