"""
Утилиты безопасности - хеширование паролей и JWT токены
"""
import logging
import os

from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from typing import Optional
import jwt

logger = logging.getLogger(__name__)

# Контекст для хеширования паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT signing key. MUST be provided via JWT_SECRET_KEY environment variable.
# The old hard-coded default was public in the repo; falling back to it silently
# would defeat the rotation. We log loudly if the env var is missing so a
# misconfigured deploy is obvious in the journal.
_ENV_SECRET = os.environ.get("JWT_SECRET_KEY", "").strip()
if not _ENV_SECRET:
    logger.error(
        "SECURITY: JWT_SECRET_KEY is not set in the environment. "
        "Falling back to a well-known compromised default — do NOT run this in production. "
        "Add JWT_SECRET_KEY=<random hex> to /opt/audiobot/backend/.env and restart the service."
    )
    _ENV_SECRET = "vasdom-audiobot-secret-key-change-in-production"

SECRET_KEY = _ENV_SECRET
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
    """Декодирует JWT токен. Возвращает None если токен невалидный или истёк."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
