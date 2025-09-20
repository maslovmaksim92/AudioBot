#!/usr/bin/env python3
"""
Test local backend search endpoint
"""

import requests
import json
import os

def test_local_search_endpoint():
    """Test POST /api/ai-knowledge/search on local backend"""
    
    # Get the backend URL from frontend env
    try:
        with open('/app/frontend/.env', 'r') as f:
            env_content = f.read()
            for line in env_content.split('\n'):
                if line.startswith('REACT_APP_BACKEND_URL='):
                    base_url = line.split('=', 1)[1].strip()
                    break
            else:
                base_url = "http://localhost:8001"
    except:
        base_url = "http://localhost:8001"
    
    endpoint = "/api/ai-knowledge/search"
    
    # Exact body from review request
    search_data = {
        "query": "psycopg3",
        "top_k": 5
    }
    
    print(f"🔍 Testing POST {endpoint} (LOCAL)")
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
    success = test_local_search_endpoint()
    print("\n" + "=" * 60)
    if success:
        print("🎉 LOCAL TEST: PASSED")
    else:
        print("💥 LOCAL TEST: FAILED")
    print("=" * 60)