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
    def __init__(self, base_url="http://localhost:8001"):
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
    
    def make_request(self, method: str, endpoint: str, data: Dict = None, timeout: int = 30, endpoint_override: str = None) -> tuple:
        """Make HTTP request and return (success, response_data, status_code)"""
        if endpoint_override:
            url = endpoint_override
        else:
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
        """Test POST /api/voice/process - Main self-learning AI chat functionality"""
        print("\n🔍 Testing Voice Processing (Self-Learning AI Chat)...")
        
        test_message = "Как часто нужно убираться в офисе? Какие есть рекомендации?"
        test_data = {
            "message": test_message,
            "session_id": self.session_id
        }
        
        success, data, status = self.make_request('POST', 'voice/process', test_data, timeout=60)
        
        if success and status == 200:
            required_fields = ['response', 'log_id', 'session_id', 'model_used', 'response_time', 'similar_found', 'learning_improved']
            has_required = all(field in data for field in required_fields)
            
            # Store log_id for feedback testing
            if 'log_id' in data:
                self.test_log_id = data['log_id']
            
            response_length = len(data.get('response', ''))
            is_meaningful_response = response_length > 20  # Should be a substantial response
            similar_found = data.get('similar_found', 0)
            learning_improved = data.get('learning_improved', False)
            
            overall_success = has_required and is_meaningful_response
            self.log_test("Voice Processing (Self-Learning)", overall_success, 
                         f"Response: {response_length} chars, Similar found: {similar_found}, Learning improved: {learning_improved}, Model: {data.get('model_used')}")
            return overall_success
        else:
            self.log_test("Voice Processing (Self-Learning)", False, f"Status: {status}, Error: {data.get('error', 'Unknown')}")
            return False

    def test_voice_feedback(self):
        """Test POST /api/voice/feedback - Rating system for learning improvement"""
        print("\n🔍 Testing Voice Feedback System (Learning Ratings)...")
        
        if not self.test_log_id:
            self.log_test("Voice Feedback", False, "No log_id available from previous test")
            return False
        
        feedback_data = {
            "log_id": self.test_log_id,
            "rating": 5,
            "feedback_text": "Отличный ответ! Очень полезная информация для клининговой компании."
        }
        
        success, data, status = self.make_request('POST', 'voice/feedback', feedback_data)
        
        if success and status == 200:
            has_success_field = 'success' in data
            is_successful = data.get('success', False)
            has_message = 'message' in data
            will_be_used = data.get('will_be_used_for_training', False)
            
            overall_success = has_success_field and is_successful and has_message
            self.log_test("Voice Feedback (Learning Ratings)", overall_success, 
                         f"Success: {is_successful}, Will train: {will_be_used}, Message: {data.get('message', '')[:50]}...")
            return overall_success
        else:
            self.log_test("Voice Feedback (Learning Ratings)", False, f"Status: {status}")
            return False

    def test_learning_stats(self):
        """Test GET /api/learning/stats - Live learning statistics"""
        print("\n🔍 Testing Learning Statistics (Real-time Metrics)...")
        success, data, status = self.make_request('GET', 'learning/stats')
        
        if success and status == 200:
            required_fields = ['total_interactions', 'positive_ratings', 'negative_ratings', 'improvement_rate']
            has_required = all(field in data for field in required_fields)
            
            # Check if we have meaningful data
            total_interactions = data.get('total_interactions', 0)
            avg_rating = data.get('avg_rating')
            improvement_rate = data.get('improvement_rate', 0)
            
            overall_success = has_required and isinstance(total_interactions, int)
            self.log_test("Learning Statistics", overall_success, 
                         f"Interactions: {total_interactions}, Avg rating: {avg_rating}, Improvement: {improvement_rate:.2f}")
            return overall_success
        else:
            self.log_test("Learning Statistics", False, f"Status: {status}")
            return False

    def test_learning_export(self):
        """Test GET /api/learning/export - Export quality data for fine-tuning"""
        print("\n🔍 Testing Learning Data Export (Quality Data)...")
        success, data, status = self.make_request('GET', 'learning/export')
        
        if success and status == 200:
            required_fields = ['total_exported', 'min_rating_used', 'data', 'export_timestamp']
            has_required = all(field in data for field in required_fields)
            
            exported_data = data.get('data', [])
            total_exported = data.get('total_exported', 0)
            min_rating = data.get('min_rating_used', 0)
            
            # Check data format for fine-tuning
            is_valid_format = True
            if exported_data and len(exported_data) > 0:
                sample = exported_data[0]
                is_valid_format = 'messages' in sample and 'metadata' in sample
            
            overall_success = has_required and is_valid_format
            self.log_test("Learning Data Export", overall_success, 
                         f"Exported: {total_exported} conversations, Min rating: {min_rating}, Valid format: {is_valid_format}")
            return overall_success
        else:
            self.log_test("Learning Data Export", False, f"Status: {status}")
            return False

    def test_similar_conversations(self):
        """Test GET /api/learning/similar/{log_id} - Similar conversations search"""
        print("\n🔍 Testing Similar Conversations Search...")
        
        if not self.test_log_id:
            self.log_test("Similar Conversations", False, "No log_id available from previous test")
            return False
        
        success, data, status = self.make_request('GET', f'learning/similar/{self.test_log_id}?limit=3')
        
        if success and status == 200:
            required_fields = ['original_message', 'found_similar', 'similar_conversations']
            has_required = all(field in data for field in required_fields)
            
            original_message = data.get('original_message', '')
            found_similar = data.get('found_similar', 0)
            similar_conversations = data.get('similar_conversations', [])
            
            # Validate structure of similar conversations
            is_valid_structure = True
            if similar_conversations and len(similar_conversations) > 0:
                sample = similar_conversations[0]
                expected_fields = ['log_id', 'user_message', 'ai_response', 'rating', 'timestamp']
                is_valid_structure = all(field in sample for field in expected_fields)
            
            overall_success = has_required and isinstance(found_similar, int)
            self.log_test("Similar Conversations Search", overall_success, 
                         f"Original: '{original_message[:30]}...', Found: {found_similar}, Valid structure: {is_valid_structure}")
            return overall_success
        else:
            self.log_test("Similar Conversations Search", False, f"Status: {status}")
            return False

    def test_additional_endpoints(self):
        """Test additional compatibility endpoints"""
        print("\n🔍 Testing Additional Compatibility Endpoints...")
        
        # Test API root
        success1, data1, status1 = self.make_request('GET', '')
        api_root_ok = success1 and status1 == 200 and 'message' in data1
        
        # Test dashboard
        success2, data2, status2 = self.make_request('GET', 'dashboard')
        dashboard_ok = success2 and status2 == 200 and 'company' in data2
        
        # Test houses
        success3, data3, status3 = self.make_request('GET', 'cleaning/houses')
        houses_ok = success3 and status3 == 200 and 'total' in data3
        
        overall_success = api_root_ok and dashboard_ok and houses_ok
        self.log_test("Additional Compatibility Endpoints", overall_success, 
                     f"API root: {api_root_ok}, Dashboard: {dashboard_ok}, Houses: {houses_ok}")
        return overall_success

    def run_comprehensive_test(self):
        """Run all tests in sequence for VasDom AudioBot v3.0"""
        print("🚀 Starting Comprehensive VasDom AudioBot v3.0 Testing")
        print("🧠 Testing MAXIMUM SELF-LEARNING AI SYSTEM")
        print(f"🌐 Testing against: {self.base_url}")
        print("=" * 70)
        
        # Test sequence - order matters for some tests
        test_results = []
        
        # Basic connectivity and system info
        test_results.append(self.test_root_endpoint())
        test_results.append(self.test_health_check())
        
        # 🧠 CORE SELF-LEARNING FUNCTIONALITY
        print("\n" + "🧠 TESTING SELF-LEARNING AI FEATURES" + "🧠")
        print("-" * 50)
        
        # Main AI chat with self-learning (this sets test_log_id)
        test_results.append(self.test_voice_process())
        
        # Rating system for learning improvement (depends on test_log_id)
        test_results.append(self.test_voice_feedback())
        
        # Live learning statistics
        test_results.append(self.test_learning_stats())
        
        # Export quality data for fine-tuning
        test_results.append(self.test_learning_export())
        
        # Similar conversations search (depends on test_log_id)
        test_results.append(self.test_similar_conversations())
        
        # Additional compatibility endpoints
        test_results.append(self.test_additional_endpoints())
        
        # Summary
        print("\n" + "=" * 70)
        print(f"📊 VASDOM AUDIOBOT v3.0 TEST SUMMARY")
        print(f"✅ Passed: {self.tests_passed}/{self.tests_run}")
        print(f"❌ Failed: {self.tests_run - self.tests_passed}/{self.tests_run}")
        
        if self.tests_passed == self.tests_run:
            print("🎉 ALL TESTS PASSED! VasDom AudioBot v3.0 Self-Learning AI is working correctly!")
            print("🧠 The AI should be learning and improving with each interaction!")
            return 0
        else:
            print("⚠️  Some tests failed. Check the details above.")
            print("🔧 The self-learning system may need attention.")
            return 1

def main():
    """Main test execution for VasDom AudioBot v3.0"""
    print("🧠 VasDom AudioBot v3.0 Backend API Tester")
    print("🚀 Testing MAXIMUM SELF-LEARNING AI SYSTEM")
    print("📋 Testing all revolutionary self-learning features:")
    print("   • Continuous learning on every dialog")
    print("   • Smart data filtering with ratings")
    print("   • Real-time learning statistics")
    print("   • Quality data export for fine-tuning")
    print("   • Similar conversation search")
    
    # Use the public URL from frontend/.env
    tester = VasDomAudioBotTester("https://smart-audiobot.preview.emergentagent.com")
    
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