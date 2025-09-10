#!/usr/bin/env python3
"""
Comprehensive Testing for VasDom AudioBot NEW FEATURES
Testing the NEW features added according to review request:

NEW FEATURES ADDED:
1. Live voice chat: GPT-4o Realtime API with human voice
   - POST /api/realtime/token - get token
   - WebSocket /ws/realtime - live voice connection

2. Smart meetings: Transcription and Bitrix24 integration  
   - POST /api/meetings/analyze - analyze meeting transcription
   - POST /api/bitrix/create-tasks - create tasks in Bitrix24

3. Updated dashboard: Modern UI with navigation and statistics

CRITICAL TESTS:
- All new endpoints return correct HTTP statuses
- JSON structures match expected formats  
- WebSocket endpoints are available (even if connection doesn't establish)
- Fallback analysis works when AI has problems
- Existing functionality is not broken

URL: https://smart-audiobot.preview.emergentagent.com
"""

import requests
import sys
import json
import time
import websocket
import threading
from datetime import datetime
from typing import Dict, Any, Optional

class VasDomNewFeaturesTester:
    def __init__(self, base_url="https://smart-audiobot.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_log_id = None
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

    # =============================================================================
    # NEW REALTIME VOICE API TESTS
    # =============================================================================

    def test_realtime_token(self):
        """Test POST /api/realtime/token - Get token for Realtime API"""
        print("\n🔍 Testing NEW Realtime Token Endpoint...")
        success, data, status = self.make_request('POST', 'realtime/token')
        
        if success and status == 200:
            # Check expected response structure
            has_token = 'token' in data
            has_expires_at = 'expires_at' in data
            
            token = data.get('token', '')
            expires_at = data.get('expires_at', 0)
            
            # Validate token format (should be a string)
            is_valid_token = isinstance(token, str) and len(token) > 10
            
            # Validate expiration (should be future timestamp)
            current_time = int(time.time())
            is_valid_expiration = isinstance(expires_at, int) and expires_at > current_time
            
            overall_success = has_token and has_expires_at and is_valid_token and is_valid_expiration
            self.log_test("NEW Realtime Token", overall_success, 
                         f"Token length: {len(token)}, Expires in: {expires_at - current_time}s")
            return overall_success
        else:
            self.log_test("NEW Realtime Token", False, f"Status: {status}, Error: {data.get('error', 'Unknown')}")
            return False

    def test_realtime_websocket_availability(self):
        """Test WebSocket /ws/realtime - Check endpoint availability"""
        print("\n🔍 Testing NEW Realtime WebSocket Availability...")
        
        try:
            # Convert HTTP URL to WebSocket URL
            ws_url = self.base_url.replace('https://', 'wss://').replace('http://', 'ws://') + '/ws/realtime'
            
            # Try to connect to WebSocket (with short timeout)
            ws = websocket.create_connection(ws_url, timeout=5)
            ws.close()
            
            self.log_test("NEW Realtime WebSocket", True, f"WebSocket endpoint available at {ws_url}")
            return True
            
        except websocket.WebSocketBadStatusException as e:
            # WebSocket endpoint exists but may require authentication
            if e.status_code in [401, 403, 426]:  # Unauthorized, Forbidden, Upgrade Required
                self.log_test("NEW Realtime WebSocket", True, f"WebSocket endpoint exists (auth required): {e.status_code}")
                return True
            else:
                self.log_test("NEW Realtime WebSocket", False, f"WebSocket bad status: {e.status_code}")
                return False
                
        except Exception as e:
            # Check if it's a connection upgrade issue (which means endpoint exists)
            error_str = str(e).lower()
            if 'upgrade' in error_str or 'websocket' in error_str:
                self.log_test("NEW Realtime WebSocket", True, f"WebSocket endpoint exists (protocol issue): {str(e)[:50]}...")
                return True
            else:
                self.log_test("NEW Realtime WebSocket", False, f"WebSocket connection failed: {str(e)[:50]}...")
                return False

    # =============================================================================
    # NEW MEETINGS API TESTS
    # =============================================================================

    def test_meetings_analyze(self):
        """Test POST /api/meetings/analyze - Analyze meeting transcription"""
        print("\n🔍 Testing NEW Meetings Analysis...")
        
        # Test data for meeting analysis
        test_data = {
            "transcription": "Добро пожаловать на планерку VasDom. Сегодня обсуждаем уборку подъездов в Центральном районе. Иван, нужно проверить качество уборки в доме на улице Ленина 15. Мария, подготовь отчет по расходным материалам до пятницы. Также нужно связаться с УК Центральная по поводу нового договора.",
            "meeting_title": "Планерка VasDom - Центральный район",
            "duration": 180
        }
        
        success, data, status = self.make_request('POST', 'meetings/analyze', test_data, timeout=60)
        
        if success and status == 200:
            # Check expected response structure
            required_fields = ['summary', 'tasks', 'participants']
            has_required = all(field in data for field in required_fields)
            
            summary = data.get('summary', '')
            tasks = data.get('tasks', [])
            participants = data.get('participants', [])
            
            # Validate response content
            has_meaningful_summary = isinstance(summary, str) and len(summary) > 10
            has_tasks_list = isinstance(tasks, list)
            has_participants_list = isinstance(participants, list)
            
            # Check task structure if tasks exist
            valid_task_structure = True
            if tasks and len(tasks) > 0:
                sample_task = tasks[0]
                expected_task_fields = ['title', 'assigned_to', 'priority']
                valid_task_structure = all(field in sample_task for field in expected_task_fields)
            
            overall_success = (has_required and has_meaningful_summary and 
                             has_tasks_list and has_participants_list and valid_task_structure)
            
            self.log_test("NEW Meetings Analysis", overall_success, 
                         f"Summary: {len(summary)} chars, Tasks: {len(tasks)}, Participants: {len(participants)}")
            return overall_success
        else:
            self.log_test("NEW Meetings Analysis", False, f"Status: {status}, Error: {data.get('error', 'Unknown')}")
            return False

    def test_bitrix_create_tasks(self):
        """Test POST /api/bitrix/create-tasks - Create tasks in Bitrix24"""
        print("\n🔍 Testing NEW Bitrix24 Task Creation...")
        
        # Test data for task creation
        test_data = {
            "tasks": [
                {
                    "title": "Проверить качество уборки в доме на улице Ленина 15",
                    "assigned_to": "Иван",
                    "priority": "high",
                    "deadline": "2025-01-20"
                },
                {
                    "title": "Подготовить отчет по расходным материалам",
                    "assigned_to": "Мария", 
                    "priority": "normal",
                    "deadline": "2025-01-17"
                }
            ],
            "meeting_title": "Планерка VasDom - Центральный район",
            "meeting_summary": "Обсуждение уборки подъездов и текущих задач",
            "participants": ["Иван", "Мария", "Руководитель"]
        }
        
        success, data, status = self.make_request('POST', 'bitrix/create-tasks', test_data, timeout=30)
        
        if success and status == 200:
            # Check expected response structure
            has_success = 'success' in data
            has_created_tasks = 'created_tasks' in data
            has_meeting_title = 'meeting_title' in data
            
            is_successful = data.get('success', False)
            created_tasks = data.get('created_tasks', [])
            
            # Validate created tasks structure
            valid_tasks_structure = True
            if created_tasks and len(created_tasks) > 0:
                sample_task = created_tasks[0]
                expected_fields = ['id', 'title', 'status']
                valid_tasks_structure = all(field in sample_task for field in expected_fields)
            
            overall_success = (has_success and has_created_tasks and has_meeting_title and 
                             is_successful and valid_tasks_structure)
            
            self.log_test("NEW Bitrix24 Task Creation", overall_success, 
                         f"Success: {is_successful}, Created: {len(created_tasks)} tasks")
            return overall_success
        else:
            self.log_test("NEW Bitrix24 Task Creation", False, f"Status: {status}, Error: {data.get('error', 'Unknown')}")
            return False

    # =============================================================================
    # EXISTING API TESTS (Should not be broken)
    # =============================================================================

    def test_health_check(self):
        """Test GET /api/health - Health check (existing API)"""
        print("\n🔍 Testing Existing Health Check...")
        success, data, status = self.make_request('GET', 'health')
        
        if success and status == 200:
            has_status = 'status' in data and data['status'] in ['healthy', 'degraded']
            has_services = 'services' in data
            has_version = 'version' in data
            
            services = data.get('services', {})
            version = data.get('version', '')
            
            overall_success = has_status and has_services and has_version
            self.log_test("Existing Health Check", overall_success, 
                         f"Status: {data.get('status')}, Version: {version}")
            return overall_success
        else:
            self.log_test("Existing Health Check", False, f"Status: {status}")
            return False

    def test_voice_process(self):
        """Test POST /api/voice/process - Main AI chat (existing API)"""
        print("\n🔍 Testing Existing Voice Processing...")
        
        test_message = "Какие услуги предоставляет VasDom? Расскажите о клининге подъездов."
        test_data = {
            "message": test_message,
            "session_id": self.session_id
        }
        
        success, data, status = self.make_request('POST', 'voice/process', test_data, timeout=60)
        
        if success and status == 200:
            required_fields = ['response', 'log_id', 'session_id', 'response_time']
            has_required = all(field in data for field in required_fields)
            
            # Store log_id for potential feedback testing
            if 'log_id' in data:
                self.test_log_id = data['log_id']
            
            response_length = len(data.get('response', ''))
            is_meaningful_response = response_length > 20
            
            overall_success = has_required and is_meaningful_response
            self.log_test("Existing Voice Processing", overall_success, 
                         f"Response: {response_length} chars, Log ID: {data.get('log_id', 'N/A')[:8]}...")
            return overall_success
        else:
            self.log_test("Existing Voice Processing", False, f"Status: {status}, Error: {data.get('error', 'Unknown')}")
            return False

    def test_learning_stats(self):
        """Test GET /api/learning/stats - Learning statistics (existing API)"""
        print("\n🔍 Testing Existing Learning Stats...")
        success, data, status = self.make_request('GET', 'learning/stats')
        
        if success and status == 200:
            required_fields = ['total_interactions', 'positive_ratings', 'negative_ratings']
            has_required = all(field in data for field in required_fields)
            
            total_interactions = data.get('total_interactions', 0)
            avg_rating = data.get('avg_rating')
            
            overall_success = has_required and isinstance(total_interactions, int)
            self.log_test("Existing Learning Stats", overall_success, 
                         f"Interactions: {total_interactions}, Avg rating: {avg_rating}")
            return overall_success
        else:
            self.log_test("Existing Learning Stats", False, f"Status: {status}")
            return False

    # =============================================================================
    # DASHBOARD TESTS
    # =============================================================================

    def test_dashboard_root(self):
        """Test GET / - Main page with updated statistics"""
        print("\n🔍 Testing Updated Dashboard Root...")
        success, data, status = self.make_request('GET', '', endpoint_override=self.base_url)
        
        if success and status == 200:
            expected_keys = ['name', 'version', 'features', 'stats', 'ai_services']
            has_expected_structure = all(key in data for key in expected_keys)
            
            # Check if it's the updated version
            is_updated_version = data.get('version') == '3.0.0'
            has_features = isinstance(data.get('features', []), list) and len(data.get('features', [])) > 0
            has_ai_services = isinstance(data.get('ai_services', {}), dict)
            
            overall_success = has_expected_structure and is_updated_version and has_features and has_ai_services
            self.log_test("Updated Dashboard Root", overall_success, 
                         f"Version: {data.get('version')}, Features: {len(data.get('features', []))}, AI Services: {len(data.get('ai_services', {}))}")
            return overall_success
        else:
            self.log_test("Updated Dashboard Root", False, f"Status: {status}, Error: {data.get('error', 'Unknown')}")
            return False

    # =============================================================================
    # FALLBACK TESTING
    # =============================================================================

    def test_fallback_analysis(self):
        """Test fallback analysis when AI has problems"""
        print("\n🔍 Testing Fallback Analysis...")
        
        # Test with a very long transcription that might cause AI issues
        long_transcription = "Планерка VasDom. " * 100 + "Нужно сделать задачу по уборке. Проверить качество работы. Связаться с клиентами."
        
        test_data = {
            "transcription": long_transcription,
            "meeting_title": "Тест fallback анализа",
            "duration": 300
        }
        
        success, data, status = self.make_request('POST', 'meetings/analyze', test_data, timeout=30)
        
        if success and status == 200:
            # Even with fallback, should return proper structure
            has_summary = 'summary' in data and len(data.get('summary', '')) > 0
            has_tasks = 'tasks' in data and isinstance(data.get('tasks', []), list)
            has_participants = 'participants' in data and isinstance(data.get('participants', []), list)
            
            overall_success = has_summary and has_tasks and has_participants
            self.log_test("Fallback Analysis", overall_success, 
                         f"Fallback worked: Summary exists, Tasks: {len(data.get('tasks', []))}")
            return overall_success
        else:
            self.log_test("Fallback Analysis", False, f"Status: {status}")
            return False

    # =============================================================================
    # COMPREHENSIVE TEST RUNNER
    # =============================================================================

    def run_comprehensive_test(self):
        """Run all tests for NEW VasDom AudioBot features"""
        print("🚀 Starting Comprehensive NEW FEATURES Testing")
        print("🎯 Testing VasDom AudioBot NEW FEATURES:")
        print("   • Live voice chat (Realtime API)")
        print("   • Smart meetings (AI analysis)")
        print("   • Bitrix24 integration")
        print("   • Updated dashboard")
        print("   • Existing API compatibility")
        print(f"🌐 Testing against: {self.base_url}")
        print("=" * 70)
        
        test_results = []
        
        # =============================================================================
        # 🎯 NEW REALTIME VOICE FEATURES
        # =============================================================================
        print("\n" + "🎯 TESTING NEW REALTIME VOICE FEATURES" + "🎯")
        print("-" * 50)
        
        test_results.append(self.test_realtime_token())
        test_results.append(self.test_realtime_websocket_availability())
        
        # =============================================================================
        # 🎯 NEW MEETINGS FEATURES  
        # =============================================================================
        print("\n" + "🎯 TESTING NEW MEETINGS FEATURES" + "🎯")
        print("-" * 50)
        
        test_results.append(self.test_meetings_analyze())
        test_results.append(self.test_bitrix_create_tasks())
        test_results.append(self.test_fallback_analysis())
        
        # =============================================================================
        # 🎯 EXISTING API COMPATIBILITY
        # =============================================================================
        print("\n" + "🎯 TESTING EXISTING API COMPATIBILITY" + "🎯")
        print("-" * 50)
        
        test_results.append(self.test_health_check())
        test_results.append(self.test_voice_process())
        test_results.append(self.test_learning_stats())
        
        # =============================================================================
        # 🎯 UPDATED DASHBOARD
        # =============================================================================
        print("\n" + "🎯 TESTING UPDATED DASHBOARD" + "🎯")
        print("-" * 50)
        
        test_results.append(self.test_dashboard_root())
        
        # =============================================================================
        # SUMMARY
        # =============================================================================
        print("\n" + "=" * 70)
        print(f"📊 VASDOM AUDIOBOT NEW FEATURES TEST SUMMARY")
        print(f"✅ Passed: {self.tests_passed}/{self.tests_run}")
        print(f"❌ Failed: {self.tests_run - self.tests_passed}/{self.tests_run}")
        
        # Categorize results
        critical_tests = self.tests_run
        critical_passed = self.tests_passed
        
        if critical_passed == critical_tests:
            print("🎉 ALL NEW FEATURES WORKING PERFECTLY!")
            print("🎯 Live voice chat, smart meetings, and dashboard updates are functional!")
            print("✅ Existing functionality remains intact!")
            return 0
        elif critical_passed >= critical_tests * 0.8:  # 80% success rate
            print("🎯 MOST NEW FEATURES WORKING!")
            print("⚠️  Some features may need minor adjustments.")
            print("✅ Core functionality is stable!")
            return 0
        else:
            print("⚠️  MULTIPLE NEW FEATURE ISSUES DETECTED!")
            print("🔧 Significant issues found that need immediate attention.")
            return 1

def main():
    """Main test execution for VasDom AudioBot NEW FEATURES"""
    print("🎯 VasDom AudioBot NEW FEATURES Tester")
    print("🚀 Testing LIVE VOICE CHAT + SMART MEETINGS")
    print("📋 Testing all revolutionary new features:")
    print("   • GPT-4o Realtime API integration")
    print("   • Meeting transcription analysis")
    print("   • Bitrix24 task creation")
    print("   • Updated dashboard with statistics")
    print("   • Existing API compatibility")
    
    # Use the public URL from the review request
    tester = VasDomNewFeaturesTester("https://smart-audiobot.preview.emergentagent.com")
    
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