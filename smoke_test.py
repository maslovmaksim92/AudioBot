#!/usr/bin/env python3
"""
VasDom AudioBot Production Smoke Test
Quick smoke test on prod https://audiobot-qci2.onrender.com
"""

import requests
import sys
import json
import time
from datetime import datetime

class SmokeTest:
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
    
    def make_request(self, method: str, endpoint: str, data=None, params=None) -> tuple:
        """Make HTTP request and return (success, response_data, status_code)"""
        url = f"{self.base_url}{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=30)
            else:
                return False, {}, 0
                
            return True, response.json() if response.content else {}, response.status_code
            
        except requests.exceptions.Timeout:
            return False, {"error": "Request timeout"}, 0
        except requests.exceptions.ConnectionError:
            return False, {"error": "Connection error"}, 0
        except Exception as e:
            return False, {"error": str(e)}, 0
    
    def make_multipart_request(self, method: str, endpoint: str, files=None, data=None) -> tuple:
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

    def test_ai_knowledge_status(self):
        """Test 1: GET /api/ai-knowledge/status?upload_id=test_smoke"""
        print("\n🧪 Test 1: GET /api/ai-knowledge/status?upload_id=test_smoke")
        
        success, data, status = self.make_request('GET', '/api/ai-knowledge/status', params={'upload_id': 'test_smoke'})
        
        if status == 200:
            if 'status' in data:
                self.log_test("AI Knowledge Status - 200 Response", True, f"Status: {data['status']}")
                return True
            else:
                self.log_test("AI Knowledge Status - 200 Response", False, f"Missing 'status' field in response: {data}")
        elif status == 500:
            detail = data.get('detail', '')
            if 'Database is not initialized' in detail:
                self.log_test("AI Knowledge Status - 500 DB Not Initialized", True, f"Expected 500 (DB not initialized): {detail}")
                return True
            else:
                self.log_test("AI Knowledge Status - 500 Other Error", False, f"Unexpected 500 error: {detail}")
        elif status == 404:
            # This is the bad case - router missing
            self.log_test("AI Knowledge Status - 404 Router Missing", False, f"404 indicates router is missing - endpoints not deployed")
        else:
            self.log_test("AI Knowledge Status - Unexpected Status", False, f"Status: {status}, Data: {data}")
        
        return False

    def test_ai_knowledge_preview(self):
        """Test 2: POST /api/ai-knowledge/preview with multipart test.txt"""
        print("\n🧪 Test 2: POST /api/ai-knowledge/preview - multipart test.txt")
        
        # Create test.txt with "Hello AI"
        txt_content = "Hello AI"
        files = {'file': ('test.txt', txt_content.encode('utf-8'), 'text/plain')}
        data = {'chunk_tokens': 600, 'overlap': 100}
        
        success, response_data, status = self.make_multipart_request('POST', '/api/ai-knowledge/preview', files=files, data=data)
        
        if status == 200:
            if 'upload_id' in response_data:
                upload_id = response_data['upload_id']
                self.log_test("AI Knowledge Preview - 200 Response", True, f"upload_id: {upload_id[:8]}...")
                return upload_id
            else:
                self.log_test("AI Knowledge Preview - 200 Response", False, f"Missing 'upload_id' in response: {response_data}")
        elif status == 500:
            detail = response_data.get('detail', '')
            if 'Database is not initialized' in detail:
                self.log_test("AI Knowledge Preview - 500 DB Not Ready", True, f"Expected 500 (DB not ready): {detail}")
            else:
                self.log_test("AI Knowledge Preview - 500 Other Error", False, f"Unexpected 500 error: {detail}")
        elif status == 404:
            self.log_test("AI Knowledge Preview - 404 Router Missing", False, f"404 indicates router is missing - endpoints not deployed")
        else:
            self.log_test("AI Knowledge Preview - Unexpected Status", False, f"Status: {status}, Data: {response_data}")
        
        return None

    def test_ai_knowledge_study(self, upload_id):
        """Test 3: POST /api/ai-knowledge/study with upload_id + category=Клининг"""
        print(f"\n🧪 Test 3: POST /api/ai-knowledge/study with upload_id + category=Клининг")
        
        if not upload_id:
            self.log_test("AI Knowledge Study - No Upload ID", False, "No upload_id from preview test")
            return
        
        data = {
            'upload_id': upload_id,
            'category': 'Клининг'
        }
        
        success, response_data, status = self.make_multipart_request('POST', '/api/ai-knowledge/study', data=data)
        
        if status == 200:
            self.log_test("AI Knowledge Study - 200 Response", True, f"Study completed successfully")
        elif status == 500:
            detail = response_data.get('detail', '')
            if 'Database is not initialized' in detail:
                self.log_test("AI Knowledge Study - 500 DB Not Ready", True, f"Expected 500 (DB not ready): {detail}")
            else:
                self.log_test("AI Knowledge Study - 500 Other Error", False, f"Unexpected 500 error: {detail}")
        elif status == 404:
            self.log_test("AI Knowledge Study - 404 Router Missing", False, f"404 indicates router is missing - endpoints not deployed")
        else:
            self.log_test("AI Knowledge Study - Unexpected Status", False, f"Status: {status}, Data: {response_data}")

    def test_crm_cleaning_filters(self):
        """Test 4: Sanity check CRM still OK: GET /api/cleaning/filters should be 200"""
        print("\n🧪 Test 4: GET /api/cleaning/filters - CRM sanity check")
        
        success, data, status = self.make_request('GET', '/api/cleaning/filters')
        
        if status == 200:
            # Check basic structure
            if isinstance(data, dict) and 'brigades' in data and 'statuses' in data:
                brigades_count = len(data.get('brigades', []))
                statuses_count = len(data.get('statuses', []))
                self.log_test("CRM Cleaning Filters - 200 Response", True, 
                            f"brigades: {brigades_count}, statuses: {statuses_count}")
            else:
                self.log_test("CRM Cleaning Filters - 200 Response", False, f"Invalid response structure: {data}")
        else:
            self.log_test("CRM Cleaning Filters - Non-200 Response", False, f"Status: {status}, Data: {data}")

    def run_smoke_tests(self):
        """Run all smoke tests as per review request"""
        print("=" * 60)
        print("🚀 VasDom AudioBot Production Smoke Test")
        print(f"🎯 Target: {self.base_url}")
        print("📋 Testing: AI Knowledge endpoints + CRM sanity check")
        print("=" * 60)
        
        # Test 1: AI Knowledge Status
        self.test_ai_knowledge_status()
        
        # Test 2: AI Knowledge Preview
        upload_id = self.test_ai_knowledge_preview()
        
        # Test 3: AI Knowledge Study (if preview returned upload_id)
        if upload_id:
            self.test_ai_knowledge_study(upload_id)
        
        # Test 4: CRM Sanity Check
        self.test_crm_cleaning_filters()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 SMOKE TEST SUMMARY")
        print("=" * 60)
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {len(self.failed_tests)}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "0%")
        
        if self.failed_tests:
            print("\n❌ FAILED TESTS:")
            for i, test in enumerate(self.failed_tests, 1):
                print(f"{i}. {test['name']}")
                if test['details']:
                    print(f"   {test['details']}")
        
        print("\n" + "=" * 60)
        
        return self.tests_passed == self.tests_run

if __name__ == "__main__":
    tester = SmokeTest()
    success = tester.run_smoke_tests()
    sys.exit(0 if success else 1)