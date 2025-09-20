#!/usr/bin/env python3
"""
Mini-flow AI Knowledge Testing Results
Production deployment: https://audiobot-qci2.onrender.com
"""

import requests
import json
import sys
from datetime import datetime

def test_mini_flow():
    """Test the complete mini-flow as specified in review request"""
    base_url = 'https://audiobot-qci2.onrender.com'
    
    print("🚀 VasDom AudioBot Backend API - Mini‑flow на проде")
    print(f"📍 Base URL: {base_url}")
    print("🔧 Testing AI Knowledge Mini-Flow per review request:")
    print("1) POST /api/ai-knowledge/preview — multipart (files: 1 txt файл с содержимым \"Search mini flow psycopg3 works\") → ожидаем 200: upload_id, chunks>0")
    print("2) GET /api/ai-knowledge/status?upload_id=<id> — ожидаем 200: status='ready'")
    print("3) POST /api/ai-knowledge/study — form: upload_id, filename='mini.txt', category='Маркетинг' → ожидаем 200: document_id, chunks>=1")
    print("4) GET /api/ai-knowledge/documents — ожидаем 200: есть документ из (3)")
    print("5) POST /api/ai-knowledge/search — body {\"query\":\"psycopg3\",\"top_k\":5} → ожидаем 200 и непустой results[]")
    print("=" * 80)
    
    results = []
    upload_id = None
    document_id = None
    
    # Test 1: POST /api/ai-knowledge/preview
    print("\n1️⃣ Testing POST /api/ai-knowledge/preview")
    test_content = "Search mini flow psycopg3 works"
    files = {'files': ('mini.txt', test_content.encode('utf-8'), 'text/plain')}
    
    try:
        response = requests.post(f'{base_url}/api/ai-knowledge/preview', files=files, timeout=60)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            upload_id = data.get('upload_id')
            chunks = data.get('chunks', 0)
            
            if upload_id and chunks > 0:
                results.append({"test": "preview", "status": "✅ PASSED", "details": f"upload_id: {upload_id[:8]}..., chunks: {chunks}"})
                print(f"   ✅ PASSED: upload_id: {upload_id[:8]}..., chunks: {chunks}")
                print(f"   Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
            else:
                results.append({"test": "preview", "status": "❌ FAILED", "details": "Missing upload_id or chunks <= 0"})
                print(f"   ❌ FAILED: Missing upload_id or chunks <= 0")
        else:
            results.append({"test": "preview", "status": "❌ FAILED", "details": f"Status: {response.status_code}"})
            print(f"   ❌ FAILED: Status: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
    except Exception as e:
        results.append({"test": "preview", "status": "❌ ERROR", "details": str(e)})
        print(f"   ❌ ERROR: {e}")
    
    if not upload_id:
        print("\n❌ Cannot proceed with remaining tests - no upload_id from preview")
        return results
    
    # Test 2: GET /api/ai-knowledge/status
    print(f"\n2️⃣ Testing GET /api/ai-knowledge/status?upload_id={upload_id[:8]}...")
    try:
        response = requests.get(f'{base_url}/api/ai-knowledge/status', params={'upload_id': upload_id}, timeout=30)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            status = data.get('status', '')
            
            if status == 'ready':
                results.append({"test": "status", "status": "✅ PASSED", "details": "status='ready'"})
                print(f"   ✅ PASSED: status='ready'")
                print(f"   Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
            else:
                results.append({"test": "status", "status": "❌ FAILED", "details": f"status='{status}' (expected 'ready')"})
                print(f"   ❌ FAILED: status='{status}' (expected 'ready')")
        else:
            results.append({"test": "status", "status": "❌ FAILED", "details": f"Status: {response.status_code}"})
            print(f"   ❌ FAILED: Status: {response.status_code}")
    except Exception as e:
        results.append({"test": "status", "status": "❌ ERROR", "details": str(e)})
        print(f"   ❌ ERROR: {e}")
    
    # Test 3: POST /api/ai-knowledge/study
    print(f"\n3️⃣ Testing POST /api/ai-knowledge/study")
    form_data = {
        'upload_id': upload_id,
        'filename': 'mini.txt',
        'category': 'Маркетинг'
    }
    
    try:
        response = requests.post(f'{base_url}/api/ai-knowledge/study', data=form_data, timeout=60)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            document_id = data.get('document_id')
            chunks = data.get('chunks', 0)
            category = data.get('category', '')
            
            if document_id and chunks >= 1:
                results.append({"test": "study", "status": "✅ PASSED", "details": f"document_id: {document_id[:8]}..., chunks: {chunks}, category: {category}"})
                print(f"   ✅ PASSED: document_id: {document_id[:8]}..., chunks: {chunks}, category: {category}")
                print(f"   Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
            else:
                results.append({"test": "study", "status": "❌ FAILED", "details": "Missing document_id or chunks < 1"})
                print(f"   ❌ FAILED: Missing document_id or chunks < 1")
        else:
            results.append({"test": "study", "status": "❌ FAILED", "details": f"Status: {response.status_code}"})
            print(f"   ❌ FAILED: Status: {response.status_code}")
    except Exception as e:
        results.append({"test": "study", "status": "❌ ERROR", "details": str(e)})
        print(f"   ❌ ERROR: {e}")
    
    if not document_id:
        print("\n❌ Cannot proceed with documents/search tests - no document_id from study")
        return results
    
    # Test 4: GET /api/ai-knowledge/documents
    print(f"\n4️⃣ Testing GET /api/ai-knowledge/documents")
    try:
        response = requests.get(f'{base_url}/api/ai-knowledge/documents', timeout=30)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            documents = data.get('documents', [])
            
            # Find our test document
            test_doc = None
            for doc in documents:
                if doc.get('filename') == 'mini.txt':
                    test_doc = doc
                    break
            
            if test_doc:
                chunks_count = test_doc.get('chunks_count', 0)
                results.append({"test": "documents", "status": "✅ PASSED", "details": f"Found 'mini.txt' with {chunks_count} chunks"})
                print(f"   ✅ PASSED: Found 'mini.txt' with {chunks_count} chunks")
                print(f"   Total documents: {len(documents)}")
                print(f"   Document details: {json.dumps(test_doc, indent=2, ensure_ascii=False)}")
            else:
                results.append({"test": "documents", "status": "❌ FAILED", "details": "Test document 'mini.txt' not found"})
                print(f"   ❌ FAILED: Test document 'mini.txt' not found")
                print(f"   Available documents: {[doc.get('filename') for doc in documents]}")
        else:
            results.append({"test": "documents", "status": "❌ FAILED", "details": f"Status: {response.status_code}"})
            print(f"   ❌ FAILED: Status: {response.status_code}")
    except Exception as e:
        results.append({"test": "documents", "status": "❌ ERROR", "details": str(e)})
        print(f"   ❌ ERROR: {e}")
    
    # Test 5: POST /api/ai-knowledge/search
    print(f"\n5️⃣ Testing POST /api/ai-knowledge/search")
    search_data = {'query': 'psycopg3', 'top_k': 5}
    
    try:
        response = requests.post(f'{base_url}/api/ai-knowledge/search', json=search_data, timeout=30)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            search_results = data.get('results', [])
            
            if isinstance(search_results, list) and len(search_results) > 0:
                results.append({"test": "search", "status": "✅ PASSED", "details": f"Found {len(search_results)} search results"})
                print(f"   ✅ PASSED: Found {len(search_results)} search results")
                print(f"   Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
                
                # Show first result as example
                if search_results:
                    print(f"   📋 Пример первого результата:")
                    print(f"   {json.dumps(search_results[0], indent=2, ensure_ascii=False)}")
            else:
                results.append({"test": "search", "status": "❌ FAILED", "details": "Empty results array"})
                print(f"   ❌ FAILED: Empty results array")
                print(f"   Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
        else:
            results.append({"test": "search", "status": "❌ FAILED", "details": f"Status: {response.status_code}"})
            print(f"   ❌ FAILED: Status: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
    except Exception as e:
        results.append({"test": "search", "status": "❌ ERROR", "details": str(e)})
        print(f"   ❌ ERROR: {e}")
    
    return results

def print_summary(results):
    """Print test summary"""
    print("\n" + "=" * 80)
    print("🎯 MINI-FLOW TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for r in results if "✅ PASSED" in r["status"])
    failed = sum(1 for r in results if "❌" in r["status"])
    total = len(results)
    
    print(f"Total Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    if total > 0:
        success_rate = (passed / total) * 100
        print(f"Success Rate: {success_rate:.1f}%")
    
    print(f"\nДетальные результаты:")
    for i, result in enumerate(results, 1):
        print(f"{i}. {result['test'].upper()}: {result['status']}")
        print(f"   {result['details']}")
    
    print("\n" + "=" * 80)
    print(f"Тестирование завершено: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

if __name__ == "__main__":
    results = test_mini_flow()
    print_summary(results)