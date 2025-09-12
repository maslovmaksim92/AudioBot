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
async def test_cleaning_houses():
    """Test cleaning houses endpoint"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/cleaning/houses")
        assert response.status_code == 200
        data = response.json()
        assert "houses" in data
        assert "total" in data
        assert "status" in data

@pytest.mark.asyncio
async def test_cleaning_brigades():
    """Test cleaning brigades endpoint"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/cleaning/brigades")
        assert response.status_code == 200
        data = response.json()
        assert "brigades" in data
        assert "total_employees" in data
        assert data["total_employees"] == 82
        assert data["total_brigades"] == 6

@pytest.mark.asyncio
async def test_cleaning_stats():
    """Test cleaning stats endpoint"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/cleaning/stats")
        assert response.status_code == 200
        data = response.json()
        assert "stats" in data
        if data["status"] == "success":
            stats = data["stats"]
            assert "total_houses" in stats
            assert "completed" in stats
            assert "in_progress" in stats