#!/usr/bin/env python3
"""
VasDom AudioBot - Production Backend API Testing
Comprehensive test suite for all implemented endpoints
"""

import requests
import sys
import json
import time
from datetime import datetime
from typing import Dict, Any, List

class VasDomAPITester:
    def __init__(self, base_url="https://smart-biz-dash.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []

    def log_test(self, name: str, success: bool, details: str = ""):
        """Log test results"""
        self.tests_run += 1
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {name}")
        if details:
            print(f"    Details: {details}")
        
        if success:
            self.tests_passed += 1
        else:
            self.failed_tests.append({"name": name, "details": details})

    def test_endpoint(self, name: str, method: str, endpoint: str, expected_status: int = 200, data: Dict = None) -> tuple:
        """Test a single endpoint"""
        url = f"{self.base_url}/{endpoint}" if not endpoint.startswith('/api') else f"{self.base_url}{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=15)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=15)
            else:
                raise ValueError(f"Unsupported method: {method}")

            success = response.status_code == expected_status
            details = f"Status: {response.status_code}, Expected: {expected_status}"
            
            if not success:
                try:
                    error_data = response.json()
                    details += f", Response: {error_data}"
                except:
                    details += f", Response: {response.text[:200]}"
            
            self.log_test(name, success, details)
            
            return success, response.json() if success and response.content else {}

        except requests.exceptions.Timeout:
            self.log_test(name, False, "Request timeout (15s)")
            return False, {}
        except requests.exceptions.ConnectionError:
            self.log_test(name, False, "Connection error")
            return False, {}
        except Exception as e:
            self.log_test(name, False, f"Error: {str(e)}")
            return False, {}

    def test_core_system(self):
        """Test core system endpoints"""
        print("\n🔍 TESTING CORE SYSTEM ENDPOINTS")
        print("=" * 50)
        
        # Test API root endpoint
        success, data = self.test_endpoint("API Root", "GET", "/api/", 200)
        if success and data:
            print(f"    🚀 API Version: {data.get('version', 'unknown')}")
            print(f"    📝 Message: {data.get('message', 'N/A')}")
            print(f"    ⚡ Status: {data.get('status', 'N/A')}")

    def test_dashboard_api(self):
        """Test dashboard endpoints"""
        print("\n📊 TESTING DASHBOARD API")
        print("=" * 50)
        
        success, data = self.test_endpoint("Dashboard Data", "GET", "/api/dashboard", 200)
        
        if success and data:
            # Validate dashboard data structure
            required_fields = ['total_employees', 'total_meetings', 'total_messages', 'system_health']
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                self.log_test("Dashboard Data Structure", False, f"Missing fields: {missing_fields}")
            else:
                self.log_test("Dashboard Data Structure", True, f"All required fields present")
                
                # Log some key metrics
                print(f"    👥 Total Employees: {data.get('total_employees', 0)}")
                print(f"    📅 Total Meetings: {data.get('total_meetings', 0)}")
                print(f"    💬 Total Messages: {data.get('total_messages', 0)}")
                print(f"    🔧 System Health: {data.get('system_health', 'unknown')}")
                print(f"    ⚠️ Recent Alerts: {data.get('recent_alerts', 0)}")

    def test_employees_api(self):
        """Test employee management endpoints"""
        print("\n👥 TESTING EMPLOYEES API")
        print("=" * 50)
        
        # Test getting all employees
        success, employees = self.test_endpoint("Get All Employees", "GET", "/api/employees", 200)
        
        if success and employees:
            employee_count = len(employees)
            self.log_test("Employee Count Check", employee_count >= 13, f"Found {employee_count} employees (expected >= 13)")
            
            # Test employee data structure
            if employees:
                first_employee = employees[0]
                required_fields = ['id', 'full_name', 'phone', 'role', 'department', 'active']
                missing_fields = [field for field in required_fields if field not in first_employee]
                
                if missing_fields:
                    self.log_test("Employee Data Structure", False, f"Missing fields: {missing_fields}")
                else:
                    self.log_test("Employee Data Structure", True, "All required fields present")
                
                # Test department filtering
                departments = list(set(emp.get('department') for emp in employees if emp.get('department')))
                print(f"    🏢 Departments found: {', '.join(departments)}")
                
                if departments:
                    test_dept = departments[0]
                    success, filtered = self.test_endpoint(f"Filter by Department ({test_dept})", "GET", f"/api/employees?department={test_dept}", 200)
                    if success and filtered:
                        print(f"    🔍 Filtered employees: {len(filtered)}")

        # Test creating new employee
        test_employee = {
            "full_name": "Test Employee",
            "phone": "89999999999",
            "role": "test_role",
            "department": "Test Department"
        }
        success, created = self.test_endpoint("Create Employee", "POST", "/api/employees", 200, test_employee)
        if success and created:
            print(f"    ✅ Created employee: {created.get('full_name', 'N/A')}")

    def test_bitrix24_integration(self):
        """Test Bitrix24 integration endpoints"""
        print("\n🏢 TESTING BITRIX24 INTEGRATION")
        print("=" * 50)
        
        # Test Bitrix24 connection
        success, result = self.test_endpoint("Bitrix24 Connection Test", "GET", "/api/bitrix24/test", 200)
        if success and result:
            print(f"    🔗 Connection Status: {result.get('status', 'unknown')}")
            if result.get('status') == 'success':
                print(f"    ✅ Bitrix24 connected successfully")
            else:
                print(f"    ❌ Bitrix24 connection issue: {result.get('message', 'N/A')}")
        
        # Test getting deals
        success, deals_result = self.test_endpoint("Get Bitrix24 Deals", "GET", "/api/bitrix24/deals", 200)
        if success and deals_result:
            deals = deals_result.get('deals', [])
            deal_count = deals_result.get('count', 0)
            print(f"    📊 Deals found: {deal_count}")
            self.log_test("Bitrix24 Deals Count", deal_count >= 50, f"Found {deal_count} deals (expected >= 50)")
        
        # Test creating task
        test_task = {
            "title": "Test Task from API",
            "description": "This is a test task created during API testing",
            "responsible_id": "1"
        }
        success, task_result = self.test_endpoint("Create Bitrix24 Task", "POST", "/api/bitrix24/create-task", 200, test_task)
        if success and task_result:
            print(f"    ✅ Task creation status: {task_result.get('status', 'unknown')}")
            if task_result.get('task_id'):
                print(f"    📝 Created task ID: {task_result.get('task_id')}")

    def test_chat_api(self):
        """Test live chat endpoints"""
        print("\n💬 TESTING LIVE CHAT API")
        print("=" * 50)
        
        # Test sending message
        test_message = {
            "sender_id": "test_user",
            "content": "Привет! Это тестовое сообщение для проверки AI ответов."
        }
        success, result = self.test_endpoint("Send Chat Message", "POST", "/api/chat/send", 200, test_message)
        if success and result:
            print(f"    📤 Message sent successfully")
            if result.get('ai_response'):
                print(f"    🤖 AI Response received: {len(result['ai_response'])} characters")
                # Wait a bit for AI processing
                time.sleep(2)
        
        # Test getting chat history
        success, history = self.test_endpoint("Get Chat History", "GET", "/api/chat/history", 200)
        if success and history:
            messages = history.get('messages', [])
            print(f"    📜 Chat history: {len(messages)} messages")
            if messages:
                latest_msg = messages[-1]
                print(f"    💬 Latest message: {latest_msg.get('content', 'N/A')[:50]}...")

    def test_meetings_api(self):
        """Test meetings/planning endpoints"""
        print("\n📅 TESTING MEETINGS API")
        print("=" * 50)
        
        # Test creating meeting
        test_meeting = {
            "title": f"Test Meeting {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "description": "Test meeting for API validation",
            "participants": ["admin", "test_user"],
            "start_time": datetime.now().isoformat(),
            "recording_text": "Обсудили планы на неделю. Нужно увеличить производительность уборки. Максим предложил новую систему контроля качества."
        }
        success, meeting = self.test_endpoint("Create Meeting", "POST", "/api/meetings", 200, test_meeting)
        meeting_id = None
        if success and meeting:
            meeting_data = meeting.get('meeting', {})
            meeting_id = meeting_data.get('id')
            print(f"    ✅ Meeting created: {meeting_data.get('title', 'N/A')}")
            print(f"    🆔 Meeting ID: {meeting_id}")
        
        # Test getting meetings
        success, meetings_result = self.test_endpoint("Get Meetings", "GET", "/api/meetings", 200)
        if success and meetings_result:
            meetings = meetings_result.get('meetings', [])
            print(f"    📋 Total meetings: {len(meetings)}")
        
        # Test meeting analysis if we have a meeting ID
        if meeting_id:
            success, analysis = self.test_endpoint("Analyze Meeting", "POST", f"/api/meetings/{meeting_id}/analyze", 200)
            if success and analysis:
                print(f"    🤖 Analysis status: {analysis.get('status', 'unknown')}")
                if analysis.get('analysis'):
                    print(f"    📊 AI Analysis received: {len(analysis['analysis'])} characters")
                bitrix_tasks = analysis.get('bitrix_tasks', [])
                print(f"    📝 Bitrix24 tasks created: {len(bitrix_tasks)}")

    def test_system_logs(self):
        """Test system logging endpoints"""
        print("\n📊 TESTING SYSTEM LOGS")
        print("=" * 50)
        
        success, logs_result = self.test_endpoint("System Logs", "GET", "/api/logs", 200)
        if success and logs_result:
            logs = logs_result.get('logs', [])
            log_count = logs_result.get('count', 0)
            print(f"    📜 Total logs: {log_count}")
            
            # Test filtering by level
            success, error_logs = self.test_endpoint("Filter Logs (ERROR)", "GET", "/api/logs?level=ERROR&limit=10", 200)
            if success and error_logs:
                error_count = error_logs.get('count', 0)
                print(f"    🚨 Error logs: {error_count}")
            
            # Test filtering by component
            success, ai_logs = self.test_endpoint("Filter Logs (AI)", "GET", "/api/logs?component=ai&limit=10", 200)
            if success and ai_logs:
                ai_count = ai_logs.get('count', 0)
                print(f"    🤖 AI logs: {ai_count}")

    def test_telegram_webhook(self):
        """Test Telegram webhook endpoint"""
        print("\n📱 TESTING TELEGRAM WEBHOOK")
        print("=" * 50)
        
        # Test webhook endpoint (should accept POST)
        test_webhook_data = {
            "update_id": 123456789,
            "message": {
                "message_id": 1,
                "from": {
                    "id": 123456789,
                    "is_bot": False,
                    "first_name": "Test",
                    "username": "testuser"
                },
                "chat": {
                    "id": 123456789,
                    "first_name": "Test",
                    "username": "testuser",
                    "type": "private"
                },
                "date": int(datetime.now().timestamp()),
                "text": "/start"
            }
        }
        
        # Note: This endpoint is not under /api prefix
        success, result = self.test_endpoint("Telegram Webhook", "POST", "/telegram/webhook", 200, test_webhook_data)
        if success and result:
            print(f"    📱 Webhook status: {result.get('status', 'unknown')}")

    def run_all_tests(self):
        """Run all test suites"""
        print("🚀 STARTING VASDOM AUDIOBOT PRODUCTION API TESTS")
        print("=" * 60)
        print(f"Testing against: {self.base_url}")
        print(f"API Base URL: {self.api_url}")
        print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Run all test suites
        self.test_core_system()
        self.test_dashboard_api()
        self.test_employees_api()
        self.test_bitrix24_integration()
        self.test_chat_api()
        self.test_meetings_api()
        self.test_system_logs()
        self.test_telegram_webhook()
        
        # Print final results
        self.print_results()

    def print_results(self):
        """Print final test results"""
        print("\n" + "=" * 60)
        print("📊 FINAL TEST RESULTS")
        print("=" * 60)
        
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        
        print(f"✅ Tests Passed: {self.tests_passed}")
        print(f"❌ Tests Failed: {len(self.failed_tests)}")
        print(f"📊 Total Tests: {self.tests_run}")
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        if self.failed_tests:
            print(f"\n❌ FAILED TESTS:")
            for i, test in enumerate(self.failed_tests, 1):
                print(f"{i}. {test['name']}")
                if test['details']:
                    print(f"   Details: {test['details']}")
        
        print(f"\nTest completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return len(self.failed_tests) == 0

def main():
    """Main test execution"""
    tester = VasDomAPITester()
    
    try:
        success = tester.run_all_tests()
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n⚠️ Tests interrupted by user")
        return 1
    except Exception as e:
        print(f"\n💥 Unexpected error: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())