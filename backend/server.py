from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Dict, Any
import uuid
from datetime import datetime
from bitrix_service import bitrix_service

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection (optional - для логов и кеша)
try:
    mongo_url = os.environ.get('MONGO_URL')
    if mongo_url:
        client = AsyncIOMotorClient(mongo_url)
        db = client[os.environ.get('DB_NAME', 'audiobot')]
        logger.info("MongoDB подключен")
    else:
        client = None
        db = None
        logger.info("MongoDB не настроен - работаем без БД")
except Exception as e:
    logger.warning(f"Ошибка подключения к MongoDB: {e}")
    client = None
    db = None

# Create the main app without a prefix
app = FastAPI(
    title="AudioBot API",
    description="API для интеграции с Bitrix24 и управления домами",
    version="1.0"
)

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Define Models
class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class StatusCheckCreate(BaseModel):
    client_name: str

class HouseResponse(BaseModel):
    id: str
    address: str
    apartments: int
    entrances: int
    floors: int
    management_company: str
    september_schedule: str

# Add your routes to the router instead of directly to app
@api_router.get("/")
async def root():
    return {"message": "AudioBot API v1.0", "status": "working"}

@api_router.get("/health")
async def health_check():
    """Проверка состояния API и интеграции с Bitrix24"""
    bitrix_status = await bitrix_service.test_connection()
    
    return {
        "api_status": "healthy",
        "bitrix_integration": bitrix_status,
        "timestamp": datetime.now().isoformat(),
        "database": "connected" if db else "disabled"
    }

# ========== BITRIX24 ENDPOINTS ==========

@api_router.get("/cleaning/houses")
async def get_houses(limit: int = 500):
    """Получение списка домов из Bitrix24 CRM"""
    try:
        houses = await bitrix_service.get_houses(limit)
        return {
            "status": "success", 
            "houses": houses,
            "total": len(houses),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Ошибка загрузки домов: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка загрузки домов: {str(e)}")

@api_router.get("/dashboard/employees")
async def get_employees():
    """Получение списка сотрудников из Bitrix24"""
    try:
        employees = await bitrix_service.get_employees()
        return {
            "status": "success",
            "employees": employees, 
            "total": len(employees),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Ошибка загрузки сотрудников: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка загрузки сотрудников: {str(e)}")

@api_router.get("/dashboard/departments")
async def get_departments():
    """Получение списка подразделений из Bitrix24"""
    try:
        departments = await bitrix_service.get_departments()
        return {
            "status": "success",
            "departments": departments,
            "total": len(departments), 
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Ошибка загрузки подразделений: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка загрузки подразделений: {str(e)}")

@api_router.get("/dashboard/statistics")
async def get_statistics():
    """Получение общей статистики для дашборда"""
    try:
        stats = await bitrix_service.get_statistics()
        return {
            "status": "success",
            "statistics": stats,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Ошибка загрузки статистики: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка загрузки статистики: {str(e)}")

# ========== LEGACY ENDPOINTS ==========

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    """Создание записи о проверке статуса (требует MongoDB)"""
    if not db:
        raise HTTPException(status_code=503, detail="База данных не настроена")
    
    status_dict = input.dict()
    status_obj = StatusCheck(**status_dict)
    _ = await db.status_checks.insert_one(status_obj.dict())
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    """Получение всех записей о проверке статуса (требует MongoDB)"""
    if not db:
        raise HTTPException(status_code=503, detail="База данных не настроена")
    
    cursor = db.status_checks.find({})
    status_checks = []
    async for document in cursor:
        status_checks.append(StatusCheck(**document))
    return status_checks

# Include the API router in the main app
app.include_router(api_router)

# Add CORS middleware
cors_origins = os.environ.get('CORS_ORIGINS', '*').split(',')
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root endpoint (без префикса /api)
@app.get("/")
async def root_redirect():
    return {"message": "AudioBot API", "documentation": "/docs", "health": "/api/health"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
async def get_status_checks():
    status_checks = await db.status_checks.find().to_list(1000)
    return [StatusCheck(**status_check) for status_check in status_checks]

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
