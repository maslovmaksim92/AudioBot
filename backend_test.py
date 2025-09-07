#!/usr/bin/env python3
"""
VasDom AI Business Management System - Backend API Testing
Comprehensive test suite for all backend endpoints
"""

import requests
import sys
import json
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
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)
            elif method == 'PATCH':
                response = requests.patch(url, json=data, headers=headers, timeout=10)
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
            self.log_test(name, False, "Request timeout (10s)")
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
        
        # Test root endpoint
        self.test_endpoint("Root Endpoint", "GET", "", 200)
        
        # Test health endpoints
        self.test_endpoint("Basic Health Check", "GET", "health", 200)
        self.test_endpoint("Detailed Health Check", "GET", "healthz", 200)

    def test_dashboard_api(self):
        """Test dashboard endpoints"""
        print("\n📊 TESTING DASHBOARD API")
        print("=" * 50)
        
        success, data = self.test_endpoint("Dashboard Data", "GET", "/api/dashboard", 200)
        
        if success and data:
            # Validate dashboard data structure
            required_fields = ['total_employees', 'active_projects', 'completed_tasks_today', 'revenue_month', 'system_health']
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                self.log_test("Dashboard Data Structure", False, f"Missing fields: {missing_fields}")
            else:
                self.log_test("Dashboard Data Structure", True, f"All required fields present")
                
                # Log some key metrics
                print(f"    📈 Total Employees: {data.get('total_employees', 0)}")
                print(f"    🏢 Active Projects: {data.get('active_projects', 0)}")
                print(f"    ✅ Tasks Completed Today: {data.get('completed_tasks_today', 0)}")
                print(f"    💰 Revenue This Month: {data.get('revenue_month', 0)} ₽")
                print(f"    🔧 System Health: {data.get('system_health', 'unknown')}")

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
                    self.test_endpoint(f"Filter by Department ({test_dept})", "GET", f"/api/employees?department={test_dept}", 200)

    def test_tasks_api(self):
        """Test task management endpoints"""
        print("\n📋 TESTING TASKS API")
        print("=" * 50)
        
        success, tasks = self.test_endpoint("Get All Tasks", "GET", "/api/tasks", 200)
        
        if success:
            task_count = len(tasks) if tasks else 0
            print(f"    📝 Total Tasks: {task_count}")
            
            # Test task filtering
            self.test_endpoint("Filter Tasks by Status", "GET", "/api/tasks?status=pending", 200)

    def test_projects_api(self):
        """Test project management endpoints"""
        print("\n🏢 TESTING PROJECTS API")
        print("=" * 50)
        
        success, projects = self.test_endpoint("Get All Projects", "GET", "/api/projects", 200)
        
        if success:
            project_count = len(projects) if projects else 0
            print(f"    🏗️ Total Projects: {project_count}")

    def test_finances_api(self):
        """Test financial endpoints"""
        print("\n💰 TESTING FINANCES API")
        print("=" * 50)
        
        success, report = self.test_endpoint("Financial Report", "GET", "/api/finances/report", 200)
        
        if success and report:
            # Validate financial report structure
            required_fields = ['period', 'totals', 'profit', 'breakdown']
            missing_fields = [field for field in required_fields if field not in report]
            
            if missing_fields:
                self.log_test("Financial Report Structure", False, f"Missing fields: {missing_fields}")
            else:
                self.log_test("Financial Report Structure", True, "All required fields present")
                
                if 'totals' in report:
                    totals = report['totals']
                    print(f"    📈 Revenue: {totals.get('revenue', 0)} ₽")
                    print(f"    📉 Expenses: {totals.get('expense', 0)} ₽")
                    print(f"    💰 Profit: {report.get('profit', 0)} ₽")

    def test_ai_endpoints(self):
        """Test AI and analytics endpoints"""
        print("\n🤖 TESTING AI ENDPOINTS")
        print("=" * 50)
        
        # Test AI analysis
        success, analysis = self.test_endpoint("AI System Analysis", "GET", "/api/ai/analysis", 200)
        
        # Test AI insights
        success, insights = self.test_endpoint("AI Insights", "GET", "/api/ai/insights", 200)
        
        if success and insights:
            print(f"    🧠 AI Status: {insights.get('ai_status', 'unknown')}")
            print(f"    💡 Active Suggestions: {insights.get('active_suggestions', 0)}")
            print(f"    ✅ Implemented Improvements: {insights.get('implemented_improvements', 0)}")
        
        # Test improvements endpoint
        self.test_endpoint("Get Improvements", "GET", "/api/improvements", 200)

    def test_system_logs(self):
        """Test system logging endpoints"""
        print("\n📊 TESTING SYSTEM LOGS")
        print("=" * 50)
        
        self.test_endpoint("System Logs", "GET", "/api/logs", 200)
        self.test_endpoint("System Logs (Limited)", "GET", "/api/logs?limit=10", 200)

    def run_all_tests(self):
        """Run all test suites"""
        print("🚀 STARTING VASDOM AI BACKEND API TESTS")
        print("=" * 60)
        print(f"Testing against: {self.base_url}")
        print(f"API Base URL: {self.api_url}")
        print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Run all test suites
        self.test_core_system()
        self.test_dashboard_api()
        self.test_employees_api()
        self.test_tasks_api()
        self.test_projects_api()
        self.test_finances_api()
        self.test_ai_endpoints()
        self.test_system_logs()
        
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