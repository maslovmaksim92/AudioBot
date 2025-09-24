#!/usr/bin/env python3
"""
VasDom AudioBot Backend API Testing - LiveKit SIP Smoke Tests
Testing backend smoke tests after removing emergentintegrations to resolve OpenAI conflicts:

1) GET /api/health -> expect 200
2) POST /api/realtime/sessions -> expect 200 on Render (OPENAI_API_KEY present) or 500 locally
3) POST /api/voice/call/start with {"phone_number":"+79001234567"} -> on Render expect 200 or detailed 4xx/5xx if LiveKit rejects; ensure no 'LiveKit not configured'
4) GET /api/voice/call/{fake}/status -> 404

Base URL: use REACT_APP_BACKEND_URL and /api prefix
"""

import requests
import sys
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional

class LiveKitSIPTester:
    def __init__(self, base_url=None):
        # Use REACT_APP_BACKEND_URL from frontend/.env
        if base_url is None:
            try:
                with open('/app/frontend/.env', 'r') as f:
                    for line in f:
                        if line.startswith('REACT_APP_BACKEND_URL='):
                            base_url = line.split('=', 1)[1].strip()
                            break
                if not base_url:
                    base_url = "https://audiobot-suite.preview.emergentagent.com"
            except:
                base_url = "https://audiobot-suite.preview.emergentagent.com"
        
        self.base_url = base_url.rstrip('/')
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []

    def log_test(self, name: str, success: bool, details: str = ""):
        """Log test result"""
        self.tests_run += 1
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"\n{status} - {name}")
        if details:
            print(f"   Details: {details}")
        
        if success:
            self.tests_passed += 1
        else:
            self.failed_tests.append({"name": name, "details": details})

    def make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, params: Optional[Dict] = None) -> tuple:
        """Make HTTP request and return (success, response_data, status_code)"""
        url = f"{self.base_url}{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=30)
            else:
                return False, {}, 0
            
            # Try to parse JSON response, but handle non-JSON responses
            try:
                response_data = response.json() if response.content else {}
            except:
                # If JSON parsing fails, return the text content
                response_data = {"error": "Non-JSON response", "content": response.text[:500]}
                
            return True, response_data, response.status_code
            
        except requests.exceptions.Timeout:
            return False, {"error": "Request timeout"}, 0
        except requests.exceptions.ConnectionError:
            return False, {"error": "Connection error"}, 0
        except Exception as e:
            return False, {"error": str(e)}, 0

    def test_livekit_sip_smoke_tests(self):
        """Run LiveKit SIP smoke tests as per review request"""
        print(f"🚀 VasDom AudioBot Backend API - LiveKit SIP Smoke Tests")
        print(f"📍 Base URL: {self.base_url}")
        print("🔧 Testing LiveKit SIP endpoints per review request:")
        print("1) GET /api/health -> expect 200")
        print("2) POST /api/realtime/sessions -> expect 200 on Render (OPENAI_API_KEY present) or 500 locally")
        print("3) POST /api/voice/call/start with {\"phone_number\":\"+79001234567\"} -> on Render expect 200 or detailed 4xx/5xx if LiveKit rejects; ensure no 'LiveKit not configured'")
        print("4) GET /api/voice/call/{fake}/status -> 404")
        print("=" * 80)
        
        # Test 1: GET /api/health
        self.test_health_endpoint()
        
        # Test 2: POST /api/realtime/sessions
        self.test_realtime_sessions()
        
        # Test 3: POST /api/voice/call/start
        self.test_voice_call_start()
        
        # Test 4: GET /api/voice/call/{fake}/status
        self.test_voice_call_status_fake()
        
        # Final summary
        self.print_summary()

    def test_health_endpoint(self):
        """Test 1: GET /api/health - expect 200"""
        print("\n1️⃣ Testing GET /api/health")
        print("   Expected: 200")
        
        success, data, status = self.make_request('GET', '/api/health')
        
        if success and status == 200:
            print(f"   ✅ Status: {status} ✓")
            print(f"   Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            # Check for ok field
            ok = data.get('ok')
            
            if ok is True:
                self.log_test("Health Endpoint", True, "✅ Status 200 ✓, JSON response with ok:true ✓")
            else:
                self.log_test("Health Endpoint", True, f"✅ Status 200 ✓, JSON response (ok={ok})")
        else:
            print(f"   ❌ Status: {status}")
            print(f"   Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
            self.log_test("Health Endpoint", False, f"❌ Status: {status} (expected 200), Data: {data}")

    def test_realtime_sessions(self):
        """Test 2: POST /api/realtime/sessions - expect 200 on Render (OPENAI_API_KEY present) or 500 locally"""
        print("\n2️⃣ Testing POST /api/realtime/sessions")
        print("   Expected: 200 on Render (OPENAI_API_KEY present) or 500 locally")
        
        request_data = {"voice": "marin"}
        
        success, data, status = self.make_request('POST', '/api/realtime/sessions', request_data)
        
        if success and status == 200:
            print(f"   ✅ Status: {status} ✓ (OPENAI_API_KEY present)")
            print(f"   Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            # Check required fields: client_secret, model, voice, expires_at
            client_secret = data.get('client_secret')
            model = data.get('model')
            voice = data.get('voice')
            expires_at = data.get('expires_at')
            
            schema_ok = all([client_secret, model, voice, expires_at])
            
            if schema_ok:
                self.log_test("Realtime Sessions - Success", True, 
                            f"✅ Status 200 ✓, schema keys present: client_secret, model, voice, expires_at ✓")
            else:
                missing_keys = []
                if not client_secret:
                    missing_keys.append("client_secret")
                if not model:
                    missing_keys.append("model")
                if not voice:
                    missing_keys.append("voice")
                if not expires_at:
                    missing_keys.append("expires_at")
                self.log_test("Realtime Sessions - Success", False, 
                            f"❌ Status 200 ✓, но отсутствуют ключи схемы: {missing_keys}")
                
        elif success and status == 500:
            print(f"   ✅ Status: {status} ✓ (OPENAI_API_KEY missing - expected locally)")
            print(f"   Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            detail = data.get('detail', '')
            
            # Check if detail mentions OPENAI_API_KEY
            if 'OPENAI_API_KEY' in detail:
                self.log_test("Realtime Sessions - Config Error", True, 
                            f"✅ Status 500 ✓ с detail о OPENAI_API_KEY: '{detail}' ✓")
            else:
                self.log_test("Realtime Sessions - Config Error", True, 
                            f"✅ Status 500 ✓ (expected when OPENAI_API_KEY missing), detail: '{detail}'")
                
        else:
            print(f"   ❌ Status: {status}")
            print(f"   Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
            self.log_test("Realtime Sessions - Unexpected", False, 
                        f"❌ Status: {status} (expected 200 or 500), Data: {data}")

    def test_voice_call_start(self):
        """Test 3: POST /api/voice/call/start with {"phone_number":"+79001234567"} - expect 200 or detailed 4xx/5xx if LiveKit rejects; ensure no 'LiveKit not configured'"""
        print("\n3️⃣ Testing POST /api/voice/call/start")
        print("   Body: {\"phone_number\":\"+79001234567\"}")
        print("   Expected: on Render expect 200 or detailed 4xx/5xx if LiveKit rejects; ensure no 'LiveKit not configured'")
        
        request_data = {"phone_number": "+79001234567"}
        
        success, data, status = self.make_request('POST', '/api/voice/call/start', request_data)
        
        if success and status == 200:
            print(f"   ✅ Status: {status} ✓ (LiveKit configured and working)")
            print(f"   Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            # Check required schema keys: call_id, room_name, status
            call_id = data.get('call_id')
            room_name = data.get('room_name')
            call_status = data.get('status')
            
            schema_ok = all([call_id, room_name, call_status])
            
            if schema_ok:
                self.log_test("Voice Call Start - Success", True, 
                            f"✅ Status 200 ✓, schema keys present: call_id, room_name, status ✓")
                self.log_test("Voice Call Start - Response Details", True, 
                            f"✅ call_id: {call_id[:8] if call_id else 'None'}..., room_name: {room_name}, status: {call_status}")
            else:
                missing_keys = []
                if not call_id:
                    missing_keys.append("call_id")
                if not room_name:
                    missing_keys.append("room_name")
                if not call_status:
                    missing_keys.append("status")
                self.log_test("Voice Call Start - Success", False, 
                            f"❌ Status 200 ✓, но отсутствуют ключи схемы: {missing_keys}")
                
        elif success and status == 500:
            print(f"   Status: {status} (Internal Server Error)")
            print(f"   Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            detail = data.get('detail', '')
            
            # Check if detail mentions LiveKit configuration - this should NOT happen per review request
            if 'LiveKit not configured' in detail:
                self.log_test("Voice Call Start - Config Error", False, 
                            f"❌ Status 500 с 'LiveKit not configured' - это не должно происходить после удаления emergentintegrations: '{detail}'")
            elif 'LiveKit' in detail or 'LIVEKIT' in detail:
                self.log_test("Voice Call Start - LiveKit Error", True, 
                            f"✅ Status 500 ✓ с detailed LiveKit error (не 'LiveKit not configured'): '{detail}' ✓")
            else:
                self.log_test("Voice Call Start - Other Error", True, 
                            f"✅ Status 500 ✓ с detailed error: '{detail}' ✓")
                
        elif success and (400 <= status < 600):
            print(f"   Status: {status} (Client/Server Error)")
            print(f"   Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            detail = data.get('detail', '')
            
            # Detailed 4xx/5xx errors are acceptable per review request
            self.log_test("Voice Call Start - Detailed Error", True, 
                        f"✅ Status {status} ✓ с detailed error response: '{detail}' ✓")
                
        else:
            print(f"   ❌ Status: {status}")
            print(f"   Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
            self.log_test("Voice Call Start - Unexpected Response", False, 
                        f"❌ Status: {status} (expected 200, 4xx, or 5xx), Data: {data}")

    def test_voice_call_status_fake(self):
        """Test 4: GET /api/voice/call/{fake}/status - expect 404"""
        print("\n4️⃣ Testing GET /api/voice/call/{fake}/status")
        print("   Expected: 404")
        
        fake_call_id = "fake-call-id-12345"
        
        success, data, status = self.make_request('GET', f'/api/voice/call/{fake_call_id}/status')
        
        if success and status == 404:
            print(f"   ✅ Status: {status} ✓")
            print(f"   Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            detail = data.get('detail', '')
            
            if 'Call not found' in detail or 'not found' in detail.lower():
                self.log_test("Voice Call Status - Fake ID", True, 
                            f"✅ Status 404 ✓ для несуществующего call_id с правильным сообщением: '{detail}' ✓")
            else:
                self.log_test("Voice Call Status - Fake ID", True, 
                            f"✅ Status 404 ✓ для несуществующего call_id (detail: '{detail}')")
        else:
            print(f"   ❌ Status: {status}")
            print(f"   Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
            self.log_test("Voice Call Status - Fake ID", False, 
                        f"❌ Status: {status} (expected 404), Data: {data}")

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 80)
        print("🎯 LIVEKIT SIP SMOKE TESTS SUMMARY")
        print("=" * 80)
        print(f"Total Tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {len(self.failed_tests)}")
        
        if self.tests_run > 0:
            success_rate = (self.tests_passed / self.tests_run) * 100
            print(f"Success Rate: {success_rate:.1f}%")
        
        if self.failed_tests:
            print(f"\n❌ FAILED TESTS ({len(self.failed_tests)}):")
            for i, test in enumerate(self.failed_tests, 1):
                print(f"{i}. {test['name']}")
                if test['details']:
                    print(f"   {test['details']}")
        else:
            print(f"\n🎉 ALL TESTS PASSED!")
        
        print("\n" + "=" * 80)

def main():
    """Main function to run the tests"""
    print("Starting LiveKit SIP Smoke Tests...")
    
    tester = LiveKitSIPTester()
    tester.test_livekit_sip_smoke_tests()
    
    # Return exit code based on test results
    if tester.failed_tests:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()