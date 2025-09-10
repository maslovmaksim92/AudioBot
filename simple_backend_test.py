#!/usr/bin/env python3
"""
Simple Backend Test for VasDom AudioBot
Tests basic functionality to identify issues
"""

import requests
import json

def test_basic_endpoints():
    """Test basic endpoints to identify what's working"""
    base_url = "https://smart-audiobot.preview.emergentagent.com"
    api_url = f"{base_url}/api"
    
    print("🔍 Testing Basic Backend Endpoints")
    print("=" * 50)
    
    endpoints_to_test = [
        ("GET", "/api/", "API Root"),
        ("GET", "/api/health", "Health Check"),
        ("GET", "/api/dashboard", "Dashboard"),
        ("GET", "/api/cleaning/houses", "Cleaning Houses"),
        ("GET", "/api/bitrix24/test", "Bitrix24 Test"),
        ("GET", "/api/telegram/status", "Telegram Status"),
    ]
    
    working_endpoints = []
    failing_endpoints = []
    
    for method, endpoint, name in endpoints_to_test:
        try:
            if method == "GET":
                response = requests.get(f"{base_url}{endpoint}", timeout=10)
            else:
                response = requests.post(f"{base_url}{endpoint}", timeout=10)
            
            if response.status_code < 400:
                working_endpoints.append((name, response.status_code))
                print(f"✅ {name}: {response.status_code}")
            else:
                failing_endpoints.append((name, response.status_code))
                print(f"❌ {name}: {response.status_code}")
                
        except Exception as e:
            failing_endpoints.append((name, f"Error: {str(e)}"))
            print(f"❌ {name}: Error - {str(e)}")
    
    print(f"\n📊 Summary:")
    print(f"✅ Working: {len(working_endpoints)}")
    print(f"❌ Failing: {len(failing_endpoints)}")
    
    return len(working_endpoints) > len(failing_endpoints)

def test_problematic_endpoints():
    """Test the endpoints that were failing"""
    base_url = "https://smart-audiobot.preview.emergentagent.com"
    api_url = f"{base_url}/api"
    
    print("\n🔍 Testing Problematic Endpoints")
    print("=" * 50)
    
    # Test learning stats
    print("Testing /api/learning/stats...")
    try:
        response = requests.get(f"{api_url}/learning/stats", timeout=10)
        print(f"Status: {response.status_code}")
        if response.status_code >= 400:
            print(f"Error response: {response.text[:200]}")
    except Exception as e:
        print(f"Exception: {str(e)}")
    
    # Test learning export
    print("\nTesting /api/learning/export...")
    try:
        response = requests.get(f"{api_url}/learning/export", timeout=10)
        print(f"Status: {response.status_code}")
        if response.status_code >= 400:
            print(f"Error response: {response.text[:200]}")
    except Exception as e:
        print(f"Exception: {str(e)}")
    
    # Test voice process with simple message
    print("\nTesting /api/voice/process...")
    try:
        data = {"message": "Hello", "session_id": "test"}
        response = requests.post(f"{api_url}/voice/process", json=data, timeout=10)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Response: {result.get('response', 'No response')[:100]}")
            print(f"Model used: {result.get('model_used', 'Unknown')}")
        else:
            print(f"Error response: {response.text[:200]}")
    except Exception as e:
        print(f"Exception: {str(e)}")

def main():
    """Main test execution"""
    print("🧠 VasDom AudioBot - Simple Backend Test")
    print("🎯 Identifying what's working and what's not")
    print("=" * 60)
    
    # Test basic endpoints
    basic_working = test_basic_endpoints()
    
    # Test problematic endpoints
    test_problematic_endpoints()
    
    print("\n" + "=" * 60)
    if basic_working:
        print("✅ Basic backend functionality is working")
        print("⚠️  Some advanced features may have issues")
    else:
        print("❌ Multiple backend issues detected")
    
    return 0 if basic_working else 1

if __name__ == "__main__":
    exit(main())