"""
Вспомогательные зависимости для аутентификации и RBAC
"""
from typing import Optional
from fastapi import Header, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.utils.security import decode_access_token
from backend.app.config.database import get_db
from backend.app.models.user import User, RoleEnum

class CurrentUser:
    id: str
    email: str
    roles: list[str]
    brigade_number: Optional[str]

    def __init__(self, id: str, email: str, roles: list[str], brigade_number: Optional[str]):
        self.id = id
        self.email = email
        self.roles = roles
        self.brigade_number = brigade_number

    def has_role(self, role: RoleEnum) -> bool:
        return role.value in (self.roles or [])

    def is_brigade(self) -> bool:
        return RoleEnum.BRIGADE.value in (self.roles or [])

    def is_presentation(self) -> bool:
        return RoleEnum.PRESENTATION.value in (self.roles or [])

async def get_current_user_optional(
    authorization: Optional[str] = Header(default=None),
    db: AsyncSession = Depends(get_db)
) -> Optional[CurrentUser]:
    """
    Извлекает пользователя из токена, если заголовок Authorization присутствует.
    Если токен отсутствует/некорректен — возвращает None (эндпоинт может работать публично).
    """
    if not authorization:
        return None
    try:
        scheme, token = authorization.split(" ", 1)
        if scheme.lower() != "bearer":
            return None
    except Exception:
        return None

    payload = decode_access_token(token)
    if not payload:
        return None
    user_id = payload.get("user_id")
    if not user_id:
        return None

    # Загрузка пользователя из БД
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        return None

    roles = [r.name.value for r in (user.roles or [])]
    return CurrentUser(id=user.id, email=user.email, roles=roles, brigade_number=user.brigade_number)


async def get_current_user(
    authorization: Optional[str] = Header(default=None),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Извлекает пользователя из токена. Требует авторизацию.
    Выбрасывает 401 если токен отсутствует или некорректен.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    
    try:
        scheme, token = authorization.split(" ", 1)
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid authentication scheme")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid authorization header format")

    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    # Загрузка пользователя из БД
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user
