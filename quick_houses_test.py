#!/usr/bin/env python3
"""
Quick Houses API Test - Быстрая проверка API домов
"""

import asyncio
import httpx
import json
from pathlib import Path

# Get backend URL from frontend/.env
def get_backend_url():
    try:
        frontend_env_path = Path(__file__).parent / "frontend" / ".env"
        if frontend_env_path.exists():
            with open(frontend_env_path, 'r') as f:
                for line in f:
                    if line.startswith('REACT_APP_BACKEND_URL='):
                        url = line.split('=', 1)[1].strip()
                        return f"{url}/api"
        return "https://crmunified.preview.emergentagent.com/api"
    except:
        return "https://crmunified.preview.emergentagent.com/api"

BACKEND_URL = get_backend_url()
print(f"🔗 Testing backend at: {BACKEND_URL}")

async def test_houses_endpoints():
    """Быстрая проверка houses API endpoints"""
    
    print("\n🏠 QUICK HOUSES API TEST")
    print("=" * 50)
    
    results = {}
    
    # Test 1: GET /api/cleaning/houses-490
    print("\n1️⃣ Testing GET /api/cleaning/houses-490...")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{BACKEND_URL}/cleaning/houses-490")
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                houses = data.get("houses", [])
                print(f"✅ SUCCESS: {len(houses)} houses loaded")
                
                if houses:
                    sample = houses[0]
                    print(f"📋 Sample house:")
                    print(f"   - Address: {sample.get('address', 'N/A')}")
                    print(f"   - Management Company: {sample.get('management_company', 'N/A')}")
                    print(f"   - September Schedule: {bool(sample.get('september_schedule'))}")
                
                results["houses-490"] = True
            else:
                print(f"❌ FAILED: {response.status_code}")
                print(f"Response: {response.text[:200]}...")
                results["houses-490"] = False
                
    except Exception as e:
        print(f"❌ ERROR: {e}")
        results["houses-490"] = False
    
    # Test 2: GET /api/cleaning/houses
    print("\n2️⃣ Testing GET /api/cleaning/houses...")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{BACKEND_URL}/cleaning/houses")
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                houses = data.get("houses", [])
                source = data.get("source", "Unknown")
                print(f"✅ SUCCESS: {len(houses)} houses loaded")
                print(f"🔗 Data source: {source}")
                
                # Analyze management companies
                uk_filled = sum(1 for h in houses if h.get('management_company') and h.get('management_company') != 'null')
                uk_null = len(houses) - uk_filled
                print(f"🏢 Management Companies: {uk_filled} filled, {uk_null} null")
                
                # Analyze schedules
                with_schedule = sum(1 for h in houses if h.get('september_schedule'))
                print(f"📅 September Schedules: {with_schedule}/{len(houses)} houses")
                
                results["houses"] = True
            else:
                print(f"❌ FAILED: {response.status_code}")
                print(f"Response: {response.text[:200]}...")
                results["houses"] = False
                
    except Exception as e:
        print(f"❌ ERROR: {e}")
        results["houses"] = False
    
    # Test 3: Check Bitrix24 webhook
    print("\n3️⃣ Testing Bitrix24 webhook...")
    try:
        webhook_url = "https://vas-dom.bitrix24.ru/rest/1/4l8hq1gqgodjt7yo/"
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(webhook_url)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ SUCCESS: Bitrix24 webhook accessible")
                results["bitrix24_webhook"] = True
            else:
                print(f"❌ FAILED: {response.status_code}")
                results["bitrix24_webhook"] = False
                
    except Exception as e:
        print(f"❌ ERROR: {e}")
        results["bitrix24_webhook"] = False
    
    # Test 4: Dashboard stats
    print("\n4️⃣ Testing GET /api/dashboard...")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{BACKEND_URL}/dashboard")
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                stats = data.get("stats", {})
                houses_count = stats.get("houses", 0)
                print(f"✅ SUCCESS: Dashboard shows {houses_count} houses")
                results["dashboard"] = True
            else:
                print(f"❌ FAILED: {response.status_code}")
                results["dashboard"] = False
                
    except Exception as e:
        print(f"❌ ERROR: {e}")
        results["dashboard"] = False
    
    # Summary
    print("\n📊 QUICK TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for r in results.values() if r)
    total = len(results)
    
    for test, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test:20} {status}")
    
    print(f"\nResult: {passed}/{total} tests passed")
    
    if passed < total:
        print("\n🚨 ISSUES FOUND:")
        for test, result in results.items():
            if not result:
                print(f"  - {test}: Not working")
    
    return results

if __name__ == "__main__":
    asyncio.run(test_houses_endpoints())