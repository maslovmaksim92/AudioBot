import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, HTMLResponse
import json

# Import configuration
from .config.settings import (
    APP_TITLE, APP_VERSION, APP_DESCRIPTION, 
    CORS_ORIGINS, FRONTEND_DASHBOARD_URL
)
from .config.database import init_database, close_database

# Import routers
from .routers import dashboard, voice, telegram, meetings, cleaning, logs
from .routers import websocket, realtime_voice

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=APP_TITLE,
    version=APP_VERSION,
    description=APP_DESCRIPTION
)

# CORS middleware с обновленной конфигурацией
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,  # Теперь читается из переменных окружения
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
logger.info(f"✅ CORS configured for origins: {CORS_ORIGINS}")

# Dashboard Routes - редирект на конфигурируемый URL
@app.get("/", response_class=HTMLResponse)  
async def root_redirect():
    """Redirect root to React dashboard"""
    return RedirectResponse(url=FRONTEND_DASHBOARD_URL, status_code=302)

@app.get("/dashbord", response_class=HTMLResponse)
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_redirect():
    """Redirect to React VasDom AudioBot Dashboard"""
    return RedirectResponse(url=FRONTEND_DASHBOARD_URL, status_code=302)

# Include routers
app.include_router(dashboard.router)
app.include_router(voice.router)
app.include_router(websocket.router)
app.include_router(realtime_voice.router)
app.include_router(telegram.router)
app.include_router(meetings.router)
app.include_router(cleaning.router)
app.include_router(logs.router)

logger.info("✅ All routers included")

# WebSocket endpoint для живого разговора
@app.websocket("/api/live-chat/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("💬 WebSocket connection accepted")
    
    try:
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
                        try:
                            # Используем реальный AI сервис
                            from .services.ai_service import AIService
                            ai_service = AIService()
                            ai_response = await ai_service.process_message(user_message, "live_chat_user")
                        except Exception as ai_error:
                            logger.error(f"❌ AI service error: {ai_error}")
                            ai_response = f"AI ответ на: '{user_message}'. Это живой разговор с VasDom AI! (Fallback режим)"
                        
                        # Отправляем ответ AI клиенту
                        await websocket.send_text(json.dumps({
                            "type": "ai_response", 
                            "message": ai_response
                        }, ensure_ascii=False))
                        
                        logger.info(f"🤖 AI response sent via WebSocket")
                        
            except json.JSONDecodeError:
                logger.error(f"❌ Invalid JSON received: {data}")
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Некорректный формат сообщения"
                }, ensure_ascii=False))
                
    except WebSocketDisconnect:
        logger.info("🔌 WebSocket client disconnected")
    except Exception as e:
        logger.error(f"❌ WebSocket error: {e}")

@app.get("/api/live-chat/status")
async def websocket_status():
    """Статус WebSocket соединений"""
    return {
        "websocket_available": True,
        "ai_service_status": "active",
        "live_chat_ready": True
    }

# Startup/Shutdown events
@app.on_event("startup")
async def startup():
    logger.info("🚀 VasDom AudioBot starting...")
    db_success = await init_database()
    if db_success:
        logger.info("🐘 PostgreSQL database ready")
    else:
        logger.warning("⚠️ Database unavailable - API will work with limited functionality")
    logger.info("✅ VasDom AudioBot started successfully")

@app.on_event("shutdown")
async def shutdown():
    logger.info("🛑 VasDom AudioBot shutting down...")
    await close_database()
    logger.info("👋 Shutdown complete")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)