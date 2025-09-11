import pytest
import asyncio
from httpx import AsyncClient
from fastapi.testclient import TestClient
from ..main import app

@pytest.mark.asyncio
async def test_api_root():
    """Test API root endpoint"""
    async with AsyncClient(base_url="http://test") as client:
        response = await client.get("/api/", follow_redirects=True)
        # Since we're testing the actual running app, use sync client for simple test
    
    # Alternative sync test
    with TestClient(app) as client:
        response = client.get("/api/")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "VasDom AudioBot API"
        assert data["version"] == "3.0.0"
        assert "features" in data

@pytest.mark.asyncio 
async def test_health_check():
    """Test health check endpoint"""
    with TestClient(app) as client:
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["healthy", "error"]
        assert "service" in data
        assert "version" in data

@pytest.mark.asyncio
async def test_dashboard_stats():
    """Test dashboard stats endpoint"""
    with TestClient(app) as client:
        response = client.get("/api/dashboard")
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
    with TestClient(app) as client:
        response = client.get("/dashboard", follow_redirects=False)
        assert response.status_code == 302
        assert "smart-facility-ai.preview.emergentagent.com" in response.headers["location"]