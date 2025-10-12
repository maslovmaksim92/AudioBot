from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
from datetime import datetime, timezone, timedelta
import os
import jwt
import logging

logger = logging.getLogger("voice")

router = APIRouter(prefix="/api/voice")

VOICE_JWT_SECRET = os.environ.get('VOICE_JWT_SECRET', None)
VOICE_JWT_ALG = os.environ.get('VOICE_JWT_ALG', 'HS256')

class TokenResponse(BaseModel):
    token: str
    session_id: str
    expires_at: str

@router.post('/token', response_model=TokenResponse)
async def voice_token() -> TokenResponse:
    session_id = os.urandom(8).hex()
    exp = datetime.now(timezone.utc) + timedelta(minutes=5)
    payload = {"sid": session_id, "exp": int(exp.timestamp())}
    if VOICE_JWT_SECRET:
        token = jwt.encode(payload, VOICE_JWT_SECRET, algorithm=VOICE_JWT_ALG)
    else:
        # Без секрета возвращаем псевдо-токен (для простого подключения без проверки)
        token = f"insecure.{session_id}.{int(exp.timestamp())}"
    return TokenResponse(token=token, session_id=session_id, expires_at=exp.isoformat())

@router.websocket('/ws/{session_id}')
async def voice_ws(websocket: WebSocket, session_id: str):
    await websocket.accept()
    try:
        while True:
            msg = await websocket.receive_text()
            # Эхо-ответ: подтверждаем соединение и возвращаем текст
            await websocket.send_json({
                "type": "ok",
                "session_id": session_id,
                "echo": msg
            })
    except WebSocketDisconnect:
        logger.info(f"Voice WS disconnected: {session_id}")
    except Exception as e:
        logger.error(f"Voice WS error [{session_id}]: {e}")
        try:
            await websocket.close()
        except Exception:
            pass