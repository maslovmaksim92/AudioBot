"""
Database connection and utilities for MongoDB
"""

import os
import logging
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

logger = logging.getLogger(__name__)

class DatabaseManager:
    """MongoDB database manager with connection handling and utilities"""
    
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.db: Optional[AsyncIOMotorDatabase] = None
        self.mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
        self.db_name = os.environ.get('DB_NAME', 'ai_assistant')
        
    async def connect(self):
        """Initialize database connection"""
        try:
            self.client = AsyncIOMotorClient(self.mongo_url)
            self.db = self.client[self.db_name]
            
            # Test connection
            await self.client.admin.command('ping')
            logger.info(f"✅ Connected to MongoDB: {self.db_name}")
            
            # Create indexes for optimization
            await self._create_indexes()
            
        except Exception as e:
            logger.error(f"❌ MongoDB connection failed: {e}")
            raise
    
    async def disconnect(self):
        """Close database connection"""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")
    
    async def _create_indexes(self):
        """Create database indexes for better performance"""
        try:
            # Conversation sessions indexes
            await self.db.conversation_sessions.create_index("user_id")
            await self.db.conversation_sessions.create_index("last_activity")
            await self.db.conversation_sessions.create_index([("is_active", 1), ("last_activity", -1)])
            
            # Conversation messages indexes
            await self.db.conversation_messages.create_index("session_id")
            await self.db.conversation_messages.create_index("timestamp")
            await self.db.conversation_messages.create_index([("session_id", 1), ("timestamp", 1)])
            
            # Employee indexes
            await self.db.employees.create_index("telegram_id")
            await self.db.employees.create_index("city")
            await self.db.employees.create_index([("is_active", 1), ("city", 1)])
            
            # Financial data indexes
            await self.db.financial_data.create_index("period")
            await self.db.financial_data.create_index("created_at")
            
            # Meeting records indexes
            await self.db.meeting_records.create_index("date")
            await self.db.meeting_records.create_index("created_at")
            
            # Notification logs indexes
            await self.db.notification_logs.create_index("created_at")
            await self.db.notification_logs.create_index("status")
            
            logger.info("✅ Database indexes created successfully")
            
        except Exception as e:
            logger.error(f"Error creating indexes: {e}")
    
    def get_collection(self, collection_name: str) -> AsyncIOMotorCollection:
        """Get MongoDB collection"""
        if self.db is None:
            raise Exception("Database not connected")
        return self.db[collection_name]
    
    async def cleanup_old_conversations(self, retention_days: int = 90):
        """Clean up old conversation data beyond retention period"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
            
            # Delete old messages
            messages_result = await self.db.conversation_messages.delete_many({
                "timestamp": {"$lt": cutoff_date}
            })
            
            # Delete old inactive sessions
            sessions_result = await self.db.conversation_sessions.delete_many({
                "last_activity": {"$lt": cutoff_date},
                "is_active": False
            })
            
            logger.info(f"Cleaned up {messages_result.deleted_count} old messages and {sessions_result.deleted_count} old sessions")
            return {
                "messages_deleted": messages_result.deleted_count,
                "sessions_deleted": sessions_result.deleted_count
            }
            
        except Exception as e:
            logger.error(f"Error cleaning up old conversations: {e}")
            return {"error": str(e)}
    
    async def get_conversation_stats(self) -> Dict[str, Any]:
        """Get conversation statistics"""
        try:
            total_sessions = await self.db.conversation_sessions.count_documents({})
            active_sessions = await self.db.conversation_sessions.count_documents({"is_active": True})
            total_messages = await self.db.conversation_messages.count_documents({})
            
            # Last 24 hours activity
            yesterday = datetime.utcnow() - timedelta(days=1)
            recent_messages = await self.db.conversation_messages.count_documents({
                "timestamp": {"$gte": yesterday}
            })
            
            return {
                "total_sessions": total_sessions,
                "active_sessions": active_sessions,
                "total_messages": total_messages,
                "recent_messages_24h": recent_messages
            }
            
        except Exception as e:
            logger.error(f"Error getting conversation stats: {e}")
            return {"error": str(e)}

# Global database manager instance
db_manager = DatabaseManager()

# Legacy support - keep existing interface
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'ai_assistant')]

async def init_database():
    """Initialize database connection (legacy support)"""
    await db_manager.connect()
    return db_manager.db

async def close_database():
    """Close database connection (legacy support)"""
    await db_manager.disconnect()

# Conversation helpers
class ConversationManager:
    """Helper class for managing conversation memory"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    async def get_or_create_session(self, session_id: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get existing session or create new one"""
        try:
            collection = self.db.get_collection("conversation_sessions")
            
            # Try to find existing session
            session = await collection.find_one({"id": session_id})
            
            if not session:
                # Create new session
                session_data = {
                    "id": session_id,
                    "user_id": user_id,
                    "context": {
                        "company": "ВасДом",
                        "business_type": "cleaning_company",
                        "cities": ["Калуга", "Кемерово"],
                        "employees": 100,
                        "houses": 600
                    },
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                    "last_activity": datetime.utcnow(),
                    "is_active": True,
                    "message_count": 0,
                    "total_tokens": 0
                }
                
                await collection.insert_one(session_data)
                session = session_data
                logger.info(f"Created new conversation session: {session_id}")
            else:
                # Update last activity
                await collection.update_one(
                    {"id": session_id},
                    {
                        "$set": {
                            "last_activity": datetime.utcnow(),
                            "updated_at": datetime.utcnow()
                        }
                    }
                )
            
            return session
            
        except Exception as e:
            logger.error(f"Error managing session {session_id}: {e}")
            # Return basic session if database fails
            return {
                "id": session_id,
                "user_id": user_id,
                "context": {"company": "ВасДом"},
                "message_count": 0
            }
    
    async def save_message(self, session_id: str, message_type: str, content: str, 
                          metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Save message to conversation history"""
        try:
            collection = self.db.get_collection("conversation_messages")
            
            message_data = {
                "id": f"{session_id}_{datetime.utcnow().timestamp()}",
                "session_id": session_id,
                "message_type": message_type,
                "content": content,
                "metadata": metadata or {},
                "timestamp": datetime.utcnow()
            }
            
            await collection.insert_one(message_data)
            
            # Update session message count
            sessions_collection = self.db.get_collection("conversation_sessions")
            await sessions_collection.update_one(
                {"id": session_id},
                {
                    "$inc": {"message_count": 1},
                    "$set": {"last_activity": datetime.utcnow()}
                }
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error saving message for session {session_id}: {e}")
            return False
    
    async def get_conversation_history(self, session_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent conversation history for context"""
        try:
            collection = self.db.get_collection("conversation_messages")
            
            cursor = collection.find(
                {"session_id": session_id}
            ).sort("timestamp", -1).limit(limit)
            
            messages = await cursor.to_list(length=limit)
            return list(reversed(messages))  # Return chronological order
            
        except Exception as e:
            logger.error(f"Error getting conversation history for {session_id}: {e}")
            return []

# Global conversation manager
conversation_manager = ConversationManager(db_manager)

# Utility functions
async def prepare_for_mongo(data: Dict[str, Any]) -> Dict[str, Any]:
    """Prepare data for MongoDB storage"""
    # Convert datetime objects to ISO strings
    for key, value in data.items():
        if isinstance(value, datetime):
            data[key] = value.isoformat()
    return data

async def parse_from_mongo(item: Dict[str, Any]) -> Dict[str, Any]:
    """Parse data from MongoDB"""
    # Convert ISO strings back to datetime objects if needed
    for key, value in item.items():
        if isinstance(value, str) and key.endswith('_at'):
            try:
                item[key] = datetime.fromisoformat(value)
            except ValueError:
                pass  # Keep as string if not a valid ISO datetime
    return item