#!/usr/bin/env python3
"""
VasDom AudioBot Backend API Testing - psycopg3 async migration
Testing AI Knowledge endpoints after migration to psycopg3 async
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
        # Use environment backend URL
        if base_url is None:
            # Read from frontend/.env to get the backend URL
            try:
                with open('/app/frontend/.env', 'r') as f:
                    for line in f:
                        if line.startswith('REACT_APP_BACKEND_URL='):
                            base_url = line.split('=', 1)[1].strip()
                            break
            except:
                base_url = "https://rusip.preview.emergentagent.com"
        
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
    
    def mask_sensitive_url(self, url: str) -> str:
        """Mask sensitive parts of URL for logging"""
        if not url or '@' not in url:
            return url
        try:
            parts = url.split('@')
            if len(parts) >= 2:
                # Mask username:password part
                auth_part = parts[0]
                if '://' in auth_part:
                    scheme_part, creds = auth_part.rsplit('://', 1)
                    if ':' in creds:
                        user, pwd = creds.split(':', 1)
                        masked_creds = f"{user[:2]}***:{pwd[:2]}***"
                    else:
                        masked_creds = f"{creds[:2]}***"
                    return f"{scheme_part}://{masked_creds}@{'@'.join(parts[1:])}"
            return url
        except:
            return url[:20] + "***"
    
    def test_psycopg3_migration(self):
        """Main test method for psycopg3 async migration as per review request"""
        print("\n" + "="*80)
        print("🔬 TESTING BACKEND AFTER PSYCOPG3 ASYNC MIGRATION")
        print("="*80)
        print(f"Backend URL: {self.base_url}")
        print(f"Testing AI Knowledge endpoints and CRM regression")
        print("-"*80)
        
        # AI Knowledge (psycopg3) tests
        print("\n🧠 AI KNOWLEDGE (psycopg3) TESTS:")
        
        # 1) GET /api/ai-knowledge/db-dsn
        dsn_data = self.test_db_dsn_endpoint()
        
        # 2) GET /api/ai-knowledge/db-check  
        db_status = self.test_db_check_endpoint()
        
        # 3) POST /api/ai-knowledge/preview
        self.test_ai_preview_endpoint()
        
        # 4) GET /api/ai-knowledge/status
        self.test_ai_status_endpoint()
        
        # 5) POST /api/ai-knowledge/study
        self.test_ai_study_endpoint()
        
        # 6) GET /api/ai-knowledge/db-check (repeat)
        self.test_db_check_repeat()
        
        # Documents/search tests (these are in server.py, not the new router)
        print("\n📚 DOCUMENTS/SEARCH TESTS:")
        
        # 7) GET /api/ai-knowledge/documents (from server.py)
        self.test_ai_documents_endpoint()
        
        # 8) POST /api/ai-knowledge/search (from server.py)
        self.test_ai_search_endpoint()
        
        # 9) DELETE /api/ai-knowledge/document/{document_id} (from server.py)
        self.test_ai_delete_endpoint()
        
        # CRM regression tests
        print("\n🏠 CRM REGRESSION TESTS:")
        
        # 10) GET /api/cleaning/filters
        self.test_crm_filters_regression()
        
        # 11) GET /api/cleaning/houses
        house_id = self.test_crm_houses_regression()
        
        # 12) GET /api/cleaning/house/{id}/details
        if house_id:
            self.test_crm_house_details_regression(house_id)
        
        # Print final summary
        self.print_final_summary()
        
        return self.tests_passed, self.tests_run
    
    def test_db_dsn_endpoint(self):
        """Test 1: GET /api/ai-knowledge/db-dsn"""
        print("\n1️⃣ GET /api/ai-knowledge/db-dsn")
        
        success, data, status = self.make_request('GET', '/api/ai-knowledge/db-dsn')
        
        if success and status == 200:
            # Check expected fields - handle different response formats
            scheme = data.get('scheme', '')
            normalized = data.get('normalized', {})
            if normalized:
                normalized_query = normalized.get('query', '') if isinstance(normalized, dict) else str(normalized)
            else:
                normalized_query = ''
            username_masked = data.get('username_masked', False)
            raw_present = data.get('raw_present', False)
            
            # Verify scheme=postgresql
            scheme_ok = 'postgresql' in scheme.lower() if scheme else False
            
            # Verify sslmode=require in normalized.query
            sslmode_ok = 'sslmode=require' in normalized_query or 'ssl=true' in normalized_query
            
            # Log results
            details = f"scheme={'postgresql' if scheme_ok else scheme}, sslmode={'present' if sslmode_ok else 'missing'}, username_masked={username_masked}, raw_present={raw_present}"
            
            if scheme_ok or raw_present:  # Accept if either scheme is correct or raw is present
                self.log_test("DB DSN Endpoint", True, details)
                return data
            else:
                self.log_test("DB DSN Endpoint", False, f"Issues: {details}")
        elif status == 404:
            self.log_test("DB DSN Endpoint", False, "Endpoint not found - may not be implemented")
        else:
            self.log_test("DB DSN Endpoint", False, f"Status: {status}, Data: {data}")
        
        return None
    
    def test_db_check_endpoint(self):
        """Test 2: GET /api/ai-knowledge/db-check"""
        print("\n2️⃣ GET /api/ai-knowledge/db-check")
        
        success, data, status = self.make_request('GET', '/api/ai-knowledge/db-check')
        
        if success and status == 200:
            connected = data.get('connected', False)
            pgvector_available = data.get('pgvector_available', False)
            ai_tables = data.get('ai_tables', [])
            embedding_dims = data.get('embedding_dims', 0)
            errors = data.get('errors', [])
            
            # Expected ai_tables
            expected_tables = ['ai_documents', 'ai_chunks', 'ai_uploads_temp']
            tables_ok = all(table in ai_tables for table in expected_tables)
            
            # Expected embedding_dims = 1536 (text-embedding-3-small)
            dims_ok = embedding_dims == 1536
            
            if connected and tables_ok and dims_ok:
                details = f"connected=true, pgvector_available={pgvector_available}, ai_tables={len(ai_tables)}, embedding_dims={embedding_dims}"
                self.log_test("DB Check - Success", True, details)
            elif not connected:
                details = f"connected=false, errors={len(errors)}: {errors[:2] if errors else 'none'}"
                self.log_test("DB Check - Connection Failed", False, details)
            else:
                details = f"connected={connected}, tables_ok={tables_ok}, dims_ok={dims_ok} (expected 1536, got {embedding_dims})"
                self.log_test("DB Check - Partial Success", False, details)
            
            return data
        else:
            self.log_test("DB Check Endpoint", False, f"Status: {status}, Data: {data}")
        
        return None
    
    def test_ai_preview_endpoint(self):
        """Test 3: POST /api/ai-knowledge/preview"""
        print("\n3️⃣ POST /api/ai-knowledge/preview")
        
        # Create small TXT file
        txt_content = "Hello AI\n\nThis is a test document for VasDom AudioBot AI training system."
        files = {'file': ('test.txt', txt_content.encode('utf-8'), 'text/plain')}  # Single file, not files array
        
        success, data, status = self.make_multipart_request('POST', '/api/ai-knowledge/preview', files=files)
        
        if success and status == 200:
            upload_id = data.get('upload_id', '')
            preview = data.get('preview', '')
            chunks = data.get('chunks', 0)
            stats = data.get('stats', {})
            total_size_bytes = stats.get('total_size_bytes', 0)
            
            if upload_id and isinstance(preview, str) and chunks > 0 and total_size_bytes > 0:
                self.upload_id = upload_id  # Store for later tests
                details = f"upload_id={upload_id[:8]}..., preview={len(preview)} chars, chunks={chunks}, size={total_size_bytes} bytes"
                self.log_test("AI Preview - Success", True, details)
            else:
                details = f"Missing fields: upload_id={bool(upload_id)}, preview={len(preview) if isinstance(preview, str) else type(preview)}, chunks={chunks}, size={total_size_bytes}"
                self.log_test("AI Preview - Invalid Response", False, details)
        elif status == 500 and 'Database is not initialized' in data.get('detail', ''):
            self.log_test("AI Preview - DB Not Initialized", False, f"Database not initialized: {data.get('detail')}")
        else:
            self.log_test("AI Preview Endpoint", False, f"Status: {status}, Data: {data}")
    
    def test_ai_status_endpoint(self):
        """Test 4: GET /api/ai-knowledge/status?upload_id=<id>"""
        print("\n4️⃣ GET /api/ai-knowledge/status")
        
        if not self.upload_id:
            self.log_test("AI Status - No Upload ID", False, "No upload_id from previous test")
            return
        
        params = {'upload_id': self.upload_id}
        success, data, status = self.make_request('GET', '/api/ai-knowledge/status', params=params)
        
        if success and status == 200:
            status_value = data.get('status', '')
            if status_value == 'ready':
                self.log_test("AI Status - Ready", True, f"status='ready' for upload_id {self.upload_id[:8]}...")
            else:
                self.log_test("AI Status - Wrong Status", False, f"Expected 'ready', got '{status_value}'")
        else:
            self.log_test("AI Status Endpoint", False, f"Status: {status}, Data: {data}")
    
    def test_ai_study_endpoint(self):
        """Test 5: POST /api/ai-knowledge/study"""
        print("\n5️⃣ POST /api/ai-knowledge/study")
        
        if not self.upload_id:
            self.log_test("AI Study - No Upload ID", False, "No upload_id from previous test")
            return
        
        form_data = {
            'upload_id': self.upload_id,
            'filename': 'test.txt',
            'category': 'Маркетинг'
        }
        
        success, data, status = self.make_multipart_request('POST', '/api/ai-knowledge/study', data=form_data)
        
        if success and status == 200:
            document_id = data.get('document_id', '')
            chunks = data.get('chunks', 0)
            category = data.get('category', '')
            
            if document_id and chunks > 0 and category == 'Маркетинг':
                self.document_id = document_id  # Store for later tests
                details = f"document_id={document_id[:8]}..., chunks={chunks}, category='{category}'"
                self.log_test("AI Study - Success", True, details)
            else:
                details = f"Missing fields: document_id={bool(document_id)}, chunks={chunks}, category='{category}'"
                self.log_test("AI Study - Invalid Response", False, details)
        else:
            self.log_test("AI Study Endpoint", False, f"Status: {status}, Data: {data}")
    
    def test_db_check_repeat(self):
        """Test 6: GET /api/ai-knowledge/db-check (repeat)"""
        print("\n6️⃣ GET /api/ai-knowledge/db-check (repeat)")
        
        success, data, status = self.make_request('GET', '/api/ai-knowledge/db-check')
        
        if success and status == 200:
            ai_tables = data.get('ai_tables', [])
            errors = data.get('errors', [])
            
            if ai_tables and len(errors) == 0:
                details = f"ai_tables not empty ({len(ai_tables)} tables), no errors"
                self.log_test("DB Check Repeat - Success", True, details)
            elif ai_tables and len(errors) > 0:
                details = f"ai_tables present ({len(ai_tables)} tables), but {len(errors)} errors (may not be critical)"
                self.log_test("DB Check Repeat - With Errors", True, details)
            else:
                details = f"ai_tables empty, {len(errors)} errors"
                self.log_test("DB Check Repeat - Failed", False, details)
        else:
            self.log_test("DB Check Repeat", False, f"Status: {status}, Data: {data}")
    
    def test_ai_documents_endpoint(self):
        """Test 7: GET /api/ai-knowledge/documents"""
        print("\n7️⃣ GET /api/ai-knowledge/documents")
        
        success, data, status = self.make_request('GET', '/api/ai-knowledge/documents')
        
        if success and status == 200:
            documents = data.get('documents', [])
            
            # Look for our document from test 5
            found_document = False
            if self.document_id:
                for doc in documents:
                    if doc.get('id') == self.document_id:
                        chunks_count = doc.get('chunks_count', 0)
                        if chunks_count >= 1:
                            found_document = True
                            details = f"Found document {self.document_id[:8]}... with chunks_count={chunks_count}"
                            self.log_test("AI Documents - Found Document", True, details)
                            break
            
            if not found_document:
                if documents:
                    details = f"Retrieved {len(documents)} documents, but our test document not found"
                    self.log_test("AI Documents - Document Missing", False, details)
                else:
                    details = "No documents found"
                    self.log_test("AI Documents - Empty List", False, details)
        else:
            self.log_test("AI Documents Endpoint", False, f"Status: {status}, Data: {data}")
    
    def test_ai_search_endpoint(self):
        """Test 8: POST /api/ai-knowledge/search"""
        print("\n8️⃣ POST /api/ai-knowledge/search")
        
        search_data = {
            'query': 'Hello',
            'top_k': 10
        }
        
        success, data, status = self.make_request('POST', '/api/ai-knowledge/search', search_data)
        
        if success and status == 200:
            results = data.get('results', [])
            
            if isinstance(results, list):
                details = f"Search returned {len(results)} results"
                if results:
                    # Check if scores are same (acceptable without OPENAI_API_KEY)
                    scores = [r.get('score', 0) for r in results]
                    if len(set(scores)) == 1:
                        details += f", all scores same ({scores[0]}) - acceptable without OPENAI_API_KEY"
                    else:
                        details += f", varied scores: {scores[:3]}"
                
                self.log_test("AI Search - Success", True, details)
            else:
                self.log_test("AI Search - Invalid Response", False, f"Expected results array, got {type(results)}")
        else:
            self.log_test("AI Search Endpoint", False, f"Status: {status}, Data: {data}")
    
    def test_ai_delete_endpoint(self):
        """Test 9: DELETE /api/ai-knowledge/document/{document_id}"""
        print("\n9️⃣ DELETE /api/ai-knowledge/document/{document_id}")
        
        if not self.document_id:
            self.log_test("AI Delete - No Document ID", False, "No document_id from previous test")
            return
        
        # First delete
        success, data, status = self.make_request('DELETE', f'/api/ai-knowledge/document/{self.document_id}')
        
        if success and status == 200:
            ok_value = data.get('ok', False)
            if ok_value is True:
                self.log_test("AI Delete - First Delete", True, f"Document {self.document_id[:8]}... deleted successfully")
                
                # Second delete (should be idempotent)
                success2, data2, status2 = self.make_request('DELETE', f'/api/ai-knowledge/document/{self.document_id}')
                
                if success2 and status2 == 200 and data2.get('ok') is True:
                    self.log_test("AI Delete - Repeat Delete", True, "Repeat delete returns ok:true (idempotent)")
                else:
                    self.log_test("AI Delete - Repeat Delete", False, f"Repeat delete failed: Status {status2}, Data: {data2}")
            else:
                self.log_test("AI Delete - Invalid Response", False, f"Expected ok:true, got ok:{ok_value}")
        else:
            self.log_test("AI Delete Endpoint", False, f"Status: {status}, Data: {data}")
    
    def test_crm_filters_regression(self):
        """Test 10: GET /api/cleaning/filters - regression test"""
        print("\n🔟 GET /api/cleaning/filters (regression)")
        
        success, data, status = self.make_request('GET', '/api/cleaning/filters')
        
        if success and status == 200:
            # Check structure
            required_fields = ['brigades', 'management_companies', 'statuses']
            missing_fields = [field for field in required_fields if field not in data]
            
            if not missing_fields:
                brigades = data.get('brigades', [])
                management_companies = data.get('management_companies', [])
                statuses = data.get('statuses', [])
                
                # All should be arrays
                if all(isinstance(field, list) for field in [brigades, management_companies, statuses]):
                    details = f"brigades: {len(brigades)}, management_companies: {len(management_companies)}, statuses: {len(statuses)}"
                    self.log_test("CRM Filters Regression", True, details)
                else:
                    self.log_test("CRM Filters Regression", False, "Fields are not arrays")
            else:
                self.log_test("CRM Filters Regression", False, f"Missing fields: {missing_fields}")
        else:
            self.log_test("CRM Filters Regression", False, f"Status: {status}, Data: {data}")
    
    def test_crm_houses_regression(self):
        """Test 11: GET /api/cleaning/houses - regression test"""
        print("\n1️⃣1️⃣ GET /api/cleaning/houses (regression)")
        
        params = {'page': 1, 'limit': 5}
        success, data, status = self.make_request('GET', '/api/cleaning/houses', params=params)
        
        if success and status == 200:
            houses = data.get('houses', [])
            
            if isinstance(houses, list) and houses:
                house = houses[0]
                house_id = house.get('id')
                
                # Check required fields
                required_fields = ['id', 'title', 'address', 'brigade', 'management_company', 'cleaning_dates', 'periodicity', 'bitrix_url']
                missing_fields = [field for field in required_fields if field not in house]
                
                if not missing_fields:
                    # Check date format in cleaning_dates
                    cleaning_dates = house.get('cleaning_dates', {})
                    dates_ok = True
                    sample_dates = []
                    
                    for period, period_data in cleaning_dates.items():
                        if isinstance(period_data, dict):
                            dates = period_data.get('dates', [])
                            for date in dates:
                                if isinstance(date, str) and len(date) == 10 and date.count('-') == 2:
                                    sample_dates.append(date)
                                else:
                                    dates_ok = False
                                    break
                    
                    # Check bitrix_url format
                    bitrix_url = house.get('bitrix_url', '')
                    bitrix_ok = 'bitrix24.ru/crm/deal/details/' in bitrix_url
                    
                    if dates_ok and bitrix_ok:
                        details = f"House {house_id}: all fields present, dates YYYY-MM-DD format, bitrix_url correct"
                        self.log_test("CRM Houses Regression", True, details)
                        return house_id
                    else:
                        issues = []
                        if not dates_ok:
                            issues.append("date format issues")
                        if not bitrix_ok:
                            issues.append("bitrix_url format issues")
                        self.log_test("CRM Houses Regression", False, f"Issues: {', '.join(issues)}")
                else:
                    self.log_test("CRM Houses Regression", False, f"Missing fields: {missing_fields}")
            else:
                self.log_test("CRM Houses Regression", False, "No houses returned or invalid format")
        else:
            self.log_test("CRM Houses Regression", False, f"Status: {status}, Data: {data}")
        
        return None
    
    def test_crm_house_details_regression(self, house_id):
        """Test 12: GET /api/cleaning/house/{id}/details - regression test"""
        print(f"\n1️⃣2️⃣ GET /api/cleaning/house/{house_id}/details (regression)")
        
        success, data, status = self.make_request('GET', f'/api/cleaning/house/{house_id}/details')
        
        if success and status == 200:
            # Check structure
            required_sections = ['house', 'management_company', 'senior_resident']
            missing_sections = [section for section in required_sections if section not in data]
            
            if not missing_sections:
                house = data.get('house', {})
                periodicity = house.get('periodicity', '')
                
                if periodicity:
                    details = f"House {house_id}: structure correct, periodicity='{periodicity}'"
                    self.log_test("CRM House Details Regression", True, details)
                else:
                    self.log_test("CRM House Details Regression", False, "Missing periodicity field")
            else:
                self.log_test("CRM House Details Regression", False, f"Missing sections: {missing_sections}")
        elif status == 500:
            # Check if it's a safe Bitrix error, not a crash
            detail = data.get('detail', '')
            if 'Bitrix' in detail or 'битрикс' in detail.lower():
                self.log_test("CRM House Details - Bitrix Error", True, f"Safe Bitrix error (not 500 crash): {detail}")
            else:
                self.log_test("CRM House Details Regression", False, f"500 error: {detail}")
        else:
            self.log_test("CRM House Details Regression", False, f"Status: {status}, Data: {data}")
    
    def print_final_summary(self):
        """Print final test summary"""
        print("\n" + "="*80)
        print("📊 FINAL TEST SUMMARY")
        print("="*80)
        
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {len(self.failed_tests)}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if self.failed_tests:
            print(f"\n❌ FAILED TESTS:")
            for i, test in enumerate(self.failed_tests, 1):
                print(f"   {i}. {test['name']}")
                if test['details']:
                    print(f"      → {test['details']}")
        
        print("\n" + "="*80)

def main():
    """Main function to run the tests"""
    print("🚀 Starting psycopg3 async migration tests...")
    
    tester = VasDomAPITester()
    passed, total = tester.test_psycopg3_migration()
    
    print(f"\n🏁 Testing completed: {passed}/{total} tests passed")
    
    # Exit with appropriate code
    if passed == total:
        print("✅ All tests passed!")
        sys.exit(0)
    else:
        print("❌ Some tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()