"""
API endpoint для получения токена OpenAI Realtime API
"""
from fastapi import APIRouter, HTTPException
import os
import logging

logger = logging.getLogger(__name__)
router = APIRouter(tags=["openai"])


@router.get("/openai/realtime-token")
async def get_realtime_token():
    """
    Получить токен для OpenAI Realtime API
    """
    try:
        api_key = os.environ.get('OPENAI_API_KEY', '')
        
        if not api_key:
            raise HTTPException(status_code=500, detail="OpenAI API key not configured")
        
        return {
            "token": api_key,
            "model": "gpt-4o-realtime-preview-2024-10-01"
        }
        
    except Exception as e:
        logger.error(f"Error getting realtime token: {e}")
        raise HTTPException(status_code=500, detail=str(e))
