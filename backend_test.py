#!/usr/bin/env python3
"""
VasDom AI Assistant Backend API Testing
Tests all endpoints for the VasDom cleaning service AI assistant
"""

import requests
import sys
import json
from datetime import datetime
from typing import Dict, Any

class VasDomAPITester:
    def __init__(self, base_url="https://ai-crm-bot.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []

    def log_test(self, name: str, success: bool, details: str = ""):
        """Log test results"""
        self.tests_run += 1
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"\n{status} - {name}")
        if details:
            print(f"   Details: {details}")
        
        if success:
            self.tests_passed += 1
        else:
            self.failed_tests.append(f"{name}: {details}")

    def test_endpoint(self, name: str, method: str, endpoint: str, expected_status: int = 200, 
                     data: Dict = None, headers: Dict = None) -> tuple[bool, Dict]:
        """Test a single endpoint"""
        url = f"{self.base_url}{endpoint}"
        if headers is None:
            headers = {'Content-Type': 'application/json'}

        try:
            print(f"\n🔍 Testing {name}...")
            print(f"   URL: {url}")
            
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=30)
            else:
                raise ValueError(f"Unsupported method: {method}")

            success = response.status_code == expected_status
            
            try:
                response_data = response.json()
            except:
                response_data = {"raw_response": response.text}

            details = f"Status: {response.status_code}, Response: {json.dumps(response_data, indent=2)[:200]}..."
            self.log_test(name, success, details)
            
            return success, response_data

        except requests.exceptions.Timeout:
            self.log_test(name, False, "Request timeout (30s)")
            return False, {}
        except requests.exceptions.ConnectionError:
            self.log_test(name, False, "Connection error - service may be down")
            return False, {}
        except Exception as e:
            self.log_test(name, False, f"Exception: {str(e)}")
            return False, {}

    def test_basic_endpoints(self):
        """Test basic service endpoints"""
        print("\n" + "="*60)
        print("🚀 TESTING BASIC ENDPOINTS")
        print("="*60)
        
        # Test root endpoint with /api prefix
        success, data = self.test_endpoint("Service Info", "GET", "/api/")
        if success:
            print(f"   Service: {data.get('service', 'Unknown')}")
            print(f"   Version: {data.get('version', 'Unknown')}")
            print(f"   Environment: {data.get('environment', 'Unknown')}")
            features = data.get('features', {})
            print(f"   Features: Telegram={features.get('telegram_bot', False)}, "
                  f"Bitrix24={features.get('bitrix24_integration', False)}, "
                  f"AI={features.get('ai_service', False)}")

        # Test basic health check with /api prefix
        self.test_endpoint("Basic Health Check", "GET", "/api/health")

        # Test detailed health check with /api prefix
        success, health_data = self.test_endpoint("Detailed Health Check", "GET", "/api/healthz")
        if success:
            services = health_data.get('services', {})
            print(f"   Service Status Summary:")
            for service_name, service_info in services.items():
                status = service_info.get('status', 'unknown')
                print(f"     - {service_name}: {status}")

    def test_dashboard_endpoints(self):
        """Test dashboard related endpoints"""
        print("\n" + "="*60)
        print("📊 TESTING DASHBOARD ENDPOINTS")
        print("="*60)
        
        # Test dashboard data with /api prefix
        success, dashboard_data = self.test_endpoint("Dashboard Data", "GET", "/api/dashboard")
        if success:
            system = dashboard_data.get('system', {})
            print(f"   System Status: {system.get('status', 'unknown')}")
            print(f"   Environment: {system.get('environment', 'unknown')}")
            
            services = dashboard_data.get('services', {})
            print(f"   Services Count: {len(services)}")

        # Test logs endpoint with /api prefix
        self.test_endpoint("System Logs", "GET", "/api/logs?lines=10")

    def test_telegram_endpoints(self):
        """Test Telegram bot endpoints"""
        print("\n" + "="*60)
        print("🤖 TESTING TELEGRAM ENDPOINTS")
        print("="*60)
        
        # Test webhook setup (GET request)
        self.test_endpoint("Set Telegram Webhook", "GET", "/telegram/set-webhook")
        
        # Note: We don't test POST /telegram/webhook as it requires valid Telegram data

    def test_ai_endpoints(self):
        """Test AI functionality endpoints"""
        print("\n" + "="*60)
        print("🤖 TESTING AI ENDPOINTS")
        print("="*60)
        
        # Test AI generation with /api prefix
        success, ai_data = self.test_endpoint("AI Response Generation", "GET", "/api/test-ai")
        if success:
            print(f"   AI Status: {ai_data.get('status', 'unknown')}")
            print(f"   Model: {ai_data.get('model', 'unknown')}")
            print(f"   Provider: {ai_data.get('provider', 'unknown')}")
            response = ai_data.get('ai_response', '')
            print(f"   Response Length: {len(response)} chars")
            print(f"   Response Preview: {response[:100]}...")
            
            # Check if response is in Russian and mentions VasDom
            if 'ВасДом' in response or 'уборк' in response.lower():
                print("   ✅ Response contains VasDom context")
            else:
                print("   ⚠️ Response may not contain VasDom context")

    def test_bitrix24_endpoints(self):
        """Test Bitrix24 CRM endpoints"""
        print("\n" + "="*60)
        print("🏢 TESTING BITRIX24 ENDPOINTS")
        print("="*60)
        
        # Test Bitrix24 connection
        success, test_data = self.test_endpoint("Bitrix24 Connection Test", "GET", "/api/bitrix24/test")
        if success:
            print(f"   Connection Status: {test_data.get('status', 'unknown')}")

        # Test getting deals
        success, deals_data = self.test_endpoint("Bitrix24 Deals", "GET", "/api/bitrix24/deals?limit=5")
        if success:
            deals = deals_data.get('deals', [])
            count = deals_data.get('count', 0)
            print(f"   Deals Retrieved: {count}")

        # Test getting cleaning houses
        success, houses_data = self.test_endpoint("Bitrix24 Cleaning Houses", "GET", "/api/bitrix24/cleaning-houses")
        if success:
            houses = houses_data.get('houses', [])
            count = houses_data.get('count', 0)
            print(f"   Cleaning Houses Retrieved: {count}")

    def test_error_handling(self):
        """Test error handling for invalid endpoints"""
        print("\n" + "="*60)
        print("🚨 TESTING ERROR HANDLING")
        print("="*60)
        
        # Test non-existent endpoint
        self.test_endpoint("Non-existent Endpoint", "GET", "/nonexistent", expected_status=404)

    def run_all_tests(self):
        """Run all test suites"""
        print("🏠 VasDom AI Assistant Backend API Testing")
        print(f"Testing against: {self.base_url}")
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            self.test_basic_endpoints()
            self.test_dashboard_endpoints()
            self.test_ai_endpoints()
            self.test_telegram_endpoints()
            self.test_bitrix24_endpoints()
            self.test_error_handling()
            
        except KeyboardInterrupt:
            print("\n\n⚠️ Testing interrupted by user")
        except Exception as e:
            print(f"\n\n❌ Unexpected error during testing: {e}")
        
        self.print_summary()

    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*60)
        print("📋 TEST SUMMARY")
        print("="*60)
        
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        
        print(f"Total Tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {len(self.failed_tests)}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if self.failed_tests:
            print(f"\n❌ FAILED TESTS:")
            for i, failure in enumerate(self.failed_tests, 1):
                print(f"   {i}. {failure}")
        
        print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Return exit code
        return 0 if len(self.failed_tests) == 0 else 1

def main():
    """Main function"""
    tester = VasDomAPITester()
    exit_code = tester.run_all_tests()
    return exit_code

if __name__ == "__main__":
    sys.exit(main())