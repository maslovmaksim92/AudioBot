"""
API роутер для аутентификации - JWT, регистрация, логин
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import timedelta

from backend.app.config.database import get_db
from backend.app.models.user import User, Role, RoleEnum
from backend.app.schemas.user import UserCreate, UserLogin, UserResponse, TokenResponse
from backend.app.utils.security import hash_password, verify_password, create_access_token
from uuid import uuid4

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """Регистрация нового пользователя"""
    
    # Проверка существования email
    result = await db.execute(select(User).where(User.email == user_data.email))
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email уже зарегистрирован"
        )
    
    # Создание пользователя
    new_user = User(
        id=str(uuid4()),
        email=user_data.email,
        full_name=user_data.full_name,
        phone=user_data.phone if user_data.phone else "",
        password_hash=hash_password(user_data.password),
        brigade_number=user_data.brigade_number if user_data.brigade_number else None,
        is_active=True
    )
    
    # Добавление ролей
    if user_data.roles:
        for role_enum in user_data.roles:
            role_result = await db.execute(select(Role).where(Role.name == role_enum))
            role = role_result.scalar_one_or_none()
            if role:
                new_user.roles.append(role)
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    return new_user

@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin, db: AsyncSession = Depends(get_db)):
    """Вход пользователя (по email или логину)"""
    
    # Поиск пользователя по email или full_name (логину)
    result = await db.execute(
        select(User).where(
            (User.email == credentials.email) | 
            (User.full_name == credentials.email) |
            (User.email.like(f"%{credentials.email}%")) |
            (User.full_name.like(f"%{credentials.email}%"))
        )
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный логин или пароль"
        )
    
    # Проверка пароля
    if not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль"
        )
    
    # Проверка активности
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Пользователь деактивирован"
        )
    
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
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "phone": user.phone,
            "roles": roles,
            "brigade_number": user.brigade_number
        }
    }

@router.get("/me", response_model=UserResponse)
async def get_current_user(
    db: AsyncSession = Depends(get_db),
    # В реальности нужен dependency для извлечения токена из заголовка
):
    """Получение текущего пользователя по токену"""
    # Заглушка - в production добавить OAuth2PasswordBearer
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Используйте /api/auth/login для получения токена"
    )