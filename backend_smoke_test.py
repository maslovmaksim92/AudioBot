#!/usr/bin/env python3
"""
VasDom AudioBot Backend Smoke Tests - Review Request
Testing backend smoke tests after latest changes to ensure backend starts and key endpoints respond correctly without crashes.

Specific tests requested:
1) GET /api/health -> expect 200 {ok:true, ts:int}
2) GET /api/voice/debug/check -> 200, JSON with flags for key presence (false in preview environment is normal)
3) POST /api/voice/ai-call with body {"phone_number":"+79001234567"} -> expect 500 with clear message (like 'LIVEKIT_URL/API_KEY/API_SECRET not configured' or 'LIVEKIT_SIP_TRUNK_ID not configured'), main thing - no exceptions and stacktrace, FastAPI response structure with detail
4) POST /api/voice/call/start with body {"phone_number":"+79001234567"} -> similar to #3, expect detailed 4xx/5xx error, but no crashes
5) POST /api/realtime/sessions with body {"voice":"marin"} -> when OPENAI_API_KEY is missing expect 500 'OPENAI_API_KEY not configured' (as before)

Base URL: use REACT_APP_BACKEND_URL from frontend/.env
"""

import requests
import sys
import json
import time
import subprocess
from datetime import datetime
from typing import Dict, Any, Optional

class BackendSmokeTestRunner:
    def __init__(self, base_url=None):
        # Use the deployed URL from frontend .env
        if base_url is None:
            try:
                with open('/app/frontend/.env', 'r') as f:
                    for line in f:
                        if line.startswith('REACT_APP_BACKEND_URL='):
                            base_url = line.split('=', 1)[1].strip()
                            break
            except:
                base_url = "https://call-bot.preview.emergentagent.com"
        
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

    def check_backend_logs(self):
        """Check backend logs for startup errors"""
        print("\n📋 Checking backend logs for startup errors...")
        try:
            # Check supervisor backend logs
            result = subprocess.run(['tail', '-n', '50', '/var/log/supervisor/backend.err.log'], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                logs = result.stdout
                if logs.strip():
                    print(f"   Backend error logs (last 50 lines):")
                    print(f"   {logs}")
                    
                    # Check for common startup errors
                    error_patterns = [
                        'SyntaxError',
                        'IndentationError', 
                        'ImportError',
                        'ModuleNotFoundError',
                        'NameError',
                        'AttributeError',
                        'TypeError',
                        'ValueError'
                    ]
                    
                    found_errors = []
                    for pattern in error_patterns:
                        if pattern in logs:
                            found_errors.append(pattern)
                    
                    if found_errors:
                        self.log_test("Backend Logs - Startup Errors", False, 
                                    f"❌ Found startup errors: {found_errors}")
                        return False
                    else:
                        self.log_test("Backend Logs - Startup Errors", True, 
                                    "✅ No critical startup errors found")
                        return True
                else:
                    self.log_test("Backend Logs - Startup Errors", True, 
                                "✅ No error logs found")
                    return True
            else:
                print(f"   ⚠️ Could not read backend logs: {result.stderr}")
                return True  # Don't fail if we can't read logs
                
        except Exception as e:
            print(f"   ⚠️ Error checking logs: {e}")
            return True  # Don't fail if we can't check logs

    def test_1_health_endpoint(self):
        """Test 1: GET /api/health -> expect 200 {ok:true, ts:int}"""
        print("\n1️⃣ Testing GET /api/health")
        print("   Expected: 200 {ok:true, ts:int}")
        
        success, data, status = self.make_request('GET', '/api/health')
        
        if success and status == 200:
            print(f"   ✅ Status: {status} ✓")
            print(f"   Response: {json.dumps(data, indent=2)}")
            
            # Check for required fields
            ok = data.get('ok')
            ts = data.get('ts')
            
            if ok is True and isinstance(ts, int):
                self.log_test("Health Endpoint", True, 
                            f"✅ Status 200 ✓, ok=true ✓, ts={ts} (int) ✓")
            else:
                issues = []
                if ok is not True:
                    issues.append(f"ok={ok} (expected true)")
                if not isinstance(ts, int):
                    issues.append(f"ts={ts} (expected int)")
                self.log_test("Health Endpoint", False, f"❌ Issues: {', '.join(issues)}")
        else:
            print(f"   ❌ Status: {status}")
            print(f"   Response: {json.dumps(data, indent=2)}")
            self.log_test("Health Endpoint", False, f"❌ Status: {status} (expected 200), Data: {data}")

    def test_2_voice_debug_check(self):
        """Test 2: GET /api/voice/debug/check -> 200, JSON with flags for key presence"""
        print("\n2️⃣ Testing GET /api/voice/debug/check")
        print("   Expected: 200, JSON with flags for key presence (false in preview environment is normal)")
        
        success, data, status = self.make_request('GET', '/api/voice/debug/check')
        
        if success and status == 200:
            print(f"   ✅ Status: {status} ✓")
            print(f"   Response: {json.dumps(data, indent=2)}")
            
            # Check for expected flag fields
            expected_flags = ['api_key_set', 'api_secret_set', 'openai_key_set', 'trunk_id_set']
            found_flags = []
            missing_flags = []
            
            for flag in expected_flags:
                if flag in data:
                    found_flags.append(f"{flag}={data[flag]}")
                else:
                    missing_flags.append(flag)
            
            if not missing_flags:
                self.log_test("Voice Debug Check", True, 
                            f"✅ Status 200 ✓, all flags present: {', '.join(found_flags)} ✓")
            else:
                self.log_test("Voice Debug Check", False, 
                            f"❌ Status 200 ✓, but missing flags: {missing_flags}")
        else:
            print(f"   ❌ Status: {status}")
            print(f"   Response: {json.dumps(data, indent=2)}")
            self.log_test("Voice Debug Check", False, f"❌ Status: {status} (expected 200), Data: {data}")

    def test_3_voice_ai_call(self):
        """Test 3: POST /api/voice/ai-call -> expect 500 with clear message, no exceptions/stacktrace"""
        print("\n3️⃣ Testing POST /api/voice/ai-call")
        print("   Body: {\"phone_number\":\"+79001234567\"}")
        print("   Expected: 500 with clear message (LIVEKIT_*/OPENAI_API_KEY not configured), no exceptions/stacktrace")
        
        request_data = {"phone_number": "+79001234567"}
        
        success, data, status = self.make_request('POST', '/api/voice/ai-call', request_data)
        
        if success and status == 500:
            print(f"   ✅ Status: {status} ✓ (Expected 500 when credentials missing)")
            print(f"   Response: {json.dumps(data, indent=2)}")
            
            detail = data.get('detail', '')
            
            # Check if it's a clear configuration error message
            config_keywords = ['LIVEKIT', 'OPENAI_API_KEY', 'not configured', 'missing']
            has_config_message = any(keyword in detail for keyword in config_keywords)
            
            # Check that it's not a stacktrace or exception
            exception_keywords = ['Traceback', 'Exception', 'Error:', 'File "', 'line ']
            has_exception = any(keyword in detail for keyword in exception_keywords)
            
            if has_config_message and not has_exception:
                self.log_test("Voice AI Call - Configuration Error", True, 
                            f"✅ Status 500 ✓, clear config message: '{detail}' ✓, no stacktrace ✓")
            else:
                issues = []
                if not has_config_message:
                    issues.append("no clear configuration message")
                if has_exception:
                    issues.append("contains stacktrace/exception")
                self.log_test("Voice AI Call - Configuration Error", False, 
                            f"❌ Issues: {', '.join(issues)}, detail: '{detail}'")
                
        elif success and status == 200:
            print(f"   ✅ Status: {status} ✓ (Credentials configured)")
            print(f"   Response: {json.dumps(data, indent=2)}")
            
            # Check for expected response structure
            call_id = data.get('call_id')
            room_name = data.get('room_name')
            call_status = data.get('status')
            
            if call_id and room_name and call_status:
                self.log_test("Voice AI Call - Success Response", True, 
                            f"✅ Status 200 ✓, call_id: {call_id[:8]}..., room_name: {room_name}, status: {call_status}")
            else:
                self.log_test("Voice AI Call - Success Response", False, 
                            f"❌ Status 200 but missing required fields in response")
        else:
            print(f"   ❌ Status: {status}")
            print(f"   Response: {json.dumps(data, indent=2)}")
            self.log_test("Voice AI Call - Unexpected Response", False, 
                        f"❌ Status: {status} (expected 200 or 500), Data: {data}")

    def test_4_voice_call_start(self):
        """Test 4: POST /api/voice/call/start -> expect detailed 4xx/5xx error, no crashes"""
        print("\n4️⃣ Testing POST /api/voice/call/start")
        print("   Body: {\"phone_number\":\"+79001234567\"}")
        print("   Expected: detailed 4xx/5xx error, no crashes")
        
        request_data = {"phone_number": "+79001234567"}
        
        success, data, status = self.make_request('POST', '/api/voice/call/start', request_data)
        
        if success and 400 <= status < 600:
            print(f"   ✅ Status: {status} ✓ (Expected 4xx/5xx when not fully configured)")
            print(f"   Response: {json.dumps(data, indent=2)}")
            
            detail = data.get('detail', '')
            
            # Check if it's a detailed error (not just generic)
            if detail and len(detail) > 10:
                # Check that it's not a stacktrace or exception
                exception_keywords = ['Traceback', 'Exception', 'Error:', 'File "', 'line ']
                has_exception = any(keyword in detail for keyword in exception_keywords)
                
                if not has_exception:
                    self.log_test("Voice Call Start - Detailed Error", True, 
                                f"✅ Status {status} ✓, detailed error: '{detail}' ✓, no stacktrace ✓")
                else:
                    self.log_test("Voice Call Start - Detailed Error", False, 
                                f"❌ Status {status} ✓, but contains stacktrace: '{detail}'")
            else:
                self.log_test("Voice Call Start - Detailed Error", False, 
                            f"❌ Status {status} ✓, but error not detailed enough: '{detail}'")
                
        elif success and status == 200:
            print(f"   ✅ Status: {status} ✓ (Credentials configured)")
            print(f"   Response: {json.dumps(data, indent=2)}")
            
            # Check for expected response structure
            call_id = data.get('call_id')
            call_status = data.get('status')
            
            if call_id and call_status:
                self.log_test("Voice Call Start - Success Response", True, 
                            f"✅ Status 200 ✓, call_id: {call_id[:8]}..., status: {call_status}")
            else:
                self.log_test("Voice Call Start - Success Response", False, 
                            f"❌ Status 200 but missing required fields in response")
        else:
            print(f"   ❌ Status: {status}")
            print(f"   Response: {json.dumps(data, indent=2)}")
            self.log_test("Voice Call Start - Unexpected Response", False, 
                        f"❌ Status: {status} (expected 200, 4xx, or 5xx), Data: {data}")

    def test_5_realtime_sessions(self):
        """Test 5: POST /api/realtime/sessions -> expect 500 'OPENAI_API_KEY not configured' when missing"""
        print("\n5️⃣ Testing POST /api/realtime/sessions")
        print("   Body: {\"voice\":\"marin\"}")
        print("   Expected: 500 'OPENAI_API_KEY not configured' when missing, or 200 when present")
        
        request_data = {"voice": "marin"}
        
        success, data, status = self.make_request('POST', '/api/realtime/sessions', request_data)
        
        if success and status == 500:
            print(f"   ✅ Status: {status} ✓ (Expected when OPENAI_API_KEY missing)")
            print(f"   Response: {json.dumps(data, indent=2)}")
            
            detail = data.get('detail', '')
            
            # Check if detail mentions OPENAI_API_KEY
            if 'OPENAI_API_KEY not configured' in detail:
                self.log_test("Realtime Sessions - Config Error", True, 
                            f"✅ Status 500 ✓, correct error message: '{detail}' ✓")
            else:
                self.log_test("Realtime Sessions - Config Error", False, 
                            f"❌ Status 500 ✓, but wrong error message: '{detail}' (expected 'OPENAI_API_KEY not configured')")
                
        elif success and status == 200:
            print(f"   ✅ Status: {status} ✓ (OPENAI_API_KEY configured)")
            print(f"   Response: {json.dumps(data, indent=2)}")
            
            # Check for expected response structure
            client_secret = data.get('client_secret')
            model = data.get('model')
            voice = data.get('voice')
            expires_at = data.get('expires_at')
            
            if client_secret and model and voice and expires_at:
                self.log_test("Realtime Sessions - Success Response", True, 
                            f"✅ Status 200 ✓, all required fields present ✓")
            else:
                missing_fields = []
                if not client_secret:
                    missing_fields.append("client_secret")
                if not model:
                    missing_fields.append("model")
                if not voice:
                    missing_fields.append("voice")
                if not expires_at:
                    missing_fields.append("expires_at")
                self.log_test("Realtime Sessions - Success Response", False, 
                            f"❌ Status 200 ✓, but missing fields: {missing_fields}")
        else:
            print(f"   ❌ Status: {status}")
            print(f"   Response: {json.dumps(data, indent=2)}")
            self.log_test("Realtime Sessions - Unexpected Response", False, 
                        f"❌ Status: {status} (expected 200 or 500), Data: {data}")

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 80)
        print("🎯 BACKEND SMOKE TEST SUMMARY")
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
            print("\n✅ ALL TESTS PASSED!")
        
        print("\n" + "=" * 80)

    def run_smoke_tests(self):
        """Run all smoke tests as per review request"""
        print(f"🚀 VasDom AudioBot Backend - Smoke Tests (Review Request)")
        print(f"📍 Base URL: {self.base_url}")
        print("🔧 Testing backend startup and key endpoints after latest changes")
        print("=" * 80)
        
        # Check backend logs first
        logs_ok = self.check_backend_logs()
        
        # Run the 5 specific tests requested
        self.test_1_health_endpoint()
        self.test_2_voice_debug_check()
        self.test_3_voice_ai_call()
        self.test_4_voice_call_start()
        self.test_5_realtime_sessions()
        
        # Final summary
        self.print_summary()
        
        # Return overall status
        return len(self.failed_tests) == 0 and logs_ok

def main():
    """Main function to run smoke tests"""
    tester = BackendSmokeTestRunner()
    success = tester.run_smoke_tests()
    
    if success:
        print("\n🎉 SMOKE TESTS PASSED - Backend is ready for push & deploy!")
        sys.exit(0)
    else:
        print("\n💥 SMOKE TESTS FAILED - Issues found that need to be fixed")
        sys.exit(1)

if __name__ == "__main__":
    main()