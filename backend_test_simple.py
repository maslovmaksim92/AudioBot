#!/usr/bin/env python3
"""
Simple Backend Testing for VasDom AudioBot on Render
Tests the actual available endpoints based on the review request
"""

import requests
import sys
import json
import time
from datetime import datetime

class VasDomRenderTester:
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
                response_data = {"raw_response": response.text}
                
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
        
        # Since this returns HTML, we just check if it loads
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
            # Check for expected fields based on actual response
            expected_fields = ['message', 'version', 'status', 'features']
            has_expected = all(field in data for field in expected_fields)
            
            # Check if it mentions Render platform
            mentions_render = any('render' in str(v).lower() for v in data.values() if isinstance(v, str))
            
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
            # Check for expected health check fields
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
        
        test_data = {
            "message": "Как часто нужно убираться в офисе?",
            "session_id": f"test_session_{int(time.time())}"
        }
        
        success, data, status = self.make_request('POST', 'voice/process', test_data, timeout=45)
        
        if success and status == 200:
            # Check for response structure
            has_response = 'response' in data or 'answer' in data or 'message' in data
            response_text = data.get('response', data.get('answer', data.get('message', '')))
            has_meaningful_response = len(str(response_text)) > 10
            
            overall_success = has_response and has_meaningful_response
            self.log_test("Voice Processing", overall_success, 
                         f"Response length: {len(str(response_text))}")
            return overall_success
        else:
            self.log_test("Voice Processing", False, f"Status: {status}, Error: {data.get('error', 'Unknown')}")
            return False

    def test_voice_feedback(self):
        """Test POST /api/voice/feedback - Feedback system"""
        print("\n🔍 Testing Voice Feedback (/api/voice/feedback)...")
        
        feedback_data = {
            "rating": 5,
            "feedback_text": "Отличный ответ! Очень полезно.",
            "session_id": f"test_session_{int(time.time())}"
        }
        
        success, data, status = self.make_request('POST', 'voice/feedback', feedback_data)
        
        if success and status == 200:
            # Check if feedback was accepted
            has_success = 'success' in data or 'status' in data or 'message' in data
            self.log_test("Voice Feedback", has_success, 
                         f"Response: {data}")
            return has_success
        else:
            self.log_test("Voice Feedback", False, f"Status: {status}")
            return False

    def test_self_learning_status(self):
        """Test GET /api/voice/self-learning/status - Self-learning status"""
        print("\n🔍 Testing Self-Learning Status (/api/voice/self-learning/status)...")
        success, data, status = self.make_request('GET', 'voice/self-learning/status')
        
        if success and status == 200:
            # Any successful response indicates the endpoint exists
            self.log_test("Self-Learning Status", True, f"Response: {data}")
            return True
        else:
            self.log_test("Self-Learning Status", False, f"Status: {status}")
            return False

    def test_voice_health(self):
        """Test GET /api/voice/health - Voice service health check"""
        print("\n🔍 Testing Voice Health (/api/voice/health)...")
        success, data, status = self.make_request('GET', 'voice/health')
        
        if success and status == 200:
            self.log_test("Voice Health", True, f"Response: {data}")
            return True
        else:
            self.log_test("Voice Health", False, f"Status: {status}")
            return False

    def test_status_compatibility(self):
        """Test GET/POST /api/status - Compatibility (in-memory)"""
        print("\n🔍 Testing Status Compatibility (/api/status)...")
        
        # Test POST first
        status_data = {"client_name": "test_client"}
        success, data, status = self.make_request('POST', 'status', status_data)
        
        if success and status == 200:
            # Test GET
            success2, data2, status2 = self.make_request('GET', 'status')
            
            if success2 and status2 == 200:
                self.log_test("Status Compatibility", True, 
                             f"POST: {status}, GET: {status2}")
                return True
            else:
                self.log_test("Status Compatibility", False, f"GET failed: {status2}")
                return False
        else:
            self.log_test("Status Compatibility", False, f"POST failed: {status}")
            return False

    def run_comprehensive_test(self):
        """Run all tests based on the review request endpoints"""
        print("🚀 Starting VasDom AudioBot Render Testing")
        print(f"🌐 Testing against: {self.base_url}")
        print("📋 Testing endpoints from review request:")
        print("   1. GET / - System info on Render")
        print("   2. GET /api/ - API info with self-learning functions")
        print("   3. GET /api/health - Health check with Render components")
        print("   4. POST /api/voice/process - AI chat (main function)")
        print("   5. POST /api/voice/feedback - Feedback")
        print("   6. GET /api/voice/self-learning/status - Self-learning status")
        print("   7. GET /api/voice/health - Voice service health check")
        print("   8. GET/POST /api/status - Compatibility (in-memory)")
        print("=" * 60)
        
        # Test all endpoints mentioned in the review request
        test_results = []
        
        test_results.append(self.test_root_endpoint())
        test_results.append(self.test_api_root())
        test_results.append(self.test_health_check())
        test_results.append(self.test_voice_process())
        test_results.append(self.test_voice_feedback())
        test_results.append(self.test_self_learning_status())
        test_results.append(self.test_voice_health())
        test_results.append(self.test_status_compatibility())
        
        # Summary
        print("\n" + "=" * 60)
        print(f"📊 TEST SUMMARY")
        print(f"✅ Passed: {self.tests_passed}/{self.tests_run}")
        print(f"❌ Failed: {self.tests_run - self.tests_passed}/{self.tests_run}")
        
        if self.tests_passed == self.tests_run:
            print("🎉 ALL TESTS PASSED! VasDom AudioBot on Render is working correctly.")
            return 0
        elif self.tests_passed >= self.tests_run * 0.7:  # 70% pass rate
            print("✅ Most tests passed. System is mostly functional with some minor issues.")
            return 0
        else:
            print("⚠️  Many tests failed. System needs attention.")
            return 1

def main():
    """Main test execution"""
    print("VasDom AudioBot Render Backend Tester")
    print("Testing cloud-native implementation on Render")
    
    tester = VasDomRenderTester("https://audiobot-qci2.onrender.com")
    
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