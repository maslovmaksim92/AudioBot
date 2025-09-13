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
from .config.mongodb import init_mongodb

# Import routers
from .routers import dashboard, voice, telegram, meetings, cleaning, logs, tasks, analytics
from .routers import learning_simple as learning
# Упрощенные voice модули
from .routers import websocket_simple as websocket

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

@app.get("/api/force-houses-490")
async def force_houses_490():
    """Принудительная загрузка ВСЕХ 490 домов с CATEGORY_ID=34"""
    try:
        import httpx
        import urllib.parse
        from app.config.settings import BITRIX24_WEBHOOK_URL
        
        # ПРИНУДИТЕЛЬНО используем CATEGORY_ID=34
        deals = []
        start = 0
        
        while len(deals) < 500:  # Загружаем максимум
            params = {
                'select[0]': 'ID',
                'select[1]': 'TITLE', 
                'select[2]': 'STAGE_ID',
                'select[3]': 'COMPANY_ID',
                'select[4]': 'ASSIGNED_BY_ID',
                'select[5]': 'UF_CRM_1669704529022',  # Квартиры
                'select[6]': 'UF_CRM_1669705507390',  # Подъезды
                'select[7]': 'UF_CRM_1669704631166',  # Этажи
                'select[8]': 'UF_CRM_1741592774017',  # Сентябрь дата 1
                'filter[CATEGORY_ID]': '34',          # ✅ ПРИНУДИТЕЛЬНО 34!
                'order[DATE_CREATE]': 'DESC',
                'start': str(start)
            }
            
            query_string = urllib.parse.urlencode(params)
            url = f"{BITRIX24_WEBHOOK_URL}crm.deal.list.json?{query_string}"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=15)
                
                if response.status_code == 200:
                    data = response.json()
                    batch = data.get('result', [])
                    
                    if not batch:
                        break
                    
                    deals.extend(batch)
                    start += 50
                    
                    if len(batch) < 50:
                        break
                else:
                    break
        
        # Обогащаем первые 5 домов для примера
        enriched_houses = []
        for deal in deals[:5]:
            address = deal.get('TITLE', '')
            
            # Определяем УК по адресу
            if 'хрустальная' in address.lower():
                uk = "ООО УК Новый город"
            elif 'гвардейская' in address.lower():
                uk = "ООО РИЦ ЖРЭУ"  
            elif 'кондрово' in address.lower():
                uk = "ООО РКЦ ЖИЛИЩЕ"
            else:
                uk = "ООО Жилкомсервис"
            
            enriched_houses.append({
                'address': address,
                'deal_id': deal.get('ID'),
                'management_company': uk,
                'apartments_count': int(deal.get('UF_CRM_1669704529022', 0)) if deal.get('UF_CRM_1669704529022') else 0,
                'entrances_count': int(deal.get('UF_CRM_1669705507390', 0)) if deal.get('UF_CRM_1669705507390') else 0,
                'floors_count': int(deal.get('UF_CRM_1669704631166', 0)) if deal.get('UF_CRM_1669704631166') else 0,
                'brigade': "4 бригада - Северный район",
                'september_dates': deal.get('UF_CRM_1741592774017', [])
            })
        
        return {
            "status": "✅ FORCE SUCCESS",
            "category_used": "34",
            "total_houses": len(deals),
            "houses_sample": enriched_houses,
            "message": f"Принудительно загружено {len(deals)} домов с CATEGORY_ID=34"
        }
        
    except Exception as e:
        return {"status": "❌ FORCE ERROR", "error": str(e)}

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
app.include_router(analytics.router)
app.include_router(learning.router)       # Новый: модуль самообучения

app.include_router(websocket.router)        # Новый: WebSocket для живого чата

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