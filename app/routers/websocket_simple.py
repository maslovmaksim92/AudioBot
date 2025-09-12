import logging
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Set

logger = logging.getLogger(__name__)
router = APIRouter(tags=["websocket"])

# Active WebSocket connections
active_connections: Set[WebSocket] = set()

@router.websocket("/api/live-chat/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.add(websocket)
    
    try:
        logger.info("💬 WebSocket connection accepted")
        
        # Отправляем приветственное сообщение
        await websocket.send_text(json.dumps({
            "type": "system",
            "message": "🚀 Подключение к VasDom AudioBot установлено!"
        }, ensure_ascii=False))
        
        while True:
            # Получаем сообщение от клиента
            data = await websocket.receive_text()
            
            try:
                message_data = json.loads(data)
                logger.info(f"📨 WebSocket received: {message_data}")
                
                if message_data.get("type") == "user_message":
                    user_message = message_data.get("message", "")
                    
                    if user_message.strip():
                        # Простой echo ответ для демонстрации
                        ai_response = f"Получено сообщение: {user_message}"
                        
                        await websocket.send_text(json.dumps({
                            "type": "ai_response",
                            "message": ai_response
                        }, ensure_ascii=False))
                        
                        logger.info(f"🤖 Echo response sent via WebSocket")
                
                elif message_data.get("type") == "ping":
                    # Пинг для поддержания соединения
                    await websocket.send_text(json.dumps({
                        "type": "pong",
                        "timestamp": message_data.get("timestamp")
                    }, ensure_ascii=False))
                    
            except json.JSONDecodeError:
                logger.error(f"❌ Invalid JSON received: {data}")
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Некорректный формат сообщения"
                }, ensure_ascii=False))
                
    except WebSocketDisconnect:
        logger.info("🔌 WebSocket client disconnected")
        active_connections.discard(websocket)
    except Exception as e:
        logger.error(f"❌ WebSocket error: {e}")
        active_connections.discard(websocket)

@router.get("/api/live-chat/status")
async def websocket_status():
    """Статус WebSocket соединений"""
    return {
        "active_connections": len(active_connections),
        "websocket_available": True,
        "ai_service_status": "active"
    }