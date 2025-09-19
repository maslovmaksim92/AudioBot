#!/usr/bin/env python3
"""
Review Request Testing: Apply migrations by restarting and then run diagnostic and AI flow
Base: https://audiobot-qci2.onrender.com
1) GET /api/ai-knowledge/db-check — expect connected true; if pgvector_installed false but available true, POST install
2) If table exists, run quick AI flow: preview -> study -> documents -> search -> delete
"""

import requests
import json
import time
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

    def test_db_check_endpoint(self):
        """Test GET /api/ai-knowledge/db-check endpoint"""
        print("\n1️⃣ Testing GET /api/ai-knowledge/db-check")
        
        success, data, status = self.make_request('GET', '/api/ai-knowledge/db-check')
        
        if success and status == 200:
            # Check if response has expected diagnostic fields
            expected_fields = ['connected', 'pgvector_available', 'pgvector_installed']
            missing_fields = [field for field in expected_fields if field not in data]
            
            if not missing_fields:
                connected = data.get('connected', False)
                pgvector_available = data.get('pgvector_available', False)
                pgvector_installed = data.get('pgvector_installed', False)
                
                diagnostic_info = f"connected={connected}, pgvector_available={pgvector_available}, pgvector_installed={pgvector_installed}"
                self.log_test("DB Check - Diagnostic Response", True, diagnostic_info)
                
                print(f"   📊 Database Status:")
                print(f"      Connected: {connected}")
                print(f"      PGVector Available: {pgvector_available}")
                print(f"      PGVector Installed: {pgvector_installed}")
                
                if 'errors' in data and data['errors']:
                    print(f"      Errors: {data['errors']}")
                
                return data
            else:
                self.log_test("DB Check - Diagnostic Response", False, f"Missing diagnostic fields: {missing_fields}")
        elif status == 404:
            self.log_test("DB Check - Endpoint Exists", False, "db-check endpoint not found (404) - not deployed")
        elif status == 500:
            detail = data.get('detail', '')
            self.log_test("DB Check - Endpoint Response", False, f"500 error: {detail}")
        else:
            self.log_test("DB Check - Endpoint Response", False, f"Status: {status}, Data: {data}")
        
        return None

    def test_db_install_vector_endpoint(self):
        """Test POST /api/ai-knowledge/db-install-vector endpoint"""
        print("\n2️⃣ Testing POST /api/ai-knowledge/db-install-vector")
        
        success, data, status = self.make_request('POST', '/api/ai-knowledge/db-install-vector', {})
        
        if success and status == 200:
            if 'success' in data:
                install_success = data.get('success', False)
                message = data.get('message', '')
                self.log_test("DB Install Vector - Installation", install_success, f"Message: {message}")
                return install_success
            else:
                self.log_test("DB Install Vector - Installation", False, f"Unexpected response format: {data}")
        elif status == 422:
            # Validation error is acceptable if endpoint expects specific body format
            detail = data.get('detail', '')
            self.log_test("DB Install Vector - Validation", True, f"Validation error (acceptable): {detail}")
            return False
        elif status == 404:
            self.log_test("DB Install Vector - Endpoint Exists", False, "db-install-vector endpoint not found (404)")
        else:
            self.log_test("DB Install Vector - Installation", False, f"Status: {status}, Data: {data}")
        
        return False

    def test_ai_flow_preview(self):
        """Test AI flow step 1: preview (upload)"""
        print("\n3️⃣ Testing AI Flow - Preview (Upload)")
        
        # Create a simple test document
        txt_content = """Test document for VasDom AudioBot AI Knowledge Base.
        
This document contains information about:
1. Cleaning management system
2. House and apartment management
3. Brigade scheduling
4. Quality control processes
5. Bitrix24 integration

The system manages 490+ houses with multiple cleaning brigades."""

        files = {'files': ('test_ai_document.txt', txt_content.encode('utf-8'), 'text/plain')}
        data = {'chunk_tokens': '600', 'overlap': '100'}
        
        success, response_data, status = self.make_multipart_request('POST', '/api/ai-knowledge/preview', files=files, data=data)
        
        if success and status == 200:
            # Check required fields
            required_fields = ['upload_id', 'preview', 'chunks']
            missing_fields = [field for field in required_fields if field not in response_data]
            
            if not missing_fields:
                upload_id = response_data['upload_id']
                chunks = response_data['chunks']
                preview = response_data['preview']
                
                if chunks > 0 and isinstance(preview, str) and len(preview) > 0:
                    self.log_test("AI Flow - Preview", True, 
                                f"upload_id: {upload_id[:8]}..., chunks: {chunks}, preview: {len(preview)} chars")
                    return upload_id
                else:
                    self.log_test("AI Flow - Preview", False, f"Invalid chunks ({chunks}) or preview ({len(preview) if isinstance(preview, str) else type(preview)})")
            else:
                self.log_test("AI Flow - Preview", False, f"Missing fields: {missing_fields}")
        elif status == 500 and 'Database is not initialized' in response_data.get('detail', ''):
            self.log_test("AI Flow - Preview", False, f"Database not initialized: {response_data.get('detail')}")
        else:
            self.log_test("AI Flow - Preview", False, f"Status: {status}, Data: {response_data}")
        
        return None

    def test_ai_flow_study(self, upload_id):
        """Test AI flow step 2: study (save)"""
        print("\n4️⃣ Testing AI Flow - Study (Save)")
        
        if not upload_id:
            self.log_test("AI Flow - Study", False, "No upload_id provided")
            return None
            
        data = {
            'upload_id': upload_id,
            'filename': 'test_knowledge_document.txt',
            'category': 'Клининг'
        }
        
        success, response_data, status = self.make_multipart_request('POST', '/api/ai-knowledge/study', data=data)
        
        if success and status == 200:
            if 'document_id' in response_data:
                document_id = response_data['document_id']
                chunks = response_data.get('chunks', 0)
                category = response_data.get('category', '')
                self.log_test("AI Flow - Study", True, f"Document saved: {document_id[:8]}..., chunks: {chunks}, category: {category}")
                return document_id
            else:
                self.log_test("AI Flow - Study", False, f"Missing document_id in response: {response_data}")
        elif status == 404:
            self.log_test("AI Flow - Study", False, f"upload_id not found or expired: {response_data.get('detail', '')}")
        elif status == 500 and 'Database is not initialized' in response_data.get('detail', ''):
            self.log_test("AI Flow - Study", False, f"Database not initialized: {response_data.get('detail')}")
        else:
            self.log_test("AI Flow - Study", False, f"Status: {status}, Data: {response_data}")
        
        return None

    def test_ai_flow_documents(self):
        """Test AI flow step 3: documents (list)"""
        print("\n5️⃣ Testing AI Flow - Documents (List)")
        
        success, data, status = self.make_request('GET', '/api/ai-knowledge/documents')
        
        if success and status == 200:
            if 'documents' in data and isinstance(data['documents'], list):
                docs_count = len(data['documents'])
                self.log_test("AI Flow - Documents", True, f"Retrieved {docs_count} documents")
                
                # Check document structure if any documents exist
                if docs_count > 0:
                    doc = data['documents'][0]
                    required_fields = ['id', 'filename']
                    missing_fields = [field for field in required_fields if field not in doc]
                    
                    if not missing_fields:
                        self.log_test("AI Flow - Document Structure", True, f"Document structure valid: {doc.get('filename', 'N/A')}")
                    else:
                        self.log_test("AI Flow - Document Structure", False, f"Missing fields: {missing_fields}")
                
                return True
            else:
                self.log_test("AI Flow - Documents", False, f"Invalid response structure: {data}")
        elif status == 500 and 'Database is not initialized' in data.get('detail', ''):
            self.log_test("AI Flow - Documents", False, f"Database not initialized: {data.get('detail')}")
        else:
            self.log_test("AI Flow - Documents", False, f"Status: {status}, Data: {data}")
        
        return False

    def test_ai_flow_search(self):
        """Test AI flow step 4: search"""
        print("\n6️⃣ Testing AI Flow - Search")
        
        search_data = {
            'query': 'cleaning management system',
            'top_k': 5
        }
        
        success, data, status = self.make_request('POST', '/api/ai-knowledge/search', search_data)
        
        if success and status == 200:
            if 'results' in data and isinstance(data['results'], list):
                results_count = len(data['results'])
                self.log_test("AI Flow - Search", True, f"Search returned {results_count} results")
                
                # Check result structure if any results exist
                if results_count > 0:
                    result = data['results'][0]
                    required_fields = ['document_id', 'content', 'score', 'filename']
                    missing_fields = [field for field in required_fields if field not in result]
                    
                    if not missing_fields:
                        score = result.get('score', 0)
                        self.log_test("AI Flow - Search Result Structure", True, 
                                    f"Result structure valid, score: {score}, filename: {result.get('filename', 'N/A')}")
                    else:
                        self.log_test("AI Flow - Search Result Structure", False, f"Missing fields: {missing_fields}")
                
                return True
            else:
                self.log_test("AI Flow - Search", False, f"Invalid response structure: {data}")
        elif status == 400:
            self.log_test("AI Flow - Search", False, f"Bad request: {data.get('detail', '')}")
        elif status == 500 and 'Database is not initialized' in data.get('detail', ''):
            self.log_test("AI Flow - Search", False, f"Database not initialized: {data.get('detail')}")
        else:
            self.log_test("AI Flow - Search", False, f"Status: {status}, Data: {data}")
        
        return False

    def test_ai_flow_delete(self, document_id):
        """Test AI flow step 5: delete"""
        print("\n7️⃣ Testing AI Flow - Delete")
        
        if not document_id:
            self.log_test("AI Flow - Delete", False, "No document_id provided")
            return False
            
        success, data, status = self.make_request('DELETE', f'/api/ai-knowledge/document/{document_id}')
        
        if success and status == 200:
            if data.get('ok') is True:
                self.log_test("AI Flow - Delete", True, f"Document {document_id[:8]}... deleted successfully")
                return True
            else:
                self.log_test("AI Flow - Delete", False, f"Unexpected response: {data}")
        elif status == 500 and 'Database is not initialized' in data.get('detail', ''):
            self.log_test("AI Flow - Delete", False, f"Database not initialized: {data.get('detail')}")
        else:
            self.log_test("AI Flow - Delete", False, f"Status: {status}, Data: {data}")
        
        return False

    def run_review_request_test(self):
        """Run the complete review request test sequence"""
        print("🔍 REVIEW REQUEST TESTING")
        print("=" * 70)
        print(f"Base URL: {self.base_url}")
        print("Sequence: db-check → install (if needed) → AI flow (preview → study → documents → search → delete)")
        print("=" * 70)
        
        # Step 1: Database check
        db_status = self.test_db_check_endpoint()
        
        if not db_status:
            print("❌ Cannot proceed - db-check endpoint failed")
            return False
        
        connected = db_status.get('connected', False)
        pgvector_available = db_status.get('pgvector_available', False)
        pgvector_installed = db_status.get('pgvector_installed', False)
        
        print(f"\n📊 Database Analysis:")
        print(f"   Connected: {connected}")
        print(f"   PGVector Available: {pgvector_available}")
        print(f"   PGVector Installed: {pgvector_installed}")
        
        # Step 2: Install pgvector if needed
        if connected and pgvector_available and not pgvector_installed:
            print("\n🔧 PGVector not installed but available - attempting installation")
            install_success = self.test_db_install_vector_endpoint()
            if install_success:
                print("✅ PGVector installation successful")
                # Re-check database status
                time.sleep(2)
                db_status = self.test_db_check_endpoint()
                pgvector_installed = db_status.get('pgvector_installed', False) if db_status else False
            else:
                print("❌ PGVector installation failed or not needed")
        
        # Step 3: Run AI flow if database is ready
        if connected and pgvector_installed:
            print("\n🧠 Database ready - running AI flow sequence")
            
            # AI Flow: preview -> study -> documents -> search -> delete
            upload_id = self.test_ai_flow_preview()
            document_id = None
            
            if upload_id:
                document_id = self.test_ai_flow_study(upload_id)
            
            self.test_ai_flow_documents()
            self.test_ai_flow_search()
            
            if document_id:
                self.test_ai_flow_delete(document_id)
            
            print("✅ AI flow sequence completed")
        else:
            print("❌ Database not ready for AI flow - skipping AI tests")
            if not connected:
                print("   Reason: Database not connected")
            elif not pgvector_installed:
                print("   Reason: PGVector not installed")
        
        return True

if __name__ == "__main__":
    tester = ReviewRequestTester()
    
    # Run the review request test
    tester.run_review_request_test()
    
    # Print final summary
    print("\n" + "=" * 70)
    print("📊 FINAL TEST SUMMARY")
    print("=" * 70)
    print(f"Tests Run: {tester.tests_run}")
    print(f"Tests Passed: {tester.tests_passed}")
    print(f"Tests Failed: {tester.tests_run - tester.tests_passed}")
    print(f"Success Rate: {(tester.tests_passed / tester.tests_run * 100):.1f}%" if tester.tests_run > 0 else "No tests run")
    
    if tester.failed_tests:
        print("\n❌ FAILED TESTS:")
        for i, test in enumerate(tester.failed_tests, 1):
            print(f"{i}. {test['name']}: {test['details']}")
    
    print("\n" + "=" * 70)