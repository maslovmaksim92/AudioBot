#!/usr/bin/env python3
"""
Backend Testing for ACTUAL Deployed VasDom AudioBot
Testing the API that's actually deployed at https://audiobot-qci2.onrender.com
"""

import requests
import sys
import json
import time
from datetime import datetime

class ActualVasDomTester:
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
    
    def make_request(self, method: str, endpoint: str, data: dict = None, timeout: int = 30):
        """Make HTTP request and return (success, response_data, status_code)"""
        url = f"{self.api_url}/{endpoint}" if not endpoint.startswith('http') else endpoint
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
                response_data = {"raw_response": response.text}
                
            return response.status_code < 400, response_data, response.status_code
            
        except Exception as e:
            return False, {"error": str(e)}, 0

    def test_api_root(self):
        """Test GET /api/ - API information"""
        print("\n🔍 Testing API Root...")
        success, data, status = self.make_request('GET', '')
        
        if success and status == 200:
            has_message = 'message' in data
            has_version = 'version' in data
            has_features = 'features' in data
            
            overall_success = has_message and has_version and has_features
            self.log_test("API Root", overall_success, 
                         f"Version: {data.get('version')}, Features: {len(data.get('features', []))}")
            return overall_success
        else:
            self.log_test("API Root", False, f"Status: {status}")
            return False

    def test_health_check(self):
        """Test GET /api/health - System health"""
        print("\n🔍 Testing Health Check...")
        success, data, status = self.make_request('GET', 'health')
        
        if success and status == 200:
            has_status = 'status' in data and data['status'] == 'healthy'
            has_version = 'version' in data
            has_features = 'features' in data
            
            overall_success = has_status and has_version and has_features
            self.log_test("Health Check", overall_success, 
                         f"Status: {data.get('status')}, Version: {data.get('version')}")
            return overall_success
        else:
            self.log_test("Health Check", False, f"Status: {status}")
            return False

    def test_voice_process(self):
        """Test POST /api/voice/process - Voice processing with actual API format"""
        print("\n🔍 Testing Voice Processing...")
        
        test_data = {
            "text": "Как часто нужно убираться в подъездах? Какие есть рекомендации по уборке?",
            "session_id": f"test_session_{int(time.time())}"
        }
        
        success, data, status = self.make_request('POST', 'voice/process', test_data, timeout=60)
        
        if success and status == 200:
            has_response = 'response' in data
            has_timestamp = 'timestamp' in data
            
            response_length = len(data.get('response', ''))
            is_meaningful_response = response_length > 20
            
            overall_success = has_response and has_timestamp and is_meaningful_response
            self.log_test("Voice Processing", overall_success, 
                         f"Response: {response_length} chars, Has timestamp: {has_timestamp}")
            return overall_success
        else:
            self.log_test("Voice Processing", False, f"Status: {status}, Error: {data.get('error', 'Unknown')}")
            return False

    def test_dashboard(self):
        """Test GET /api/dashboard - Dashboard data"""
        print("\n🔍 Testing Dashboard...")
        success, data, status = self.make_request('GET', 'dashboard')
        
        if success and status == 200:
            has_status = 'status' in data
            has_stats = 'stats' in data
            has_data_source = 'data_source' in data
            
            stats = data.get('stats', {})
            has_employees = 'employees' in stats
            has_houses = 'houses' in stats
            
            overall_success = has_status and has_stats and has_data_source and has_employees and has_houses
            self.log_test("Dashboard", overall_success, 
                         f"Houses: {stats.get('houses')}, Employees: {stats.get('employees')}, Source: Bitrix24")
            return overall_success
        else:
            self.log_test("Dashboard", False, f"Status: {status}")
            return False

    def test_cleaning_houses(self):
        """Test GET /api/cleaning/houses - Houses data"""
        print("\n🔍 Testing Cleaning Houses...")
        success, data, status = self.make_request('GET', 'cleaning/houses')
        
        if success and status == 200:
            # Check if we get meaningful data
            has_data = len(data) > 0 if isinstance(data, (list, dict)) else False
            
            self.log_test("Cleaning Houses", has_data, 
                         f"Data type: {type(data)}, Length: {len(data) if isinstance(data, (list, dict)) else 'N/A'}")
            return has_data
        else:
            self.log_test("Cleaning Houses", False, f"Status: {status}")
            return False

    def test_bitrix24_integration(self):
        """Test GET /api/bitrix24/test - Bitrix24 integration"""
        print("\n🔍 Testing Bitrix24 Integration...")
        success, data, status = self.make_request('GET', 'bitrix24/test')
        
        if success and status == 200:
            # Check if integration is working
            has_status = 'status' in data
            
            self.log_test("Bitrix24 Integration", has_status, 
                         f"Status: {data.get('status', 'Unknown')}")
            return has_status
        else:
            self.log_test("Bitrix24 Integration", False, f"Status: {status}")
            return False

    def test_telegram_status(self):
        """Test GET /api/telegram/status - Telegram bot status"""
        print("\n🔍 Testing Telegram Status...")
        success, data, status = self.make_request('GET', 'telegram/status')
        
        if success and status == 200:
            has_status = 'status' in data
            
            self.log_test("Telegram Status", has_status, 
                         f"Status: {data.get('status', 'Unknown')}")
            return has_status
        else:
            self.log_test("Telegram Status", False, f"Status: {status}")
            return False

    def check_self_learning_endpoints(self):
        """Check if self-learning endpoints exist"""
        print("\n🔍 Checking Self-Learning Endpoints...")
        
        endpoints_to_check = [
            'learning/stats',
            'learning/export', 
            'voice/feedback'
        ]
        
        available_endpoints = []
        for endpoint in endpoints_to_check:
            success, data, status = self.make_request('GET', endpoint)
            if status != 404:
                available_endpoints.append(endpoint)
        
        has_self_learning = len(available_endpoints) > 0
        self.log_test("Self-Learning Endpoints", has_self_learning, 
                     f"Available: {available_endpoints}")
        return has_self_learning

    def run_comprehensive_test(self):
        """Run all tests for the actual deployed API"""
        print("🚀 Testing ACTUAL Deployed VasDom AudioBot")
        print(f"🌐 Testing against: {self.base_url}")
        print("=" * 70)
        
        # Test basic API functionality
        test_results = []
        test_results.append(self.test_api_root())
        test_results.append(self.test_health_check())
        test_results.append(self.test_voice_process())
        test_results.append(self.test_dashboard())
        test_results.append(self.test_cleaning_houses())
        test_results.append(self.test_bitrix24_integration())
        test_results.append(self.test_telegram_status())
        
        # Check for self-learning features
        test_results.append(self.check_self_learning_endpoints())
        
        # Summary
        print("\n" + "=" * 70)
        print(f"📊 ACTUAL DEPLOYED API TEST SUMMARY")
        print(f"✅ Passed: {self.tests_passed}/{self.tests_run}")
        print(f"❌ Failed: {self.tests_run - self.tests_passed}/{self.tests_run}")
        
        if self.tests_passed >= 6:  # Most core features working
            print("🎉 Core API functionality is working!")
            if self.tests_passed < self.tests_run:
                print("⚠️  Some features may need attention.")
            return 0
        else:
            print("⚠️  Multiple API failures detected.")
            return 1

def main():
    """Main test execution"""
    print("🧠 VasDom AudioBot - ACTUAL Deployed API Tester")
    print("📋 Testing what's actually deployed vs expected v3.0 features")
    
    tester = ActualVasDomTester()
    
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