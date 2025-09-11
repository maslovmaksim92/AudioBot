#!/usr/bin/env python3
"""
VasDom AudioBot Frontend Integration Test
Tests frontend-backend integration without browser automation
"""

import requests
import json
import time

def test_frontend_backend_integration():
    """Test if frontend can successfully communicate with backend"""
    backend_url = "http://localhost:8001"
    frontend_url = "http://localhost:3000"
    
    print("🚀 Testing VasDom AudioBot Frontend-Backend Integration")
    print("=" * 60)
    
    # Test 1: Frontend is serving
    try:
        response = requests.get(frontend_url, timeout=5)
        if response.status_code == 200 and "root" in response.text:
            print("✅ Frontend is serving HTML correctly")
            if "bundle.js" in response.text:
                print("✅ Frontend includes React bundle")
        else:
            print("❌ Frontend serving issue")
            return False
    except Exception as e:
        print(f"❌ Frontend connection failed: {e}")
        return False
    
    # Test 2: Backend API is accessible from frontend perspective
    try:
        # Test the same endpoints the frontend would call
        dashboard_response = requests.get(f"{backend_url}/api/dashboard", timeout=10)
        if dashboard_response.status_code == 200:
            data = dashboard_response.json()
            if data.get("status") == "success":
                stats = data.get("stats", {})
                print(f"✅ Dashboard API working - Houses: {stats.get('houses', 0)}, Employees: {stats.get('employees', 0)}")
            else:
                print("❌ Dashboard API returned error")
                return False
        else:
            print(f"❌ Dashboard API failed with status {dashboard_response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Backend API connection failed: {e}")
        return False
    
    # Test 3: Voice AI endpoint (critical functionality)
    try:
        voice_data = {
            "text": "Тест интеграции VasDom AI",
            "user_id": "integration_test"
        }
        voice_response = requests.post(f"{backend_url}/api/voice/process", 
                                     json=voice_data, timeout=15)
        if voice_response.status_code == 200:
            response_data = voice_response.json()
            if "response" in response_data and len(response_data["response"]) > 10:
                print("✅ Voice AI integration working")
                print(f"   🤖 AI Response: {response_data['response'][:100]}...")
            else:
                print("❌ Voice AI returned invalid response")
                return False
        else:
            print(f"❌ Voice AI failed with status {voice_response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Voice AI integration failed: {e}")
        return False
    
    # Test 4: Cleaning houses data (Bitrix24 integration)
    try:
        houses_response = requests.get(f"{backend_url}/api/cleaning/houses?limit=10", timeout=10)
        if houses_response.status_code == 200:
            houses_data = houses_response.json()
            if houses_data.get("status") == "success" and "houses" in houses_data:
                house_count = len(houses_data["houses"])
                print(f"✅ Cleaning houses data available - {house_count} houses loaded")
                if house_count > 0:
                    sample_house = houses_data["houses"][0]
                    print(f"   🏠 Sample house: {sample_house.get('address', 'No address')}")
            else:
                print("❌ Cleaning houses data invalid")
                return False
        else:
            print(f"❌ Cleaning houses API failed with status {houses_response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cleaning houses integration failed: {e}")
        return False
    
    print("=" * 60)
    print("✅ All frontend-backend integration tests passed!")
    print("🎉 VasDom AudioBot system is ready for use")
    return True

if __name__ == "__main__":
    success = test_frontend_backend_integration()
    exit(0 if success else 1)