#!/usr/bin/env python3
"""
Review Request: Re-run diagnostics after scrubbing PGSSLMODE env.
Base: https://audiobot-qci2.onrender.com
1) GET /api/ai-knowledge/db-dsn — capture JSON including env_sslmode
2) GET /api/ai-knowledge/db-check — expect connected true now; else capture errors
If connected & installed, proceed to quick AI flow.
"""

import requests
import json
import sys
from typing import Dict, Any, Optional

class DiagnosticsTester:
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

    def mask_sensitive_url(self, url):
        """Mask sensitive parts of database URL for logging"""
        if not url or not isinstance(url, str):
            return url
        
        # Mask password in URL
        import re
        # Pattern to match postgresql://username:password@host:port/database
        pattern = r'(postgresql[^:]*://[^:]+:)([^@]+)(@.*)'
        masked = re.sub(pattern, r'\1***\3', url)
        return masked

    def test_db_dsn_endpoint(self):
        """Test GET /api/ai-knowledge/db-dsn endpoint - Review Request Step 1"""
        print("\n1️⃣ Testing GET /api/ai-knowledge/db-dsn")
        
        success, data, status = self.make_request('GET', '/api/ai-knowledge/db-dsn')
        
        if success and status == 200:
            # Check if response has expected DSN fields
            expected_fields = ['raw_present', 'raw_contains_sslmode', 'raw', 'normalized']
            missing_fields = [field for field in expected_fields if field not in data]
            
            if not missing_fields:
                raw_present = data.get('raw_present', False)
                raw_contains_sslmode = data.get('raw_contains_sslmode', False)
                raw = data.get('raw', '')
                normalized = data.get('normalized', '')
                
                # Log detailed DSN info (mask sensitive parts)
                raw_masked = self.mask_sensitive_url(raw) if raw else 'N/A'
                normalized_masked = self.mask_sensitive_url(normalized) if normalized else 'N/A'
                
                dsn_info = f"raw_present={raw_present}, raw_contains_sslmode={raw_contains_sslmode}"
                self.log_test("DB DSN - Endpoint Response", True, dsn_info)
                
                print(f"   📋 DSN Analysis:")
                print(f"      Raw URL Present: {raw_present}")
                print(f"      Raw Contains sslmode: {raw_contains_sslmode}")
                print(f"      Raw URL: {raw_masked}")
                print(f"      Normalized URL: {normalized_masked}")
                
                # Check for env_sslmode field as requested
                if 'env_sslmode' in data:
                    print(f"      Env sslmode: {data['env_sslmode']}")
                
                return data
            else:
                self.log_test("DB DSN - Endpoint Response", False, f"Missing DSN fields: {missing_fields}")
        elif status == 404:
            self.log_test("DB DSN - Endpoint Exists", False, "db-dsn endpoint not found (404) - not deployed")
        elif status == 500:
            detail = data.get('detail', '')
            self.log_test("DB DSN - Endpoint Response", False, f"500 error: {detail}")
        else:
            self.log_test("DB DSN - Endpoint Response", False, f"Status: {status}, Data: {data}")
        
        return None

    def test_db_check_endpoint(self):
        """Test GET /api/ai-knowledge/db-check endpoint - Review Request Step 2"""
        print("\n2️⃣ Testing GET /api/ai-knowledge/db-check")
        
        success, data, status = self.make_request('GET', '/api/ai-knowledge/db-check')
        
        if success and status == 200:
            # Check if response has expected fields
            expected_fields = ['connected', 'pgvector_available', 'pgvector_installed']
            missing_fields = [field for field in expected_fields if field not in data]
            
            if not missing_fields:
                connected = data.get('connected', False)
                pgvector_available = data.get('pgvector_available', False)
                pgvector_installed = data.get('pgvector_installed', False)
                errors = data.get('errors', [])
                ai_tables = data.get('ai_tables', {})
                embedding_dims = data.get('embedding_dims', 0)
                
                db_info = f"connected={connected}, pgvector_available={pgvector_available}, pgvector_installed={pgvector_installed}"
                self.log_test("DB Check - Endpoint Response", True, db_info)
                
                print(f"   📊 Database Status:")
                print(f"      Connected: {connected}")
                print(f"      PGVector Available: {pgvector_available}")
                print(f"      PGVector Installed: {pgvector_installed}")
                print(f"      AI Tables: {ai_tables}")
                print(f"      Embedding Dimensions: {embedding_dims}")
                print(f"      Errors: {len(errors)} found")
                
                if errors:
                    print("   📋 Error Details:")
                    for i, error in enumerate(errors[:5], 1):  # Show first 5 errors
                        print(f"      {i}. {error}")
                
                return data
            else:
                self.log_test("DB Check - Endpoint Response", False, f"Missing fields: {missing_fields}")
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
        print("\n3️⃣ Testing POST /api/ai-knowledge/db-install-vector")
        
        success, data, status = self.make_request('POST', '/api/ai-knowledge/db-install-vector', {})
        
        if success and status == 200:
            self.log_test("DB Install Vector - Success", True, f"pgvector installation successful")
            return True
        elif status == 422:
            # Validation error is expected if no body provided
            self.log_test("DB Install Vector - Validation", True, f"Validation error (expected): {data.get('detail', '')}")
            return False
        elif status == 404:
            self.log_test("DB Install Vector - Endpoint Exists", False, "db-install-vector endpoint not found (404)")
            return False
        elif status == 500:
            detail = data.get('detail', '')
            self.log_test("DB Install Vector - Error", False, f"500 error: {detail}")
            return False
        else:
            self.log_test("DB Install Vector - Response", False, f"Status: {status}, Data: {data}")
            return False

    def test_quick_ai_flow(self):
        """Test quick AI flow: upload → save → search → delete"""
        print("\n🧠 QUICK AI FLOW TESTING")
        print("-" * 40)
        
        # Step 1: Upload a simple document
        txt_content = """VasDom AudioBot Test Document
        
This is a test document for the AI knowledge system.
The system manages cleaning operations for residential buildings.
Key features include:
- House management
- Brigade scheduling  
- Quality control
- Bitrix24 integration
"""
        
        files = {'files': ('ai_flow_test.txt', txt_content.encode('utf-8'), 'text/plain')}
        data = {'chunk_tokens': '600', 'overlap': '100'}
        
        print("   📤 Uploading test document...")
        success, upload_data, status = self.make_multipart_request('POST', '/api/ai-knowledge/upload', files=files, data=data)
        
        if success and status == 200 and 'upload_id' in upload_data:
            upload_id = upload_data['upload_id']
            chunks = upload_data.get('chunks', 0)
            print(f"   ✅ Upload successful: {chunks} chunks, upload_id: {upload_id[:8]}...")
            
            # Step 2: Save the document
            print("   💾 Saving document...")
            save_data = {'upload_id': upload_id, 'filename': 'ai_flow_test.txt'}
            success, save_response, status = self.make_multipart_request('POST', '/api/ai-knowledge/save', data=save_data)
            
            if success and status == 200 and 'document_id' in save_response:
                document_id = save_response['document_id']
                print(f"   ✅ Save successful: document_id: {document_id[:8]}...")
                
                # Step 3: Search for content
                print("   🔍 Searching for content...")
                search_data = {'query': 'VasDom cleaning', 'top_k': 5}
                success, search_response, status = self.make_request('POST', '/api/ai-knowledge/search', search_data)
                
                if success and status == 200 and 'results' in search_response:
                    results = search_response['results']
                    print(f"   ✅ Search successful: {len(results)} results found")
                    
                    # Step 4: Delete the document
                    print("   🗑️  Deleting test document...")
                    success, delete_response, status = self.make_request('DELETE', f'/api/ai-knowledge/document/{document_id}')
                    
                    if success and status == 200 and delete_response.get('ok'):
                        print("   ✅ Delete successful")
                        self.log_test("Quick AI Flow - Complete", True, 
                                    f"Full AI flow completed: upload → save → search ({len(results)} results) → delete")
                        return True
                    else:
                        print(f"   ❌ Delete failed: Status {status}")
                        self.log_test("Quick AI Flow - Delete", False, f"Delete failed: {status}")
                else:
                    print(f"   ❌ Search failed: Status {status}")
                    self.log_test("Quick AI Flow - Search", False, f"Search failed: {status}")
            else:
                print(f"   ❌ Save failed: Status {status}")
                self.log_test("Quick AI Flow - Save", False, f"Save failed: {status}")
        else:
            print(f"   ❌ Upload failed: Status {status}")
            self.log_test("Quick AI Flow - Upload", False, f"Upload failed: {status}")
        
        return False

    def run_review_request_diagnostics(self):
        """
        Review Request: Re-run diagnostics after scrubbing PGSSLMODE env.
        """
        print("\n🔍 REVIEW REQUEST: DIAGNOSTICS AFTER SCRUBBING PGSSLMODE ENV")
        print("=" * 70)
        print(f"Base URL: {self.base_url}")
        print("Testing diagnostics after PGSSLMODE environment variable scrubbing")
        print("-" * 70)
        
        # Step 1: GET /api/ai-knowledge/db-dsn — capture JSON including env_sslmode
        dsn_data = self.test_db_dsn_endpoint()
        
        # Step 2: GET /api/ai-knowledge/db-check — expect connected true now; else capture errors
        db_status = self.test_db_check_endpoint()
        
        if db_status:
            connected = db_status.get('connected', False)
            pgvector_available = db_status.get('pgvector_available', False)
            pgvector_installed = db_status.get('pgvector_installed', False)
            errors = db_status.get('errors', [])
            
            print(f"\n📊 Database Connection Analysis:")
            print(f"   Connected: {connected}")
            print(f"   PGVector Available: {pgvector_available}")
            print(f"   PGVector Installed: {pgvector_installed}")
            print(f"   Errors: {len(errors)} found")
            
            if errors:
                print("   Error Details:")
                for i, error in enumerate(errors[:3], 1):  # Show first 3 errors
                    print(f"      {i}. {error}")
            
            if connected and pgvector_available and pgvector_installed:
                print("\n✅ Database fully connected and configured!")
                print("3️⃣ Step 3: Proceeding to quick AI flow testing...")
                self.test_quick_ai_flow()
            elif connected and pgvector_available and not pgvector_installed:
                print("\n🔧 Database connected but pgvector not installed")
                print("3️⃣ Step 3: Installing pgvector extension...")
                install_result = self.test_db_install_vector_endpoint()
                if install_result:
                    print("4️⃣ Step 4: Re-checking database status...")
                    updated_status = self.test_db_check_endpoint()
                    if updated_status and updated_status.get('pgvector_installed'):
                        print("5️⃣ Step 5: Proceeding to quick AI flow testing...")
                        self.test_quick_ai_flow()
            elif not connected:
                print("\n❌ Database still not connected after PGSSLMODE scrubbing")
                if errors:
                    print("   Root cause analysis:")
                    for error in errors:
                        if 'sslmode' in error.lower():
                            print(f"   🔍 SSL Mode Issue: {error}")
                        elif 'connection' in error.lower():
                            print(f"   🔍 Connection Issue: {error}")
                        elif 'authentication' in error.lower():
                            print(f"   🔍 Auth Issue: {error}")
                self.log_test("Review Request - Database Connection", False, 
                            f"Database not connected. Errors: {len(errors)}")
            else:
                print(f"\n❓ Unexpected database state")
                self.log_test("Review Request - Database State", False, 
                            f"Unexpected: connected={connected}, available={pgvector_available}, installed={pgvector_installed}")
        else:
            print("\n❌ Could not retrieve database status")
            self.log_test("Review Request - DB Check", False, "Failed to get database status")
        
        return True

if __name__ == "__main__":
    tester = DiagnosticsTester()
    
    print("🚀 VasDom AudioBot Backend Testing - REVIEW REQUEST: Diagnostics after scrubbing PGSSLMODE env")
    print("=" * 70)
    print(f"Testing deployed backend: {tester.base_url}")
    print("Goal: Test db-dsn → db-check → AI flow sequence")
    print("=" * 70)
    
    # Run the focused review request test
    tester.run_review_request_diagnostics()
    
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
    
    # Exit with appropriate code
    sys.exit(0 if tester.tests_passed == tester.tests_run else 1)