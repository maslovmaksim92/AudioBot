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
async def test_api_root():
    """Test API root endpoint"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "VasDom AudioBot API"
        assert data["version"] == "3.0.0"
        assert "features" in data

@pytest.mark.asyncio 
async def test_health_check():
    """Test health check endpoint"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["healthy", "error"]
        assert "service" in data
        assert "version" in data

@pytest.mark.asyncio
async def test_dashboard_stats():
    """Test dashboard stats endpoint"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/dashboard")
        assert response.status_code == 200
        data = response.json()
        assert "stats" in data
        assert "status" in data
        # Check that stats has required fields
        stats = data["stats"]
        assert "employees" in stats
        assert "houses" in stats
        assert "entrances" in stats
        assert "apartments" in stats

@pytest.mark.asyncio
async def test_dashboard_redirect():
    """Test dashboard redirect"""
    async with AsyncClient(app=app, base_url="http://test", follow_redirects=False) as client:
        response = await client.get("/dashboard")
        assert response.status_code == 302
        assert "smart-facility-ai.preview.emergentagent.com" in response.headers["location"]