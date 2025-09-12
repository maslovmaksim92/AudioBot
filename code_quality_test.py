#!/usr/bin/env python3
"""
Code Quality Fixes Testing - Focused on specific fixes mentioned in review
"""

import requests
import json
import sys
import time
from datetime import datetime

class CodeQualityTester:
    def __init__(self, base_url="https://vasdom-clean.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []

    def log_test(self, name, success, details=""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED")
        else:
            self.failed_tests.append({"name": name, "details": details})
            print(f"❌ {name} - FAILED: {details}")

    def test_x_api_key_header_validation(self):
        """Test X-API-Key header validation fix in security.py"""
        try:
            print("🔑 Testing X-API-Key Header Validation Fix...")
            
            # Test 1: Normal request without auth (should work with optional_auth)
            response1 = requests.post(f"{self.api_url}/voice/process", 
                                    json={"text": "Test message", "user_id": "test"}, 
                                    timeout=15)
            
            print(f"   📝 Request without auth: {response1.status_code}")
            
            # Test 2: Request with X-API-Key header (should be handled properly)
            headers = {"X-API-Key": "test-key-value"}
            response2 = requests.post(f"{self.api_url}/voice/process", 
                                    json={"text": "Test message", "user_id": "test"}, 
                                    headers=headers,
                                    timeout=15)
            
            print(f"   🔑 Request with X-API-Key: {response2.status_code}")
            
            # Test 3: Request with Bearer token
            headers_bearer = {"Authorization": "Bearer test-token"}
            response3 = requests.post(f"{self.api_url}/voice/process", 
                                    json={"text": "Test message", "user_id": "test"}, 
                                    headers=headers_bearer,
                                    timeout=15)
            
            print(f"   🔐 Request with Bearer token: {response3.status_code}")
            
            # Success criteria: All requests should be handled without crashing
            # (either 200 for success or 401 for auth failure, not 500 for crash)
            success = all(code in [200, 401, 422] for code in [response1.status_code, response2.status_code, response3.status_code])
            
            if success:
                print("   ✅ X-API-Key header validation working properly - no crashes")
            else:
                print("   ❌ X-API-Key header validation causing issues")
            
            self.log_test("X-API-Key Header Validation Fix", success, 
                         f"No auth: {response1.status_code}, X-API-Key: {response2.status_code}, Bearer: {response3.status_code}")
            return success
        except Exception as e:
            self.log_test("X-API-Key Header Validation Fix", False, str(e))
            return False

    def test_voice_api_exception_handling(self):
        """Test Voice API exception handling - should return HTTP 500 on errors, not HTTP 200"""
        try:
            print("🎤 Testing Voice API Exception Handling Fix...")
            
            # Test 1: Invalid JSON structure (should return 422 validation error)
            response1 = requests.post(f"{self.api_url}/voice/process", 
                                    json={"invalid_field": "test"}, 
                                    timeout=15)
            
            print(f"   📝 Invalid JSON structure: {response1.status_code}")
            
            # Test 2: Valid structure but potentially error-inducing content
            # This might cause processing errors that should return 500, not 200
            error_data = {
                "text": "🔥" * 500 + "CAUSE_ERROR_TEST",  # Very long text
                "user_id": "error_test_user"
            }
            
            response2 = requests.post(f"{self.api_url}/voice/process", 
                                    json=error_data, 
                                    timeout=20)
            
            print(f"   🔥 Error-inducing content: {response2.status_code}")
            
            # Test 3: Normal valid request (should work)
            normal_data = {
                "text": "Привет, как дела?",
                "user_id": "normal_test"
            }
            
            response3 = requests.post(f"{self.api_url}/voice/process", 
                                    json=normal_data, 
                                    timeout=15)
            
            print(f"   ✅ Normal request: {response3.status_code}")
            
            # Success criteria:
            # 1. Invalid JSON should return 422 (validation error)
            # 2. Processing errors should return 500 (not 200 with masked error)
            # 3. Normal requests should return 200
            
            validation_ok = response1.status_code == 422
            error_handling_ok = response2.status_code in [200, 500]  # Either processes or fails properly
            normal_ok = response3.status_code == 200
            
            # Check if error response is properly formatted (not 200 with hidden error)
            if response2.status_code == 200:
                try:
                    data = response2.json()
                    # If it returns 200, it should have a proper response, not an error message
                    has_proper_response = "response" in data and len(data.get("response", "")) > 0
                    if not has_proper_response:
                        print("   ❌ Returns HTTP 200 but with empty/error response - should be HTTP 500")
                        error_handling_ok = False
                    else:
                        print("   ✅ Processes long text successfully")
                except:
                    print("   ❌ Returns HTTP 200 but invalid JSON - should be HTTP 500")
                    error_handling_ok = False
            elif response2.status_code == 500:
                print("   ✅ Processing error correctly returns HTTP 500 (not masked as 200)")
            
            success = validation_ok and error_handling_ok and normal_ok
            
            if success:
                print("   ✅ Voice API exception handling working correctly")
            else:
                print("   ❌ Voice API exception handling has issues")
            
            self.log_test("Voice API Exception Handling (HTTP 500 fix)", success, 
                         f"Validation: {response1.status_code}, Error: {response2.status_code}, Normal: {response3.status_code}")
            return success
        except Exception as e:
            self.log_test("Voice API Exception Handling (HTTP 500 fix)", False, str(e))
            return False

    def test_database_style_improvements(self):
        """Test that database.py style improvements don't break functionality"""
        try:
            print("🗄️ Testing Database.py Style Improvements...")
            
            # Test that health endpoint still works (uses database config)
            response1 = requests.get(f"{self.api_url}/health", timeout=10)
            print(f"   🏥 Health endpoint: {response1.status_code}")
            
            if response1.status_code == 200:
                data = response1.json()
                has_db_info = any(key in data for key in ["database", "service", "status"])
                print(f"   📊 Database info present: {'✅' if has_db_info else '❌'}")
            
            # Test that dashboard still works (uses database for stats)
            response2 = requests.get(f"{self.api_url}/dashboard", timeout=15)
            print(f"   📊 Dashboard endpoint: {response2.status_code}")
            
            if response2.status_code == 200:
                data = response2.json()
                has_stats = "stats" in data and isinstance(data["stats"], dict)
                print(f"   📈 Statistics present: {'✅' if has_stats else '❌'}")
            
            success = response1.status_code == 200 and response2.status_code == 200
            
            if success:
                print("   ✅ Database configuration working after style improvements")
            else:
                print("   ❌ Database configuration broken after style changes")
            
            self.log_test("Database.py Style Improvements (no break)", success, 
                         f"Health: {response1.status_code}, Dashboard: {response2.status_code}")
            return success
        except Exception as e:
            self.log_test("Database.py Style Improvements (no break)", False, str(e))
            return False

    def test_final_newlines_fix(self):
        """Test that adding final newlines doesn't break file parsing"""
        try:
            print("📄 Testing Final Newlines Fix...")
            
            # Test that API root still works (tests main app loading)
            response1 = requests.get(f"{self.api_url}/", timeout=10)
            print(f"   🌐 API root: {response1.status_code}")
            
            # Test that routers still work (tests router file parsing)
            response2 = requests.get(f"{self.api_url}/health", timeout=10)
            print(f"   🔗 Router endpoints: {response2.status_code}")
            
            # Test that services still work (tests service file parsing)
            response3 = requests.post(f"{self.api_url}/voice/process", 
                                    json={"text": "Test", "user_id": "newline_test"}, 
                                    timeout=15)
            print(f"   🤖 Service processing: {response3.status_code}")
            
            success = all(code in [200, 422] for code in [response1.status_code, response2.status_code, response3.status_code])
            
            if success:
                print("   ✅ All files parsing correctly after newline additions")
            else:
                print("   ❌ File parsing issues after newline changes")
            
            self.log_test("Final Newlines Fix (no parsing issues)", success, 
                         f"Root: {response1.status_code}, Health: {response2.status_code}, Voice: {response3.status_code}")
            return success
        except Exception as e:
            self.log_test("Final Newlines Fix (no parsing issues)", False, str(e))
            return False

    def test_key_endpoints_still_working(self):
        """Test that key endpoints mentioned in review are still working"""
        try:
            print("🔑 Testing Key Endpoints Still Working...")
            
            endpoints_to_test = [
                ("/health", "Health Check"),
                ("/dashboard", "Dashboard"),
                ("/cleaning/houses", "Cleaning Houses"),
                ("/cleaning/filters", "Cleaning Filters")
            ]
            
            results = {}
            
            for endpoint, name in endpoints_to_test:
                try:
                    response = requests.get(f"{self.api_url}{endpoint}", timeout=15)
                    results[name] = response.status_code
                    print(f"   {name}: {response.status_code}")
                except Exception as e:
                    results[name] = f"Error: {e}"
                    print(f"   {name}: Error - {e}")
            
            # All should return 200
            success = all(isinstance(code, int) and code == 200 for code in results.values())
            
            if success:
                print("   ✅ All key endpoints working correctly")
            else:
                print("   ❌ Some key endpoints have issues")
            
            self.log_test("Key Endpoints Still Working", success, str(results))
            return success
        except Exception as e:
            self.log_test("Key Endpoints Still Working", False, str(e))
            return False

    def run_all_tests(self):
        """Run all code quality fix tests"""
        print("🚀 VasDom AudioBot - Code Quality Fixes Testing")
        print(f"🔗 Testing API at: {self.api_url}")
        print("📋 FIXED ISSUES TO TEST:")
        print("   1. X-API-Key Header Validation - в security.py исправлена проверка заголовка")
        print("   2. Voice API Exception Handling - в voice.py исправлена обработка исключений (HTTP 500)")
        print("   3. Database.py Style Improvements - улучшена читаемость кода")
        print("   4. Code Quality Fixes - добавлены финальные переводы строк")
        print("🎯 CRITICAL TESTING FOCUS:")
        print("   - /api/voice/process с ошибками должен возвращать HTTP 500")
        print("   - X-API-Key аутентификация должна работать правильно")
        print("   - Основная функциональность не должна быть сломана")
        print("=" * 80)
        
        # Run focused tests for each fix
        self.test_x_api_key_header_validation()
        self.test_voice_api_exception_handling()
        self.test_database_style_improvements()
        self.test_final_newlines_fix()
        self.test_key_endpoints_still_working()
        
        # Print results
        print("=" * 80)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} passed")
        
        if self.failed_tests:
            print("\n❌ Failed Tests:")
            for test in self.failed_tests:
                print(f"   • {test['name']}: {test['details']}")
        
        success_rate = (self.tests_passed / self.tests_run) * 100 if self.tests_run > 0 else 0
        print(f"✅ Success Rate: {success_rate:.1f}%")
        
        # Summary for main agent
        print("\n🔧 CODE QUALITY FIXES VERIFICATION:")
        x_api_key_fixed = not any("X-API-Key" in test["name"] for test in self.failed_tests)
        voice_error_fixed = not any("Exception Handling" in test["name"] for test in self.failed_tests)
        database_ok = not any("Database.py" in test["name"] for test in self.failed_tests)
        newlines_ok = not any("Newlines" in test["name"] for test in self.failed_tests)
        endpoints_ok = not any("Endpoints" in test["name"] for test in self.failed_tests)
        
        print(f"   1. X-API-Key Header Validation Fix: {'✅' if x_api_key_fixed else '❌'}")
        print(f"   2. Voice API Exception Handling Fix: {'✅' if voice_error_fixed else '❌'}")
        print(f"   3. Database.py Style Improvements: {'✅' if database_ok else '❌'}")
        print(f"   4. Final Newlines Addition: {'✅' if newlines_ok else '❌'}")
        print(f"   5. Key Endpoints Functionality: {'✅' if endpoints_ok else '❌'}")
        
        return self.tests_passed == self.tests_run

def main():
    """Main test execution"""
    tester = CodeQualityTester()
    
    try:
        all_passed = tester.run_all_tests()
        return 0 if all_passed else 1
    except KeyboardInterrupt:
        print("\n⏹️ Tests interrupted by user")
        return 1
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())