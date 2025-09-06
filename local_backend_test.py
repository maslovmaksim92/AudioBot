#!/usr/bin/env python3
"""
Local Backend API Testing for VasDom AI Assistant
Tests the local backend endpoints to verify functionality
"""

import requests
import sys
import json
from datetime import datetime

class LocalBackendTester:
    def __init__(self, base_url="http://localhost:8001"):
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

    def test_endpoint(self, name: str, endpoint: str) -> tuple[bool, dict]:
        """Test a single endpoint"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            print(f"\n🔍 Testing {name}...")
            print(f"   URL: {url}")
            
            response = requests.get(url, timeout=10)
            success = response.status_code == 200
            
            try:
                response_data = response.json()
            except:
                response_data = {"raw_response": response.text}

            details = f"Status: {response.status_code}"
            if success and response_data:
                if 'status' in response_data:
                    details += f", Status: {response_data['status']}"
                if 'ai_response' in response_data:
                    ai_response = response_data['ai_response']
                    details += f", AI Response Length: {len(ai_response)}"
                    details += f", Contains VasDom: {'ВасДом' in ai_response}"
                    details += f", Contains Kaluga: {'Калуг' in ai_response}"
                    details += f", Contains cleaning: {'уборк' in ai_response.lower()}"
            
            self.log_test(name, success, details)
            return success, response_data

        except Exception as e:
            self.log_test(name, False, f"Exception: {str(e)}")
            return False, {}

    def run_tests(self):
        """Run all tests"""
        print("🏠 VasDom AI Assistant Local Backend Testing")
        print(f"Testing against: {self.base_url}")
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Test basic endpoints
        print("\n" + "="*60)
        print("🚀 TESTING LOCAL BACKEND ENDPOINTS")
        print("="*60)
        
        # Test service info
        self.test_endpoint("Service Info", "/")
        
        # Test health checks
        self.test_endpoint("Basic Health Check", "/health")
        self.test_endpoint("Detailed Health Check", "/healthz")
        
        # Test AI functionality
        success, ai_data = self.test_endpoint("AI Response Generation", "/test-ai")
        if success and ai_data:
            print(f"   🤖 AI Model: {ai_data.get('model', 'unknown')}")
            print(f"   🤖 AI Provider: {ai_data.get('provider', 'unknown')}")
            ai_response = ai_data.get('ai_response', '')
            print(f"   🤖 Response Preview: {ai_response[:150]}...")
        
        # Test dashboard
        self.test_endpoint("Dashboard Data", "/dashboard")
        
        # Test logs
        self.test_endpoint("System Logs", "/logs?lines=5")
        
        # Test Telegram
        self.test_endpoint("Telegram Webhook Setup", "/telegram/set-webhook")
        
        # Test Bitrix24
        self.test_endpoint("Bitrix24 Connection", "/api/bitrix24/test")
        self.test_endpoint("Bitrix24 Deals", "/api/bitrix24/deals?limit=3")
        self.test_endpoint("Bitrix24 Cleaning Houses", "/api/bitrix24/cleaning-houses")
        
        self.print_summary()

    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*60)
        print("📋 LOCAL BACKEND TEST SUMMARY")
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
        
        return 0 if len(self.failed_tests) == 0 else 1

def main():
    """Main function"""
    tester = LocalBackendTester()
    exit_code = tester.run_tests()
    return exit_code

if __name__ == "__main__":
    sys.exit(main())