#!/usr/bin/env python3
"""
VasDom AudioBot Backend API Testing - Quick Re-check after sslrootcert
Testing specific AI Knowledge diagnostics endpoints:
1) GET /api/ai-knowledge/db-dsn — normalized.query должен содержать строку 'sslmode=require'
2) GET /api/ai-knowledge/db-check — ожидаем connected=true. Если нет — приложи errors[]
Base URL: https://audiobot-qci2.onrender.com
"""

import requests
import sys
import json
import time
import io
from datetime import datetime
from typing import Dict, Any, Optional

class VasDomAPITester:
    def __init__(self, base_url=None):
        # Use the deployed URL from review request
        if base_url is None:
            base_url = "https://audiobot-qci2.onrender.com"
        
        self.base_url = base_url.rstrip('/')
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []
        self.upload_id = None  # Store upload_id for flow testing
        self.document_id = None  # Store document_id for flow testing

    def log_test(self, name: str, success: bool, details: str = ""):
        """Log test result"""
        self.tests_run += 1
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"\n{status} - {name}")
        if details:
            print(f"   Details: {details}")
        
        if success:
            self.tests_passed += 1
        else:
            self.failed_tests.append({"name": name, "details": details})

    def make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, params: Optional[Dict] = None) -> tuple:
        """Make HTTP request and return (success, response_data, status_code)"""
        url = f"{self.base_url}{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params, timeout=60)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=60)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=60)
            else:
                return False, {}, 0
                
            return True, response.json() if response.content else {}, response.status_code
            
        except requests.exceptions.Timeout:
            return False, {"error": "Request timeout"}, 0
        except requests.exceptions.ConnectionError:
            return False, {"error": "Connection error"}, 0
        except Exception as e:
            return False, {"error": str(e)}, 0

    def make_multipart_request(self, method: str, endpoint: str, files: dict = None, data: dict = None) -> tuple:
        """Make multipart HTTP request for file uploads"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method == 'POST':
                response = requests.post(url, files=files, data=data, timeout=60)
            else:
                return False, {}, 0
                
            return True, response.json() if response.content else {}, response.status_code
            
        except requests.exceptions.Timeout:
            return False, {"error": "Request timeout"}, 0
        except requests.exceptions.ConnectionError:
            return False, {"error": "Connection error"}, 0
        except Exception as e:
            return False, {"error": str(e)}, 0

    def test_review_request_quick_check(self):
        """Quick re-check of AI Knowledge diagnostics after sslrootcert addition"""
        print("\n🧠 QUICK RE-CHECK: AI KNOWLEDGE DIAGNOSTICS")
        print("=" * 70)
        print("Testing after adding sslrootcert:")
        print("1) GET /api/ai-knowledge/db-dsn — normalized.query должен содержать 'sslmode=require'")
        print("2) GET /api/ai-knowledge/db-check — ожидаем connected=true")
        print("-" * 70)
        
        # Test 1: GET /api/ai-knowledge/db-dsn
        self.test_ai_db_dsn_quick()
        
        # Test 2: GET /api/ai-knowledge/db-check
        self.test_ai_db_check_quick()
    
    def test_ai_db_dsn_quick(self):
        """Test 1: GET /api/ai-knowledge/db-dsn - normalized.query должен содержать 'sslmode=require'"""
        print("\n1️⃣ Testing GET /api/ai-knowledge/db-dsn")
        
        success, data, status = self.make_request('GET', '/api/ai-knowledge/db-dsn')
        
        if success and status == 200:
            print(f"   Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            # Check for normalized field
            if 'normalized' in data:
                normalized = data['normalized']
                if isinstance(normalized, dict):
                    query = normalized.get('query', '')
                    
                    # Check query contains sslmode=require
                    if 'sslmode=require' in str(query):
                        self.log_test("DB DSN - sslmode=require in query", True, 
                                    f"✅ normalized.query содержит 'sslmode=require': {query}")
                    else:
                        self.log_test("DB DSN - sslmode=require in query", False, 
                                    f"❌ normalized.query НЕ содержит 'sslmode=require': {query}")
                elif isinstance(normalized, str):
                    # Handle case where normalized might be a string
                    if 'sslmode=require' in normalized:
                        self.log_test("DB DSN - sslmode=require in query", True, 
                                    f"✅ normalized содержит 'sslmode=require': {normalized}")
                    else:
                        self.log_test("DB DSN - sslmode=require in query", False, 
                                    f"❌ normalized НЕ содержит 'sslmode=require': {normalized}")
                else:
                    self.log_test("DB DSN - sslmode=require in query", False, 
                                f"❌ normalized имеет неожиданный тип: {type(normalized)}")
            else:
                self.log_test("DB DSN - sslmode=require in query", False, 
                            "❌ Отсутствует поле 'normalized' в ответе")
        else:
            self.log_test("DB DSN - sslmode=require in query", False, 
                        f"❌ Status: {status}, Data: {data}")
    
    def test_ai_db_check_quick(self):
        """Test 2: GET /api/ai-knowledge/db-check - ожидаем connected=true"""
        print("\n2️⃣ Testing GET /api/ai-knowledge/db-check")
        
        success, data, status = self.make_request('GET', '/api/ai-knowledge/db-check')
        
        if success and status == 200:
            print(f"   Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            connected = data.get('connected', False)
            errors = data.get('errors', [])
            
            if connected:
                self.log_test("DB Check - connected=true", True, 
                            "✅ connected=true - база данных подключена успешно")
            else:
                error_details = errors if errors else ["Нет конкретных ошибок"]
                self.log_test("DB Check - connected=true", False, 
                            f"❌ connected=false. Errors: {error_details}")
                
                # Print detailed error information
                if errors:
                    print("   📋 Детальные ошибки:")
                    for i, error in enumerate(errors, 1):
                        print(f"      {i}. {error}")
        else:
            self.log_test("DB Check - connected=true", False, 
                        f"❌ Status: {status}, Data: {data}")

    def run_quick_check(self):
        """Run quick re-check tests for the review request"""
        print(f"🚀 VasDom AudioBot Backend API - Quick Re-check after sslrootcert")
        print(f"📍 Base URL: {self.base_url}")
        print("🔧 Проверка диагностических эндпоинтов AI Knowledge")
        print("=" * 80)
        
        # Quick diagnostics check
        self.test_review_request_quick_check()
        
        # Final summary
        self.print_summary()
    
    def test_ai_db_dsn(self):
        """Test 1: GET /api/ai-knowledge/db-dsn - should return normalized.scheme='postgresql' and normalized.query='sslmode=require'"""
        print("\n1️⃣ Testing GET /api/ai-knowledge/db-dsn")
        
        success, data, status = self.make_request('GET', '/api/ai-knowledge/db-dsn')
        
        if success and status == 200:
            # Check for normalized field
            if 'normalized' in data:
                normalized = data['normalized']
                if isinstance(normalized, dict):
                    scheme = normalized.get('scheme', '')
                    query = normalized.get('query', '')
                    
                    # Check scheme
                    if scheme == 'postgresql':
                        scheme_ok = True
                    else:
                        scheme_ok = False
                    
                    # Check query contains sslmode=require
                    if 'sslmode=require' in query:
                        query_ok = True
                    else:
                        query_ok = False
                    
                    if scheme_ok and query_ok:
                        self.log_test("AI DB DSN - Normalized Format", True, 
                                    f"scheme='postgresql' ✓, query contains 'sslmode=require' ✓")
                    else:
                        issues = []
                        if not scheme_ok:
                            issues.append(f"scheme='{scheme}' (expected 'postgresql')")
                        if not query_ok:
                            issues.append(f"query='{query}' (missing 'sslmode=require')")
                        self.log_test("AI DB DSN - Normalized Format", False, f"Issues: {', '.join(issues)}")
                else:
                    self.log_test("AI DB DSN - Normalized Format", False, f"normalized should be dict, got {type(normalized)}")
            else:
                self.log_test("AI DB DSN - Normalized Format", False, "Missing 'normalized' field in response")
        else:
            self.log_test("AI DB DSN - Normalized Format", False, f"Status: {status}, Data: {data}")
    
    def test_ai_db_check(self):
        """Test 2: GET /api/ai-knowledge/db-check - should return connected=true"""
        print("\n2️⃣ Testing GET /api/ai-knowledge/db-check")
        
        success, data, status = self.make_request('GET', '/api/ai-knowledge/db-check')
        
        if success and status == 200:
            connected = data.get('connected', False)
            errors = data.get('errors', [])
            
            if connected:
                self.log_test("AI DB Check - Connection", True, "connected=true ✓")
                return data
            else:
                error_summary = errors[:3] if errors else ['No specific errors']
                self.log_test("AI DB Check - Connection", False, f"connected=false, errors: {error_summary}")
                return data
        else:
            self.log_test("AI DB Check - Connection", False, f"Status: {status}, Data: {data}")
            return None
    
    def test_ai_preview(self):
        """Test 3: POST /api/ai-knowledge/preview - multipart with files, expect upload_id and chunks>0"""
        print("\n3️⃣ Testing POST /api/ai-knowledge/preview")
        
        # Create test file content
        test_content = "Hello AI psycopg3. This is a test document for the VasDom AudioBot system."
        files = {'files': ('test_psycopg3.txt', test_content.encode('utf-8'), 'text/plain')}
        
        success, data, status = self.make_multipart_request('POST', '/api/ai-knowledge/preview', files=files)
        
        if success and status == 200:
            upload_id = data.get('upload_id')
            chunks = data.get('chunks', 0)
            
            if upload_id and chunks > 0:
                self.log_test("AI Preview - File Upload", True, 
                            f"upload_id: {upload_id[:8]}..., chunks: {chunks} ✓")
                self.upload_id = upload_id
                return upload_id
            else:
                self.log_test("AI Preview - File Upload", False, 
                            f"Missing upload_id or chunks=0: upload_id={upload_id}, chunks={chunks}")
        else:
            self.log_test("AI Preview - File Upload", False, f"Status: {status}, Data: {data}")
        
        return None
    
    def test_ai_status(self, upload_id):
        """Test 4: GET /api/ai-knowledge/status?upload_id=<id> - expect status='ready'"""
        print(f"\n4️⃣ Testing GET /api/ai-knowledge/status?upload_id={upload_id[:8]}...")
        
        success, data, status = self.make_request('GET', '/api/ai-knowledge/status', params={'upload_id': upload_id})
        
        if success and status == 200:
            upload_status = data.get('status', '')
            
            if upload_status == 'ready':
                self.log_test("AI Status - Upload Ready", True, "status='ready' ✓")
            else:
                self.log_test("AI Status - Upload Ready", False, f"status='{upload_status}' (expected 'ready')")
        else:
            self.log_test("AI Status - Upload Ready", False, f"Status: {status}, Data: {data}")
    
    def test_ai_study(self, upload_id):
        """Test 5: POST /api/ai-knowledge/study - form data, expect document_id and chunks>=1"""
        print(f"\n5️⃣ Testing POST /api/ai-knowledge/study")
        
        form_data = {
            'upload_id': upload_id,
            'filename': 'psycopg3.txt',
            'category': 'Маркетинг'
        }
        
        success, data, status = self.make_multipart_request('POST', '/api/ai-knowledge/study', data=form_data)
        
        if success and status == 200:
            document_id = data.get('document_id')
            chunks = data.get('chunks', 0)
            
            if document_id and chunks >= 1:
                self.log_test("AI Study - Document Created", True, 
                            f"document_id: {document_id[:8]}..., chunks: {chunks} ✓")
                self.document_id = document_id
                return document_id
            else:
                self.log_test("AI Study - Document Created", False, 
                            f"Missing document_id or chunks<1: document_id={document_id}, chunks={chunks}")
        else:
            self.log_test("AI Study - Document Created", False, f"Status: {status}, Data: {data}")
        
        return None
    
    def test_ai_documents(self):
        """Test 6: GET /api/ai-knowledge/documents - should show document with chunks_count>=1"""
        print("\n6️⃣ Testing GET /api/ai-knowledge/documents")
        
        success, data, status = self.make_request('GET', '/api/ai-knowledge/documents')
        
        if success and status == 200:
            documents = data.get('documents', [])
            
            if documents:
                # Find our test document
                test_doc = None
                for doc in documents:
                    if doc.get('filename') == 'psycopg3.txt':
                        test_doc = doc
                        break
                
                if test_doc:
                    chunks_count = test_doc.get('chunks_count', 0)
                    if chunks_count >= 1:
                        self.log_test("AI Documents - Test Document Present", True, 
                                    f"Found 'psycopg3.txt' with chunks_count: {chunks_count} ✓")
                    else:
                        self.log_test("AI Documents - Test Document Present", False, 
                                    f"Document found but chunks_count={chunks_count} (expected >=1)")
                else:
                    self.log_test("AI Documents - Test Document Present", False, 
                                "Test document 'psycopg3.txt' not found in documents list")
            else:
                self.log_test("AI Documents - Test Document Present", False, "No documents found")
        else:
            self.log_test("AI Documents - Test Document Present", False, f"Status: {status}, Data: {data}")
    
    def test_ai_search_psycopg3(self):
        """Test 7: POST /api/ai-knowledge/search - body {"query":"psycopg3","top_k":5} - expect results[]"""
        print("\n7️⃣ Testing POST /api/ai-knowledge/search")
        
        search_data = {
            'query': 'psycopg3',
            'top_k': 5
        }
        
        success, data, status = self.make_request('POST', '/api/ai-knowledge/search', search_data)
        
        if success and status == 200:
            results = data.get('results', [])
            
            if isinstance(results, list):
                self.log_test("AI Search - Query Results", True, 
                            f"Search returned {len(results)} results ✓")
                
                # Check if any results contain our test content
                if results:
                    found_psycopg3 = any('psycopg3' in result.get('content', '').lower() for result in results)
                    if found_psycopg3:
                        self.log_test("AI Search - Content Match", True, "Found 'psycopg3' in search results ✓")
                    else:
                        self.log_test("AI Search - Content Match", False, "No results contain 'psycopg3'")
            else:
                self.log_test("AI Search - Query Results", False, f"results should be array, got {type(results)}")
        else:
            self.log_test("AI Search - Query Results", False, f"Status: {status}, Data: {data}")
    
    def test_ai_delete_document_final(self, document_id):
        """Test 8: DELETE /api/ai-knowledge/document/{document_id} - expect 200 {ok:true}"""
        print(f"\n8️⃣ Testing DELETE /api/ai-knowledge/document/{document_id[:8]}...")
        
        success, data, status = self.make_request('DELETE', f'/api/ai-knowledge/document/{document_id}')
        
        if success and status == 200:
            ok = data.get('ok', False)
            
            if ok is True:
                self.log_test("AI Delete - Document Removed", True, "Document deleted successfully ✓")
            else:
                self.log_test("AI Delete - Document Removed", False, f"Expected ok=true, got ok={ok}")
        else:
            self.log_test("AI Delete - Document Removed", False, f"Status: {status}, Data: {data}")
    
    def test_review_request_crm_regression(self):
        """Test CRM regression as per review request"""
        print("\n🏠 REVIEW REQUEST: CRM REGRESSION TESTS")
        print("=" * 70)
        
        # Test 9: GET /api/cleaning/filters
        self.test_crm_filters_regression()
        
        # Test 10: GET /api/cleaning/houses?page=1&limit=5
        self.test_crm_houses_regression()
    
    def test_crm_filters_regression(self):
        """Test 9: GET /api/cleaning/filters - expect 200"""
        print("\n9️⃣ Testing GET /api/cleaning/filters (regression)")
        
        success, data, status = self.make_request('GET', '/api/cleaning/filters')
        
        if success and status == 200:
            # Check basic structure
            if isinstance(data, dict):
                required_fields = ['brigades', 'management_companies', 'statuses']
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    brigades_count = len(data.get('brigades', []))
                    companies_count = len(data.get('management_companies', []))
                    statuses_count = len(data.get('statuses', []))
                    
                    self.log_test("CRM Filters - Regression", True, 
                                f"Structure valid: brigades={brigades_count}, companies={companies_count}, statuses={statuses_count} ✓")
                else:
                    self.log_test("CRM Filters - Regression", False, f"Missing fields: {missing_fields}")
            else:
                self.log_test("CRM Filters - Regression", False, f"Expected dict, got {type(data)}")
        else:
            self.log_test("CRM Filters - Regression", False, f"Status: {status}, Data: {data}")
    
    def test_crm_houses_regression(self):
        """Test 10: GET /api/cleaning/houses?page=1&limit=5 - expect 200"""
        print("\n🔟 Testing GET /api/cleaning/houses?page=1&limit=5 (regression)")
        
        success, data, status = self.make_request('GET', '/api/cleaning/houses', params={'page': 1, 'limit': 5})
        
        if success and status == 200:
            # Check basic structure
            if isinstance(data, dict):
                required_fields = ['houses', 'total', 'page', 'limit', 'pages']
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    houses = data.get('houses', [])
                    total = data.get('total', 0)
                    page = data.get('page', 0)
                    limit = data.get('limit', 0)
                    pages = data.get('pages', 0)
                    
                    self.log_test("CRM Houses - Regression", True, 
                                f"Structure valid: houses={len(houses)}, total={total}, page={page}, limit={limit}, pages={pages} ✓")
                else:
                    self.log_test("CRM Houses - Regression", False, f"Missing fields: {missing_fields}")
            else:
                self.log_test("CRM Houses - Regression", False, f"Expected dict, got {type(data)}")
        else:
            self.log_test("CRM Houses - Regression", False, f"Status: {status}, Data: {data}")

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 80)
        print("🎯 TEST SUMMARY")
        print("=" * 80)
        print(f"Total Tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {len(self.failed_tests)}")
        
        if self.tests_run > 0:
            success_rate = (self.tests_passed / self.tests_run) * 100
            print(f"Success Rate: {success_rate:.1f}%")
        
        if self.failed_tests:
            print(f"\n❌ FAILED TESTS ({len(self.failed_tests)}):")
            for i, test in enumerate(self.failed_tests, 1):
                print(f"{i}. {test['name']}")
                if test['details']:
                    print(f"   {test['details']}")
        
        print("\n" + "=" * 80)

    def run_review_request_tests(self):
        """Run specific tests for the review request"""
        print(f"🚀 VasDom AudioBot Backend API - Review Request Testing")
        print(f"📍 Base URL: {self.base_url}")
        print("🔧 Testing after fixes: scrub PGSSL env, sslmode=require, keepalive/timeout")
        print("=" * 80)
        
        # AI Knowledge endpoints (Tests 1-8)
        self.test_review_request_ai_knowledge()
        
        # CRM regression tests (Tests 9-10)
        self.test_review_request_crm_regression()
        
        # Final summary
        self.print_summary()

if __name__ == "__main__":
    tester = VasDomAPITester()
    tester.run_quick_check()