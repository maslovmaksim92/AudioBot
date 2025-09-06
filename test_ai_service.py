#!/usr/bin/env python3
"""
Test AI Service directly
"""

import asyncio
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent / "backend"))

from ai_service import AIService
from dotenv import load_dotenv

# Load environment variables
load_dotenv(Path(__file__).parent / "backend" / ".env")

async def test_ai_service():
    """Test AI service functionality"""
    api_key = os.getenv("EMERGENT_LLM_KEY")
    print(f"🔑 API Key present: {bool(api_key)}")
    
    if not api_key:
        print("❌ No API key found")
        return
    
    # Initialize AI service
    ai_service = AIService(api_key)
    
    # Test health check
    print("\n🏥 Testing AI Service Health Check...")
    health = await ai_service.health_check()
    print(f"Health Status: {health}")
    
    # Test simple response
    print("\n🤖 Testing AI Response Generation...")
    try:
        response = await ai_service.generate_response("Привет! Расскажи о ваших услугах.")
        print(f"AI Response: {response}")
        print(f"Response length: {len(response)} characters")
    except Exception as e:
        print(f"❌ AI Response Error: {e}")
    
    # Test intent analysis
    print("\n🎯 Testing Intent Analysis...")
    try:
        intent = await ai_service.analyze_user_intent("Хочу заказать уборку подъезда")
        print(f"Intent Analysis: {intent}")
    except Exception as e:
        print(f"❌ Intent Analysis Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_ai_service())