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
async def test_telegram_webhook():
    """Test Telegram webhook endpoint"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        webhook_data = {
            "update_id": 123456789,
            "message": {
                "message_id": 1,
                "from": {"id": 123, "first_name": "TestUser"},
                "chat": {"id": 123, "type": "private"},
                "date": 1234567890,
                "text": "Сколько домов у VasDom?"
            }
        }
        response = await client.post("/telegram/webhook", json=webhook_data)
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] in ["processed", "received"]

@pytest.mark.asyncio
async def test_telegram_status():
    """Test Telegram status endpoint"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/telegram/status")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "bot_token" in data
        assert "webhook_url" in data