#!/usr/bin/env python3
"""
Focused test for POST /api/ai-knowledge/search endpoint per review request
"""

import requests
import json

def test_search_endpoint():
    """Test POST /api/ai-knowledge/search with specific body from review request"""
    base_url = "https://audiobot-qci2.onrender.com"
    endpoint = "/api/ai-knowledge/search"
    
    # Exact body from review request
    search_data = {
        "query": "psycopg3",
        "top_k": 5
    }
    
    print(f"🔍 Testing POST {endpoint}")
    print(f"📍 URL: {base_url}{endpoint}")
    print(f"📋 Body: {json.dumps(search_data, ensure_ascii=False)}")
    print(f"🎯 Expected: Status 200 with results[] (допускается пустой массив)")
    print("=" * 60)
    
    try:
        response = requests.post(
            f"{base_url}{endpoint}",
            json=search_data,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        print(f"📊 Status Code: {response.status_code}")
        print(f"📄 Response Headers: {dict(response.headers)}")
        
        # Try to get response body
        try:
            response_data = response.json()
            print(f"📝 Response Body: {json.dumps(response_data, indent=2, ensure_ascii=False)}")
        except:
            print(f"📝 Response Text: {response.text}")
        
        # Check if meets review request requirements
        if response.status_code == 200:
            try:
                data = response.json()
                results = data.get('results', [])
                if isinstance(results, list):
                    print(f"✅ SUCCESS: Status 200 ✓, results[] is array with {len(results)} items ✓")
                    return True
                else:
                    print(f"❌ FAIL: Status 200 ✓, but results is not array: {type(results)}")
                    return False
            except:
                print(f"❌ FAIL: Status 200 ✓, but response is not valid JSON")
                return False
        else:
            print(f"❌ FAIL: Status {response.status_code} (expected 200)")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ FAIL: Request timeout")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ FAIL: Connection error")
        return False
    except Exception as e:
        print(f"❌ FAIL: Exception: {e}")
        return False

if __name__ == "__main__":
    success = test_search_endpoint()
    print("\n" + "=" * 60)
    if success:
        print("🎉 REVIEW REQUEST REQUIREMENT: PASSED")
    else:
        print("💥 REVIEW REQUEST REQUIREMENT: FAILED")
    print("=" * 60)