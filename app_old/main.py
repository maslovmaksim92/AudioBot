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
from .routers import dashboard, voice, telegram, meetings, cleaning, logs, analytics

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
app.include_router(telegram.router)
app.include_router(meetings.router)
app.include_router(cleaning.router)
app.include_router(logs.router)
app.include_router(analytics.router)

logger.info("✅ All routers included")

# Test analytics endpoint directly in main.py
@app.get("/api/analytics-test")
async def analytics_test():
    """Test analytics endpoint"""
    return {"status": "success", "message": "Analytics endpoint working!"}

# DIRECT Bitrix24 fields debug endpoint
@app.get("/api/bitrix-raw-debug")
async def bitrix_raw_debug():
    """Debug endpoint for raw Bitrix24 data analysis"""
    try:
        from .services.bitrix_service import BitrixService
        from .config.settings import BITRIX24_WEBHOOK_URL
        
        bitrix = BitrixService(BITRIX24_WEBHOOK_URL)
        
        # Получаем ОДНУ сделку со ВСЕМИ полями для анализа
        import httpx
        import urllib.parse
        
        params = {
            'select[0]': 'ID',
            'select[1]': 'TITLE', 
            'select[2]': 'COMPANY_ID',
            'select[3]': 'ASSIGNED_BY_ID',
            'select[4]': 'UF_CRM_1669704529022',   # Квартиры
            'select[5]': 'UF_CRM_1669705507390',   # Подъезды
            'select[6]': 'UF_CRM_1669704631166',   # Этажи
            'select[7]': 'UF_CRM_1741592855565',   # Тип уборки 1
            'select[8]': 'UF_CRM_1741592945060',   # Тип уборки 2
            'filter[CATEGORY_ID]': '34',
            'start': '0'
        }
        
        query_string = urllib.parse.urlencode(params)
        url = f"{BITRIX24_WEBHOOK_URL}crm.deal.list.json?{query_string}"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('result') and len(data['result']) > 0:
                    first_deal = data['result'][0]
                    
                    return {
                        "status": "success",
                        "webhook_url": BITRIX24_WEBHOOK_URL[:30] + "...",
                        "deal_count": len(data['result']),
                        "first_deal_raw": first_deal,
                        "key_fields_analysis": {
                            "ID": first_deal.get('ID', 'MISSING'),
                            "TITLE": first_deal.get('TITLE', 'MISSING'),
                            "COMPANY_ID": first_deal.get('COMPANY_ID', 'MISSING'),
                            "ASSIGNED_BY_ID": first_deal.get('ASSIGNED_BY_ID', 'MISSING'),
                            "apartments": first_deal.get('UF_CRM_1669704529022', 'MISSING'),
                            "entrances": first_deal.get('UF_CRM_1669705507390', 'MISSING'),
                            "floors": first_deal.get('UF_CRM_1669704631166', 'MISSING'),
                            "cleaning_type_1": first_deal.get('UF_CRM_1741592855565', 'MISSING'),
                            "cleaning_type_2": first_deal.get('UF_CRM_1741592945060', 'MISSING')
                        },
                        "timestamp": "2025-09-12T16:45:00Z"
                    }
                else:
                    return {"status": "error", "message": "No deals found"}
            else:
                return {"status": "error", "message": f"HTTP {response.status_code}"}
                
    except Exception as e:
        return {"status": "error", "message": str(e)}

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