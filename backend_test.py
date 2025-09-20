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
            
            # Try to parse JSON response, but handle non-JSON responses
            try:
                response_data = response.json() if response.content else {}
            except:
                # If JSON parsing fails, return the text content
                response_data = {"error": "Non-JSON response", "content": response.text[:500]}
                
            return True, response_data, response.status_code
            
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
        """Test 7: POST /api/ai-knowledge/search - body {"query":"psycopg3","top_k":5} - expect 200, results[] не пуст"""
        print("\n7️⃣ Testing POST /api/ai-knowledge/search")
        
        search_data = {
            'query': 'psycopg3',
            'top_k': 5
        }
        
        success, data, status = self.make_request('POST', '/api/ai-knowledge/search', search_data)
        
        if success and status == 200:
            print(f"   Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            results = data.get('results', [])
            
            if isinstance(results, list) and len(results) > 0:
                self.log_test("AI Search - Query Results", True, 
                            f"✅ Search returned {len(results)} results (results[] не пуст) ✓")
                
                # Check if any results contain our test content
                found_psycopg3 = any('psycopg3' in result.get('content', '').lower() for result in results)
                if found_psycopg3:
                    self.log_test("AI Search - Content Match", True, "✅ Found 'psycopg3' in search results ✓")
                else:
                    self.log_test("AI Search - Content Match", False, "❌ No results contain 'psycopg3'")
            else:
                if isinstance(results, list):
                    self.log_test("AI Search - Query Results", False, f"❌ results[] is empty (expected не пуст)")
                else:
                    self.log_test("AI Search - Query Results", False, f"❌ results should be array, got {type(results)}")
        elif status == 500:
            # Handle database connection issues gracefully
            self.log_test("AI Search - Query Results", False, f"❌ Status: {status} - Database connection issue (expected due to SSL errors)")
        else:
            self.log_test("AI Search - Query Results", False, f"❌ Status: {status}, Data: {data}")
    
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

    def test_mini_flow_review_request(self):
        """Mini-flow review request testing as specified"""
        print(f"🚀 VasDom AudioBot Backend API - Mini‑flow на проде")
        print(f"📍 Base URL: {self.base_url}")
        print("🔧 Testing AI Knowledge Mini-Flow per review request:")
        print("1) POST /api/ai-knowledge/preview — multipart (files: 1 txt файл с содержимым \"Search mini flow psycopg3 works\") → ожидаем 200: upload_id, chunks>0")
        print("2) GET /api/ai-knowledge/status?upload_id=<id> — ожидаем 200: status='ready'")
        print("3) POST /api/ai-knowledge/study — form: upload_id, filename='mini.txt', category='Маркетинг' → ожидаем 200: document_id, chunks>=1")
        print("4) GET /api/ai-knowledge/documents — ожидаем 200: есть документ из (3)")
        print("5) POST /api/ai-knowledge/search — body {\"query\":\"psycopg3\",\"top_k\":5} → ожидаем 200 и непустой results[]")
        print("=" * 80)
        
        # Test 1: POST /api/ai-knowledge/preview
        upload_id = self.test_mini_flow_preview()
        
        if upload_id:
            # Test 2: GET /api/ai-knowledge/status
            self.test_mini_flow_status(upload_id)
            
            # Test 3: POST /api/ai-knowledge/study
            document_id = self.test_mini_flow_study(upload_id)
            
            if document_id:
                # Test 4: GET /api/ai-knowledge/documents
                self.test_mini_flow_documents()
                
                # Test 5: POST /api/ai-knowledge/search
                self.test_mini_flow_search()
            else:
                print("❌ Cannot proceed with documents/search tests - no document_id from study")
        else:
            print("❌ Cannot proceed with mini-flow tests - no upload_id from preview")
        
        # Final summary
        self.print_summary()

    def test_mini_flow_preview(self):
        """Test 1: POST /api/ai-knowledge/preview - multipart with specific content"""
        print("\n1️⃣ Testing POST /api/ai-knowledge/preview")
        print("   Content: 'Search mini flow psycopg3 works'")
        print("   Expected: 200: upload_id, chunks>0")
        
        # Create test file content as specified in review request
        test_content = "Search mini flow psycopg3 works"
        files = {'files': ('mini.txt', test_content.encode('utf-8'), 'text/plain')}
        
        success, data, status = self.make_multipart_request('POST', '/api/ai-knowledge/preview', files=files)
        
        if success and status == 200:
            print(f"   ✅ Status: {status} ✓")
            print(f"   Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            upload_id = data.get('upload_id')
            chunks = data.get('chunks', 0)
            
            if upload_id and chunks > 0:
                self.log_test("Mini-Flow Preview", True, 
                            f"✅ upload_id: {upload_id[:8]}..., chunks: {chunks} ✓")
                self.upload_id = upload_id
                return upload_id
            else:
                issues = []
                if not upload_id:
                    issues.append("missing upload_id")
                if chunks <= 0:
                    issues.append(f"chunks={chunks} (expected >0)")
                self.log_test("Mini-Flow Preview", False, f"❌ Issues: {', '.join(issues)}")
        else:
            print(f"   ❌ Status: {status}")
            print(f"   Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
            self.log_test("Mini-Flow Preview", False, f"❌ Status: {status} (expected 200), Data: {data}")
        
        return None

    def test_mini_flow_status(self, upload_id):
        """Test 2: GET /api/ai-knowledge/status?upload_id=<id> - expect status='ready'"""
        print(f"\n2️⃣ Testing GET /api/ai-knowledge/status?upload_id={upload_id[:8]}...")
        print("   Expected: 200: status='ready'")
        
        success, data, status = self.make_request('GET', '/api/ai-knowledge/status', params={'upload_id': upload_id})
        
        if success and status == 200:
            print(f"   ✅ Status: {status} ✓")
            print(f"   Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            upload_status = data.get('status', '')
            
            if upload_status == 'ready':
                self.log_test("Mini-Flow Status", True, "✅ status='ready' ✓")
            else:
                self.log_test("Mini-Flow Status", False, f"❌ status='{upload_status}' (expected 'ready')")
        else:
            print(f"   ❌ Status: {status}")
            print(f"   Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
            self.log_test("Mini-Flow Status", False, f"❌ Status: {status} (expected 200), Data: {data}")

    def test_mini_flow_study(self, upload_id):
        """Test 3: POST /api/ai-knowledge/study - form data with specific parameters"""
        print(f"\n3️⃣ Testing POST /api/ai-knowledge/study")
        print("   Form: upload_id, filename='mini.txt', category='Маркетинг'")
        print("   Expected: 200: document_id, chunks>=1")
        
        form_data = {
            'upload_id': upload_id,
            'filename': 'mini.txt',
            'category': 'Маркетинг'
        }
        
        success, data, status = self.make_multipart_request('POST', '/api/ai-knowledge/study', data=form_data)
        
        if success and status == 200:
            print(f"   ✅ Status: {status} ✓")
            print(f"   Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            document_id = data.get('document_id')
            chunks = data.get('chunks', 0)
            
            if document_id and chunks >= 1:
                self.log_test("Mini-Flow Study", True, 
                            f"✅ document_id: {document_id[:8]}..., chunks: {chunks} ✓")
                self.document_id = document_id
                return document_id
            else:
                issues = []
                if not document_id:
                    issues.append("missing document_id")
                if chunks < 1:
                    issues.append(f"chunks={chunks} (expected >=1)")
                self.log_test("Mini-Flow Study", False, f"❌ Issues: {', '.join(issues)}")
        else:
            print(f"   ❌ Status: {status}")
            print(f"   Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
            self.log_test("Mini-Flow Study", False, f"❌ Status: {status} (expected 200), Data: {data}")
        
        return None

    def test_mini_flow_documents(self):
        """Test 4: GET /api/ai-knowledge/documents - should show document from study"""
        print("\n4️⃣ Testing GET /api/ai-knowledge/documents")
        print("   Expected: 200: есть документ из (3)")
        
        success, data, status = self.make_request('GET', '/api/ai-knowledge/documents')
        
        if success and status == 200:
            print(f"   ✅ Status: {status} ✓")
            
            documents = data.get('documents', [])
            print(f"   Total documents: {len(documents)}")
            
            if documents:
                # Find our test document
                test_doc = None
                for doc in documents:
                    if doc.get('filename') == 'mini.txt':
                        test_doc = doc
                        break
                
                if test_doc:
                    chunks_count = test_doc.get('chunks_count', 0)
                    print(f"   Found 'mini.txt': {json.dumps(test_doc, indent=2, ensure_ascii=False)}")
                    self.log_test("Mini-Flow Documents", True, 
                                f"✅ Found 'mini.txt' with chunks_count: {chunks_count} ✓")
                else:
                    self.log_test("Mini-Flow Documents", False, 
                                "❌ Test document 'mini.txt' not found in documents list")
            else:
                self.log_test("Mini-Flow Documents", False, "❌ No documents found")
        else:
            print(f"   ❌ Status: {status}")
            print(f"   Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
            self.log_test("Mini-Flow Documents", False, f"❌ Status: {status} (expected 200), Data: {data}")

    def test_mini_flow_search(self):
        """Test 5: POST /api/ai-knowledge/search - body {"query":"psycopg3","top_k":5} - expect 200 and non-empty results[]"""
        print("\n5️⃣ Testing POST /api/ai-knowledge/search")
        print("   Body: {\"query\":\"psycopg3\",\"top_k\":5}")
        print("   Expected: 200 и непустой results[]")
        
        search_data = {
            'query': 'psycopg3',
            'top_k': 5
        }
        
        success, data, status = self.make_request('POST', '/api/ai-knowledge/search', search_data)
        
        if success and status == 200:
            print(f"   ✅ Status: {status} ✓")
            print(f"   Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            results = data.get('results', [])
            
            if isinstance(results, list) and len(results) > 0:
                self.log_test("Mini-Flow Search", True, 
                            f"✅ Status 200 ✓, results[] не пуст ✓ (размер массива: {len(results)})")
                
                # Show example results as requested
                print(f"   📋 Примеры результатов поиска:")
                for i, result in enumerate(results[:2], 1):  # Show first 2 results
                    print(f"   {i}. {json.dumps(result, indent=2, ensure_ascii=False)}")
            else:
                if isinstance(results, list):
                    self.log_test("Mini-Flow Search", False, 
                                f"❌ Status 200 ✓, но results[] пуст (размер массива: {len(results)})")
                else:
                    self.log_test("Mini-Flow Search", False, 
                                f"❌ Status 200 ✓, но results должен быть массивом, получен {type(results)}")
        else:
            print(f"   ❌ Status: {status}")
            print(f"   Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
            self.log_test("Mini-Flow Search", False, 
                        f"❌ Status: {status} (expected 200), Data: {data}")

    def test_quick_review_request(self):
        """Quick re-test on deploy as per review request"""
        print(f"🚀 VasDom AudioBot Backend API - Быстрый повторный тест на деплое")
        print(f"📍 Base URL: {self.base_url}")
        print("🔧 Testing specific endpoints per review request:")
        print("1) GET /api/ai-knowledge/db-check — ожидаем: Status 200, connected=true, embedding_dims=1536")
        print("2) POST /api/ai-knowledge/search — body {\"query\":\"psycopg3\",\"top_k\":5} — ожидаем Status 200 и непустой results[]")
        print("=" * 80)
        
        # Test 1: GET /api/ai-knowledge/db-check
        self.test_quick_db_check()
        
        # Check if there are documents in the database first
        self.test_documents_availability()
        
        # Test 2: POST /api/ai-knowledge/search
        self.test_quick_search_psycopg3()
        
        # Final summary
        self.print_summary()
        """Test 1: GET /api/ai-knowledge/db-check - expecting Status 200, connected=true, embedding_dims=1536"""
        print("\n1️⃣ Testing GET /api/ai-knowledge/db-check")
        print("   Expected: Status 200, connected=true, embedding_dims=1536")
        
        success, data, status = self.make_request('GET', '/api/ai-knowledge/db-check')
        
        if success and status == 200:
            print(f"   ✅ Status: {status} ✓")
            print(f"   Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            connected = data.get('connected', False)
            embedding_dims = data.get('embedding_dims')
            
            # Check connected=true
            connected_ok = connected is True
            
            # Check embedding_dims=1536
            dims_ok = embedding_dims == 1536
            
            if connected_ok and dims_ok:
                self.log_test("DB Check - Review Request Requirements", True, 
                            f"✅ Status 200 ✓, connected=true ✓, embedding_dims=1536 ✓")
            else:
                issues = []
                if not connected_ok:
                    issues.append(f"connected={connected} (expected true)")
                if not dims_ok:
                    issues.append(f"embedding_dims={embedding_dims} (expected 1536)")
                self.log_test("DB Check - Review Request Requirements", False, f"❌ Issues: {', '.join(issues)}")
        else:
            self.log_test("DB Check - Review Request Requirements", False, f"❌ Status: {status} (expected 200), Data: {data}")

    def test_documents_availability(self):
        """Check if there are any documents available for search"""
        print("\n📋 Checking document availability for search")
        
        success, data, status = self.make_request('GET', '/api/ai-knowledge/documents')
        
        if success and status == 200:
            documents = data.get('documents', [])
            print(f"   Documents in database: {len(documents)}")
            
            if documents:
                print("   Available documents:")
                for i, doc in enumerate(documents[:3], 1):  # Show first 3 documents
                    filename = doc.get('filename', 'Unknown')
                    chunks = doc.get('chunks_count', 0)
                    print(f"   {i}. {filename} ({chunks} chunks)")
            else:
                print("   ⚠️ No documents found in database - search may return empty results")
        else:
            print(f"   ❌ Failed to check documents: Status {status}")

    def test_quick_search_psycopg3(self):
        """Test 2: POST /api/ai-knowledge/search - body {"query":"psycopg3","top_k":5} - expecting Status 200 и непустой results[]"""
        print("\n2️⃣ Testing POST /api/ai-knowledge/search")
        print("   Body: {\"query\":\"psycopg3\",\"top_k\":5}")
        print("   Expected: Status 200 и непустой results[]")
        
        search_data = {
            'query': 'psycopg3',
            'top_k': 5
        }
        
        success, data, status = self.make_request('POST', '/api/ai-knowledge/search', search_data)
        
        if success and status == 200:
            print(f"   ✅ Status: {status} ✓")
            print(f"   Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            results = data.get('results', [])
            
            if isinstance(results, list) and len(results) > 0:
                self.log_test("Search - Review Request Requirements", True, 
                            f"✅ Status 200 ✓, results[] не пуст ✓ (размер массива: {len(results)})")
                
                # Show example of first element as requested
                if results:
                    first_result = results[0]
                    print(f"   📋 Пример первого элемента: {json.dumps(first_result, indent=2, ensure_ascii=False)}")
            else:
                if isinstance(results, list):
                    self.log_test("Search - Review Request Requirements", False, 
                                f"❌ Status 200 ✓, но results[] пуст (размер массива: {len(results)})")
                else:
                    self.log_test("Search - Review Request Requirements", False, 
                                f"❌ Status 200 ✓, но results должен быть массивом, получен {type(results)}")
        elif success and status == 500:
            print(f"   ❌ Status: {status} (Internal Server Error)")
            print(f"   Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
            self.log_test("Search - Review Request Requirements", False, 
                        f"❌ Status: {status} (expected 200) - Internal Server Error. Response: {data}")
        else:
            print(f"   ❌ Status: {status}")
            print(f"   Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
            self.log_test("Search - Review Request Requirements", False, 
                        f"❌ Status: {status} (expected 200), Data: {data}")

    def run_review_request_tests(self):
        """Run comprehensive tests for the review request"""
        print(f"🚀 VasDom AudioBot Backend API - Полный сквозной бэкенд‑тест")
        print(f"📍 Base URL: {self.base_url}")
        print("🔧 Testing AI Knowledge (psycopg3) + CRM Regression")
        print("=" * 80)
        
        # AI Knowledge endpoints (Tests 1-8)
        self.test_review_request_ai_knowledge()
        
        # CRM regression tests (Tests 9-10)
        self.test_review_request_crm_regression()
        
        # Final summary
        self.print_summary()

    def test_quick_db_check(self):
        """Test 1: GET /api/ai-knowledge/db-check - expecting Status 200, connected=true, embedding_dims=1536"""
        print("\n1️⃣ Testing GET /api/ai-knowledge/db-check")
        print("   Expected: Status 200, connected=true, embedding_dims=1536")
        
        success, data, status = self.make_request('GET', '/api/ai-knowledge/db-check')
        
        if success and status == 200:
            print(f"   ✅ Status: {status} ✓")
            print(f"   Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            connected = data.get('connected', False)
            embedding_dims = data.get('embedding_dims')
            
            # Check connected=true
            connected_ok = connected is True
            
            # Check embedding_dims=1536
            dims_ok = embedding_dims == 1536
            
            if connected_ok and dims_ok:
                self.log_test("DB Check - Review Request Requirements", True, 
                            f"✅ Status 200 ✓, connected=true ✓, embedding_dims=1536 ✓")
            else:
                issues = []
                if not connected_ok:
                    issues.append(f"connected={connected} (expected true)")
                if not dims_ok:
                    issues.append(f"embedding_dims={embedding_dims} (expected 1536)")
                self.log_test("DB Check - Review Request Requirements", False, f"❌ Issues: {', '.join(issues)}")
        else:
            self.log_test("DB Check - Review Request Requirements", False, f"❌ Status: {status} (expected 200), Data: {data}")

    def test_specific_review_request(self):
        """Specific review request testing: db-check and search endpoints only"""
        print(f"🚀 VasDom AudioBot Backend API - Повторный быстрый тест на проде")
        print(f"📍 Base URL: {self.base_url}")
        print("🔧 Testing specific endpoints per review request:")
        print("1) GET /api/ai-knowledge/db-check — ожидаем 200, connected=true, embedding_dims=1536")
        print("2) POST /api/ai-knowledge/search — body {\"query\":\"psycopg3\",\"top_k\":5} — ожидаем 200 и results[] (допускается пустой массив)")
        print("=" * 80)
        
        # Test 1: GET /api/ai-knowledge/db-check
        self.test_quick_db_check()
        
        # Test 2: POST /api/ai-knowledge/search
        self.test_quick_search_psycopg3()
        
        # Final summary
        self.print_summary()

    def test_review_request_mini_flow(self):
        """Test the specific mini-flow from review request"""
        print(f"🚀 VasDom AudioBot Backend API - Повторный mini‑flow после фикса study на проде")
        print(f"📍 Base URL: {self.base_url}")
        print("🔧 Testing AI Knowledge Mini-Flow per review request:")
        print("1) POST /api/ai-knowledge/preview — TXT 'UX test psycopg3 search 2' → 200: upload_id, chunks>0")
        print("2) GET /api/ai-knowledge/status — 200: status='ready'")
        print("3) POST /api/ai-knowledge/study — form: upload_id, filename='ux2.txt', category='Маркетинг' → 200: document_id, chunks>=1")
        print("4) GET /api/ai-knowledge/documents — 200: есть 'ux2.txt'")
        print("5) POST /api/ai-knowledge/search — body {\"query\":\"psycopg3\",\"top_k\":5} → 200, results[] не пустой")
        print("6) DELETE /api/ai-knowledge/document/{document_id} — 200 {ok:true}")
        print("=" * 80)
        
        # Test 1: POST /api/ai-knowledge/preview
        upload_id = self.test_review_preview()
        
        if upload_id:
            # Test 2: GET /api/ai-knowledge/status
            self.test_review_status(upload_id)
            
            # Test 3: POST /api/ai-knowledge/study
            document_id = self.test_review_study(upload_id)
            
            if document_id:
                # Test 4: GET /api/ai-knowledge/documents
                self.test_review_documents()
                
                # Test 5: POST /api/ai-knowledge/search
                self.test_review_search()
                
                # Test 6: DELETE /api/ai-knowledge/document/{document_id}
                self.test_review_delete(document_id)
            else:
                print("❌ Cannot proceed with documents/search/delete tests - no document_id from study")
        else:
            print("❌ Cannot proceed with mini-flow tests - no upload_id from preview")
        
        # Final summary
        self.print_summary()

    def test_review_preview(self):
        """Test 1: POST /api/ai-knowledge/preview - TXT 'UX test psycopg3 search 2'"""
        print("\n1️⃣ Testing POST /api/ai-knowledge/preview")
        print("   Content: 'UX test psycopg3 search 2'")
        print("   Expected: 200: upload_id, chunks>0")
        
        # Create test file content as specified in review request
        test_content = "UX test psycopg3 search 2"
        files = {'files': ('ux2.txt', test_content.encode('utf-8'), 'text/plain')}
        
        success, data, status = self.make_multipart_request('POST', '/api/ai-knowledge/preview', files=files)
        
        if success and status == 200:
            print(f"   ✅ Status: {status} ✓")
            print(f"   Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            upload_id = data.get('upload_id')
            chunks = data.get('chunks', 0)
            
            if upload_id and chunks > 0:
                self.log_test("Review Request Preview", True, 
                            f"✅ upload_id: {upload_id[:8]}..., chunks: {chunks} ✓")
                self.upload_id = upload_id
                return upload_id
            else:
                issues = []
                if not upload_id:
                    issues.append("missing upload_id")
                if chunks <= 0:
                    issues.append(f"chunks={chunks} (expected >0)")
                self.log_test("Review Request Preview", False, f"❌ Issues: {', '.join(issues)}")
        else:
            print(f"   ❌ Status: {status}")
            print(f"   Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
            self.log_test("Review Request Preview", False, f"❌ Status: {status} (expected 200), Data: {data}")
        
        return None

    def test_review_status(self, upload_id):
        """Test 2: GET /api/ai-knowledge/status - 200: status='ready'"""
        print(f"\n2️⃣ Testing GET /api/ai-knowledge/status")
        print("   Expected: 200: status='ready'")
        
        success, data, status = self.make_request('GET', '/api/ai-knowledge/status', params={'upload_id': upload_id})
        
        if success and status == 200:
            print(f"   ✅ Status: {status} ✓")
            print(f"   Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            upload_status = data.get('status', '')
            
            if upload_status == 'ready':
                self.log_test("Review Request Status", True, "✅ status='ready' ✓")
            else:
                self.log_test("Review Request Status", False, f"❌ status='{upload_status}' (expected 'ready')")
        else:
            print(f"   ❌ Status: {status}")
            print(f"   Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
            self.log_test("Review Request Status", False, f"❌ Status: {status} (expected 200), Data: {data}")

    def test_review_study(self, upload_id):
        """Test 3: POST /api/ai-knowledge/study - form: upload_id, filename='ux2.txt', category='Маркетинг'"""
        print(f"\n3️⃣ Testing POST /api/ai-knowledge/study")
        print("   Form: upload_id, filename='ux2.txt', category='Маркетинг'")
        print("   Expected: 200: document_id, chunks>=1")
        
        form_data = {
            'upload_id': upload_id,
            'filename': 'ux2.txt',
            'category': 'Маркетинг'
        }
        
        success, data, status = self.make_multipart_request('POST', '/api/ai-knowledge/study', data=form_data)
        
        if success and status == 200:
            print(f"   ✅ Status: {status} ✓")
            print(f"   Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            document_id = data.get('document_id')
            chunks = data.get('chunks', 0)
            
            if document_id and chunks >= 1:
                self.log_test("Review Request Study", True, 
                            f"✅ document_id: {document_id[:8]}..., chunks: {chunks} ✓")
                self.document_id = document_id
                return document_id
            else:
                issues = []
                if not document_id:
                    issues.append("missing document_id")
                if chunks < 1:
                    issues.append(f"chunks={chunks} (expected >=1)")
                self.log_test("Review Request Study", False, f"❌ Issues: {', '.join(issues)}")
        else:
            print(f"   ❌ Status: {status}")
            print(f"   Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
            self.log_test("Review Request Study", False, f"❌ Status: {status} (expected 200), Data: {data}")
        
        return None

    def test_review_documents(self):
        """Test 4: GET /api/ai-knowledge/documents - 200: есть 'ux2.txt'"""
        print("\n4️⃣ Testing GET /api/ai-knowledge/documents")
        print("   Expected: 200: есть 'ux2.txt'")
        
        success, data, status = self.make_request('GET', '/api/ai-knowledge/documents')
        
        if success and status == 200:
            print(f"   ✅ Status: {status} ✓")
            
            documents = data.get('documents', [])
            print(f"   Total documents: {len(documents)}")
            
            if documents:
                # Find our test document
                test_doc = None
                for doc in documents:
                    if doc.get('filename') == 'ux2.txt':
                        test_doc = doc
                        break
                
                if test_doc:
                    chunks_count = test_doc.get('chunks_count', 0)
                    print(f"   Found 'ux2.txt': {json.dumps(test_doc, indent=2, ensure_ascii=False)}")
                    self.log_test("Review Request Documents", True, 
                                f"✅ Found 'ux2.txt' with chunks_count: {chunks_count} ✓")
                else:
                    self.log_test("Review Request Documents", False, 
                                "❌ Test document 'ux2.txt' not found in documents list")
            else:
                self.log_test("Review Request Documents", False, "❌ No documents found")
        else:
            print(f"   ❌ Status: {status}")
            print(f"   Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
            self.log_test("Review Request Documents", False, f"❌ Status: {status} (expected 200), Data: {data}")

    def test_review_search(self):
        """Test 5: POST /api/ai-knowledge/search - body {"query":"psycopg3","top_k":5} → 200, results[] не пустой"""
        print("\n5️⃣ Testing POST /api/ai-knowledge/search")
        print("   Body: {\"query\":\"psycopg3\",\"top_k\":5}")
        print("   Expected: 200, results[] не пустой")
        
        search_data = {
            'query': 'psycopg3',
            'top_k': 5
        }
        
        success, data, status = self.make_request('POST', '/api/ai-knowledge/search', search_data)
        
        if success and status == 200:
            print(f"   ✅ Status: {status} ✓")
            print(f"   Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            results = data.get('results', [])
            
            if isinstance(results, list) and len(results) > 0:
                self.log_test("Review Request Search", True, 
                            f"✅ Status 200 ✓, results[] не пустой ✓ (размер массива: {len(results)})")
                
                # Show example results as requested
                print(f"   📋 Примеры результатов поиска:")
                for i, result in enumerate(results[:2], 1):  # Show first 2 results
                    print(f"   {i}. {json.dumps(result, indent=2, ensure_ascii=False)}")
            else:
                if isinstance(results, list):
                    self.log_test("Review Request Search", False, 
                                f"❌ Status 200 ✓, но results[] пустой (размер массива: {len(results)})")
                else:
                    self.log_test("Review Request Search", False, 
                                f"❌ Status 200 ✓, но results должен быть массивом, получен {type(results)}")
        else:
            print(f"   ❌ Status: {status}")
            print(f"   Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
            self.log_test("Review Request Search", False, 
                        f"❌ Status: {status} (expected 200), Data: {data}")

    def test_review_delete(self, document_id):
        """Test 6: DELETE /api/ai-knowledge/document/{document_id} - 200 {ok:true}"""
        print(f"\n6️⃣ Testing DELETE /api/ai-knowledge/document/{document_id[:8]}...")
        print("   Expected: 200 {ok:true}")
        
        success, data, status = self.make_request('DELETE', f'/api/ai-knowledge/document/{document_id}')
        
        if success and status == 200:
            print(f"   ✅ Status: {status} ✓")
            print(f"   Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            ok = data.get('ok', False)
            
            if ok is True:
                self.log_test("Review Request Delete", True, "✅ Document deleted successfully {ok:true} ✓")
            else:
                self.log_test("Review Request Delete", False, f"❌ Expected ok=true, got ok={ok}")
        else:
            print(f"   ❌ Status: {status}")
            print(f"   Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
            self.log_test("Review Request Delete", False, f"❌ Status: {status} (expected 200), Data: {data}")

    def test_production_review_request(self):
        """Test all 8 endpoints from the review request on production"""
        print(f"🚀 VasDom AudioBot Backend API - Постдеплойный e2e тест на проде")
        print(f"📍 Base URL: {self.base_url}")
        print("🔧 Testing all 8 endpoints per review request:")
        print("1) GET /api/ai-knowledge/db-dsn — 200; normalized.scheme='postgresql', query включает sslmode=require")
        print("2) GET /api/ai-knowledge/db-check — 200; connected=true, embedding_dims=1536")
        print("3) POST /api/ai-knowledge/preview — 200: upload_id, chunks>0 (files: TXT \"Final UX test psycopg3\")")
        print("4) GET /api/ai-knowledge/status — 200: status='ready'")
        print("5) POST /api/ai-knowledge/study — 200: document_id, chunks>=1 (принимает FormData/JSON)")
        print("6) GET /api/ai-knowledge/documents — 200: документ присутствует")
        print("7) POST /api/ai-knowledge/search — 200: results[] не пустой")
        print("8) DELETE /api/ai-knowledge/document/{document_id} — 200 {ok:true}")
        print("=" * 80)
        
        # Test 1: GET /api/ai-knowledge/db-dsn
        self.test_production_db_dsn()
        
        # Test 2: GET /api/ai-knowledge/db-check
        db_connected = self.test_production_db_check()
        
        # Test 3: POST /api/ai-knowledge/preview
        upload_id = self.test_production_preview()
        
        if upload_id:
            # Test 4: GET /api/ai-knowledge/status
            self.test_production_status(upload_id)
            
            # Test 5: POST /api/ai-knowledge/study
            document_id = self.test_production_study(upload_id)
            
            if document_id:
                # Test 6: GET /api/ai-knowledge/documents
                self.test_production_documents()
                
                # Test 7: POST /api/ai-knowledge/search
                self.test_production_search()
                
                # Test 8: DELETE /api/ai-knowledge/document/{document_id}
                self.test_production_delete(document_id)
            else:
                print("❌ Cannot proceed with documents/search/delete tests - no document_id from study")
                # Still test the endpoints to see their responses
                self.test_production_documents()
                self.test_production_search()
        else:
            print("❌ Cannot proceed with flow tests - no upload_id from preview")
            # Still test the remaining endpoints to see their responses
            self.test_production_status("dummy-upload-id")
            self.test_production_documents()
            self.test_production_search()
        
        # Final summary
        self.print_summary()

    def test_production_db_dsn(self):
        """Test 1: GET /api/ai-knowledge/db-dsn"""
        print("\n1️⃣ Testing GET /api/ai-knowledge/db-dsn")
        print("   Expected: 200; normalized.scheme='postgresql', query включает sslmode=require")
        
        success, data, status = self.make_request('GET', '/api/ai-knowledge/db-dsn')
        
        if success and status == 200:
            print(f"   ✅ Status: {status} ✓")
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
                    
                    if scheme_ok and query_ok:
                        self.log_test("Production DB DSN", True, 
                                    f"✅ normalized.scheme='postgresql' ✓, query включает sslmode=require ✓")
                    else:
                        issues = []
                        if not scheme_ok:
                            issues.append(f"scheme='{scheme}' (expected 'postgresql')")
                        if not query_ok:
                            issues.append(f"query missing sslmode=require: {query}")
                        self.log_test("Production DB DSN", False, f"❌ Issues: {', '.join(issues)}")
                else:
                    self.log_test("Production DB DSN", False, f"❌ normalized should be dict, got {type(normalized)}")
            else:
                self.log_test("Production DB DSN", False, "❌ Missing 'normalized' field in response")
        else:
            self.log_test("Production DB DSN", False, f"❌ Status: {status}, Data: {data}")

    def test_production_db_check(self):
        """Test 2: GET /api/ai-knowledge/db-check"""
        print("\n2️⃣ Testing GET /api/ai-knowledge/db-check")
        print("   Expected: 200; connected=true, embedding_dims=1536")
        
        success, data, status = self.make_request('GET', '/api/ai-knowledge/db-check')
        
        if success and status == 200:
            print(f"   ✅ Status: {status} ✓")
            print(f"   Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            connected = data.get('connected', False)
            embedding_dims = data.get('embedding_dims')
            
            if connected and embedding_dims == 1536:
                self.log_test("Production DB Check", True, 
                            f"✅ connected=true ✓, embedding_dims=1536 ✓")
                return True
            else:
                issues = []
                if not connected:
                    issues.append(f"connected={connected} (expected true)")
                if embedding_dims != 1536:
                    issues.append(f"embedding_dims={embedding_dims} (expected 1536)")
                self.log_test("Production DB Check", False, f"❌ Issues: {', '.join(issues)}")
                return False
        else:
            self.log_test("Production DB Check", False, f"❌ Status: {status}, Data: {data}")
            return False

    def test_production_preview(self):
        """Test 3: POST /api/ai-knowledge/preview"""
        print("\n3️⃣ Testing POST /api/ai-knowledge/preview")
        print("   Content: 'Final UX test psycopg3'")
        print("   Expected: 200: upload_id, chunks>0")
        
        # Create test file content as specified in review request
        test_content = "Final UX test psycopg3"
        files = {'files': ('final_ux_test.txt', test_content.encode('utf-8'), 'text/plain')}
        
        success, data, status = self.make_multipart_request('POST', '/api/ai-knowledge/preview', files=files)
        
        if success and status == 200:
            print(f"   ✅ Status: {status} ✓")
            print(f"   Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            upload_id = data.get('upload_id')
            chunks = data.get('chunks', 0)
            
            if upload_id and chunks > 0:
                self.log_test("Production Preview", True, 
                            f"✅ upload_id: {upload_id[:8]}..., chunks: {chunks} ✓")
                self.upload_id = upload_id
                return upload_id
            else:
                issues = []
                if not upload_id:
                    issues.append("missing upload_id")
                if chunks <= 0:
                    issues.append(f"chunks={chunks} (expected >0)")
                self.log_test("Production Preview", False, f"❌ Issues: {', '.join(issues)}")
        else:
            print(f"   ❌ Status: {status}")
            print(f"   Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
            self.log_test("Production Preview", False, f"❌ Status: {status} (expected 200), Data: {data}")
        
        return None

    def test_production_status(self, upload_id):
        """Test 4: GET /api/ai-knowledge/status"""
        print(f"\n4️⃣ Testing GET /api/ai-knowledge/status")
        print("   Expected: 200: status='ready'")
        
        success, data, status = self.make_request('GET', '/api/ai-knowledge/status', params={'upload_id': upload_id})
        
        if success and status == 200:
            print(f"   ✅ Status: {status} ✓")
            print(f"   Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            upload_status = data.get('status', '')
            
            if upload_status == 'ready':
                self.log_test("Production Status", True, "✅ status='ready' ✓")
            else:
                self.log_test("Production Status", False, f"❌ status='{upload_status}' (expected 'ready')")
        else:
            print(f"   ❌ Status: {status}")
            print(f"   Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
            self.log_test("Production Status", False, f"❌ Status: {status} (expected 200), Data: {data}")

    def test_production_study(self, upload_id):
        """Test 5: POST /api/ai-knowledge/study"""
        print(f"\n5️⃣ Testing POST /api/ai-knowledge/study")
        print("   Form: upload_id, filename='final_test.txt'")
        print("   Expected: 200: document_id, chunks>=1")
        
        form_data = {
            'upload_id': upload_id,
            'filename': 'final_test.txt'
        }
        
        success, data, status = self.make_multipart_request('POST', '/api/ai-knowledge/study', data=form_data)
        
        if success and status == 200:
            print(f"   ✅ Status: {status} ✓")
            print(f"   Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            document_id = data.get('document_id')
            chunks = data.get('chunks', 0)
            
            if document_id and chunks >= 1:
                self.log_test("Production Study", True, 
                            f"✅ document_id: {document_id[:8]}..., chunks: {chunks} ✓")
                self.document_id = document_id
                return document_id
            else:
                issues = []
                if not document_id:
                    issues.append("missing document_id")
                if chunks < 1:
                    issues.append(f"chunks={chunks} (expected >=1)")
                self.log_test("Production Study", False, f"❌ Issues: {', '.join(issues)}")
        else:
            print(f"   ❌ Status: {status}")
            print(f"   Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
            self.log_test("Production Study", False, f"❌ Status: {status} (expected 200), Data: {data}")
        
        return None

    def test_production_documents(self):
        """Test 6: GET /api/ai-knowledge/documents"""
        print("\n6️⃣ Testing GET /api/ai-knowledge/documents")
        print("   Expected: 200: документ присутствует")
        
        success, data, status = self.make_request('GET', '/api/ai-knowledge/documents')
        
        if success and status == 200:
            print(f"   ✅ Status: {status} ✓")
            
            documents = data.get('documents', [])
            print(f"   Total documents: {len(documents)}")
            
            if documents:
                self.log_test("Production Documents", True, 
                            f"✅ Found {len(documents)} documents ✓")
                # Show first few documents
                for i, doc in enumerate(documents[:3], 1):
                    filename = doc.get('filename', 'Unknown')
                    chunks = doc.get('chunks_count', 0)
                    print(f"   {i}. {filename} ({chunks} chunks)")
            else:
                self.log_test("Production Documents", False, "❌ No documents found")
        else:
            print(f"   ❌ Status: {status}")
            print(f"   Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
            self.log_test("Production Documents", False, f"❌ Status: {status} (expected 200), Data: {data}")

    def test_production_search(self):
        """Test 7: POST /api/ai-knowledge/search"""
        print("\n7️⃣ Testing POST /api/ai-knowledge/search")
        print("   Body: {\"query\":\"psycopg3\",\"top_k\":5}")
        print("   Expected: 200: results[] не пустой")
        
        search_data = {
            'query': 'psycopg3',
            'top_k': 5
        }
        
        success, data, status = self.make_request('POST', '/api/ai-knowledge/search', search_data)
        
        if success and status == 200:
            print(f"   ✅ Status: {status} ✓")
            print(f"   Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            results = data.get('results', [])
            
            if isinstance(results, list) and len(results) > 0:
                self.log_test("Production Search", True, 
                            f"✅ Status 200 ✓, results[] не пустой ✓ (размер массива: {len(results)})")
            else:
                if isinstance(results, list):
                    self.log_test("Production Search", False, 
                                f"❌ Status 200 ✓, но results[] пустой (размер массива: {len(results)})")
                else:
                    self.log_test("Production Search", False, 
                                f"❌ Status 200 ✓, но results должен быть массивом, получен {type(results)}")
        else:
            print(f"   ❌ Status: {status}")
            print(f"   Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
            self.log_test("Production Search", False, 
                        f"❌ Status: {status} (expected 200), Data: {data}")

    def test_production_delete(self, document_id):
        """Test 8: DELETE /api/ai-knowledge/document/{document_id}"""
        print(f"\n8️⃣ Testing DELETE /api/ai-knowledge/document/{document_id[:8]}...")
        print("   Expected: 200 {ok:true}")
        
        success, data, status = self.make_request('DELETE', f'/api/ai-knowledge/document/{document_id}')
        
        if success and status == 200:
            print(f"   ✅ Status: {status} ✓")
            print(f"   Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            ok = data.get('ok', False)
            
            if ok is True:
                self.log_test("Production Delete", True, "✅ Document deleted successfully {ok:true} ✓")
            else:
                self.log_test("Production Delete", False, f"❌ Expected ok=true, got ok={ok}")
        else:
            print(f"   ❌ Status: {status}")
            print(f"   Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
            self.log_test("Production Delete", False, f"❌ Status: {status} (expected 200), Data: {data}")

    def test_specific_review_request_flow(self):
        """Test the specific review request flow with real embeddings"""
        print(f"🚀 VasDom AudioBot Backend API - Review Request: Real Embeddings Test")
        print(f"📍 Base URL: {self.base_url}")
        print("🔧 Testing AI Knowledge flow with real embeddings (OPENAI_API_KEY set):")
        print("1) POST /api/ai-knowledge/preview — 200: upload_id, chunks>0 (files: TXT \"OpenAI embeddings test. The keyword is psycopg3. This line should match the search.\")")
        print("2) POST /api/ai-knowledge/study — 200: document_id, chunks>=1 (FormData)")
        print("3) POST /api/ai-knowledge/search — 200: body {\"query\":\"psycopg3\",\"top_k\":5} → expect results[] not empty, first element score>0")
        print("4) DELETE /api/ai-knowledge/document/{document_id} — 200 {ok:true}")
        print("=" * 80)
        
        # Test 1: POST /api/ai-knowledge/preview
        upload_id = self.test_specific_preview()
        
        if upload_id:
            # Test 2: POST /api/ai-knowledge/study
            document_id = self.test_specific_study(upload_id)
            
            if document_id:
                # Test 3: POST /api/ai-knowledge/search
                self.test_specific_search()
                
                # Test 4: DELETE /api/ai-knowledge/document/{document_id}
                self.test_specific_delete(document_id)
            else:
                print("❌ Cannot proceed with search/delete tests - no document_id from study")
        else:
            print("❌ Cannot proceed with flow tests - no upload_id from preview")
        
        # Final summary
        self.print_summary()

    def test_specific_preview(self):
        """Test 1: POST /api/ai-knowledge/preview with specific content"""
        print("\n1️⃣ Testing POST /api/ai-knowledge/preview")
        print("   Content: 'OpenAI embeddings test. The keyword is psycopg3. This line should match the search.'")
        print("   Expected: 200: upload_id, chunks>0")
        
        # Create test file content as specified in review request
        test_content = "OpenAI embeddings test. The keyword is psycopg3. This line should match the search."
        files = {'files': ('embeddings_test.txt', test_content.encode('utf-8'), 'text/plain')}
        
        success, data, status = self.make_multipart_request('POST', '/api/ai-knowledge/preview', files=files)
        
        if success and status == 200:
            print(f"   ✅ Status: {status} ✓")
            print(f"   Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            upload_id = data.get('upload_id')
            chunks = data.get('chunks', 0)
            
            if upload_id and chunks > 0:
                self.log_test("Specific Preview - Real Embeddings", True, 
                            f"✅ upload_id: {upload_id[:8]}..., chunks: {chunks} ✓")
                self.upload_id = upload_id
                return upload_id
            else:
                issues = []
                if not upload_id:
                    issues.append("missing upload_id")
                if chunks <= 0:
                    issues.append(f"chunks={chunks} (expected >0)")
                self.log_test("Specific Preview - Real Embeddings", False, f"❌ Issues: {', '.join(issues)}")
        else:
            print(f"   ❌ Status: {status}")
            print(f"   Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
            self.log_test("Specific Preview - Real Embeddings", False, f"❌ Status: {status} (expected 200), Data: {data}")
        
        return None

    def test_specific_study(self, upload_id):
        """Test 2: POST /api/ai-knowledge/study with FormData"""
        print(f"\n2️⃣ Testing POST /api/ai-knowledge/study")
        print("   Form: upload_id, filename='embeddings_test.txt'")
        print("   Expected: 200: document_id, chunks>=1")
        
        form_data = {
            'upload_id': upload_id,
            'filename': 'embeddings_test.txt'
        }
        
        success, data, status = self.make_multipart_request('POST', '/api/ai-knowledge/study', data=form_data)
        
        if success and status == 200:
            print(f"   ✅ Status: {status} ✓")
            print(f"   Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            document_id = data.get('document_id')
            chunks = data.get('chunks', 0)
            
            if document_id and chunks >= 1:
                self.log_test("Specific Study - Real Embeddings", True, 
                            f"✅ document_id: {document_id[:8]}..., chunks: {chunks} ✓")
                self.document_id = document_id
                return document_id
            else:
                issues = []
                if not document_id:
                    issues.append("missing document_id")
                if chunks < 1:
                    issues.append(f"chunks={chunks} (expected >=1)")
                self.log_test("Specific Study - Real Embeddings", False, f"❌ Issues: {', '.join(issues)}")
        else:
            print(f"   ❌ Status: {status}")
            print(f"   Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
            self.log_test("Specific Study - Real Embeddings", False, f"❌ Status: {status} (expected 200), Data: {data}")
        
        return None

    def test_specific_search(self):
        """Test 3: POST /api/ai-knowledge/search with specific query"""
        print("\n3️⃣ Testing POST /api/ai-knowledge/search")
        print("   Body: {\"query\":\"psycopg3\",\"top_k\":5}")
        print("   Expected: 200: results[] not empty, first element score>0")
        
        search_data = {
            'query': 'psycopg3',
            'top_k': 5
        }
        
        success, data, status = self.make_request('POST', '/api/ai-knowledge/search', search_data)
        
        if success and status == 200:
            print(f"   ✅ Status: {status} ✓")
            print(f"   Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            results = data.get('results', [])
            
            if isinstance(results, list) and len(results) > 0:
                first_result = results[0]
                first_score = first_result.get('score', 0) if isinstance(first_result, dict) else 0
                
                if first_score > 0:
                    self.log_test("Specific Search - Real Embeddings", True, 
                                f"✅ results[] not empty ✓ (count: {len(results)}), first element score: {first_score} > 0 ✓")
                    
                    # Show detailed results as requested
                    print(f"   📋 Search Results Details:")
                    for i, result in enumerate(results, 1):
                        if isinstance(result, dict):
                            score = result.get('score', 0)
                            content_preview = result.get('content', '')[:100] + '...' if len(result.get('content', '')) > 100 else result.get('content', '')
                            print(f"   {i}. Score: {score}, Content: {content_preview}")
                else:
                    self.log_test("Specific Search - Real Embeddings", False, 
                                f"❌ results[] not empty ✓ (count: {len(results)}), but first element score: {first_score} <= 0")
            else:
                if isinstance(results, list):
                    self.log_test("Specific Search - Real Embeddings", False, 
                                f"❌ results[] is empty (count: {len(results)}) - expected not empty")
                else:
                    self.log_test("Specific Search - Real Embeddings", False, 
                                f"❌ results should be array, got {type(results)}")
        else:
            print(f"   ❌ Status: {status}")
            print(f"   Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
            self.log_test("Specific Search - Real Embeddings", False, 
                        f"❌ Status: {status} (expected 200), Data: {data}")

    def test_specific_delete(self, document_id):
        """Test 4: DELETE /api/ai-knowledge/document/{document_id}"""
        print(f"\n4️⃣ Testing DELETE /api/ai-knowledge/document/{document_id[:8]}...")
        print("   Expected: 200 {ok:true}")
        
        success, data, status = self.make_request('DELETE', f'/api/ai-knowledge/document/{document_id}')
        
        if success and status == 200:
            print(f"   ✅ Status: {status} ✓")
            print(f"   Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            ok = data.get('ok', False)
            
            if ok is True:
                self.log_test("Specific Delete - Real Embeddings", True, "✅ Document deleted successfully {ok:true} ✓")
            else:
                self.log_test("Specific Delete - Real Embeddings", False, f"❌ Expected ok=true, got ok={ok}")
        else:
            print(f"   ❌ Status: {status}")
            print(f"   Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
            self.log_test("Specific Delete - Real Embeddings", False, f"❌ Status: {status} (expected 200), Data: {data}")


if __name__ == "__main__":
    tester = VasDomAPITester()
    # Run the specific review request test
    tester.test_specific_review_request_flow()