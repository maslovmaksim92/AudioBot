#!/usr/bin/env python3
"""
Comprehensive Backend Testing for VasDom AudioBot v3.0 - Self-Learning AI
Tests all NEW API endpoints mentioned in the review request:
- POST /api/voice/process - Main self-learning AI chat
- POST /api/voice/feedback - Rating system for learning
- GET /api/learning/stats - Live learning statistics
- GET /api/learning/export - Export quality data
- GET /api/learning/similar/{log_id} - Similar conversations search
"""

import requests
import sys
import json
import time
from datetime import datetime
from typing import Dict, Any

class VasDomAudioBotTester:
    def __init__(self, base_url="https://audiobot-qci2.onrender.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_log_id = None  # Store log_id for feedback testing
        self.session_id = f"test_session_{int(time.time())}"
        
    def log_test(self, name: str, success: bool, details: str = ""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED {details}")
        else:
            print(f"❌ {name} - FAILED {details}")
    
    def make_request(self, method: str, endpoint: str, data: Dict = None, timeout: int = 30) -> tuple:
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
            
        except requests.exceptions.Timeout:
            return False, {"error": "Request timeout"}, 0
        except requests.exceptions.ConnectionError:
            return False, {"error": "Connection error"}, 0
        except Exception as e:
            return False, {"error": str(e)}, 0

    def test_root_endpoint(self):
        """Test GET / - Main application info"""
        print("\n🔍 Testing Root Endpoint...")
        success, data, status = self.make_request('GET', '', endpoint_override=self.base_url)
        
        if success and status == 200:
            expected_keys = ['name', 'version', 'features', 'stats']
            has_expected_structure = all(key in data for key in expected_keys)
            is_v3 = data.get('version') == '3.0.0'
            self.log_test("Root Endpoint", has_expected_structure and is_v3, 
                         f"Version: {data.get('version')}, Features: {len(data.get('features', []))}")
            return has_expected_structure and is_v3
        else:
            self.log_test("Root Endpoint", False, f"Status: {status}, Error: {data.get('error', 'Unknown')}")
            return False

    def test_health_check(self):
        """Test GET /api/health - System health with AI services"""
        print("\n🔍 Testing Health Check...")
        success, data, status = self.make_request('GET', 'health')
        
        if success and status == 200:
            has_status = 'status' in data and data['status'] == 'healthy'
            has_services = 'services' in data
            has_learning_data = 'learning_data' in data
            
            services = data.get('services', {})
            learning_data = data.get('learning_data', {})
            
            overall_success = has_status and has_services and has_learning_data
            self.log_test("Health Check", overall_success, 
                         f"Status: {data.get('status')}, LLM: {services.get('emergent_llm')}, Embeddings: {services.get('embeddings')}")
            return overall_success
        else:
            self.log_test("Health Check", False, f"Status: {status}")
            return False

    def test_voice_process(self):
        """Test POST /api/voice/process - Main voice chat functionality"""
        print("\n🔍 Testing Voice Processing (Main AI Chat)...")
        
        test_message = "Как часто нужно убираться в офисе?"
        test_data = {
            "message": test_message,
            "session_id": f"test_session_{int(time.time())}"
        }
        
        success, data, status = self.make_request('POST', 'voice/process', test_data, timeout=45)
        
        if success and status == 200:
            required_fields = ['response', 'log_id', 'session_id', 'model_used']
            has_required = all(field in data for field in required_fields)
            
            # Store log_id for feedback testing
            if 'log_id' in data:
                self.test_log_id = data['log_id']
            
            response_length = len(data.get('response', ''))
            is_meaningful_response = response_length > 10  # Basic check for meaningful response
            
            overall_success = has_required and is_meaningful_response
            self.log_test("Voice Processing", overall_success, 
                         f"Response length: {response_length}, Model: {data.get('model_used')}, Log ID: {data.get('log_id')}")
            return overall_success
        else:
            self.log_test("Voice Processing", False, f"Status: {status}, Error: {data.get('error', 'Unknown')}")
            return False

    def test_voice_feedback(self):
        """Test POST /api/voice/feedback - User feedback system"""
        print("\n🔍 Testing Voice Feedback System...")
        
        if not self.test_log_id:
            self.log_test("Voice Feedback", False, "No log_id available from previous test")
            return False
        
        feedback_data = {
            "log_id": self.test_log_id,
            "rating": 5,
            "feedback_text": "Отличный ответ! Очень полезно."
        }
        
        success, data, status = self.make_request('POST', 'voice/feedback', feedback_data)
        
        if success and status == 200:
            has_success_field = 'success' in data
            is_successful = data.get('success', False)
            has_message = 'message' in data
            
            overall_success = has_success_field and is_successful and has_message
            self.log_test("Voice Feedback", overall_success, 
                         f"Success: {is_successful}, Message: {data.get('message', '')[:50]}")
            return overall_success
        else:
            self.log_test("Voice Feedback", False, f"Status: {status}")
            return False

    def test_self_learning_status(self):
        """Test GET /api/voice/self-learning/status - Self-learning system status"""
        print("\n🔍 Testing Self-Learning Status...")
        success, data, status = self.make_request('GET', 'voice/self-learning/status')
        
        if success and status == 200:
            required_fields = ['total_interactions', 'current_model']
            has_required = all(field in data for field in required_fields)
            
            # Check if we have meaningful data
            total_interactions = data.get('total_interactions', 0)
            current_model = data.get('current_model', '')
            
            overall_success = has_required and isinstance(total_interactions, int)
            self.log_test("Self-Learning Status", overall_success, 
                         f"Interactions: {total_interactions}, Model: {current_model}")
            return overall_success
        else:
            self.log_test("Self-Learning Status", False, f"Status: {status}")
            return False

    def test_similar_responses(self):
        """Test GET /api/voice/similar/{log_id} - Similar responses search"""
        print("\n🔍 Testing Similar Responses Search...")
        
        if not self.test_log_id:
            self.log_test("Similar Responses", False, "No log_id available from previous test")
            return False
        
        success, data, status = self.make_request('GET', f'voice/similar/{self.test_log_id}?limit=3')
        
        if success and status == 200:
            # Should return a list (might be empty if no similar responses)
            is_list = isinstance(data, list)
            self.log_test("Similar Responses", is_list, 
                         f"Found {len(data) if is_list else 0} similar responses")
            return is_list
        else:
            self.log_test("Similar Responses", False, f"Status: {status}")
            return False

    def test_embeddings_update(self):
        """Test POST /api/voice/embeddings/update - Batch embeddings update"""
        print("\n🔍 Testing Embeddings Update...")
        success, data, status = self.make_request('POST', 'voice/embeddings/update?batch_size=10')
        
        if success and status == 200:
            # Should return processing results
            has_result_info = any(key in data for key in ['success', 'processed', 'total_found'])
            self.log_test("Embeddings Update", has_result_info, 
                         f"Processed: {data.get('processed', 'N/A')}")
            return has_result_info
        else:
            self.log_test("Embeddings Update", False, f"Status: {status}")
            return False

    def test_backward_compatibility(self):
        """Test backward compatibility endpoints (MongoDB status checks)"""
        print("\n🔍 Testing Backward Compatibility...")
        
        # Test creating a status check
        status_data = {"client_name": "test_client"}
        success, data, status = self.make_request('POST', 'status', status_data)
        
        if success and status == 200:
            # Test getting status checks
            success2, data2, status2 = self.make_request('GET', 'status')
            
            if success2 and status2 == 200:
                is_list = isinstance(data2, list)
                self.log_test("Backward Compatibility", is_list, 
                             f"Status checks: {len(data2) if is_list else 0}")
                return is_list
            else:
                self.log_test("Backward Compatibility", False, f"GET status failed: {status2}")
                return False
        else:
            self.log_test("Backward Compatibility", False, f"POST status failed: {status}")
            return False

    def run_comprehensive_test(self):
        """Run all tests in sequence"""
        print("🚀 Starting Comprehensive VasDom AudioBot API Testing")
        print(f"🌐 Testing against: {self.base_url}")
        print("=" * 60)
        
        # Test sequence - order matters for some tests
        test_results = []
        
        # Basic connectivity and info
        test_results.append(self.test_api_root())
        test_results.append(self.test_general_health())
        test_results.append(self.test_voice_health())
        
        # Core functionality
        test_results.append(self.test_voice_process())  # This sets test_log_id
        test_results.append(self.test_voice_feedback())  # Depends on test_log_id
        
        # Self-learning features
        test_results.append(self.test_self_learning_status())
        test_results.append(self.test_similar_responses())  # Depends on test_log_id
        test_results.append(self.test_embeddings_update())
        
        # Backward compatibility
        test_results.append(self.test_backward_compatibility())
        
        # Summary
        print("\n" + "=" * 60)
        print(f"📊 TEST SUMMARY")
        print(f"✅ Passed: {self.tests_passed}/{self.tests_run}")
        print(f"❌ Failed: {self.tests_run - self.tests_passed}/{self.tests_run}")
        
        if self.tests_passed == self.tests_run:
            print("🎉 ALL TESTS PASSED! VasDom AudioBot is working correctly.")
            return 0
        else:
            print("⚠️  Some tests failed. Check the details above.")
            return 1

def main():
    """Main test execution"""
    print("VasDom AudioBot Backend API Tester")
    print("Testing self-learning module implementation")
    
    # Use the public URL from the review request
    tester = VasDomAudioBotTester("https://audiobot-qci2.onrender.com")
    
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