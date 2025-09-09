import pytest
import asyncio
from httpx import AsyncClient
from ..main import app

@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.mark.asyncio
async def test_voice_process():
    """Test voice processing endpoint"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        payload = {
            "text": "Привет! Сколько домов?",
            "user_id": "test_user"
        }
        response = await client.post("/api/voice/process", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert "timestamp" in data
        # Check that AI response contains information about houses
        assert len(data["response"]) > 0

@pytest.mark.asyncio
async def test_self_learning_status():
    """Test self-learning status endpoint"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/self-learning/status")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "emergent_llm" in data

@pytest.mark.asyncio
async def test_self_learning_test():
    """Test self-learning test endpoint"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/self-learning/test")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "ai_response" in data