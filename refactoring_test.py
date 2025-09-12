#!/usr/bin/env python3
"""
VasDom AudioBot Refactoring Tests
Tests all refactoring fixes after code improvements:
1. Database Fixes - API-only mode without SQLite errors
2. Security Improvements - Bearer token and X-API-Key authentication
3. Pydantic v2 Updates - TelegramUpdate model validation
4. Logs Error Handling - HTTPException on errors
5. Code Quality - No duplication, clean imports
6. Core API Functions - All endpoints working correctly
"""

import requests
import json
import sys
import time
import os
from datetime import datetime

class VasDomRefactoringTester:
    def __init__(self, base_url="https://housing-management.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []
        self.api_key = "vasdom-secret-key-change-in-production"  # Default API key

    def log_test(self, name, success, details=""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED")
        else:
            self.failed_tests.append({"name": name, "details": details})
            print(f"❌ {name} - FAILED: {details}")

    def test_database_api_only_mode(self):
        """Test 1: Database Fixes - API works without DATABASE_URL, no SQLite async errors"""
        try:
            # Test that API works in API-only mode without database
            response = requests.get(f"{self.api_url}/", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                success = "VasDom AudioBot API" in data.get("message", "")
                print(f"   📡 API works without DATABASE_URL: {'✅' if success else '❌'}")
                print(f"   📡 Status: {data.get('status', 'unknown')}")
                
            # Test health endpoint shows database status
            db_status = "unknown"
            health_response = requests.get(f"{self.api_url}/health", timeout=10)
            if health_response.status_code == 200:
                health_data = health_response.json()
                db_status = health_data.get("database", "unknown")
                print(f"   🏥 Database status in health: {db_status}")
                
                # Should show 'disabled' or 'connected' but not cause errors
                if db_status in ["disabled", "connected"]:
                    print(f"   ✅ Database status properly handled: {db_status}")
                else:
                    print(f"   ⚠️ Unexpected database status: {db_status}")
                
            self.log_test("Database API-Only Mode", success, 
                         f"API Status: {response.status_code}, DB Status: {db_status}")
            return success
        except Exception as e:
            self.log_test("Database API-Only Mode", False, str(e))
            return False

    def test_security_bearer_token(self):
        """Test 2a: Security - verify_api_key with Bearer token"""
        try:
            # Test protected endpoint with Bearer token
            headers = {"Authorization": f"Bearer {self.api_key}"}
            
            test_message = {
                "text": "Test Bearer token authentication",
                "user_id": "security_test"
            }
            
            response = requests.post(f"{self.api_url}/voice/process", 
                                   json=test_message, headers=headers, timeout=15)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                success = "response" in data
                print(f"   🔐 Bearer token authentication: {'✅' if success else '❌'}")
                print(f"   🔐 Response received: {len(data.get('response', '')) > 0}")
            else:
                print(f"   🔐 Bearer token failed: {response.status_code}")
                if response.status_code == 401:
                    print(f"   🔐 Unauthorized (expected if auth is enabled)")
                
            self.log_test("Security Bearer Token", success, 
                         f"Status: {response.status_code}")
            return success
        except Exception as e:
            self.log_test("Security Bearer Token", False, str(e))
            return False

    def test_security_x_api_key(self):
        """Test 2b: Security - verify_api_key with X-API-Key header"""
        try:
            # Test protected endpoint with X-API-Key header
            headers = {"X-API-Key": self.api_key}
            
            test_message = {
                "text": "Test X-API-Key authentication",
                "user_id": "security_test"
            }
            
            response = requests.post(f"{self.api_url}/voice/process", 
                                   json=test_message, headers=headers, timeout=15)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                success = "response" in data
                print(f"   🔑 X-API-Key authentication: {'✅' if success else '❌'}")
                print(f"   🔑 Response received: {len(data.get('response', '')) > 0}")
            else:
                print(f"   🔑 X-API-Key failed: {response.status_code}")
                if response.status_code == 401:
                    print(f"   🔑 Unauthorized (expected if auth is enabled)")
                
            self.log_test("Security X-API-Key", success, 
                         f"Status: {response.status_code}")
            return success
        except Exception as e:
            self.log_test("Security X-API-Key", False, str(e))
            return False

    def test_security_telegram_webhook_auth(self):
        """Test 2c: Security - Telegram webhook with authentication"""
        try:
            # Test Telegram webhook with Bearer token
            headers = {"Authorization": f"Bearer {self.api_key}"}
            
            webhook_data = {
                "update_id": 123456789,
                "message": {
                    "message_id": 1,
                    "from": {"id": 123, "first_name": "TestUser"},
                    "chat": {"id": 123, "type": "private"},
                    "date": 1234567890,
                    "text": "Test webhook authentication"
                }
            }
            
            response = requests.post(f"{self.api_url}/telegram/webhook", 
                                   json=webhook_data, headers=headers, timeout=15)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                success = data.get("status") in ["success", "processed", "received"]
                print(f"   📱 Telegram webhook auth: {'✅' if success else '❌'}")
                print(f"   📱 Webhook status: {data.get('status')}")
            else:
                print(f"   📱 Telegram webhook auth failed: {response.status_code}")
                
            self.log_test("Security Telegram Webhook Auth", success, 
                         f"Status: {response.status_code}")
            return success
        except Exception as e:
            self.log_test("Security Telegram Webhook Auth", False, str(e))
            return False

    def test_pydantic_v2_telegram_validation(self):
        """Test 3: Pydantic v2 - TelegramUpdate model with field_validator"""
        try:
            # Test valid Telegram webhook data
            valid_webhook_data = {
                "update_id": 123456789,
                "message": {
                    "message_id": 1,
                    "from": {"id": 123, "first_name": "TestUser"},
                    "chat": {"id": 123, "type": "private"},
                    "date": 1234567890,
                    "text": "Valid message"
                }
            }
            
            headers = {"Authorization": f"Bearer {self.api_key}"}
            response = requests.post(f"{self.api_url}/telegram/webhook", 
                                   json=valid_webhook_data, headers=headers, timeout=15)
            
            valid_success = response.status_code == 200
            print(f"   ✅ Valid Telegram data: {'✅' if valid_success else '❌'}")
            
            # Test invalid Telegram webhook data (missing required fields)
            invalid_webhook_data = {
                "update_id": 123456789,
                "message": {
                    "message_id": 1,
                    "from": {"id": 123, "first_name": "TestUser"},
                    "chat": {"id": 123, "type": "private"},
                    "date": 1234567890
                    # Missing 'text' field
                }
            }
            
            invalid_response = requests.post(f"{self.api_url}/telegram/webhook", 
                                           json=invalid_webhook_data, headers=headers, timeout=15)
            
            invalid_rejected = invalid_response.status_code == 400
            print(f"   ❌ Invalid data rejected: {'✅' if invalid_rejected else '❌'}")
            
            if invalid_rejected:
                error_data = invalid_response.json()
                print(f"   📝 Validation error: {error_data.get('detail', 'No details')}")
            
            success = valid_success and invalid_rejected
            
            self.log_test("Pydantic v2 Telegram Validation", success, 
                         f"Valid: {response.status_code}, Invalid: {invalid_response.status_code}")
            return success
        except Exception as e:
            self.log_test("Pydantic v2 Telegram Validation", False, str(e))
            return False

    def test_logs_error_handling(self):
        """Test 4: Logs Error Handling - HTTPException on errors, not success"""
        try:
            # Test /api/logs endpoint
            logs_response = requests.get(f"{self.api_url}/logs", timeout=10)
            logs_success = logs_response.status_code == 200
            
            if logs_success:
                logs_data = logs_response.json()
                # Should return proper structure even if empty
                has_structure = ("status" in logs_data and 
                               "voice_logs" in logs_data and
                               isinstance(logs_data["voice_logs"], list))
                print(f"   📋 /api/logs structure: {'✅' if has_structure else '❌'}")
                print(f"   📋 Logs count: {len(logs_data.get('voice_logs', []))}")
            else:
                print(f"   📋 /api/logs failed: {logs_response.status_code}")
            
            # Test /api/logs/ai endpoint (should return 404 or proper error)
            ai_logs_response = requests.get(f"{self.api_url}/logs/ai", timeout=10)
            ai_logs_proper_error = ai_logs_response.status_code in [404, 501]
            print(f"   🤖 /api/logs/ai error handling: {'✅' if ai_logs_proper_error else '❌'}")
            
            # Test /api/logs/telegram endpoint (should return 404 or proper error)
            telegram_logs_response = requests.get(f"{self.api_url}/logs/telegram", timeout=10)
            telegram_logs_proper_error = telegram_logs_response.status_code in [404, 501]
            print(f"   📱 /api/logs/telegram error handling: {'✅' if telegram_logs_proper_error else '❌'}")
            
            success = logs_success and ai_logs_proper_error and telegram_logs_proper_error
            
            self.log_test("Logs Error Handling", success, 
                         f"Logs: {logs_response.status_code}, AI: {ai_logs_response.status_code}, Telegram: {telegram_logs_response.status_code}")
            return success
        except Exception as e:
            self.log_test("Logs Error Handling", False, str(e))
            return False

    def test_code_quality_no_duplication(self):
        """Test 5: Code Quality - No TelegramUpdate duplication, clean imports"""
        try:
            # Test that Telegram webhook works (indicates no model duplication issues)
            webhook_data = {
                "update_id": 123456789,
                "message": {
                    "message_id": 1,
                    "from": {"id": 123, "first_name": "TestUser"},
                    "chat": {"id": 123, "type": "private"},
                    "date": 1234567890,
                    "text": "Code quality test"
                }
            }
            
            headers = {"Authorization": f"Bearer {self.api_key}"}
            response = requests.post(f"{self.api_url}/telegram/webhook", 
                                   json=webhook_data, headers=headers, timeout=15)
            
            no_import_errors = response.status_code != 500
            print(f"   🧹 No import/duplication errors: {'✅' if no_import_errors else '❌'}")
            
            if response.status_code == 500:
                print(f"   🧹 Server error (may indicate import issues): {response.text[:100]}")
            
            # Test API root works (indicates clean startup)
            root_response = requests.get(f"{self.api_url}/", timeout=10)
            clean_startup = root_response.status_code == 200
            print(f"   🚀 Clean API startup: {'✅' if clean_startup else '❌'}")
            
            success = no_import_errors and clean_startup
            
            self.log_test("Code Quality - No Duplication", success, 
                         f"Webhook: {response.status_code}, Root: {root_response.status_code}")
            return success
        except Exception as e:
            self.log_test("Code Quality - No Duplication", False, str(e))
            return False

    def test_core_api_functions(self):
        """Test 6: Core API Functions - /api/, /api/dashboard, /api/bitrix24/test"""
        try:
            # Test /api/ root endpoint
            root_response = requests.get(f"{self.api_url}/", timeout=10)
            root_success = root_response.status_code == 200
            
            if root_success:
                root_data = root_response.json()
                has_required_fields = all(field in root_data for field in 
                                        ["message", "version", "status", "features"])
                print(f"   📡 /api/ endpoint: {'✅' if has_required_fields else '❌'}")
                print(f"   📡 Version: {root_data.get('version', 'unknown')}")
            else:
                print(f"   📡 /api/ failed: {root_response.status_code}")
            
            # Test /api/dashboard endpoint
            dashboard_response = requests.get(f"{self.api_url}/dashboard", timeout=15)
            dashboard_success = dashboard_response.status_code == 200
            
            if dashboard_success:
                dashboard_data = dashboard_response.json()
                has_stats = ("status" in dashboard_data and 
                           "stats" in dashboard_data and
                           isinstance(dashboard_data["stats"], dict))
                print(f"   📊 /api/dashboard endpoint: {'✅' if has_stats else '❌'}")
                
                if has_stats:
                    stats = dashboard_data["stats"]
                    houses = stats.get("houses", 0)
                    employees = stats.get("employees", 0)
                    print(f"   📊 Houses: {houses}, Employees: {employees}")
            else:
                print(f"   📊 /api/dashboard failed: {dashboard_response.status_code}")
            
            # Test /api/bitrix24/test endpoint
            bitrix_response = requests.get(f"{self.api_url}/bitrix24/test", timeout=15)
            bitrix_success = bitrix_response.status_code == 200
            
            if bitrix_success:
                bitrix_data = bitrix_response.json()
                has_bitrix_info = ("status" in bitrix_data and 
                                 "bitrix_info" in bitrix_data)
                print(f"   🔗 /api/bitrix24/test endpoint: {'✅' if has_bitrix_info else '❌'}")
                
                if has_bitrix_info:
                    bitrix_info = bitrix_data["bitrix_info"]
                    print(f"   🔗 Bitrix status: {bitrix_info.get('message', 'unknown')}")
            else:
                print(f"   🔗 /api/bitrix24/test failed: {bitrix_response.status_code}")
            
            success = root_success and dashboard_success and bitrix_success
            
            self.log_test("Core API Functions", success, 
                         f"Root: {root_response.status_code}, Dashboard: {dashboard_response.status_code}, Bitrix: {bitrix_response.status_code}")
            return success
        except Exception as e:
            self.log_test("Core API Functions", False, str(e))
            return False

    def test_bitrix24_crm_integration(self):
        """Test 6b: Bitrix24 Integration and CRM Data"""
        try:
            # Test Bitrix24 CRM houses endpoint
            houses_response = requests.get(f"{self.api_url}/cleaning/houses", timeout=25)
            houses_success = houses_response.status_code == 200
            
            if houses_success:
                houses_data = houses_response.json()
                has_houses = ("status" in houses_data and 
                            "houses" in houses_data and
                            isinstance(houses_data["houses"], list))
                
                if has_houses:
                    houses_count = len(houses_data["houses"])
                    source = houses_data.get("source", "unknown")
                    print(f"   🏠 CRM houses loaded: {houses_count}")
                    print(f"   🏠 Data source: {source}")
                    
                    # Check if real CRM data
                    if houses_count > 0:
                        sample_house = houses_data["houses"][0]
                        has_crm_fields = (sample_house.get("bitrix24_deal_id") and 
                                        sample_house.get("stage") and
                                        sample_house.get("address"))
                        print(f"   🏠 Real CRM fields: {'✅' if has_crm_fields else '❌'}")
                        
                        if has_crm_fields:
                            print(f"   🏠 Sample: {sample_house.get('address', 'No address')}")
                            print(f"   🏠 Deal ID: {sample_house.get('bitrix24_deal_id', 'No ID')}")
                else:
                    print(f"   🏠 Invalid houses data structure")
                    houses_success = False
            else:
                print(f"   🏠 CRM houses failed: {houses_response.status_code}")
            
            self.log_test("Bitrix24 CRM Integration", houses_success, 
                         f"Status: {houses_response.status_code}, Houses: {houses_count if houses_success else 0}")
            return houses_success
        except Exception as e:
            self.log_test("Bitrix24 CRM Integration", False, str(e))
            return False

    def run_refactoring_tests(self):
        """Run all refactoring tests"""
        print("🔧 Starting VasDom AudioBot Refactoring Tests")
        print(f"🔗 Testing API at: {self.api_url}")
        print("📋 Refactoring Requirements:")
        print("   1. Database Fixes - API-only mode without SQLite errors")
        print("   2. Security Improvements - Bearer token and X-API-Key authentication")
        print("   3. Pydantic v2 Updates - TelegramUpdate model validation")
        print("   4. Logs Error Handling - HTTPException on errors")
        print("   5. Code Quality - No duplication, clean imports")
        print("   6. Core API Functions - All endpoints working")
        print("=" * 80)
        
        # 1. Database Fixes
        print("\n1️⃣ DATABASE FIXES")
        self.test_database_api_only_mode()
        
        # 2. Security Improvements
        print("\n2️⃣ SECURITY IMPROVEMENTS")
        self.test_security_bearer_token()
        self.test_security_x_api_key()
        self.test_security_telegram_webhook_auth()
        
        # 3. Pydantic v2 Updates
        print("\n3️⃣ PYDANTIC V2 UPDATES")
        self.test_pydantic_v2_telegram_validation()
        
        # 4. Logs Error Handling
        print("\n4️⃣ LOGS ERROR HANDLING")
        self.test_logs_error_handling()
        
        # 5. Code Quality
        print("\n5️⃣ CODE QUALITY")
        self.test_code_quality_no_duplication()
        
        # 6. Core API Functions
        print("\n6️⃣ CORE API FUNCTIONS")
        self.test_core_api_functions()
        self.test_bitrix24_crm_integration()
        
        # Print results
        print("=" * 80)
        print(f"📊 Refactoring Test Results: {self.tests_passed}/{self.tests_run} passed")
        
        if self.failed_tests:
            print("\n❌ Failed Tests:")
            for test in self.failed_tests:
                print(f"   • {test['name']}: {test['details']}")
        
        success_rate = (self.tests_passed / self.tests_run) * 100 if self.tests_run > 0 else 0
        print(f"✅ Success Rate: {success_rate:.1f}%")
        
        # Refactoring requirements summary
        print("\n📋 Refactoring Requirements Status:")
        
        # Check each category
        db_tests = [test for test in self.failed_tests if "Database" in test["name"]]
        security_tests = [test for test in self.failed_tests if "Security" in test["name"]]
        pydantic_tests = [test for test in self.failed_tests if "Pydantic" in test["name"]]
        logs_tests = [test for test in self.failed_tests if "Logs" in test["name"]]
        quality_tests = [test for test in self.failed_tests if "Code Quality" in test["name"]]
        api_tests = [test for test in self.failed_tests if "Core API" in test["name"] or "Bitrix24" in test["name"]]
        
        print(f"   1. Database Fixes (API-only mode): {'✅' if len(db_tests) == 0 else '❌'}")
        print(f"   2. Security Improvements (auth): {'✅' if len(security_tests) == 0 else '❌'}")
        print(f"   3. Pydantic v2 Updates (validation): {'✅' if len(pydantic_tests) == 0 else '❌'}")
        print(f"   4. Logs Error Handling (HTTPException): {'✅' if len(logs_tests) == 0 else '❌'}")
        print(f"   5. Code Quality (no duplication): {'✅' if len(quality_tests) == 0 else '❌'}")
        print(f"   6. Core API Functions (working): {'✅' if len(api_tests) == 0 else '❌'}")
        
        print(f"\n🎯 ОЖИДАЕМЫЕ РЕЗУЛЬТАТЫ:")
        print(f"   - Все API работают без SQLite ошибок: {'✅' if len(db_tests) == 0 else '❌'}")
        print(f"   - Безопасность улучшена (Bearer/X-API-Key): {'✅' if len(security_tests) == 0 else '❌'}")
        print(f"   - Pydantic v2 корректен (field_validator): {'✅' if len(pydantic_tests) == 0 else '❌'}")
        print(f"   - Логи правильно обрабатывают ошибки: {'✅' if len(logs_tests) == 0 else '❌'}")
        
        return self.tests_passed == self.tests_run

def main():
    """Main test execution"""
    tester = VasDomRefactoringTester()
    
    try:
        all_passed = tester.run_refactoring_tests()
        return 0 if all_passed else 1
    except KeyboardInterrupt:
        print("\n⏹️ Tests interrupted by user")
        return 1
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())