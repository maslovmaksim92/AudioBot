#!/usr/bin/env python3
"""
VasDom AudioBot Backend API Testing Suite
Tests all backend endpoints systematically
"""

import requests
import json
import sys
import time
from datetime import datetime

class AudioBotAPITester:
    def __init__(self, base_url="https://audiobot-live-1.preview.emergentagent.com"):
        self.base_url = base_url
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

    def test_api_status(self):
        """Test basic API status endpoint"""
        try:
            response = requests.get(f"{self.base_url}/api/", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                expected_keys = ["message", "status"]
                has_keys = all(key in data for key in expected_keys)
                if has_keys and "VasDom AudioBot" in data.get("message", ""):
                    self.log_test("API Status Check", True)
                    print(f"   Response: {data}")
                    return True
                else:
                    self.log_test("API Status Check", False, f"Unexpected response format: {data}")
            else:
                self.log_test("API Status Check", False, f"Status code: {response.status_code}")
                
        except Exception as e:
            self.log_test("API Status Check", False, f"Exception: {str(e)}")
        
        return False

    def test_chat_message(self):
        """Test AI chat message endpoint"""
        try:
            test_message = "Привет! Как дела?"
            payload = {"message": test_message}
            
            response = requests.post(
                f"{self.base_url}/api/chat/message",
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=30  # AI responses can take time
            )
            
            if response.status_code == 200:
                data = response.json()
                if "response" in data and "message_id" in data:
                    ai_response = data["response"]
                    if ai_response and len(ai_response) > 0:
                        self.log_test("AI Chat Message", True)
                        print(f"   User: {test_message}")
                        print(f"   AI: {ai_response[:100]}...")
                        return data["message_id"]
                    else:
                        self.log_test("AI Chat Message", False, "Empty AI response")
                else:
                    self.log_test("AI Chat Message", False, f"Missing required fields in response: {data}")
            else:
                self.log_test("AI Chat Message", False, f"Status code: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_test("AI Chat Message", False, f"Exception: {str(e)}")
        
        return None

    def test_chat_history(self):
        """Test chat history retrieval"""
        try:
            response = requests.get(f"{self.base_url}/api/chat/messages", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    self.log_test("Chat History Retrieval", True)
                    print(f"   Found {len(data)} messages in history")
                    
                    # Check message structure if any messages exist
                    if len(data) > 0:
                        message = data[0]
                        required_fields = ["id", "message", "response", "timestamp"]
                        if all(field in message for field in required_fields):
                            print("   Message structure is correct")
                        else:
                            print(f"   Warning: Message missing fields: {message}")
                    
                    return True
                else:
                    self.log_test("Chat History Retrieval", False, f"Expected list, got: {type(data)}")
            else:
                self.log_test("Chat History Retrieval", False, f"Status code: {response.status_code}")
                
        except Exception as e:
            self.log_test("Chat History Retrieval", False, f"Exception: {str(e)}")
        
        return False

    def test_realtime_token(self):
        """Test OpenAI Realtime API token generation"""
        try:
            response = requests.post(
                f"{self.base_url}/api/realtime/token",
                headers={'Content-Type': 'application/json'},
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                if "token" in data and "expires_at" in data:
                    token = data["token"]
                    expires_at = data["expires_at"]
                    
                    if token and isinstance(expires_at, int):
                        self.log_test("Realtime Token Generation", True)
                        print(f"   Token length: {len(token)} characters")
                        print(f"   Expires at: {datetime.fromtimestamp(expires_at)}")
                        return token
                    else:
                        self.log_test("Realtime Token Generation", False, "Invalid token or expiry format")
                else:
                    self.log_test("Realtime Token Generation", False, f"Missing required fields: {data}")
            else:
                self.log_test("Realtime Token Generation", False, f"Status code: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_test("Realtime Token Generation", False, f"Exception: {str(e)}")
        
        return None

    def test_voice_processing(self):
        """Test voice text processing endpoint"""
        try:
            test_text = "Расскажи короткую шутку"
            payload = {"text": test_text}
            
            response = requests.post(
                f"{self.base_url}/api/voice/process",
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if "response" in data:
                    ai_response = data["response"]
                    if ai_response and len(ai_response) > 0:
                        self.log_test("Voice Processing", True)
                        print(f"   Input: {test_text}")
                        print(f"   AI Response: {ai_response[:100]}...")
                        return True
                    else:
                        self.log_test("Voice Processing", False, "Empty AI response")
                else:
                    self.log_test("Voice Processing", False, f"Missing 'response' field: {data}")
            else:
                self.log_test("Voice Processing", False, f"Status code: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_test("Voice Processing", False, f"Exception: {str(e)}")
        
        return False

    def test_status_endpoints(self):
        """Test status check endpoints"""
        try:
            # Test POST status
            test_client = f"test_client_{int(time.time())}"
            payload = {"client_name": test_client}
            
            response = requests.post(
                f"{self.base_url}/api/status",
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["id", "client_name", "timestamp"]
                if all(field in data for field in required_fields):
                    self.log_test("Status Creation", True)
                    print(f"   Created status for client: {data['client_name']}")
                    
                    # Test GET status
                    get_response = requests.get(f"{self.base_url}/api/status", timeout=10)
                    if get_response.status_code == 200:
                        status_list = get_response.json()
                        if isinstance(status_list, list):
                            self.log_test("Status Retrieval", True)
                            print(f"   Retrieved {len(status_list)} status records")
                            return True
                        else:
                            self.log_test("Status Retrieval", False, f"Expected list, got: {type(status_list)}")
                    else:
                        self.log_test("Status Retrieval", False, f"GET status code: {get_response.status_code}")
                else:
                    self.log_test("Status Creation", False, f"Missing required fields: {data}")
            else:
                self.log_test("Status Creation", False, f"Status code: {response.status_code}")
                
        except Exception as e:
            self.log_test("Status Creation", False, f"Exception: {str(e)}")
        
        return False

    def run_all_tests(self):
        """Run all backend tests"""
        print("🚀 Starting VasDom AudioBot Backend API Tests")
        print(f"🌐 Testing against: {self.base_url}")
        print("=" * 60)
        
        # Test basic connectivity first
        if not self.test_api_status():
            print("\n❌ Basic API connectivity failed. Stopping tests.")
            return False
        
        print("\n📝 Testing Core Functionality...")
        
        # Test AI chat functionality
        message_id = self.test_chat_message()
        time.sleep(1)  # Brief pause between tests
        
        self.test_chat_history()
        time.sleep(1)
        
        # Test voice functionality
        self.test_voice_processing()
        time.sleep(1)
        
        # Test realtime token generation
        self.test_realtime_token()
        time.sleep(1)
        
        # Test status endpoints
        self.test_status_endpoints()
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        print(f"✅ Tests Passed: {self.tests_passed}/{self.tests_run}")
        print(f"❌ Tests Failed: {len(self.failed_tests)}/{self.tests_run}")
        
        if self.failed_tests:
            print("\n🔍 FAILED TESTS DETAILS:")
            for i, test in enumerate(self.failed_tests, 1):
                print(f"{i}. {test['name']}: {test['details']}")
        
        success_rate = (self.tests_passed / self.tests_run) * 100 if self.tests_run > 0 else 0
        print(f"\n📈 Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 80:
            print("🎉 Backend API is functioning well!")
            return True
        else:
            print("⚠️  Backend API has significant issues that need attention.")
            return False

def main():
    """Main test execution"""
    tester = AudioBotAPITester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())