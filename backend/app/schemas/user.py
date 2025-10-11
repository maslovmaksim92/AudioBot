"""
Pydantic схемы для пользователей и аутентификации (логины могут быть без домена)
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from backend.app.models.user import RoleEnum

class UserBase(BaseModel):
    """Базовая схема пользователя"""
    email: str  # логин может быть без домена (например, m.masl@)
    full_name: str
    phone: Optional[str] = ""

class UserCreate(UserBase):
    """Схема создания пользователя"""
    password: str = Field(..., min_length=6)
    roles: List[RoleEnum] = []
    brigade_number: Optional[str] = None

class UserLogin(BaseModel):
    """Схема входа пользователя"""
    email: str  # допускаем логин без домена
    password: str

class UserResponse(UserBase):
    """Схема ответа с данными пользователя"""
    id: str
    roles: List[str] = []
    brigade_number: Optional[str] = None
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True
        arbitrary_types_allowed = True
        
    @classmethod
    def from_orm(cls, user):
        """Преобразование ORM модели в Pydantic схему"""
        data = {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "phone": user.phone,
            "roles": [role.name.value for role in user.roles],
            "brigade_number": user.brigade_number,
            "is_active": user.is_active,
            "created_at": user.created_at
        }
        return cls(**data)

class UserInToken(BaseModel):
    """Данные пользователя в токене"""
    id: str
    email: str
    full_name: str
    phone: str
    roles: List[str]
    brigade_number: Optional[str] = None

class TokenResponse(BaseModel):
    """Схема ответа с токеном"""
    access_token: str
    token_type: str = "bearer"
    user: UserInToken

class UserUpdate(BaseModel):
    """Схема обновления пользователя"""
    full_name: Optional[str] = None
    phone: Optional[str] = None
    password: Optional[str] = None
    roles: Optional[List[RoleEnum]] = None
    brigade_number: Optional[str] = None
    is_active: Optional[bool] = None