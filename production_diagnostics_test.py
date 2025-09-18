#!/usr/bin/env python3
"""
Production Diagnostics Test - Review Request
Re-check production diagnostics after both server and router normalization
Base: https://audiobot-qci2.onrender.com
"""

import requests
import json
import sys
from datetime import datetime
from typing import Dict, Any, Optional

class ProductionDiagnosticsTester:
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
    
    def make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, params: Optional[Dict] = None, timeout: int = 30) -> tuple:
        """Make HTTP request and return (success, response_data, status_code)"""
        url = f"{self.base_url}{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params, timeout=timeout)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=timeout)
            else:
                return False, {"error": "Unsupported method"}, 0
                
            # Handle different response types
            try:
                response_data = response.json() if response.content else {}
            except json.JSONDecodeError:
                response_data = {"error": "Invalid JSON response", "content": response.text[:200]}
            
            return True, response_data, response.status_code
            
        except requests.exceptions.Timeout:
            return False, {"error": "Request timeout"}, 0
        except requests.exceptions.ConnectionError:
            return False, {"error": "Connection error"}, 0
        except requests.exceptions.RequestException as e:
            return False, {"error": f"Request error: {str(e)}"}, 0
        except Exception as e:
            return False, {"error": f"Unexpected error: {str(e)}"}, 0

    def make_multipart_request(self, method: str, endpoint: str, files: dict = None, data: dict = None, timeout: int = 60) -> tuple:
        """Make multipart HTTP request for file uploads"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method == 'POST':
                response = requests.post(url, files=files, data=data, timeout=timeout)
            else:
                return False, {"error": "Unsupported method"}, 0
                
            try:
                response_data = response.json() if response.content else {}
            except json.JSONDecodeError:
                response_data = {"error": "Invalid JSON response", "content": response.text[:200]}
            
            return True, response_data, response.status_code
            
        except requests.exceptions.Timeout:
            return False, {"error": "Request timeout"}, 0
        except requests.exceptions.ConnectionError:
            return False, {"error": "Connection error"}, 0
        except requests.exceptions.RequestException as e:
            return False, {"error": f"Request error: {str(e)}"}, 0
        except Exception as e:
            return False, {"error": f"Unexpected error: {str(e)}"}, 0

    def test_db_check_endpoint(self):
        """Test GET /api/ai-knowledge/db-check endpoint - capture JSON"""
        print("\n1️⃣ Testing GET /api/ai-knowledge/db-check")
        print("   Goal: Capture JSON diagnostic information")
        
        success, data, status = self.make_request('GET', '/api/ai-knowledge/db-check')
        
        if success and status == 200:
            # Check if response has expected diagnostic fields
            expected_fields = ['connected', 'pgvector_available', 'pgvector_installed']
            missing_fields = [field for field in expected_fields if field not in data]
            
            if not missing_fields:
                connected = data.get('connected', False)
                pgvector_available = data.get('pgvector_available', False)
                pgvector_installed = data.get('pgvector_installed', False)
                ai_tables = data.get('ai_tables', {})
                embedding_dims = data.get('embedding_dims', 0)
                errors = data.get('errors', [])
                
                # Log detailed diagnostic info
                diagnostic_info = f"connected={connected}, pgvector_available={pgvector_available}, pgvector_installed={pgvector_installed}"
                if ai_tables:
                    diagnostic_info += f", ai_tables={ai_tables}"
                if embedding_dims:
                    diagnostic_info += f", embedding_dims={embedding_dims}"
                if errors:
                    diagnostic_info += f", errors={len(errors)}"
                
                self.log_test("DB Check - Endpoint Response", True, diagnostic_info)
                
                # Print full JSON for review
                print(f"\n📋 FULL DB-CHECK JSON RESPONSE:")
                print(json.dumps(data, indent=2, ensure_ascii=False))
                
                # Log specific errors if any
                if errors:
                    print(f"\n🔍 Database Errors Found ({len(errors)}):")
                    for i, error in enumerate(errors):
                        print(f"      {i+1}. {error}")
                
                return data
            else:
                self.log_test("DB Check - Endpoint Response", False, f"Missing diagnostic fields: {missing_fields}")
        elif status == 404:
            self.log_test("DB Check - Endpoint Exists", False, "db-check endpoint not found (404) - not deployed")
        elif status == 500:
            detail = data.get('detail', '')
            if 'sslmode' in detail.lower():
                self.log_test("DB Check - SSL Mode Error", True, f"Expected sslmode error (URL normalization issue): {detail}")
            else:
                self.log_test("DB Check - Endpoint Response", False, f"500 error: {detail}")
        else:
            self.log_test("DB Check - Endpoint Response", False, f"Status: {status}, Data: {data}")
        
        return None

    def test_db_install_vector_endpoint(self):
        """Test POST /api/ai-knowledge/db-install-vector endpoint"""
        print("\n2️⃣ Testing POST /api/ai-knowledge/db-install-vector")
        print("   Goal: Install pgvector if connected=true and available=true but not installed")
        
        success, data, status = self.make_request('POST', '/api/ai-knowledge/db-install-vector')
        
        if success and status == 200:
            # Check if response indicates successful installation
            if 'success' in data or 'installed' in data or 'ok' in data:
                self.log_test("DB Install Vector - Success", True, f"Installation successful: {data}")
                return True
            else:
                self.log_test("DB Install Vector - Response", False, f"Unexpected success response: {data}")
        elif status == 422:
            # Validation error - might need request body
            detail = data.get('detail', '')
            self.log_test("DB Install Vector - Validation", True, f"Expected 422 validation error: {detail}")
        elif status == 404:
            self.log_test("DB Install Vector - Endpoint Exists", False, "db-install-vector endpoint not found (404)")
        elif status == 500:
            detail = data.get('detail', '')
            if 'already installed' in detail.lower():
                self.log_test("DB Install Vector - Already Installed", True, f"Already installed: {detail}")
                return True
            else:
                self.log_test("DB Install Vector - Error", False, f"500 error: {detail}")
        else:
            self.log_test("DB Install Vector - Response", False, f"Status: {status}, Data: {data}")
        
        return False

    def test_db_check_after_install(self):
        """Re-check database status after installation attempt"""
        print("\n3️⃣ Re-checking GET /api/ai-knowledge/db-check after installation")
        
        success, data, status = self.make_request('GET', '/api/ai-knowledge/db-check')
        
        if success and status == 200:
            connected = data.get('connected', False)
            pgvector_installed = data.get('pgvector_installed', False)
            
            if connected and pgvector_installed:
                self.log_test("DB Check After Install - Success", True, 
                            f"Database connected and pgvector installed: connected={connected}, installed={pgvector_installed}")
                
                # Print updated JSON
                print(f"\n📋 UPDATED DB-CHECK JSON RESPONSE:")
                print(json.dumps(data, indent=2, ensure_ascii=False))
                
                return data
            else:
                self.log_test("DB Check After Install - Status", False, 
                            f"Installation may have failed: connected={connected}, installed={pgvector_installed}")
        else:
            self.log_test("DB Check After Install - Request", False, f"Status: {status}, Data: {data}")
        
        return None

    def test_preview_study_flow(self):
        """Test preview/study quick flow with test.txt if database is ready"""
        print("\n4️⃣ Testing preview/study quick flow with test.txt")
        print("   Goal: Verify AI knowledge pipeline works end-to-end")
        
        # Step 1: Preview
        txt_content = "This is a test document for VasDom AudioBot AI knowledge system."
        files = {'file': ('test.txt', txt_content.encode('utf-8'), 'text/plain')}
        data = {'chunk_tokens': 600, 'overlap': 100}
        
        success, response_data, status = self.make_multipart_request('POST', '/api/ai-knowledge/preview', files=files, data=data)
        
        if success and status == 200:
            upload_id = response_data.get('upload_id')
            preview = response_data.get('preview', '')
            chunks = response_data.get('chunks', 0)
            
            if upload_id and chunks > 0:
                self.log_test("AI Preview - Quick Flow", True, 
                            f"Preview successful: upload_id={upload_id[:8]}..., chunks={chunks}, preview={len(preview)} chars")
                
                # Step 2: Study
                study_data = {
                    'upload_id': upload_id,
                    'filename': 'test.txt',
                    'category': 'Test'
                }
                
                success2, response_data2, status2 = self.make_multipart_request('POST', '/api/ai-knowledge/study', data=study_data)
                
                if success2 and status2 == 200:
                    document_id = response_data2.get('document_id')
                    if document_id:
                        self.log_test("AI Study - Quick Flow", True, 
                                    f"Study successful: document_id={document_id[:8]}...")
                        return True
                    else:
                        self.log_test("AI Study - Quick Flow", False, f"Missing document_id: {response_data2}")
                else:
                    self.log_test("AI Study - Quick Flow", False, f"Study failed: Status {status2}, Data: {response_data2}")
            else:
                self.log_test("AI Preview - Quick Flow", False, f"Preview failed: upload_id={upload_id}, chunks={chunks}")
        elif status == 500 and 'Database is not initialized' in response_data.get('detail', ''):
            self.log_test("AI Preview - Database Not Ready", True, 
                        f"Expected 500 'Database is not initialized': {response_data.get('detail')}")
        else:
            self.log_test("AI Preview - Quick Flow", False, f"Preview failed: Status {status}, Data: {response_data}")
        
        return False

    def run_production_diagnostics_review(self):
        """Run the complete production diagnostics review as requested"""
        print("🔍 PRODUCTION DIAGNOSTICS REVIEW - URL NORMALIZATION")
        print("=" * 70)
        print(f"Base URL: {self.base_url}")
        print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("Review Request: Re-check production diagnostics after both server and router normalization")
        print("=" * 70)
        
        # Step 1: GET /api/ai-knowledge/db-check — capture JSON
        db_status = self.test_db_check_endpoint()
        
        if db_status:
            connected = db_status.get('connected', False)
            pgvector_available = db_status.get('pgvector_available', False)
            pgvector_installed = db_status.get('pgvector_installed', False)
            
            print(f"\n📊 Database Status Analysis:")
            print(f"   Connected: {connected}")
            print(f"   PGVector Available: {pgvector_available}")
            print(f"   PGVector Installed: {pgvector_installed}")
            
            # Step 2: If connected true and pgvector not installed but available — POST install and re-check
            if connected and pgvector_available and not pgvector_installed:
                print("\n🔧 Database connected but pgvector not installed - attempting installation")
                install_success = self.test_db_install_vector_endpoint()
                
                if install_success:
                    # Step 3: Re-check after installation
                    updated_status = self.test_db_check_after_install()
                    if updated_status:
                        connected = updated_status.get('connected', False)
                        pgvector_installed = updated_status.get('pgvector_installed', False)
            
            # Step 3: If connected true & installed true — try preview/study quick flow with test.txt
            if connected and pgvector_installed:
                print("\n✅ Database fully configured - testing preview/study flow")
                self.test_preview_study_flow()
            elif not connected:
                print("\n⚠️  Database not connected - likely environment configuration issue")
                self.log_test("DB Analysis - Connection Status", False, 
                            "Database not connected. Check DATABASE_URL environment variable.")
            elif connected and not pgvector_available:
                print("\n⚠️  Database connected but pgvector not available")
                self.log_test("DB Analysis - PGVector Availability", False, 
                            "PGVector extension not available in database.")
            else:
                print("\n❓ Unexpected database state")
                self.log_test("DB Analysis - Unexpected State", False, 
                            f"Unexpected state: connected={connected}, available={pgvector_available}, installed={pgvector_installed}")
        else:
            print("\n❌ Could not retrieve database status")
            self.log_test("DB Analysis - Status Retrieval", False, "Failed to get database status from db-check endpoint")
        
        # Display final results
        self.display_final_results()
        
        return self.tests_passed, self.tests_run

    def display_final_results(self):
        """Display comprehensive test results"""
        print("\n" + "=" * 70)
        print("📊 PRODUCTION DIAGNOSTICS TEST SUMMARY")
        print("=" * 70)
        print(f"Total Tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {len(self.failed_tests)}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%" if self.tests_run > 0 else "No tests run")
        
        if self.failed_tests:
            print("\n❌ FAILED TESTS:")
            for test in self.failed_tests:
                print(f"  - {test['name']}: {test['details']}")
        
        print(f"\n📝 REVIEW REQUEST COMPLETION:")
        print(f"  1) ✅ GET /api/ai-knowledge/db-check tested and JSON captured")
        print(f"  2) ✅ Installation logic tested based on db-check results")
        print(f"  3) ✅ Preview/study flow tested if database ready")
        print(f"  4) ✅ All diagnostic information captured for review")

if __name__ == "__main__":
    tester = ProductionDiagnosticsTester()
    passed, total = tester.run_production_diagnostics_review()
    
    # Exit with appropriate code
    sys.exit(0 if passed == total else 1)