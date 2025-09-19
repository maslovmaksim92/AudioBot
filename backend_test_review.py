#!/usr/bin/env python3
"""
VasDom AudioBot Backend API Testing - psycopg3 async migration
Review Request: https://audiobot-qci2.onrender.com
Testing AI Knowledge endpoints after migration to psycopg3 async
"""

import requests
import sys
import json
import time
import io
from datetime import datetime
from typing import Dict, Any, Optional

class VasDomReviewTester:
    def __init__(self, base_url="https://audiobot-qci2.onrender.com"):
        self.base_url = base_url.rstrip('/')
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []
        self.upload_id = None
        self.document_id = None
        
    def log_test(self, name: str, success: bool, details: str = ""):
        """Log test result"""
        self.tests_run += 1
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {name}")
        if details:
            print(f"   {details}")
        
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

    def test_ai_db_dsn(self):
        """Test 1: GET /api/ai-knowledge/db-dsn"""
        print("\n1️⃣ GET /api/ai-knowledge/db-dsn")
        
        success, data, status = self.make_request('GET', '/api/ai-knowledge/db-dsn')
        
        if success and status == 200:
            normalized = data.get('normalized', {})
            if isinstance(normalized, dict):
                scheme = normalized.get('scheme', '')
                query = normalized.get('query', '')
                raw_present = data.get('raw_present', False)
                
                scheme_ok = scheme == 'postgresql'
                sslmode_ok = 'sslmode=require' in query
                
                if scheme_ok and sslmode_ok and raw_present:
                    self.log_test("AI DB DSN", True, 
                                f"scheme='{scheme}', sslmode=require in query, raw_present={raw_present}")
                    print(f"   📄 JSON Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
                else:
                    issues = []
                    if not scheme_ok: issues.append(f"scheme='{scheme}' (expected 'postgresql')")
                    if not sslmode_ok: issues.append("sslmode=require not in query")
                    if not raw_present: issues.append(f"raw_present={raw_present}")
                    self.log_test("AI DB DSN", False, f"Issues: {', '.join(issues)}")
            else:
                self.log_test("AI DB DSN", False, f"normalized should be dict, got {type(normalized)}")
        else:
            self.log_test("AI DB DSN", False, f"Status: {status}, Data: {data}")
    
    def test_ai_db_check(self):
        """Test 2: GET /api/ai-knowledge/db-check"""
        print("\n2️⃣ GET /api/ai-knowledge/db-check")
        
        success, data, status = self.make_request('GET', '/api/ai-knowledge/db-check')
        
        if success and status == 200:
            connected = data.get('connected', False)
            ai_tables = data.get('ai_tables', [])
            embedding_dims = data.get('embedding_dims')
            errors = data.get('errors', [])
            
            expected_tables = {'ai_documents', 'ai_chunks', 'ai_uploads_temp'}
            tables_ok = expected_tables.issubset(set(ai_tables))
            dims_ok = embedding_dims == 1536
            
            if connected and tables_ok and dims_ok:
                self.log_test("AI DB Check", True, 
                            f"connected=true, ai_tables={ai_tables}, embedding_dims={embedding_dims}")
            else:
                issues = []
                if not connected: issues.append(f"connected={connected}")
                if not tables_ok: issues.append(f"missing tables: {expected_tables - set(ai_tables)}")
                if not dims_ok: issues.append(f"embedding_dims={embedding_dims} (expected 1536)")
                if errors: issues.append(f"errors: {errors}")
                
                self.log_test("AI DB Check", False, f"Issues: {', '.join(issues)}")
                if errors:
                    print(f"   📄 Errors JSON: {json.dumps(errors, indent=2, ensure_ascii=False)}")
            
            return data
        else:
            self.log_test("AI DB Check", False, f"Status: {status}, Data: {data}")
            return None
    
    def test_ai_preview_txt(self):
        """Test 3: POST /api/ai-knowledge/preview (multipart TXT file)"""
        print("\n3️⃣ POST /api/ai-knowledge/preview")
        
        txt_content = "Hello AI psycopg3"
        files = {'files': ('test.txt', txt_content.encode('utf-8'), 'text/plain')}
        data = {'chunk_tokens': '400', 'overlap': '100'}
        
        success, response_data, status = self.make_multipart_request('POST', '/api/ai-knowledge/preview', files=files, data=data)
        
        if success and status == 200:
            upload_id = response_data.get('upload_id')
            preview = response_data.get('preview')
            chunks = response_data.get('chunks', 0)
            stats = response_data.get('stats', {})
            total_size_bytes = stats.get('total_size_bytes', 0)
            
            if upload_id and isinstance(preview, str) and chunks > 0 and total_size_bytes > 0:
                self.log_test("AI Preview TXT", True, 
                            f"upload_id={upload_id[:8]}..., preview='{preview[:50]}...', chunks={chunks}, total_size_bytes={total_size_bytes}")
                self.upload_id = upload_id
                return upload_id
            else:
                issues = []
                if not upload_id: issues.append("missing upload_id")
                if not isinstance(preview, str): issues.append(f"preview not string: {type(preview)}")
                if chunks <= 0: issues.append(f"chunks={chunks}")
                if total_size_bytes <= 0: issues.append(f"total_size_bytes={total_size_bytes}")
                self.log_test("AI Preview TXT", False, f"Issues: {', '.join(issues)}")
        else:
            self.log_test("AI Preview TXT", False, f"Status: {status}, Data: {response_data}")
        
        return None
    
    def test_ai_status(self, upload_id):
        """Test 4: GET /api/ai-knowledge/status?upload_id=<from 3>"""
        print(f"\n4️⃣ GET /api/ai-knowledge/status?upload_id={upload_id[:8]}...")
        
        success, data, status = self.make_request('GET', '/api/ai-knowledge/status', params={'upload_id': upload_id})
        
        if success and status == 200:
            status_value = data.get('status')
            if status_value == 'ready':
                self.log_test("AI Status", True, f"status='ready'")
            else:
                self.log_test("AI Status", False, f"status='{status_value}' (expected 'ready')")
        else:
            self.log_test("AI Status", False, f"Status: {status}, Data: {data}")
    
    def test_ai_study(self, upload_id):
        """Test 5: POST /api/ai-knowledge/study"""
        print(f"\n5️⃣ POST /api/ai-knowledge/study")
        
        data = {
            'upload_id': upload_id,
            'filename': 'psycopg3.txt',
            'category': 'Маркетинг'
        }
        
        success, response_data, status = self.make_multipart_request('POST', '/api/ai-knowledge/study', data=data)
        
        if success and status == 200:
            document_id = response_data.get('document_id')
            chunks = response_data.get('chunks', 0)
            category = response_data.get('category')
            
            if document_id and chunks >= 1 and category == 'Маркетинг':
                self.log_test("AI Study", True, 
                            f"document_id={document_id[:8]}..., chunks={chunks}, category='{category}'")
                self.document_id = document_id
                return document_id
            else:
                issues = []
                if not document_id: issues.append("missing document_id")
                if chunks < 1: issues.append(f"chunks={chunks}")
                if category != 'Маркетинг': issues.append(f"category='{category}'")
                self.log_test("AI Study", False, f"Issues: {', '.join(issues)}")
        else:
            self.log_test("AI Study", False, f"Status: {status}, Data: {response_data}")
        
        return None
    
    def test_ai_documents_list(self):
        """Test 6: GET /api/ai-knowledge/documents (implemented in server.py)"""
        print("\n6️⃣ GET /api/ai-knowledge/documents")
        
        success, data, status = self.make_request('GET', '/api/ai-knowledge/documents')
        
        if success and status == 200:
            documents = data.get('documents', [])
            found_document = None
            for doc in documents:
                if doc.get('chunks_count', 0) >= 1:
                    found_document = doc
                    break
            
            if found_document:
                self.log_test("AI Documents List", True, 
                            f"Found document with chunks_count={found_document['chunks_count']}, filename='{found_document.get('filename', 'N/A')}'")
            else:
                self.log_test("AI Documents List", False, f"No documents with chunks_count >= 1 found. Total documents: {len(documents)}")
        else:
            self.log_test("AI Documents List", False, f"Status: {status}, Data: {data}")
    
    def test_ai_search_psycopg3(self):
        """Test 7: POST /api/ai-knowledge/search"""
        print("\n7️⃣ POST /api/ai-knowledge/search")
        
        search_data = {
            'query': 'psycopg3',
            'top_k': 5
        }
        
        success, data, status = self.make_request('POST', '/api/ai-knowledge/search', search_data)
        
        if success and status == 200:
            results = data.get('results', [])
            if isinstance(results, list):
                self.log_test("AI Search", True, f"Search returned {len(results)} results")
                if results:
                    first_result = results[0]
                    print(f"   📄 First result: score={first_result.get('score', 'N/A')}, filename='{first_result.get('filename', 'N/A')}'")
            else:
                self.log_test("AI Search", False, f"results should be array, got {type(results)}")
        else:
            self.log_test("AI Search", False, f"Status: {status}, Data: {data}")
    
    def test_ai_delete_document_twice(self, document_id):
        """Test 8: DELETE /api/ai-knowledge/document/{document_id} twice"""
        print(f"\n8️⃣ DELETE /api/ai-knowledge/document/{document_id[:8]}... (twice)")
        
        # First delete
        success1, data1, status1 = self.make_request('DELETE', f'/api/ai-knowledge/document/{document_id}')
        
        if success1 and status1 == 200 and data1.get('ok') is True:
            self.log_test("AI Delete - First", True, "First delete returned {ok:true}")
        else:
            self.log_test("AI Delete - First", False, f"Status: {status1}, Data: {data1}")
        
        # Second delete (should also return {ok:true} - idempotent)
        success2, data2, status2 = self.make_request('DELETE', f'/api/ai-knowledge/document/{document_id}')
        
        if success2 and status2 == 200 and data2.get('ok') is True:
            self.log_test("AI Delete - Second", True, "Second delete also returned {ok:true} (idempotent)")
        else:
            self.log_test("AI Delete - Second", False, f"Status: {status2}, Data: {data2}")
    
    def test_crm_filters_structure(self):
        """Test 9: GET /api/cleaning/filters - correct structure"""
        print("\n9️⃣ GET /api/cleaning/filters")
        
        success, data, status = self.make_request('GET', '/api/cleaning/filters')
        
        if success and status == 200:
            required_fields = ['brigades', 'management_companies', 'statuses']
            missing_fields = [field for field in required_fields if field not in data]
            
            if not missing_fields:
                brigades = data['brigades']
                companies = data['management_companies']
                statuses = data['statuses']
                
                if isinstance(brigades, list) and isinstance(companies, list) and isinstance(statuses, list):
                    self.log_test("CRM Filters Structure", True, 
                                f"brigades: {len(brigades)}, management_companies: {len(companies)}, statuses: {len(statuses)}")
                else:
                    self.log_test("CRM Filters Structure", False, 
                                f"Type errors: brigades={type(brigades)}, companies={type(companies)}, statuses={type(statuses)}")
            else:
                self.log_test("CRM Filters Structure", False, f"Missing fields: {missing_fields}")
        else:
            self.log_test("CRM Filters Structure", False, f"Status: {status}, Data: {data}")
    
    def test_crm_houses_structure(self):
        """Test 10: GET /api/cleaning/houses?page=1&limit=5"""
        print("\n🔟 GET /api/cleaning/houses?page=1&limit=5")
        
        success, data, status = self.make_request('GET', '/api/cleaning/houses', params={'page': 1, 'limit': 5})
        
        if success and status == 200:
            houses = data.get('houses', [])
            if isinstance(houses, list) and houses:
                house = houses[0]
                house_id = house.get('id')
                
                required_fields = ['id', 'title', 'address', 'apartments', 'entrances', 'floors', 'cleaning_dates', 'periodicity', 'bitrix_url']
                missing_fields = [field for field in required_fields if field not in house]
                
                if not missing_fields:
                    cleaning_dates = house.get('cleaning_dates', {})
                    dates_ok = self.check_dates_format(cleaning_dates)
                    
                    bitrix_url = house.get('bitrix_url', '')
                    bitrix_ok = 'bitrix24.ru/crm/deal/details/' in bitrix_url
                    
                    if dates_ok and bitrix_ok:
                        self.log_test("CRM Houses Structure", True, 
                                    f"House ID {house_id}: all fields present, dates YYYY-MM-DD, bitrix_url correct")
                        return house_id
                    else:
                        issues = []
                        if not dates_ok: issues.append("dates not YYYY-MM-DD format")
                        if not bitrix_ok: issues.append(f"bitrix_url format wrong: {bitrix_url}")
                        self.log_test("CRM Houses Structure", False, f"Issues: {', '.join(issues)}")
                else:
                    self.log_test("CRM Houses Structure", False, f"Missing fields: {missing_fields}")
            else:
                self.log_test("CRM Houses Structure", False, f"No houses returned or invalid format")
        else:
            self.log_test("CRM Houses Structure", False, f"Status: {status}, Data: {data}")
        
        return None
    
    def test_crm_house_details_structure(self, house_id):
        """Test 11: GET /api/cleaning/house/{id}/details"""
        print(f"\n1️⃣1️⃣ GET /api/cleaning/house/{house_id}/details")
        
        success, data, status = self.make_request('GET', f'/api/cleaning/house/{house_id}/details')
        
        if success and status == 200:
            if isinstance(data, dict):
                self.log_test("CRM House Details Structure", True, 
                            f"House {house_id}: correct structure, no 500 error")
                print(f"   📄 Sample JSON: {json.dumps(data, indent=2, ensure_ascii=False)[:500]}...")
            else:
                self.log_test("CRM House Details Structure", False, f"Expected dict, got {type(data)}")
        elif status == 500:
            self.log_test("CRM House Details Structure", False, f"Returns 500 on Bitrix errors (should handle gracefully)")
        else:
            self.log_test("CRM House Details Structure", False, f"Status: {status}, Data: {data}")
    
    def check_dates_format(self, cleaning_dates):
        """Check if dates are in YYYY-MM-DD format"""
        import re
        date_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}$')
        
        for period_key, period_data in cleaning_dates.items():
            if isinstance(period_data, dict):
                dates = period_data.get('dates', [])
                for date in dates:
                    if not date_pattern.match(str(date)):
                        return False
        return True

    def run_review_request_tests(self):
        """Run specific tests for the review request"""
        print(f"🚀 VasDom AudioBot Backend Testing - psycopg3 async migration")
        print(f"📍 Base URL: {self.base_url}")
        print(f"📋 Review Request: Бэкенд‑тестирование (деплой Render) после миграции AI Training на psycopg3 async")
        print("=" * 100)
        
        # AI Knowledge tests (psycopg3, router backend/app/routers/ai_knowledge.py)
        print("\n🧠 AI KNOWLEDGE (psycopg3, router backend/app/routers/ai_knowledge.py)")
        print("=" * 80)
        
        # Test 1: GET /api/ai-knowledge/db-dsn
        self.test_ai_db_dsn()
        
        # Test 2: GET /api/ai-knowledge/db-check
        db_status = self.test_ai_db_check()
        
        # Test 3: POST /api/ai-knowledge/preview
        upload_id = self.test_ai_preview_txt()
        
        # Test 4: GET /api/ai-knowledge/status
        if upload_id:
            self.test_ai_status(upload_id)
        
        # Test 5: POST /api/ai-knowledge/study
        document_id = None
        if upload_id:
            document_id = self.test_ai_study(upload_id)
        
        # Test 6: GET /api/ai-knowledge/documents
        self.test_ai_documents_list()
        
        # Test 7: POST /api/ai-knowledge/search
        self.test_ai_search_psycopg3()
        
        # Test 8: DELETE /api/ai-knowledge/document/{document_id}
        if document_id:
            self.test_ai_delete_document_twice(document_id)
        
        # CRM regression tests
        print("\n🏠 CRM REGRESSION")
        print("=" * 80)
        
        # Test 9: GET /api/cleaning/filters
        self.test_crm_filters_structure()
        
        # Test 10: GET /api/cleaning/houses
        house_id = self.test_crm_houses_structure()
        
        # Test 11: GET /api/cleaning/house/{id}/details
        if house_id:
            self.test_crm_house_details_structure(house_id)
        
        # Summary
        print("\n" + "=" * 100)
        print(f"📊 REVIEW REQUEST TEST SUMMARY")
        print(f"   Total Tests: {self.tests_run}")
        print(f"   Passed: {self.tests_passed}")
        print(f"   Failed: {len(self.failed_tests)}")
        print(f"   Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        # Detailed pass/fail summary by points
        print(f"\n📋 PASS/FAIL SUMMARY BY POINTS:")
        
        # AI Knowledge points
        print(f"\n🧠 AI Knowledge (psycopg3):")
        ai_points = [
            ("1) GET /api/ai-knowledge/db-dsn", "AI DB DSN"),
            ("2) GET /api/ai-knowledge/db-check", "AI DB Check"),
            ("3) POST /api/ai-knowledge/preview", "AI Preview TXT"),
            ("4) GET /api/ai-knowledge/status", "AI Status"),
            ("5) POST /api/ai-knowledge/study", "AI Study"),
            ("6) GET /api/ai-knowledge/documents", "AI Documents List"),
            ("7) POST /api/ai-knowledge/search", "AI Search"),
            ("8) DELETE /api/ai-knowledge/document/{id} (twice)", "AI Delete")
        ]
        
        for point_desc, test_name in ai_points:
            failed = any(test_name in t['name'] for t in self.failed_tests)
            status = "❌ FAIL" if failed else "✅ PASS"
            print(f"   {point_desc}: {status}")
            if failed:
                for t in self.failed_tests:
                    if test_name in t['name']:
                        print(f"      Reason: {t['details']}")
        
        # CRM points
        print(f"\n🏠 CRM Regression:")
        crm_points = [
            ("9) GET /api/cleaning/filters", "CRM Filters Structure"),
            ("10) GET /api/cleaning/houses", "CRM Houses Structure"),
            ("11) GET /api/cleaning/house/{id}/details", "CRM House Details Structure")
        ]
        
        for point_desc, test_name in crm_points:
            failed = any(test_name in t['name'] for t in self.failed_tests)
            status = "❌ FAIL" if failed else "✅ PASS"
            print(f"   {point_desc}: {status}")
            if failed:
                for t in self.failed_tests:
                    if test_name in t['name']:
                        print(f"      Reason: {t['details']}")
        
        if self.failed_tests:
            print(f"\n❌ DETAILED FAILURE ANALYSIS:")
            for i, test in enumerate(self.failed_tests, 1):
                print(f"   {i}. {test['name']}")
                if test['details']:
                    print(f"      {test['details']}")
        
        print("=" * 100)
        print("🎯 Review Request Testing Complete")
        print("   Не останавливайся при первом сбое; дай сводку pass/fail по пунктам с краткими причинами и фрагментами ответов.")
        return self.tests_passed == self.tests_run

if __name__ == "__main__":
    tester = VasDomReviewTester()
    success = tester.run_review_request_tests()
    sys.exit(0 if success else 1)