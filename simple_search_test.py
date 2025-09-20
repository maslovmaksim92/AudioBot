#!/usr/bin/env python3
"""
Review Request Testing - Specific Test for POST /api/ai-knowledge/search
Testing: POST /api/ai-knowledge/search — body {"query":"psycopg3","top_k":5} → ожидаем 200 и results[] (даже если пустой массив, но не 500)
Base URL: https://audiobot-qci2.onrender.com
"""

import requests
import json
import sys

def test_ai_knowledge_search():
    """Test POST /api/ai-knowledge/search as per review request"""
    base_url = "https://audiobot-qci2.onrender.com"
    endpoint = "/api/ai-knowledge/search"
    url = f"{base_url}{endpoint}"
    
    # Request body as specified in review request
    search_data = {
        'query': 'psycopg3',
        'top_k': 5
    }
    
    print(f"🚀 Review Request Testing")
    print(f"📍 Base URL: {base_url}")
    print(f"🔧 Testing: POST {endpoint}")
    print(f"📋 Body: {json.dumps(search_data, ensure_ascii=False)}")
    print("🎯 Expected: Status 200 и results[] (даже если пустой массив, но не 500)")
    print("=" * 80)
    
    try:
        # Make the request
        headers = {'Content-Type': 'application/json'}
        response = requests.post(url, json=search_data, headers=headers, timeout=60)
        
        print(f"\n📊 РЕЗУЛЬТАТ:")
        print(f"Status Code: {response.status_code}")
        
        # Try to parse JSON response
        try:
            response_data = response.json() if response.content else {}
            print(f"Response Body: {json.dumps(response_data, indent=2, ensure_ascii=False)}")
        except:
            print(f"Response Body (non-JSON): {response.text[:500]}")
            response_data = {"error": "Non-JSON response", "content": response.text[:500]}
        
        # Evaluate the result
        print(f"\n🎯 ОЦЕНКА:")
        
        if response.status_code == 200:
            print("✅ Status Code: 200 ✓ (ожидалось 200)")
            
            # Check if results field exists and is an array
            if 'results' in response_data:
                results = response_data['results']
                if isinstance(results, list):
                    print(f"✅ results[] field: array ✓ (размер: {len(results)})")
                    
                    if len(results) > 0:
                        print("✅ results[] не пустой ✓")
                        print(f"📋 Пример ответа: {json.dumps(results[0], indent=2, ensure_ascii=False)}")
                    else:
                        print("⚠️ results[] пустой массив (это допустимо по требованиям)")
                    
                    print(f"\n🎉 УСПЕХ: Все требования выполнены!")
                    print(f"   - Status: 200 ✓")
                    print(f"   - results[] существует и является массивом ✓")
                    print(f"   - Не возвращает 500 ✓")
                    return True
                else:
                    print(f"❌ results field должен быть массивом, получен {type(results)}")
            else:
                print("❌ Отсутствует поле 'results' в ответе")
        elif response.status_code == 500:
            print("❌ Status Code: 500 ✗ (ожидалось 200, НЕ 500)")
            print("❌ ПРОВАЛ: Возвращает 500 вместо 200")
        else:
            print(f"❌ Status Code: {response.status_code} ✗ (ожидалось 200)")
        
        return False
        
    except requests.exceptions.Timeout:
        print("❌ Request timeout")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ Connection error")
        return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_ai_knowledge_search()
    sys.exit(0 if success else 1)