#!/usr/bin/env python3
"""
VasDom AudioBot Backend API Testing - Review Request
Quick re-check after adding psycopg2-binary
"""

import requests
import sys
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional

class VasDomAPITester:
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

    def test_review_request_psycopg2_binary(self):
        """Test review request: Quick re-check after adding psycopg2-binary"""
        print("\n🔍 REVIEW REQUEST: Quick re-check after adding psycopg2-binary")
        print("=" * 70)
        print(f"Base URL: {self.base_url}")
        print("Testing sequence: db-check → install (if needed) → AI flow")
        print("-" * 70)
        
        # Step 1: GET /api/ai-knowledge/db-check — expect connected true now
        print("\n1️⃣ Step 1: Database Connection Check")
        db_status = self.test_db_check_endpoint()
        
        if not db_status:
            print("❌ Cannot proceed - db-check endpoint failed")
            return False
        
        connected = db_status.get('connected', False)
        pgvector_installed = db_status.get('pgvector_installed', False)
        errors = db_status.get('errors', [])
        
        # Step 2: If connected and pgvector not installed, POST install and re-check
        if connected and not pgvector_installed:
            print("\n2️⃣ Step 2: Installing PGVector Extension")
            install_success = self.test_db_install_vector()
            
            if install_success:
                print("\n2️⃣b Step 2b: Re-checking after installation")
                db_status_after = self.test_db_check_endpoint()
                if db_status_after and db_status_after.get('pgvector_installed', False):
                    print("✅ PGVector installation successful")
                    pgvector_installed = True
                else:
                    print("❌ PGVector installation may have failed")
        elif connected and pgvector_installed:
            print("\n✅ Step 2: PGVector already installed, skipping installation")
        elif not connected:
            print(f"\n❌ Step 2: Cannot install PGVector - database not connected")
            if errors:
                print(f"   Database errors: {errors}")
            return False
        
        # Step 3: If ready, run quick AI flow preview->study->documents->search->delete
        if connected and pgvector_installed:
            print("\n3️⃣ Step 3: Quick AI Flow Test")
            self.test_ai_flow_sequence()
        else:
            print(f"\n❌ Step 3: Cannot test AI flow - prerequisites not met (connected={connected}, pgvector={pgvector_installed})")
        
        return True
    
    def test_db_check_endpoint(self):
        """Test GET /api/ai-knowledge/db-check endpoint"""
        success, data, status = self.make_request('GET', '/api/ai-knowledge/db-check')
        
        if success and status == 200:
            connected = data.get('connected', False)
            pgvector_available = data.get('pgvector_available', False)
            pgvector_installed = data.get('pgvector_installed', False)
            errors = data.get('errors', [])
            
            status_msg = f"connected={connected}, pgvector_available={pgvector_available}, pgvector_installed={pgvector_installed}"
            if errors:
                status_msg += f", errors={len(errors)}"
            
            self.log_test("DB Check - Connection Status", connected, status_msg)
            
            if errors:
                print(f"   ⚠️  Database errors detected:")
                for error in errors[:3]:  # Show first 3 errors
                    print(f"      - {error}")
            
            return data
        else:
            self.log_test("DB Check - Endpoint", False, f"Status: {status}, Data: {data}")
            return None
    
    def test_db_install_vector(self):
        """Test POST /api/ai-knowledge/db-install-vector endpoint"""
        success, data, status = self.make_request('POST', '/api/ai-knowledge/db-install-vector', {})
        
        if success and status == 200:
            result = data.get('result', '')
            self.log_test("DB Install Vector - Success", True, f"Result: {result}")
            return True
        elif status == 422:
            # Validation error is expected if no body provided, try with proper body
            install_data = {"confirm": True}
            success, data, status = self.make_request('POST', '/api/ai-knowledge/db-install-vector', install_data)
            if success and status == 200:
                result = data.get('result', '')
                self.log_test("DB Install Vector - Success", True, f"Result: {result}")
                return True
            else:
                self.log_test("DB Install Vector - After Retry", False, f"Status: {status}, Data: {data}")
        else:
            self.log_test("DB Install Vector - Failed", False, f"Status: {status}, Data: {data}")
        
        return False
    
    def test_ai_flow_sequence(self):
        """Test quick AI flow: preview->study->documents->search->delete"""
        print("   🔄 Testing AI Flow Sequence...")
        
        # Step 1: Preview (upload)
        txt_content = "Test document for VasDom AudioBot AI system. This contains information about cleaning schedules and brigade management."
        files = {'files': ('test_flow.txt', txt_content.encode('utf-8'), 'text/plain')}
        
        success, data, status = self.make_multipart_request('POST', '/api/ai-knowledge/preview', files=files)
        
        if not (success and status == 200 and 'upload_id' in data):
            self.log_test("AI Flow - Preview", False, f"Preview failed: Status {status}")
            return False
        
        upload_id = data['upload_id']
        self.log_test("AI Flow - Preview", True, f"Upload ID: {upload_id[:8]}...")
        
        # Step 2: Study (save)
        study_data = {
            'upload_id': upload_id,
            'filename': 'test_flow_document.txt',
            'category': 'Testing'
        }
        
        success, data, status = self.make_multipart_request('POST', '/api/ai-knowledge/study', data=study_data)
        
        if not (success and status == 200 and 'document_id' in data):
            self.log_test("AI Flow - Study", False, f"Study failed: Status {status}")
            return False
        
        document_id = data['document_id']
        self.log_test("AI Flow - Study", True, f"Document ID: {document_id[:8]}...")
        
        # Step 3: Documents (list)
        success, data, status = self.make_request('GET', '/api/ai-knowledge/documents')
        
        if success and status == 200 and 'documents' in data:
            docs_count = len(data['documents'])
            self.log_test("AI Flow - Documents", True, f"Found {docs_count} documents")
        else:
            self.log_test("AI Flow - Documents", False, f"Documents list failed: Status {status}")
        
        # Step 4: Search
        search_data = {'query': 'VasDom', 'top_k': 5}
        success, data, status = self.make_request('POST', '/api/ai-knowledge/search', search_data)
        
        if success and status == 200 and 'results' in data:
            results_count = len(data['results'])
            self.log_test("AI Flow - Search", True, f"Found {results_count} search results")
        else:
            self.log_test("AI Flow - Search", False, f"Search failed: Status {status}")
        
        # Step 5: Delete
        success, data, status = self.make_request('DELETE', f'/api/ai-knowledge/document/{document_id}')
        
        if success and status == 200 and data.get('ok'):
            self.log_test("AI Flow - Delete", True, f"Document deleted successfully")
        else:
            self.log_test("AI Flow - Delete", False, f"Delete failed: Status {status}")
        
        return True

    def print_final_summary(self):
        """Print final test summary"""
        print("\n" + "=" * 70)
        print("📊 FINAL TEST SUMMARY")
        print("=" * 70)
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed / self.tests_run * 100):.1f}%" if self.tests_run > 0 else "No tests run")
        
        if self.failed_tests:
            print("\n❌ FAILED TESTS:")
            for i, test in enumerate(self.failed_tests, 1):
                print(f"{i}. {test['name']}: {test['details']}")
        else:
            print("\n✅ ALL TESTS PASSED!")

if __name__ == "__main__":
    tester = VasDomAPITester()
    
    print("🚀 VasDom AudioBot Backend Testing - REVIEW REQUEST: psycopg2-binary re-check")
    print("=" * 70)
    print(f"Testing deployed backend: {tester.base_url}")
    print("Goal: Test db-check → install (if needed) → AI flow sequence")
    print("=" * 70)
    
    # Run the focused review request test
    tester.test_review_request_psycopg2_binary()
    
    # Print final summary
    tester.print_final_summary()
    
    # Exit with appropriate code
    sys.exit(0 if tester.tests_passed == tester.tests_run else 1)