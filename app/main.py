import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, HTMLResponse

# Import configuration
from .config.settings import (
    APP_TITLE, APP_VERSION, APP_DESCRIPTION, 
    CORS_ORIGINS, FRONTEND_DASHBOARD_URL
)
from .config.database import init_database, close_database

# Import routers
from .routers import dashboard, voice, telegram, meetings, cleaning, logs
from .routers import websocket

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
app.include_router(telegram.router)
app.include_router(meetings.router)
app.include_router(cleaning.router)
app.include_router(logs.router)

logger.info("✅ All routers included")

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