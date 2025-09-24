#!/usr/bin/env python3
"""
LiveKit SIP on Render Test - Review Request
Re-test backend on Render for LiveKit SIP after removing unsupported field:
1) POST /api/voice/call/start with {"phone_number":"+79001234567"} -> expect 200 with {call_id, room_name, status} or detailed 4xx/5xx (but not schema error)
2) If 200: immediately GET /api/voice/call/{call_id}/status until status != 'ringing' (max 5 polls)
3) Report status codes and body snippets
Base URL: https://audiobot-qci2.onrender.com (all routes prefixed with /api)
"""

import requests
import sys
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional

class LiveKitRenderTester:
    def __init__(self, base_url="https://audiobot-qci2.onrender.com"):
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
                response = requests.get(url, headers=headers, params=params, timeout=60)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=60)
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

    def test_livekit_render_review_request(self):
        """Test LiveKit SIP on Render after removing unsupported field as per review request"""
        print(f"🚀 LiveKit SIP on Render - Review Request Test")
        print(f"📍 Base URL: {self.base_url}")
        print("🔧 Re-test backend on Render for LiveKit SIP after removing unsupported field:")
        print("1) POST /api/voice/call/start with {\"phone_number\":\"+79001234567\"} -> expect 200 with {call_id, room_name, status} or detailed 4xx/5xx (but not schema error)")
        print("2) If 200: immediately GET /api/voice/call/{call_id}/status until status != 'ringing' (max 5 polls)")
        print("3) Report status codes and body snippets")
        print("=" * 80)
        
        # Test 1: POST /api/voice/call/start
        call_id = self.test_livekit_call_start_render()
        
        # Test 2: If 200, poll status
        if call_id:
            self.test_livekit_call_status_polling(call_id)
        
        # Final summary
        self.print_summary()

    def test_livekit_call_start_render(self):
        """Test POST /api/voice/call/start on Render - expect 200 or detailed 4xx/5xx (not schema error)"""
        print("\n1️⃣ Testing POST /api/voice/call/start on Render")
        print("   Body: {\"phone_number\":\"+79001234567\"}")
        print("   Expected: 200 with {call_id, room_name, status} or detailed 4xx/5xx (but NOT schema error)")
        
        request_data = {"phone_number": "+79001234567"}
        
        success, data, status = self.make_request('POST', '/api/voice/call/start', request_data)
        
        print(f"   📊 Status Code: {status}")
        print(f"   📋 Response Body: {json.dumps(data, indent=2, ensure_ascii=False)}")
        
        if success and status == 200:
            # Check required schema keys: call_id, room_name, status
            call_id = data.get('call_id')
            room_name = data.get('room_name')
            call_status = data.get('status')
            
            if call_id and room_name and call_status:
                self.log_test("LiveKit Call Start - Success Response", True, 
                            f"✅ Status 200 ✓, call_id: {call_id[:8] if call_id else 'None'}..., room_name: {room_name}, status: {call_status}")
                return call_id
            else:
                missing_keys = []
                if not call_id:
                    missing_keys.append("call_id")
                if not room_name:
                    missing_keys.append("room_name")
                if not call_status:
                    missing_keys.append("status")
                self.log_test("LiveKit Call Start - Schema Issue", False, 
                            f"❌ Status 200 but missing required keys: {missing_keys}")
                
        elif success and 400 <= status < 600:
            # Check if it's a detailed error (not schema error)
            detail = data.get('detail', '')
            
            # Check for schema-related errors (these should NOT happen per review request)
            schema_error_indicators = ['schema', 'validation', 'field required', 'invalid type']
            is_schema_error = any(indicator in detail.lower() for indicator in schema_error_indicators)
            
            if is_schema_error:
                self.log_test("LiveKit Call Start - Schema Error (UNEXPECTED)", False, 
                            f"❌ Status {status} with schema error (should not happen): '{detail}'")
            else:
                # This is expected - detailed 4xx/5xx error
                self.log_test("LiveKit Call Start - Detailed Error (EXPECTED)", True, 
                            f"✅ Status {status} with detailed error (expected): '{detail}'")
                
        else:
            self.log_test("LiveKit Call Start - Unexpected Response", False, 
                        f"❌ Unexpected response: Status {status}, Success: {success}, Data: {data}")
        
        return None

    def test_livekit_call_status_polling(self, call_id):
        """Test GET /api/voice/call/{call_id}/status polling until status != 'ringing' (max 5 polls)"""
        print(f"\n2️⃣ Testing GET /api/voice/call/{call_id[:8]}../status polling")
        print("   Expected: Poll until status != 'ringing' (max 5 polls)")
        
        max_polls = 5
        poll_interval = 2  # seconds
        
        for poll_num in range(1, max_polls + 1):
            print(f"\n   📊 Poll #{poll_num}/{max_polls}")
            
            success, data, status = self.make_request('GET', f'/api/voice/call/{call_id}/status')
            
            print(f"   📊 Status Code: {status}")
            print(f"   📋 Response Body: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            if success and status == 200:
                call_status = data.get('status', '')
                
                if call_status != 'ringing':
                    self.log_test(f"LiveKit Call Status - Poll #{poll_num} (Final)", True, 
                                f"✅ Status changed from 'ringing' to '{call_status}' after {poll_num} polls")
                    return
                else:
                    print(f"   ⏳ Status still 'ringing', continuing polling...")
                    if poll_num < max_polls:
                        time.sleep(poll_interval)
            else:
                self.log_test(f"LiveKit Call Status - Poll #{poll_num} (Error)", False, 
                            f"❌ Status: {status}, Data: {data}")
                return
        
        # If we reach here, status was still 'ringing' after max polls
        self.log_test("LiveKit Call Status - Max Polls Reached", True, 
                    f"✅ Completed {max_polls} polls, status remained 'ringing' (normal for test call)")

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 80)
        print("🎯 TEST SUMMARY")
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
        
        print("\n" + "=" * 80)

if __name__ == "__main__":
    # Use the Render URL from review request
    base_url = "https://audiobot-qci2.onrender.com"
    
    tester = LiveKitRenderTester(base_url)
    tester.test_livekit_render_review_request()