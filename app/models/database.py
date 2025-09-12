from sqlalchemy import Column, String, DateTime, Text, Integer, Boolean
from datetime import datetime
from ..config.database import Base

class VoiceLogDB(Base):
    __tablename__ = "voice_logs"
    
    id = Column(String, primary_key=True)
    user_message = Column(Text)
    ai_response = Column(Text)
    user_id = Column(String)
    context = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)

class MeetingDB(Base):
    __tablename__ = "meetings"
    
    id = Column(String, primary_key=True)
    title = Column(String)
    transcription = Column(Text)
    summary = Column(Text)
    status = Column(String, default="active")
    created_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime)

class AITaskDB(Base):
    __tablename__ = "ai_tasks"
    
    id = Column(String, primary_key=True)
    title = Column(String)
    description = Column(Text)
    scheduled_time = Column(DateTime)
    recurring = Column(Boolean, default=False)
    status = Column(String, default="pending")
    chat_messages = Column(Text)  # JSON string
    created_at = Column(DateTime, default=datetime.utcnow)