import logging
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Set
from ..services.ai_service import AIService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["websocket"])

# Initialize AI service
ai_service = AIService()

# Active WebSocket connections
active_connections: Set[WebSocket] = set()
user_connections: Dict[str, WebSocket] = {}

class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.user_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: str = None):
        await websocket.accept()
        self.active_connections.add(websocket)
        if user_id:
            self.user_connections[user_id] = websocket
        logger.info(f"💬 WebSocket connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket, user_id: str = None):
        self.active_connections.discard(websocket)
        if user_id and user_id in self.user_connections:
            del self.user_connections[user_id]
        logger.info(f"💬 WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def send_message(self, websocket: WebSocket, message: dict):
        try:
            await websocket.send_text(json.dumps(message, ensure_ascii=False))
        except Exception as e:
            logger.error(f"❌ Error sending WebSocket message: {e}")
            self.disconnect(websocket)

    async def broadcast(self, message: dict):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message, ensure_ascii=False))
            except Exception as e:
                logger.error(f"❌ Error broadcasting to WebSocket: {e}")
                disconnected.append(connection)
        
        # Clean up disconnected connections
        for conn in disconnected:
            self.active_connections.discard(conn)

manager = ConnectionManager()

@router.websocket("/live-chat/ws")
async def websocket_endpoint(websocket: WebSocket):
    user_id = "live_chat_user"  # Можно получить из query params или headers
    await manager.connect(websocket, user_id)
    
    try:
        # Отправляем приветственное сообщение
        await manager.send_message(websocket, {
            "type": "system",
            "message": "🚀 Подключение к VasDom AudioBot установлено!"
        })
        
        while True:
            # Получаем сообщение от клиента
            data = await websocket.receive_text()
            
            try:
                message_data = json.loads(data)
                logger.info(f"📨 WebSocket received: {message_data}")
                
                if message_data.get("type") == "user_message":
                    user_message = message_data.get("message", "")
                    user_id = message_data.get("user_id", "anonymous")
                    
                    if user_message.strip():
                        # Обрабатываем сообщение через AI
                        try:
                            ai_response = await ai_service.process_message(user_message, user_id)
                            
                            # Отправляем ответ AI клиенту
                            await manager.send_message(websocket, {
                                "type": "ai_response",
                                "message": ai_response
                            })
                            
                            logger.info(f"🤖 AI response sent via WebSocket")
                            
                        except Exception as ai_error:
                            logger.error(f"❌ AI processing error: {ai_error}")
                            await manager.send_message(websocket, {
                                "type": "ai_response",
                                "message": "Извините, произошла ошибка при обработке вашего сообщения. Попробуйте еще раз.",
                                "error": True
                            })
                
                elif message_data.get("type") == "ping":
                    # Пинг для поддержания соединения
                    await manager.send_message(websocket, {
                        "type": "pong",
                        "timestamp": message_data.get("timestamp")
                    })
                    
            except json.JSONDecodeError:
                logger.error(f"❌ Invalid JSON received: {data}")
                await manager.send_message(websocket, {
                    "type": "error",
                    "message": "Некорректный формат сообщения"
                })
                
    except WebSocketDisconnect:
        logger.info("🔌 WebSocket client disconnected")
        manager.disconnect(websocket, user_id)
    except Exception as e:
        logger.error(f"❌ WebSocket error: {e}")
        manager.disconnect(websocket, user_id)

@router.get("/live-chat/status")
async def websocket_status():
    """Статус WebSocket соединений"""
    return {
        "active_connections": len(manager.active_connections),
        "user_connections": len(manager.user_connections),
        "websocket_available": True,
        "ai_service_status": "active"
    }

@router.post("/live-chat/broadcast")
async def broadcast_message(message: dict):
    """Отправить сообщение всем подключенным клиентам"""
    await manager.broadcast({
        "type": "broadcast",
        "message": message.get("text", ""),
        "timestamp": message.get("timestamp")
    })
    
    return {
        "status": "success",
        "recipients": len(manager.active_connections)
    }