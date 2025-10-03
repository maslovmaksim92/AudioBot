#!/usr/bin/env python3
"""
AI Outbound Flow Testing - Review Request
Run backend smoke tests focusing on AI outbound flow after buffering + model upgrade.
"""

import requests
import json
import time
import subprocess
from datetime import datetime

class AIOutboundTester:
    def __init__(self):
        # Use the correct backend URL from frontend .env
        self.base_url = "https://call-bot.preview.emergentagent.com"
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

    def make_request(self, method: str, endpoint: str, data=None):
        """Make HTTP request and return (success, response_data, status_code)"""
        url = f"{self.base_url}{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=30)
            else:
                return False, {}, 0
            
            try:
                response_data = response.json() if response.content else {}
            except:
                response_data = {"error": "Non-JSON response", "content": response.text[:500]}
                
            return True, response_data, response.status_code
            
        except Exception as e:
            return False, {"error": str(e)}, 0

    def test_health_with_timestamp(self):
        """Test 1: GET /api/health - expect 200 JSON with ts"""
        print("\n1️⃣ Testing GET /api/health")
        print("   Expected: 200 and JSON with ts")
        
        success, data, status = self.make_request('GET', '/api/health')
        
        if success and status == 200:
            print(f"   ✅ Status: {status} ✓")
            print(f"   Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            ok = data.get('ok')
            ts = data.get('ts')
            
            if ok is True and ts is not None:
                try:
                    ts_int = int(ts)
                    current_time = int(time.time())
                    if abs(ts_int - current_time) < 3600:
                        self.log_test("Health with Timestamp", True, 
                                    f"✅ Status 200 ✓, ok=true ✓, ts={ts} (valid timestamp) ✓")
                    else:
                        self.log_test("Health with Timestamp", False, 
                                    f"❌ ts={ts} seems invalid (too far from current time)")
                except (ValueError, TypeError):
                    self.log_test("Health with Timestamp", False, 
                                f"❌ ts={ts} is not a valid integer timestamp")
            else:
                issues = []
                if ok is not True:
                    issues.append(f"ok={ok} (expected true)")
                if ts is None:
                    issues.append("ts field missing")
                self.log_test("Health with Timestamp", False, f"❌ Issues: {', '.join(issues)}")
        else:
            self.log_test("Health with Timestamp", False, f"❌ Status: {status}, Data: {data}")

    def test_voice_debug_check(self):
        """Test 2: GET /api/voice/debug/check - expect 200 and flags present"""
        print("\n2️⃣ Testing GET /api/voice/debug/check")
        print("   Expected: 200 and flags present")
        
        success, data, status = self.make_request('GET', '/api/voice/debug/check')
        
        if success and status == 200:
            print(f"   ✅ Status: {status} ✓")
            print(f"   Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            expected_flags = ['api_key_set', 'api_secret_set', 'openai_key_set', 'trunk_id_set']
            missing_flags = [flag for flag in expected_flags if flag not in data]
            
            if not missing_flags:
                flag_values = {flag: data.get(flag) for flag in expected_flags}
                self.log_test("Voice Debug Check", True, 
                            f"✅ Status 200 ✓, all flags present: {flag_values} ✓")
            else:
                self.log_test("Voice Debug Check", False, 
                            f"❌ Missing flags: {missing_flags}")
        else:
            self.log_test("Voice Debug Check", False, f"❌ Status: {status}, Data: {data}")

    def test_ai_call_endpoint(self):
        """Test 3: POST /api/voice/ai-call - expect 200 or structured 4xx/5xx, no stacktrace"""
        print("\n3️⃣ Testing POST /api/voice/ai-call")
        print("   Body: {\"phone_number\":\"+79001234567\"}")
        print("   Expected: 200 or structured 4xx/5xx based on LiveKit config; ensure no stacktrace")
        
        request_data = {"phone_number": "+79001234567"}
        
        success, data, status = self.make_request('POST', '/api/voice/ai-call', request_data)
        
        if success and status == 200:
            print(f"   ✅ Status: {status} ✓ (LiveKit configured)")
            print(f"   Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            call_id = data.get('call_id')
            room_name = data.get('room_name')
            call_status = data.get('status')
            
            if call_id and room_name and call_status:
                self.log_test("AI Call Endpoint", True, 
                            f"✅ Status 200 ✓, call_id: {call_id[:8]}..., room_name: {room_name}, status: {call_status}")
                return call_id
            else:
                missing_keys = []
                if not call_id:
                    missing_keys.append("call_id")
                if not room_name:
                    missing_keys.append("room_name")
                if not call_status:
                    missing_keys.append("status")
                self.log_test("AI Call Endpoint", False, 
                            f"❌ Status 200 ✓, but missing keys: {missing_keys}")
                return call_id
                
        elif success and (400 <= status < 600):
            print(f"   ✅ Status: {status} ✓ (Expected 4xx/5xx when LiveKit not fully configured)")
            print(f"   Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            detail = data.get('detail', '')
            
            # Check for stacktrace indicators (should not be present)
            stacktrace_indicators = ['Traceback', 'File "/', 'line ', 'Exception:', 'Error:']
            has_stacktrace = any(indicator in detail for indicator in stacktrace_indicators)
            
            if not has_stacktrace:
                self.log_test("AI Call Endpoint", True, 
                            f"✅ Status {status} ✓, structured error without stacktrace: '{detail}'")
            else:
                self.log_test("AI Call Endpoint", False, 
                            f"❌ Status {status} ✓, but response contains stacktrace")
            return None
        else:
            self.log_test("AI Call Endpoint", False, 
                        f"❌ Unexpected status: {status}, Data: {data}")
            return None

    def test_ai_worker_logs_analysis(self, call_id):
        """Test 4: Analyze logs for AI worker patterns"""
        print(f"\n4️⃣ Analyzing backend logs for AI worker patterns")
        if call_id:
            print(f"   Looking for call_id: {call_id[:8]}...")
        else:
            print("   No call_id available, checking general patterns")
        
        try:
            # Get recent backend logs (both stdout and stderr)
            log_files = ['/var/log/supervisor/backend.out.log', '/var/log/supervisor/backend.err.log']
            all_logs = ""
            
            for log_file in log_files:
                try:
                    result = subprocess.run(['tail', '-n', '200', log_file], 
                                          capture_output=True, text=True, timeout=10)
                    if result.returncode == 0:
                        all_logs += f"\n=== {log_file} ===\n" + result.stdout
                except Exception as e:
                    print(f"   ⚠️ Could not read {log_file}: {e}")
            
            if all_logs:
                print(f"   📋 Recent backend logs analysis:")
                
                # Check for (a) OpenAI WS connects using gpt-realtime
                openai_ws_patterns = ["gpt-realtime", "model=gpt-realtime"]
                openai_ws_found = any(pattern in all_logs for pattern in openai_ws_patterns)
                
                if openai_ws_found:
                    self.log_test("OpenAI WS gpt-realtime", True, 
                                "✅ Found OpenAI WS connection using gpt-realtime model")
                else:
                    self.log_test("OpenAI WS gpt-realtime", False, 
                                "❌ No evidence of OpenAI WS connection using gpt-realtime")
                
                # Check for (b) PSTN->OpenAI commit logs show appended_ms >= 100ms
                commit_pattern = "Commit input buffer: appended_ms="
                commit_logs = [line for line in all_logs.split('\n') if commit_pattern in line]
                
                if commit_logs:
                    appended_ms_values = []
                    for log_line in commit_logs:
                        try:
                            start = log_line.find("appended_ms=") + len("appended_ms=")
                            end = log_line.find(" ", start)
                            if end == -1:
                                end = log_line.find("(", start)
                            if end == -1:
                                end = len(log_line)
                            ms_str = log_line[start:end].strip()
                            ms_value = float(ms_str)
                            appended_ms_values.append(ms_value)
                        except Exception:
                            continue
                    
                    if appended_ms_values:
                        min_ms = min(appended_ms_values)
                        max_ms = max(appended_ms_values)
                        avg_ms = sum(appended_ms_values) / len(appended_ms_values)
                        
                        if min_ms >= 100:
                            self.log_test("PSTN Commit >= 100ms", True, 
                                        f"✅ Found {len(appended_ms_values)} commit logs, all >= 100ms (min={min_ms:.1f}, max={max_ms:.1f}, avg={avg_ms:.1f})")
                        else:
                            self.log_test("PSTN Commit >= 100ms", False, 
                                        f"❌ Found {len(appended_ms_values)} commit logs, but some < 100ms (min={min_ms:.1f})")
                    else:
                        self.log_test("PSTN Commit >= 100ms", False, 
                                    "❌ Found commit logs but could not parse appended_ms values")
                else:
                    self.log_test("PSTN Commit >= 100ms", False, 
                                "❌ No PSTN->OpenAI commit logs found")
                
                # Check for (c) no 'input_audio_buffer_commit_empty' errors
                empty_commit_pattern = "input_audio_buffer_commit_empty"
                empty_commit_found = empty_commit_pattern in all_logs
                
                if not empty_commit_found:
                    self.log_test("No Empty Commit Errors", True, 
                                "✅ No 'input_audio_buffer_commit_empty' errors found")
                else:
                    self.log_test("No Empty Commit Errors", False, 
                                "❌ Found 'input_audio_buffer_commit_empty' errors in logs")
                
                # Check for (d) OpenAI->LK audio chunks observed
                audio_chunk_patterns = ["OpenAI->LK audio:", "response.audio.delta", "capture_frame"]
                audio_chunks_found = any(pattern in all_logs for pattern in audio_chunk_patterns)
                
                if audio_chunks_found:
                    chunk_count = sum(all_logs.count(pattern) for pattern in audio_chunk_patterns)
                    self.log_test("OpenAI->LK Audio Chunks", True, 
                                f"✅ Found {chunk_count} references to OpenAI->LK audio chunks")
                else:
                    self.log_test("OpenAI->LK Audio Chunks", False, 
                                "❌ No OpenAI->LK audio chunks observed in logs")
                
                # Show relevant log excerpts
                print(f"   📋 Relevant log excerpts:")
                relevant_lines = []
                for line in all_logs.split('\n')[-100:]:  # Last 100 lines
                    if any(pattern in line.lower() for pattern in ['gpt-realtime', 'commit input buffer', 'openai->lk', 'audio', 'ai-call']):
                        relevant_lines.append(line)
                
                for line in relevant_lines[-15:]:  # Show last 15 relevant lines
                    print(f"   {line}")
                    
            else:
                self.log_test("Log Analysis", False, 
                            "❌ Could not read backend logs for analysis")
                
        except Exception as e:
            print(f"   ❌ Error analyzing logs: {e}")
            self.log_test("Log Analysis", False, f"❌ Error analyzing logs: {e}")

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 80)
        print("🎯 AI OUTBOUND FLOW TEST SUMMARY")
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

    def run_tests(self):
        """Run all AI outbound flow tests"""
        print(f"🚀 VasDom AudioBot Backend API - AI Outbound Flow Testing")
        print(f"📍 Base URL: {self.base_url}")
        print("🔧 Testing AI outbound flow after buffering + model upgrade per review request:")
        print("1) Verify GET /api/health => 200 and JSON with ts")
        print("2) Verify GET /api/voice/debug/check => 200 and flags present")
        print("3) POST /api/voice/ai-call with phone_number \"+79001234567\" should return 200 or structured 4xx/5xx based on LiveKit config; ensure no stacktrace")
        print("4) Tail logs for AI worker to confirm: (a) OpenAI WS connects using gpt-realtime, (b) PSTN->OpenAI commit logs show appended_ms >= 100ms, (c) no 'input_audio_buffer_commit_empty' errors, (d) OpenAI->LK audio chunks observed")
        print("=" * 80)
        
        # Test 1: GET /api/health
        self.test_health_with_timestamp()
        
        # Test 2: GET /api/voice/debug/check
        self.test_voice_debug_check()
        
        # Test 3: POST /api/voice/ai-call
        call_id = self.test_ai_call_endpoint()
        
        # Test 4: Analyze logs for AI worker patterns
        self.test_ai_worker_logs_analysis(call_id)
        
        # Final summary
        self.print_summary()

if __name__ == "__main__":
    tester = AIOutboundTester()
    tester.run_tests()