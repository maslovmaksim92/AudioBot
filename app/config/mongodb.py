import os
import logging
from pathlib import Path
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient

# Load environment variables
ROOT_DIR = Path(__file__).parent.parent.parent
load_dotenv(ROOT_DIR / '.env')

logger = logging.getLogger(__name__)

# MongoDB configuration
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017/vasdom_audiobot')

# Global MongoDB client
mongo_client = None
mongo_db = None

async def init_mongodb():
    """Initialize MongoDB connection"""
    global mongo_client, mongo_db
    
    try:
        # Extract database name from URL
        if '/' in MONGO_URL:
            db_name = MONGO_URL.split('/')[-1]
        else:
            db_name = 'vasdom_audiobot'
        
        logger.info(f"🔗 Connecting to MongoDB: {db_name}")
        
        # Create async client
        mongo_client = AsyncIOMotorClient(MONGO_URL)
        mongo_db = mongo_client[db_name]
        
        # Test connection
        await mongo_client.admin.command('ping')
        logger.info("✅ MongoDB connected successfully")
        
        return mongo_db
        
    except Exception as e:
        logger.error(f"❌ MongoDB connection failed: {e}")
        return None

def get_sync_db():
    """Get synchronous MongoDB connection for non-async operations"""
    try:
        client = MongoClient(MONGO_URL)
        if '/' in MONGO_URL:
            db_name = MONGO_URL.split('/')[-1]
        else:
            db_name = 'vasdom_audiobot'
        return client[db_name]
    except Exception as e:
        logger.error(f"❌ Sync MongoDB connection failed: {e}")
        return None

async def get_mongo_db():
    """Get async MongoDB database instance"""
    global mongo_db
    if mongo_db is None:
        mongo_db = await init_mongodb()
    return mongo_db

# Collections
class Collections:
    VOICE_LOGS = "voice_logs"
    MEETINGS = "meetings" 
    AI_TASKS = "ai_tasks"
    EMPLOYEES = "employees"
    HOUSES = "houses"
    TRAINING_DATA = "training_data"
    CHAT_SESSIONS = "chat_sessions"