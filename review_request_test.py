#!/usr/bin/env python3
"""
Review Request Backend Testing
Testing deployed backend at https://audiobot-qci2.onrender.com
Focus: AI Training + CRM endpoints as per review request
"""

import requests
import json
import io
from typing import Dict, Any, Optional

class ReviewRequestTester:
    def __init__(self, base_url="https://audiobot-qci2.onrender.com"):
        self.base_url = base_url.rstrip('/')
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []
        
    def log_test(self, name: str, success: bool, details: str = ""):
        """Log test result"""
        self.tests_run += 1
        status = "✅ PASSED" if success else "❌ FAILED"
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
                response = requests.get(url, headers=headers, params=params, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=30)
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

    def test_ai_knowledge_preview(self):
        """Test 1: POST /api/ai-knowledge/preview"""
        print("\n1️⃣ POST /api/ai-knowledge/preview")
        
        # Create "Hello AI" test.txt file
        txt_content = "Hello AI"
        files = {'file': ('test.txt', txt_content.encode('utf-8'), 'text/plain')}
        data = {'chunk_tokens': 600, 'overlap': 100}
        
        success, response_data, status = self.make_multipart_request('POST', '/api/ai-knowledge/preview', files=files, data=data)
        
        if success and status == 200:
            # Check required fields: upload_id, preview, chunks>=1, stats.total_size_bytes>0
            upload_id = response_data.get('upload_id')
            preview = response_data.get('preview')
            chunks = response_data.get('chunks', 0)
            stats = response_data.get('stats', {})
            total_size_bytes = stats.get('total_size_bytes', 0)
            
            if (upload_id and isinstance(upload_id, str) and
                preview and isinstance(preview, str) and
                chunks >= 1 and
                total_size_bytes > 0):
                
                self.log_test("AI Preview", True, 
                            f"upload_id: {upload_id[:8]}..., chunks: {chunks}, size: {total_size_bytes} bytes")
                return upload_id
            else:
                self.log_test("AI Preview", False, 
                            f"Invalid response: upload_id={bool(upload_id)}, chunks={chunks}, size={total_size_bytes}")
        else:
            self.log_test("AI Preview", False, f"Status: {status}, Response: {response_data}")
        
        return None

    def test_ai_knowledge_study(self, upload_id):
        """Test 2: POST /api/ai-knowledge/study"""
        print("\n2️⃣ POST /api/ai-knowledge/study")
        
        if not upload_id:
            self.log_test("AI Study", False, "No upload_id from preview")
            return None
        
        data = {
            'upload_id': upload_id,
            'filename': 'test.txt',
            'category': 'Клининг'
        }
        
        success, response_data, status = self.make_multipart_request('POST', '/api/ai-knowledge/study', data=data)
        
        if success and status == 200:
            document_id = response_data.get('document_id')
            chunks = response_data.get('chunks', 0)
            category = response_data.get('category')
            
            if document_id and chunks >= 1 and category:
                self.log_test("AI Study", True, 
                            f"document_id: {document_id[:8]}..., chunks: {chunks}, category: {category}")
                return document_id
            else:
                self.log_test("AI Study", False, 
                            f"Invalid response: document_id={bool(document_id)}, chunks={chunks}, category={category}")
        else:
            self.log_test("AI Study", False, f"Status: {status}, Response: {response_data}")
        
        return None

    def test_ai_knowledge_status(self, upload_id, expected_status):
        """Test 3: GET /api/ai-knowledge/status"""
        print(f"\n3️⃣ GET /api/ai-knowledge/status (expecting '{expected_status}')")
        
        if not upload_id:
            self.log_test("AI Status", False, "No upload_id provided")
            return
        
        success, response_data, status = self.make_request('GET', '/api/ai-knowledge/status', params={'upload_id': upload_id})
        
        if success and status == 200:
            actual_status = response_data.get('status')
            if actual_status == expected_status:
                self.log_test("AI Status", True, f"Status: {actual_status}")
            else:
                self.log_test("AI Status", False, f"Expected '{expected_status}', got '{actual_status}'")
        elif status == 404:
            if expected_status == 'not found':
                self.log_test("AI Status", True, "Upload not found (acceptable)")
            else:
                self.log_test("AI Status", False, f"Upload not found, expected '{expected_status}'")
        else:
            self.log_test("AI Status", False, f"Status: {status}, Response: {response_data}")

    def test_ai_knowledge_documents(self):
        """Test 4: GET /api/ai-knowledge/documents"""
        print("\n4️⃣ GET /api/ai-knowledge/documents")
        
        success, response_data, status = self.make_request('GET', '/api/ai-knowledge/documents')
        
        if success and status == 200:
            documents = response_data.get('documents', [])
            if isinstance(documents, list):
                # Check if any document has chunks_count >= 1
                valid_docs = [doc for doc in documents if doc.get('chunks_count', 0) >= 1]
                self.log_test("AI Documents", True, 
                            f"Found {len(documents)} documents, {len(valid_docs)} with chunks >= 1")
            else:
                self.log_test("AI Documents", False, f"Expected documents array, got {type(documents)}")
        else:
            self.log_test("AI Documents", False, f"Status: {status}, Response: {response_data}")

    def test_ai_knowledge_search(self):
        """Test 5: POST /api/ai-knowledge/search"""
        print("\n5️⃣ POST /api/ai-knowledge/search")
        
        search_data = {
            'query': 'Hello',
            'top_k': 5
        }
        
        success, response_data, status = self.make_request('POST', '/api/ai-knowledge/search', search_data)
        
        if success and status == 200:
            results = response_data.get('results', [])
            if isinstance(results, list):
                self.log_test("AI Search", True, f"Search returned {len(results)} results")
            else:
                self.log_test("AI Search", False, f"Expected results array, got {type(results)}")
        else:
            self.log_test("AI Search", False, f"Status: {status}, Response: {response_data}")

    def test_ai_knowledge_delete(self, document_id):
        """Test 6: DELETE /api/ai-knowledge/document/{document_id}"""
        print("\n6️⃣ DELETE /api/ai-knowledge/document/{document_id}")
        
        if not document_id:
            self.log_test("AI Delete", False, "No document_id provided")
            return
        
        # First delete
        success, response_data, status = self.make_request('DELETE', f'/api/ai-knowledge/document/{document_id}')
        
        if success and status == 200:
            ok = response_data.get('ok')
            if ok is True:
                self.log_test("AI Delete (First)", True, f"Document deleted: {ok}")
                
                # Second delete (should also return 200)
                success2, response_data2, status2 = self.make_request('DELETE', f'/api/ai-knowledge/document/{document_id}')
                if success2 and status2 == 200:
                    self.log_test("AI Delete (Repeat)", True, "Repeated delete returns 200")
                else:
                    self.log_test("AI Delete (Repeat)", False, f"Status: {status2}, Response: {response_data2}")
            else:
                self.log_test("AI Delete (First)", False, f"Expected ok:true, got {ok}")
        else:
            self.log_test("AI Delete (First)", False, f"Status: {status}, Response: {response_data}")

    def test_crm_cleaning_filters(self):
        """Test 7: GET /api/cleaning/filters"""
        print("\n7️⃣ GET /api/cleaning/filters")
        
        success, response_data, status = self.make_request('GET', '/api/cleaning/filters')
        
        if success and status == 200:
            brigades = response_data.get('brigades', [])
            management_companies = response_data.get('management_companies', [])
            
            brigades_ok = isinstance(brigades, list) and len(brigades) > 0
            companies_ok = isinstance(management_companies, list) and len(management_companies) == 0
            
            if brigades_ok and companies_ok:
                self.log_test("CRM Filters", True, 
                            f"brigades: {len(brigades)} (non-empty), management_companies: [] (empty)")
                print(f"   Sample brigades: {brigades[:5]}")
            else:
                self.log_test("CRM Filters", False, 
                            f"brigades non-empty: {brigades_ok}, management_companies empty: {companies_ok}")
        else:
            self.log_test("CRM Filters", False, f"Status: {status}, Response: {response_data}")

    def test_crm_cleaning_houses(self):
        """Test 8: GET /api/cleaning/houses"""
        print("\n8️⃣ GET /api/cleaning/houses?page=1&limit=50")
        
        success, response_data, status = self.make_request('GET', '/api/cleaning/houses', 
                                                         params={'page': 1, 'limit': 50})
        
        if success and status == 200:
            houses = response_data.get('houses', [])
            total = response_data.get('total', 0)
            
            if isinstance(houses, list) and len(houses) > 0:
                # Check required fields in first house
                house = houses[0]
                required_fields = ['id', 'title', 'address', 'apartments', 'entrances', 'floors', 
                                 'cleaning_dates', 'periodicity', 'bitrix_url']
                missing_fields = [field for field in required_fields if field not in house]
                
                if not missing_fields:
                    self.log_test("CRM Houses", True, 
                                f"houses: {len(houses)}, total: {total}, all required fields present")
                    print(f"   Sample house: ID={house['id']}, title='{house['title'][:30]}...', brigade='{house.get('brigade', 'N/A')}'")
                else:
                    self.log_test("CRM Houses", False, f"Missing fields: {missing_fields}")
            else:
                self.log_test("CRM Houses", False, f"Expected non-empty houses array, got {len(houses)} houses")
        else:
            self.log_test("CRM Houses", False, f"Status: {status}, Response: {response_data}")

    def test_logistics_route_optional(self):
        """Test 9: POST /api/logistics/route (optional)"""
        print("\n9️⃣ POST /api/logistics/route (optional)")
        
        # Test with 1 point - should return 400 'Минимум 2 точки' if exists, 404 if not
        test_data = {
            "points": [{"address": "Москва, Красная площадь"}],
            "optimize": False
        }
        
        success, response_data, status = self.make_request('POST', '/api/logistics/route', test_data)
        
        if status == 400:
            detail = response_data.get('detail', '')
            if 'Минимум 2 точки' in detail:
                self.log_test("Logistics Route", True, f"Endpoint exists, correct validation: {detail}")
            else:
                self.log_test("Logistics Route", False, f"Wrong validation message: {detail}")
        elif status == 404:
            self.log_test("Logistics Route", True, "Endpoint not implemented (404 acceptable)")
        else:
            self.log_test("Logistics Route", False, f"Unexpected status: {status}, Response: {response_data}")

    def run_full_test(self):
        """Run all tests as per review request"""
        print("🚀 REVIEW REQUEST BACKEND TESTING")
        print("=" * 60)
        print(f"Base URL: {self.base_url}")
        print("Testing: AI Training + CRM endpoints")
        print("=" * 60)
        
        # AI Training Tests
        print("\n🧠 AI TRAINING ENDPOINTS")
        print("-" * 40)
        
        upload_id = self.test_ai_knowledge_preview()
        
        # Test status before study (should be 'ready')
        if upload_id:
            self.test_ai_knowledge_status(upload_id, 'ready')
        
        document_id = None
        if upload_id:
            document_id = self.test_ai_knowledge_study(upload_id)
        
        # Test status after study (should be 'done')
        if upload_id and document_id:
            self.test_ai_knowledge_status(upload_id, 'done')
        
        self.test_ai_knowledge_documents()
        self.test_ai_knowledge_search()
        
        if document_id:
            self.test_ai_knowledge_delete(document_id)
        
        # CRM Regression Tests
        print("\n🏠 CRM REGRESSION TESTS")
        print("-" * 40)
        
        self.test_crm_cleaning_filters()
        self.test_crm_cleaning_houses()
        
        # Optional Logistics Test
        print("\n🚛 OPTIONAL LOGISTICS TEST")
        print("-" * 40)
        
        self.test_logistics_route_optional()
        
        # Final Summary
        print("\n" + "=" * 60)
        print("📊 FINAL SUMMARY")
        print("=" * 60)
        print(f"Total Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {len(self.failed_tests)}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        if self.failed_tests:
            print("\n❌ FAILED TESTS:")
            print("-" * 40)
            for i, test in enumerate(self.failed_tests, 1):
                print(f"{i}. {test['name']}")
                if test['details']:
                    print(f"   {test['details']}")
        
        print("\n" + "=" * 60)

if __name__ == "__main__":
    tester = ReviewRequestTester()
    tester.run_full_test()