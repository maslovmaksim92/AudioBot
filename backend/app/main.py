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
from .routers import dashboard, voice, telegram, meetings, cleaning, logs, tasks

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=APP_TITLE,
    version=APP_VERSION,
    description=APP_DESCRIPTION
)

# CORS middleware с безопасными настройками для продакшена
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,  # Читается из переменных окружения
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

@app.get("/api/debug-houses")
async def debug_houses_endpoint():
    """Временный endpoint для отладки проблем с домами"""
    try:
        from app.services.bitrix_service import BitrixService
        from app.config.settings import BITRIX24_WEBHOOK_URL
        
        bitrix = BitrixService(BITRIX24_WEBHOOK_URL)
        deals = await bitrix.get_deals_optimized(limit=2)
        
        if not deals:
            return {"error": "No deals loaded", "bitrix_url": BITRIX24_WEBHOOK_URL[:50]}
        
        # Анализируем первую сделку
        first_deal = deals[0]
        
        return {
            "status": "debug_success",
            "version": "DEBUG-v1",
            "total_deals": len(deals),
            "first_deal_analysis": {
                "ID": first_deal.get('ID'),
                "TITLE": first_deal.get('TITLE'),
                "COMPANY_ID": first_deal.get('COMPANY_ID'),
                "COMPANY_TITLE": first_deal.get('COMPANY_TITLE'),
                "ASSIGNED_BY_ID": first_deal.get('ASSIGNED_BY_ID'),
                "ASSIGNED_BY_NAME": first_deal.get('ASSIGNED_BY_NAME'),
                "apartments": first_deal.get('UF_CRM_1669704529022'),
                "entrances": first_deal.get('UF_CRM_1669705507390'),
                "floors": first_deal.get('UF_CRM_1669704631166'),
                "september_date_1": first_deal.get('UF_CRM_1741592774017'),
                "september_type_1": first_deal.get('UF_CRM_1741592855565')
            }
        }
    except Exception as e:
        return {"error": str(e), "status": "debug_failed"}

@app.get("/api/version-check")
async def version_check():
    """Простая проверка версии развернутого кода - FORCE UPDATE v2"""
    return {
        "status": "success",
        "version": "3.0-FIXED-FORCE-UPDATE",
        "build_timestamp": "2025-09-12T09:35:00Z",
        "features": {
            "management_companies_fixed": True,
            "september_schedules": True,
            "490_houses_loading": True,
            "production_debug_endpoints": True,
            "database_independent": True
        },
        "deployment_status": "FORCE UPDATED FOR RENDER"
    }

# Include routers
app.include_router(dashboard.router)
app.include_router(voice.router)
app.include_router(telegram.router)
app.include_router(meetings.router)
app.include_router(cleaning.router)
app.include_router(tasks.router)
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