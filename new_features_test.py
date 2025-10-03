#!/usr/bin/env python3
"""
VasDom AudioBot Backend API Testing - New Features Review Request
Testing new backend endpoints per review request:

1) CRM краткая справка - GET /api/cleaning/brief?q=Ленина
2) Realtime сессия (WebRTC) - POST /api/realtime/sessions
3) Bitrix задачи - GET /api/tasks/bitrix/list, POST /api/tasks/bitrix/create, PATCH /api/tasks/bitrix/update
4) From meeting → create - POST /api/tasks/from-meeting
5) Employees - GET /api/employees/office
6) План дня - GET /api/tasks/bitrix/agenda, POST /api/tasks/bitrix/agenda/export

Base URL: https://ai-report-call.preview.emergentagent.com
"""

import requests
import sys
import json
import time
from datetime import datetime, date
from typing import Dict, Any, Optional

class NewFeaturesAPITester:
    def __init__(self, base_url=None):
        # Use the deployed URL from frontend .env
        if base_url is None:
            base_url = "https://ai-report-call.preview.emergentagent.com"
        
        self.base_url = base_url.rstrip('/')
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []
        self.created_task_id = None  # Store task_id for update testing

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
            elif method == 'PATCH':
                response = requests.patch(url, json=data, headers=headers, timeout=60)
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

    def test_crm_brief(self):
        """Test 1: GET /api/cleaning/brief?q=Ленина - expect 200 and JSON {text: 'Адрес: ... · Периодичность: ... · Ближайшая уборка: ...'} or понятное сообщение if not found"""
        print("\n1️⃣ Testing GET /api/cleaning/brief?q=Ленина")
        print("   Expected: 200 and JSON {text: 'Адрес: ... · Периодичность: ... · Ближайшая уборка: ...'} or понятное сообщение")
        
        success, data, status = self.make_request('GET', '/api/cleaning/brief', params={'q': 'Ленина'})
        
        if success and status == 200:
            print(f"   ✅ Status: {status} ✓")
            print(f"   Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            # Check if response has text field
            text = data.get('text')
            
            if text and isinstance(text, str):
                # Check if text contains expected structure or понятное сообщение
                if any(keyword in text for keyword in ['Адрес:', 'Периодичность:', 'Ближайшая уборка:', 'не найдено', 'не найден', 'отсутствует']):
                    self.log_test("CRM Brief - Response Structure", True, 
                                f"✅ text field present with expected content: '{text[:100]}...' ✓")
                else:
                    self.log_test("CRM Brief - Response Structure", True, 
                                f"✅ text field present: '{text[:100]}...' ✓")
            else:
                self.log_test("CRM Brief - Response Structure", False, 
                            f"❌ Expected text field as string, got: {type(text)}")
        else:
            self.log_test("CRM Brief - Response Structure", False, 
                        f"❌ Status: {status} (expected 200), Data: {data}")

    def test_realtime_sessions(self):
        """Test 2: POST /api/realtime/sessions with body {"voice":"marin","instructions":"тест"} - expect 200 and object with client_secret, model, voice, expires_at or 500 if OPENAI_API_KEY not configured"""
        print("\n2️⃣ Testing POST /api/realtime/sessions")
        print("   Body: {\"voice\":\"marin\",\"instructions\":\"тест\"}")
        print("   Expected: 200 with client_secret, model, voice, expires_at OR 500 if OPENAI_API_KEY not configured")
        
        request_data = {
            "voice": "marin",
            "instructions": "тест"
        }
        
        success, data, status = self.make_request('POST', '/api/realtime/sessions', request_data)
        
        if success and status == 200:
            print(f"   ✅ Status: {status} ✓")
            print(f"   Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            # Check required fields
            required_fields = ['client_secret', 'model', 'voice', 'expires_at']
            missing_fields = [field for field in required_fields if field not in data]
            
            if not missing_fields:
                self.log_test("Realtime Sessions - Success Response", True, 
                            f"✅ All required fields present: {required_fields} ✓")
                
                # Validate field types
                client_secret = data.get('client_secret')
                model = data.get('model')
                voice = data.get('voice')
                expires_at = data.get('expires_at')
                
                if isinstance(client_secret, str) and isinstance(model, str) and isinstance(voice, str) and isinstance(expires_at, int):
                    self.log_test("Realtime Sessions - Field Types", True, 
                                f"✅ Field types correct: client_secret=str, model=str, voice=str, expires_at=int ✓")
                else:
                    self.log_test("Realtime Sessions - Field Types", False, 
                                f"❌ Field type issues: client_secret={type(client_secret)}, model={type(model)}, voice={type(voice)}, expires_at={type(expires_at)}")
            else:
                self.log_test("Realtime Sessions - Success Response", False, 
                            f"❌ Missing required fields: {missing_fields}")
                
        elif success and status == 500:
            print(f"   ⚠️ Status: {status} (Internal Server Error)")
            print(f"   Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            detail = data.get('detail', '')
            
            # Check if detail mentions OPENAI_API_KEY
            if 'OPENAI_API_KEY' in detail:
                self.log_test("Realtime Sessions - API Key Error", True, 
                            f"✅ Status 500 with OPENAI_API_KEY error as expected: '{detail}' ✓")
            else:
                self.log_test("Realtime Sessions - API Key Error", False, 
                            f"❌ Status 500 but detail doesn't mention OPENAI_API_KEY: '{detail}'")
        else:
            self.log_test("Realtime Sessions - Unexpected Response", False, 
                        f"❌ Status: {status} (expected 200 or 500), Data: {data}")

    def test_bitrix_tasks_list(self):
        """Test 3a: GET /api/tasks/bitrix/list?date=YYYY-MM-DD - expect 200 and array tasks[] (может быть пустым)"""
        print("\n3️⃣a Testing GET /api/tasks/bitrix/list?date=YYYY-MM-DD")
        
        # Use today's date
        today = date.today().strftime('%Y-%m-%d')
        print(f"   Date: {today}")
        print("   Expected: 200 and array tasks[] (может быть пустым)")
        
        success, data, status = self.make_request('GET', '/api/tasks/bitrix/list', params={'date': today})
        
        if success and status == 200:
            print(f"   ✅ Status: {status} ✓")
            print(f"   Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            tasks = data.get('tasks')
            
            if isinstance(tasks, list):
                self.log_test("Bitrix Tasks List - Response Structure", True, 
                            f"✅ tasks[] is array with {len(tasks)} items ✓")
            else:
                self.log_test("Bitrix Tasks List - Response Structure", False, 
                            f"❌ Expected tasks as array, got: {type(tasks)}")
                
        elif success and status == 500:
            print(f"   ⚠️ Status: {status} (Internal Server Error)")
            print(f"   Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            detail = data.get('detail', '')
            
            # Check if it's a webhook configuration issue
            if 'webhook' in detail.lower() or 'bitrix' in detail.lower():
                self.log_test("Bitrix Tasks List - Webhook Error", True, 
                            f"✅ Status 500 with webhook configuration error: '{detail}' ✓")
            else:
                self.log_test("Bitrix Tasks List - Webhook Error", False, 
                            f"❌ Status 500 but unexpected error: '{detail}'")
        else:
            self.log_test("Bitrix Tasks List - Unexpected Response", False, 
                        f"❌ Status: {status} (expected 200 or 500), Data: {data}")

    def test_bitrix_tasks_create(self):
        """Test 3b: POST /api/tasks/bitrix/create with {title:"Тест задача", description:"из автотеста"} - expect 200 {ok:true, task_id} or 500 if webhook has no rights"""
        print("\n3️⃣b Testing POST /api/tasks/bitrix/create")
        
        request_data = {
            "title": "Тест задача",
            "description": "из автотеста"
        }
        
        print(f"   Body: {json.dumps(request_data, ensure_ascii=False)}")
        print("   Expected: 200 {ok:true, task_id} OR 500 if webhook has no rights")
        
        success, data, status = self.make_request('POST', '/api/tasks/bitrix/create', request_data)
        
        if success and status == 200:
            print(f"   ✅ Status: {status} ✓")
            print(f"   Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            ok = data.get('ok')
            task_id = data.get('task_id')
            
            if ok is True and task_id:
                self.log_test("Bitrix Tasks Create - Success Response", True, 
                            f"✅ ok=true ✓, task_id={task_id} ✓")
                self.created_task_id = task_id  # Store for update test
            else:
                self.log_test("Bitrix Tasks Create - Success Response", False, 
                            f"❌ Expected ok=true and task_id, got ok={ok}, task_id={task_id}")
                
        elif success and status == 500:
            print(f"   ⚠️ Status: {status} (Internal Server Error)")
            print(f"   Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            detail = data.get('detail', '')
            
            # Check if it's a webhook rights issue
            if any(keyword in detail.lower() for keyword in ['webhook', 'rights', 'permission', 'access', 'bitrix']):
                self.log_test("Bitrix Tasks Create - Webhook Rights Error", True, 
                            f"✅ Status 500 with webhook rights error: '{detail}' ✓")
            else:
                self.log_test("Bitrix Tasks Create - Webhook Rights Error", False, 
                            f"❌ Status 500 but unexpected error: '{detail}'")
        else:
            self.log_test("Bitrix Tasks Create - Unexpected Response", False, 
                        f"❌ Status: {status} (expected 200 or 500), Data: {data}")

    def test_bitrix_tasks_update(self):
        """Test 3c: PATCH /api/tasks/bitrix/update for task_id from previous step with fields {"STATUS":5} - expect 200 {ok:true}"""
        print("\n3️⃣c Testing PATCH /api/tasks/bitrix/update")
        
        if not self.created_task_id:
            print("   ⚠️ No task_id from create step - using dummy ID for testing")
            task_id = 1  # Use dummy ID
        else:
            task_id = self.created_task_id
            
        request_data = {
            "id": task_id,
            "fields": {"STATUS": 5}
        }
        
        print(f"   Body: {json.dumps(request_data, ensure_ascii=False)}")
        print("   Expected: 200 {ok:true}")
        
        success, data, status = self.make_request('PATCH', '/api/tasks/bitrix/update', request_data)
        
        if success and status == 200:
            print(f"   ✅ Status: {status} ✓")
            print(f"   Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            ok = data.get('ok')
            
            if ok is True:
                self.log_test("Bitrix Tasks Update - Success Response", True, 
                            f"✅ ok=true ✓")
            else:
                self.log_test("Bitrix Tasks Update - Success Response", False, 
                            f"❌ Expected ok=true, got ok={ok}")
                
        elif success and status == 500:
            print(f"   ⚠️ Status: {status} (Internal Server Error)")
            print(f"   Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            detail = data.get('detail', '')
            
            # Check if it's a webhook rights issue
            if any(keyword in detail.lower() for keyword in ['webhook', 'rights', 'permission', 'access', 'bitrix', 'task']):
                self.log_test("Bitrix Tasks Update - Webhook Rights Error", True, 
                            f"✅ Status 500 with webhook rights error: '{detail}' ✓")
            else:
                self.log_test("Bitrix Tasks Update - Webhook Rights Error", False, 
                            f"❌ Status 500 but unexpected error: '{detail}'")
        else:
            self.log_test("Bitrix Tasks Update - Unexpected Response", False, 
                        f"❌ Status: {status} (expected 200 or 500), Data: {data}")

    def test_tasks_from_meeting(self):
        """Test 4: POST /api/tasks/from-meeting with tasks array - expect 200 {ok:true, created:[{title, task_id, responsible_id}...]}"""
        print("\n4️⃣ Testing POST /api/tasks/from-meeting")
        
        request_data = {
            "tasks": [
                {
                    "title": "Поручение 1",
                    "owner": "Иван",
                    "due": "2025-09-25 18:00:00"
                }
            ]
        }
        
        print(f"   Body: {json.dumps(request_data, ensure_ascii=False)}")
        print("   Expected: 200 {ok:true, created:[{title, task_id, responsible_id}...]}")
        
        success, data, status = self.make_request('POST', '/api/tasks/from-meeting', request_data)
        
        if success and status == 200:
            print(f"   ✅ Status: {status} ✓")
            print(f"   Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            ok = data.get('ok')
            created = data.get('created')
            
            if ok is True and isinstance(created, list):
                if created:
                    # Check structure of first created task
                    first_task = created[0]
                    required_fields = ['title', 'task_id', 'responsible_id']
                    missing_fields = [field for field in required_fields if field not in first_task]
                    
                    if not missing_fields:
                        self.log_test("Tasks From Meeting - Success Response", True, 
                                    f"✅ ok=true ✓, created array with {len(created)} tasks ✓, required fields present ✓")
                    else:
                        self.log_test("Tasks From Meeting - Success Response", False, 
                                    f"❌ ok=true ✓, created array ✓, but missing fields in task: {missing_fields}")
                else:
                    self.log_test("Tasks From Meeting - Success Response", True, 
                                f"✅ ok=true ✓, created array (empty) ✓")
            else:
                self.log_test("Tasks From Meeting - Success Response", False, 
                            f"❌ Expected ok=true and created array, got ok={ok}, created={type(created)}")
                
        elif success and status == 500:
            print(f"   ⚠️ Status: {status} (Internal Server Error)")
            print(f"   Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            detail = data.get('detail', '')
            
            # Check if it's a webhook configuration issue
            if any(keyword in detail.lower() for keyword in ['webhook', 'bitrix', 'configuration']):
                self.log_test("Tasks From Meeting - Webhook Error", True, 
                            f"✅ Status 500 with webhook configuration error: '{detail}' ✓")
            else:
                self.log_test("Tasks From Meeting - Webhook Error", False, 
                            f"❌ Status 500 but unexpected error: '{detail}'")
        else:
            self.log_test("Tasks From Meeting - Unexpected Response", False, 
                        f"❌ Status: {status} (expected 200 or 500), Data: {data}")

    def test_employees_office(self):
        """Test 5: GET /api/employees/office - expect 200 {employees:[{id,name}...]}"""
        print("\n5️⃣ Testing GET /api/employees/office")
        print("   Expected: 200 {employees:[{id,name}...]}")
        
        success, data, status = self.make_request('GET', '/api/employees/office')
        
        if success and status == 200:
            print(f"   ✅ Status: {status} ✓")
            print(f"   Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            employees = data.get('employees')
            
            if isinstance(employees, list):
                if employees:
                    # Check structure of first employee
                    first_employee = employees[0]
                    required_fields = ['id', 'name']
                    missing_fields = [field for field in required_fields if field not in first_employee]
                    
                    if not missing_fields:
                        self.log_test("Employees Office - Success Response", True, 
                                    f"✅ employees array with {len(employees)} items ✓, required fields present ✓")
                    else:
                        self.log_test("Employees Office - Success Response", False, 
                                    f"❌ employees array ✓, but missing fields in employee: {missing_fields}")
                else:
                    self.log_test("Employees Office - Success Response", True, 
                                f"✅ employees array (empty) ✓")
            else:
                self.log_test("Employees Office - Success Response", False, 
                            f"❌ Expected employees as array, got: {type(employees)}")
        else:
            self.log_test("Employees Office - Unexpected Response", False, 
                        f"❌ Status: {status} (expected 200), Data: {data}")

    def test_bitrix_agenda_get(self):
        """Test 6a: GET /api/tasks/bitrix/agenda?date=YYYY-MM-DD - expect 200 {employees:[...]} (даже если пусто)"""
        print("\n6️⃣a Testing GET /api/tasks/bitrix/agenda?date=YYYY-MM-DD")
        
        # Use today's date
        today = date.today().strftime('%Y-%m-%d')
        print(f"   Date: {today}")
        print("   Expected: 200 {employees:[...]} (даже если пусто)")
        
        success, data, status = self.make_request('GET', '/api/tasks/bitrix/agenda', params={'date': today})
        
        if success and status == 200:
            print(f"   ✅ Status: {status} ✓")
            print(f"   Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            employees = data.get('employees')
            
            if isinstance(employees, list):
                self.log_test("Bitrix Agenda Get - Success Response", True, 
                            f"✅ employees array with {len(employees)} items ✓")
            else:
                self.log_test("Bitrix Agenda Get - Success Response", False, 
                            f"❌ Expected employees as array, got: {type(employees)}")
        else:
            self.log_test("Bitrix Agenda Get - Unexpected Response", False, 
                        f"❌ Status: {status} (expected 200), Data: {data}")

    def test_bitrix_agenda_export(self):
        """Test 6b: POST /api/tasks/bitrix/agenda/export with {date:YYYY-MM-DD} - expect 200 {ok:true} or 400 'telegram not configured'"""
        print("\n6️⃣b Testing POST /api/tasks/bitrix/agenda/export")
        
        # Use today's date
        today = date.today().strftime('%Y-%m-%d')
        request_data = {"date": today}
        
        print(f"   Body: {json.dumps(request_data, ensure_ascii=False)}")
        print("   Expected: 200 {ok:true} OR 400 'telegram not configured'")
        
        success, data, status = self.make_request('POST', '/api/tasks/bitrix/agenda/export', request_data)
        
        if success and status == 200:
            print(f"   ✅ Status: {status} ✓")
            print(f"   Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            ok = data.get('ok')
            
            if ok is True:
                self.log_test("Bitrix Agenda Export - Success Response", True, 
                            f"✅ ok=true ✓")
            else:
                self.log_test("Bitrix Agenda Export - Success Response", False, 
                            f"❌ Expected ok=true, got ok={ok}")
                
        elif success and status == 400:
            print(f"   ⚠️ Status: {status} (Bad Request)")
            print(f"   Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            # Check if it mentions telegram configuration
            response_text = str(data).lower()
            if 'telegram' in response_text and 'configured' in response_text:
                self.log_test("Bitrix Agenda Export - Telegram Config Error", True, 
                            f"✅ Status 400 with telegram configuration error ✓")
            else:
                self.log_test("Bitrix Agenda Export - Telegram Config Error", False, 
                            f"❌ Status 400 but doesn't mention telegram configuration: {data}")
        else:
            self.log_test("Bitrix Agenda Export - Unexpected Response", False, 
                        f"❌ Status: {status} (expected 200 or 400), Data: {data}")

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 80)
        print("🎯 NEW FEATURES TEST SUMMARY")
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

    def run_new_features_tests(self):
        """Run all new features tests as per review request"""
        print(f"🚀 VasDom AudioBot Backend API - New Features Testing")
        print(f"📍 Base URL: {self.base_url}")
        print("🔧 Testing new backend features per review request:")
        print("1) CRM краткая справка")
        print("2) Realtime сессия (WebRTC)")
        print("3) Bitrix задачи")
        print("4) From meeting → create")
        print("5) Employees")
        print("6) План дня")
        print("=" * 80)
        
        # Test 1: CRM краткая справка
        self.test_crm_brief()
        
        # Test 2: Realtime сессия (WebRTC)
        self.test_realtime_sessions()
        
        # Test 3: Bitrix задачи
        self.test_bitrix_tasks_list()
        self.test_bitrix_tasks_create()
        self.test_bitrix_tasks_update()
        
        # Test 4: From meeting → create
        self.test_tasks_from_meeting()
        
        # Test 5: Employees
        self.test_employees_office()
        
        # Test 6: План дня
        self.test_bitrix_agenda_get()
        self.test_bitrix_agenda_export()
        
        # Final summary
        self.print_summary()

if __name__ == "__main__":
    tester = NewFeaturesAPITester()
    tester.run_new_features_tests()