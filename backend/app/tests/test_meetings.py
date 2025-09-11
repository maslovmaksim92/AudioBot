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
async def test_start_meeting_recording():
    """Test start meeting recording endpoint"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/meetings/start-recording")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "meeting_id" in data
        if data["status"] == "success":
            assert "message" in data

@pytest.mark.asyncio
async def test_get_meetings():
    """Test get meetings endpoint"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/meetings")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "meetings" in data
        assert isinstance(data["meetings"], list)

@pytest.mark.asyncio
async def test_stop_meeting_recording():
    """Test stop meeting recording endpoint"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # First start a meeting
        start_response = await client.post("/api/meetings/start-recording")
        if start_response.status_code == 200:
            start_data = start_response.json()
            if start_data.get("status") == "success":
                meeting_id = start_data["meeting_id"]
                
                # Then stop it
                stop_response = await client.post(f"/api/meetings/stop-recording?meeting_id={meeting_id}")
                assert stop_response.status_code == 200
                stop_data = stop_response.json()
                assert "status" in stop_data