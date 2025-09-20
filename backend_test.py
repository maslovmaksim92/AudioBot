#!/usr/bin/env python3
"""
VasDom AudioBot Backend API Testing - Full Review Request Testing
Testing comprehensive backend endpoints per review request:

AI Knowledge (psycopg3):
1) GET /api/ai-knowledge/db-dsn — 200; normalized.scheme='postgresql', normalized.query содержит sslmode='require', raw_present=true
2) GET /api/ai-knowledge/db-check — 200; ожидаем connected=true, ai_tables включает ai_documents/ai_chunks/ai_uploads_temp; embedding_dims=1536
3) POST /api/ai-knowledge/preview — multipart с ключом files и одним TXT ("Hello AI psycopg3 end-to-end"); 200: upload_id, chunks>0, stats.total_size_bytes>0
4) GET /api/ai-knowledge/status?upload_id=<id> — 200: status='ready'
5) POST /api/ai-knowledge/study — form: upload_id, filename='psycopg3.txt', category='Маркетинг'; 200: document_id, chunks>=1, category='Маркетинг'
6) GET /api/ai-knowledge/documents — 200; документ из (5) присутствует, chunks_count>=1
7) POST /api/ai-knowledge/search — body {"query":"psycopg3","top_k":5} — 200, results[] не пуст
8) DELETE /api/ai-knowledge/document/{document_id} — 200 {ok:true}

Регресс CRM:
9) GET /api/cleaning/filters — 200
10) GET /api/cleaning/houses?page=1&limit=5 — 200

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

    def test_review_request_ai_knowledge(self):
        """Run full AI Knowledge flow testing per review request"""
        print("\n🧠 AI KNOWLEDGE ENDPOINTS (psycopg3)")
        print("=" * 70)
        print("Testing full AI Knowledge flow:")
        print("1) db-dsn → 2) db-check → 3) preview → 4) status → 5) study → 6) documents → 7) search → 8) delete")
        print("-" * 70)
        
        # Test 1: GET /api/ai-knowledge/db-dsn
        self.test_ai_db_dsn()
        
        # Test 2: GET /api/ai-knowledge/db-check
        db_check_data = self.test_ai_db_check()
        
        # Only proceed with AI flow if database is connected
        if db_check_data and db_check_data.get('connected', False):
            print("\n✅ Database connected - proceeding with AI flow tests")
            
            # Test 3: POST /api/ai-knowledge/preview
            upload_id = self.test_ai_preview()
            
            if upload_id:
                # Test 4: GET /api/ai-knowledge/status
                self.test_ai_status(upload_id)
                
                # Test 5: POST /api/ai-knowledge/study
                document_id = self.test_ai_study(upload_id)
                
                if document_id:
                    # Test 6: GET /api/ai-knowledge/documents
                    self.test_ai_documents()
                    
                    # Test 7: POST /api/ai-knowledge/search
                    self.test_ai_search_psycopg3()
                    
                    # Test 8: DELETE /api/ai-knowledge/document/{document_id}
                    self.test_ai_delete_document_final(document_id)
                else:
                    print("❌ Cannot proceed with documents/search/delete tests - no document_id from study")
            else:
                print("❌ Cannot proceed with AI flow tests - no upload_id from preview")
        else:
            print("❌ Cannot proceed with AI flow tests - database not connected")
            # Still test the endpoints to see their error responses
            print("\n⚠️ Testing AI endpoints without database connection:")
            self.test_ai_preview()
            self.test_ai_documents()
            self.test_ai_search_psycopg3()
    
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
                    query = normalized.get('query', {})
                    
                    # Check if query is dict and contains sslmode=require
                    if isinstance(query, dict):
                        sslmode_value = query.get('sslmode', '')
                        if sslmode_value == 'require':
                            self.log_test("DB DSN - sslmode=require in query", True, 
                                        f"✅ normalized.query содержит sslmode='require': {query}")
                        else:
                            self.log_test("DB DSN - sslmode=require in query", False, 
                                        f"❌ normalized.query.sslmode='{sslmode_value}' (ожидалось 'require'): {query}")
                    elif isinstance(query, str):
                        # Handle case where query might be a string
                        if 'sslmode=require' in query:
                            self.log_test("DB DSN - sslmode=require in query", True, 
                                        f"✅ normalized.query содержит 'sslmode=require': {query}")
                        else:
                            self.log_test("DB DSN - sslmode=require in query", False, 
                                        f"❌ normalized.query НЕ содержит 'sslmode=require': {query}")
                    else:
                        self.log_test("DB DSN - sslmode=require in query", False, 
                                    f"❌ normalized.query имеет неожиданный тип: {type(query)}")
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
        """Test 1: GET /api/ai-knowledge/db-dsn - should return normalized.scheme='postgresql', normalized.query contains sslmode='require', raw_present=true"""
        print("\n1️⃣ Testing GET /api/ai-knowledge/db-dsn")
        
        success, data, status = self.make_request('GET', '/api/ai-knowledge/db-dsn')
        
        if success and status == 200:
            print(f"   Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            # Check for normalized field
            if 'normalized' in data:
                normalized = data['normalized']
                if isinstance(normalized, dict):
                    scheme = normalized.get('scheme', '')
                    query = normalized.get('query', '')
                    
                    # Check scheme
                    scheme_ok = scheme == 'postgresql'
                    
                    # Check query contains sslmode=require (handle both dict and string formats)
                    query_ok = False
                    if isinstance(query, dict):
                        query_ok = query.get('sslmode') == 'require'
                    elif isinstance(query, str):
                        query_ok = 'sslmode=require' in query
                    
                    # Check raw_present
                    raw_present = data.get('raw_present', False)
                    
                    if scheme_ok and query_ok and raw_present:
                        self.log_test("AI DB DSN - Full Requirements", True, 
                                    f"✅ normalized.scheme='postgresql' ✓, normalized.query contains sslmode='require' ✓, raw_present=true ✓")
                    else:
                        issues = []
                        if not scheme_ok:
                            issues.append(f"scheme='{scheme}' (expected 'postgresql')")
                        if not query_ok:
                            issues.append(f"query missing sslmode='require': {query}")
                        if not raw_present:
                            issues.append(f"raw_present={raw_present} (expected true)")
                        self.log_test("AI DB DSN - Full Requirements", False, f"❌ Issues: {', '.join(issues)}")
                else:
                    self.log_test("AI DB DSN - Full Requirements", False, f"❌ normalized should be dict, got {type(normalized)}")
            else:
                self.log_test("AI DB DSN - Full Requirements", False, "❌ Missing 'normalized' field in response")
        else:
            self.log_test("AI DB DSN - Full Requirements", False, f"❌ Status: {status}, Data: {data}")
    
    def test_ai_db_check(self):
        """Test 2: GET /api/ai-knowledge/db-check - should return connected=true, ai_tables includes required tables, embedding_dims=1536"""
        print("\n2️⃣ Testing GET /api/ai-knowledge/db-check")
        
        success, data, status = self.make_request('GET', '/api/ai-knowledge/db-check')
        
        if success and status == 200:
            print(f"   Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            connected = data.get('connected', False)
            ai_tables = data.get('ai_tables', [])
            embedding_dims = data.get('embedding_dims')
            errors = data.get('errors', [])
            
            # Check required AI tables
            required_tables = {'ai_documents', 'ai_chunks', 'ai_uploads_temp'}
            found_tables = set(ai_tables) if isinstance(ai_tables, list) else set()
            tables_ok = required_tables.issubset(found_tables)
            
            # Check embedding dimensions
            dims_ok = embedding_dims == 1536
            
            if connected and tables_ok and dims_ok:
                self.log_test("AI DB Check - Full Requirements", True, 
                            f"✅ connected=true ✓, ai_tables includes {required_tables} ✓, embedding_dims=1536 ✓")
                return data
            else:
                issues = []
                if not connected:
                    issues.append(f"connected=false (errors: {errors[:2]})")
                if not tables_ok:
                    missing = required_tables - found_tables
                    issues.append(f"missing ai_tables: {missing}")
                if not dims_ok:
                    issues.append(f"embedding_dims={embedding_dims} (expected 1536)")
                self.log_test("AI DB Check - Full Requirements", False, f"❌ Issues: {', '.join(issues)}")
                return data
        else:
            self.log_test("AI DB Check - Full Requirements", False, f"❌ Status: {status}, Data: {data}")
            return None
    
    def test_ai_preview(self):
        """Test 3: POST /api/ai-knowledge/preview - multipart with files key and TXT file, expect upload_id, chunks>0, stats.total_size_bytes>0"""
        print("\n3️⃣ Testing POST /api/ai-knowledge/preview")
        
        # Create test file content as specified in review request
        test_content = "Hello AI psycopg3 end-to-end. This is a comprehensive test document for the VasDom AudioBot system using psycopg3 async database connectivity."
        files = {'files': ('test_psycopg3.txt', test_content.encode('utf-8'), 'text/plain')}
        
        success, data, status = self.make_multipart_request('POST', '/api/ai-knowledge/preview', files=files)
        
        if success and status == 200:
            print(f"   Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            upload_id = data.get('upload_id')
            chunks = data.get('chunks', 0)
            stats = data.get('stats', {})
            total_size_bytes = stats.get('total_size_bytes', 0) if isinstance(stats, dict) else 0
            
            if upload_id and chunks > 0 and total_size_bytes > 0:
                self.log_test("AI Preview - File Upload", True, 
                            f"✅ upload_id: {upload_id[:8]}..., chunks: {chunks} ✓, stats.total_size_bytes: {total_size_bytes} ✓")
                self.upload_id = upload_id
                return upload_id
            else:
                issues = []
                if not upload_id:
                    issues.append("missing upload_id")
                if chunks <= 0:
                    issues.append(f"chunks={chunks} (expected >0)")
                if total_size_bytes <= 0:
                    issues.append(f"stats.total_size_bytes={total_size_bytes} (expected >0)")
                self.log_test("AI Preview - File Upload", False, f"❌ Issues: {', '.join(issues)}")
        else:
            self.log_test("AI Preview - File Upload", False, f"❌ Status: {status}, Data: {data}")
        
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
        """Test 5: POST /api/ai-knowledge/study - form data with upload_id, filename='psycopg3.txt', category='Маркетинг', expect document_id, chunks>=1, category='Маркетинг'"""
        print(f"\n5️⃣ Testing POST /api/ai-knowledge/study")
        
        form_data = {
            'upload_id': upload_id,
            'filename': 'psycopg3.txt',
            'category': 'Маркетинг'
        }
        
        success, data, status = self.make_multipart_request('POST', '/api/ai-knowledge/study', data=form_data)
        
        if success and status == 200:
            print(f"   Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            document_id = data.get('document_id')
            chunks = data.get('chunks', 0)
            category = data.get('category', '')
            
            if document_id and chunks >= 1 and category == 'Маркетинг':
                self.log_test("AI Study - Document Created", True, 
                            f"✅ document_id: {document_id[:8]}..., chunks: {chunks} ✓, category: '{category}' ✓")
                self.document_id = document_id
                return document_id
            else:
                issues = []
                if not document_id:
                    issues.append("missing document_id")
                if chunks < 1:
                    issues.append(f"chunks={chunks} (expected >=1)")
                if category != 'Маркетинг':
                    issues.append(f"category='{category}' (expected 'Маркетинг')")
                self.log_test("AI Study - Document Created", False, f"❌ Issues: {', '.join(issues)}")
        else:
            self.log_test("AI Study - Document Created", False, f"❌ Status: {status}, Data: {data}")
        
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