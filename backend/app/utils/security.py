"""
Утилиты безопасности - хеширование паролей и JWT токены
"""
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from typing import Optional
import jwt

# Контекст для хеширования паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Секретный ключ для JWT (в продакшене должен быть в .env)
SECRET_KEY = "vasdom-audiobot-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 дней

def hash_password(password: str) -> str:
    """Хеширует пароль"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверяет пароль"""
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Создает JWT токен"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt

def decode_access_token(token: str) -> Optional[dict]:
    """Декодирует JWT токен"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.JWTError:
        return None