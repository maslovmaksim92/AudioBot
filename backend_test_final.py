#!/usr/bin/env python3
"""
Final Backend Testing for VasDom AudioBot on Render
Tests the actual available endpoints from OpenAPI spec
"""

import requests
import sys
import json
import time
from datetime import datetime

class VasDomFinalTester:
    def __init__(self, base_url="https://audiobot-qci2.onrender.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        
    def log_test(self, name: str, success: bool, details: str = ""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED {details}")
        else:
            print(f"❌ {name} - FAILED {details}")
    
    def make_request(self, method: str, endpoint: str, data: dict = None, timeout: int = 30) -> tuple:
        """Make HTTP request and return (success, response_data, status_code)"""
        if endpoint.startswith('http'):
            url = endpoint
        elif endpoint.startswith('/'):
            url = f"{self.base_url}{endpoint}"
        else:
            url = f"{self.api_url}/{endpoint}" if endpoint else self.api_url
            
        headers = {'Content-Type': 'application/json'}
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=timeout)
            else:
                return False, {}, 0
                
            try:
                response_data = response.json()
            except:
                response_data = {"raw_response": response.text[:200]}
                
            return response.status_code < 400, response_data, response.status_code
            
        except requests.exceptions.Timeout:
            return False, {"error": "Request timeout"}, 0
        except requests.exceptions.ConnectionError:
            return False, {"error": "Connection error"}, 0
        except Exception as e:
            return False, {"error": str(e)}, 0

    def test_root_endpoint(self):
        """Test GET / - System information on Render"""
        print("\n🔍 Testing Root Endpoint (/)...")
        success, data, status = self.make_request('GET', '/')
        
        if status == 200:
            self.log_test("Root Endpoint", True, f"Status: {status} - Frontend loaded")
            return True
        else:
            self.log_test("Root Endpoint", False, f"Status: {status}")
            return False

    def test_api_root(self):
        """Test GET /api/ - API information with self-learning functions"""
        print("\n🔍 Testing API Root (/api/)...")
        success, data, status = self.make_request('GET', '')
        
        if success and status == 200:
            expected_fields = ['message', 'version', 'status', 'features']
            has_expected = all(field in data for field in expected_fields)
            
            # Check for Render-specific info
            has_render_info = 'render' in str(data).lower() or 'emergent' in str(data).lower()
            
            overall_success = has_expected
            self.log_test("API Root", overall_success, 
                         f"Version: {data.get('version')}, Features: {len(data.get('features', []))}")
            return overall_success
        else:
            self.log_test("API Root", False, f"Status: {status}")
            return False

    def test_health_check(self):
        """Test GET /api/health - Health check with Render components"""
        print("\n🔍 Testing Health Check (/api/health)...")
        success, data, status = self.make_request('GET', 'health')
        
        if success and status == 200:
            expected_fields = ['status', 'service', 'version']
            has_expected = all(field in data for field in expected_fields)
            
            is_healthy = data.get('status') == 'healthy'
            
            overall_success = has_expected and is_healthy
            self.log_test("Health Check", overall_success, 
                         f"Status: {data.get('status')}, Service: {data.get('service')}")
            return overall_success
        else:
            self.log_test("Health Check", False, f"Status: {status}")
            return False

    def test_voice_process(self):
        """Test POST /api/voice/process - AI chat (main function)"""
        print("\n🔍 Testing Voice Processing (/api/voice/process)...")
        
        # Use the correct schema from OpenAPI spec
        test_data = {
            "text": "Как часто нужно убираться в офисе?",
            "user_id": f"test_user_{int(time.time())}"
        }
        
        success, data, status = self.make_request('POST', 'voice/process', test_data, timeout=45)
        
        if success and status == 200:
            # Check for response structure based on ChatResponse schema
            has_response = 'response' in data
            response_text = data.get('response', '')
            has_meaningful_response = len(str(response_text)) > 10
            
            overall_success = has_response and has_meaningful_response
            self.log_test("Voice Processing", overall_success, 
                         f"Response length: {len(str(response_text))}")
            return overall_success
        else:
            self.log_test("Voice Processing", False, f"Status: {status}, Error: {data.get('error', 'Unknown')}")
            return False

    def test_self_learning_status(self):
        """Test GET /api/self-learning/status - Self-learning status"""
        print("\n🔍 Testing Self-Learning Status (/api/self-learning/status)...")
        success, data, status = self.make_request('GET', 'self-learning/status')
        
        if success and status == 200:
            self.log_test("Self-Learning Status", True, f"Response: {data}")
            return True
        else:
            self.log_test("Self-Learning Status", False, f"Status: {status}")
            return False

    def test_self_learning_test(self):
        """Test POST /api/self-learning/test - Test self-learning system"""
        print("\n🔍 Testing Self-Learning Test (/api/self-learning/test)...")
        success, data, status = self.make_request('POST', 'self-learning/test')
        
        if success and status == 200:
            self.log_test("Self-Learning Test", True, f"Response: {data}")
            return True
        else:
            self.log_test("Self-Learning Test", False, f"Status: {status}")
            return False

    def test_dashboard_stats(self):
        """Test GET /api/dashboard - Dashboard with Bitrix24 CRM data"""
        print("\n🔍 Testing Dashboard Stats (/api/dashboard)...")
        success, data, status = self.make_request('GET', 'dashboard')
        
        if success and status == 200:
            self.log_test("Dashboard Stats", True, f"Response keys: {list(data.keys()) if isinstance(data, dict) else 'Non-dict response'}")
            return True
        else:
            self.log_test("Dashboard Stats", False, f"Status: {status}")
            return False

    def test_telegram_status(self):
        """Test GET /api/telegram/status - Telegram bot status"""
        print("\n🔍 Testing Telegram Status (/api/telegram/status)...")
        success, data, status = self.make_request('GET', 'telegram/status')
        
        if success and status == 200:
            self.log_test("Telegram Status", True, f"Response: {data}")
            return True
        else:
            self.log_test("Telegram Status", False, f"Status: {status}")
            return False

    def test_cleaning_houses(self):
        """Test GET /api/cleaning/houses - All houses from Bitrix24"""
        print("\n🔍 Testing Cleaning Houses (/api/cleaning/houses)...")
        success, data, status = self.make_request('GET', 'cleaning/houses?limit=5')
        
        if success and status == 200:
            self.log_test("Cleaning Houses", True, f"Response type: {type(data)}")
            return True
        else:
            self.log_test("Cleaning Houses", False, f"Status: {status}")
            return False

    def test_bitrix24_integration(self):
        """Test GET /api/bitrix24/test - Test Bitrix24 integration"""
        print("\n🔍 Testing Bitrix24 Integration (/api/bitrix24/test)...")
        success, data, status = self.make_request('GET', 'bitrix24/test')
        
        if success and status == 200:
            self.log_test("Bitrix24 Integration", True, f"Response: {data}")
            return True
        else:
            self.log_test("Bitrix24 Integration", False, f"Status: {status}")
            return False

    def test_logs_endpoints(self):
        """Test various log endpoints"""
        print("\n🔍 Testing Log Endpoints...")
        
        endpoints = [
            ('logs', 'System Logs'),
            ('logs/ai', 'AI Logs'),
            ('logs/telegram', 'Telegram Logs')
        ]
        
        all_passed = True
        for endpoint, name in endpoints:
            success, data, status = self.make_request('GET', endpoint)
            if success and status == 200:
                print(f"  ✅ {name} - PASSED")
            else:
                print(f"  ❌ {name} - FAILED (Status: {status})")
                all_passed = False
        
        self.log_test("Log Endpoints", all_passed, f"Tested {len(endpoints)} endpoints")
        return all_passed

    def run_comprehensive_test(self):
        """Run all tests based on the actual OpenAPI spec"""
        print("🚀 Starting VasDom AudioBot Final Testing")
        print(f"🌐 Testing against: {self.base_url}")
        print("📋 Testing actual available endpoints from OpenAPI spec:")
        print("=" * 60)
        
        # Test all available endpoints
        test_results = []
        
        # Core endpoints
        test_results.append(self.test_root_endpoint())
        test_results.append(self.test_api_root())
        test_results.append(self.test_health_check())
        
        # Main functionality
        test_results.append(self.test_voice_process())
        test_results.append(self.test_self_learning_status())
        test_results.append(self.test_self_learning_test())
        
        # Dashboard and integrations
        test_results.append(self.test_dashboard_stats())
        test_results.append(self.test_telegram_status())
        test_results.append(self.test_cleaning_houses())
        test_results.append(self.test_bitrix24_integration())
        
        # Logging
        test_results.append(self.test_logs_endpoints())
        
        # Summary
        print("\n" + "=" * 60)
        print(f"📊 FINAL TEST SUMMARY")
        print(f"✅ Passed: {self.tests_passed}/{self.tests_run}")
        print(f"❌ Failed: {self.tests_run - self.tests_passed}/{self.tests_run}")
        
        success_rate = (self.tests_passed / self.tests_run) * 100 if self.tests_run > 0 else 0
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 80:
            print("🎉 EXCELLENT! VasDom AudioBot on Render is working well.")
            return 0
        elif success_rate >= 60:
            print("✅ GOOD! Most functionality is working with minor issues.")
            return 0
        else:
            print("⚠️  NEEDS ATTENTION! Many endpoints are failing.")
            return 1

def main():
    """Main test execution"""
    print("VasDom AudioBot Final Backend Tester")
    print("Testing actual endpoints from OpenAPI specification")
    
    tester = VasDomFinalTester("https://audiobot-qci2.onrender.com")
    
    try:
        return tester.run_comprehensive_test()
    except KeyboardInterrupt:
        print("\n⏹️  Testing interrupted by user")
        return 1
    except Exception as e:
        print(f"\n💥 Unexpected error during testing: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())