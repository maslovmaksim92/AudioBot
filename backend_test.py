#!/usr/bin/env python3
"""
🧪 Comprehensive Backend API Testing for AudioBot Bitrix24 Integration
Tests all API endpoints and validates expected data structure and content
"""

import requests
import sys
import json
from datetime import datetime
from typing import Dict, Any, List

class AudioBotAPITester:
    def __init__(self, base_url="https://bitrix-bridge.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name: str, success: bool, details: str = "", data: Any = None):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            
        result = {
            'name': name,
            'success': success,
            'details': details,
            'data': data,
            'timestamp': datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {name}")
        if details:
            print(f"    Details: {details}")
        if not success and data:
            print(f"    Response: {json.dumps(data, indent=2)}")

    def test_health_endpoint(self) -> bool:
        """Test /api/health endpoint"""
        try:
            response = requests.get(f"{self.api_url}/health", timeout=30)
            
            if response.status_code != 200:
                self.log_test("Health Check", False, f"HTTP {response.status_code}", response.text)
                return False
                
            data = response.json()
            
            # Validate required fields
            required_fields = ['api_status', 'bitrix_integration', 'timestamp']
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                self.log_test("Health Check", False, f"Missing fields: {missing_fields}", data)
                return False
                
            # Check API status
            if data.get('api_status') != 'healthy':
                self.log_test("Health Check", False, f"API not healthy: {data.get('api_status')}", data)
                return False
                
            # Check Bitrix integration status
            bitrix_status = data.get('bitrix_integration', {})
            if not isinstance(bitrix_status, dict) or bitrix_status.get('status') != 'success':
                self.log_test("Health Check", False, f"Bitrix integration issue: {bitrix_status}", data)
                return False
                
            self.log_test("Health Check", True, "API healthy, Bitrix24 connected")
            return True
            
        except Exception as e:
            self.log_test("Health Check", False, f"Exception: {str(e)}")
            return False

    def test_houses_endpoint(self) -> bool:
        """Test /api/cleaning/houses endpoint"""
        try:
            response = requests.get(f"{self.api_url}/cleaning/houses", timeout=30)
            
            if response.status_code != 200:
                self.log_test("Houses Endpoint", False, f"HTTP {response.status_code}", response.text)
                return False
                
            data = response.json()
            
            # Validate response structure
            if 'houses' not in data or 'total' not in data:
                self.log_test("Houses Endpoint", False, "Missing houses or total field", data)
                return False
                
            houses = data['houses']
            total = data['total']
            
            # Check if we have expected number of houses (should be 5 demo houses)
            if total != 5:
                self.log_test("Houses Endpoint", False, f"Expected 5 houses, got {total}", data)
                return False
                
            # Validate house structure
            required_house_fields = ['id', 'address', 'apartments', 'entrances', 'floors', 'management_company']
            for i, house in enumerate(houses):
                missing_fields = [field for field in required_house_fields if field not in house]
                if missing_fields:
                    self.log_test("Houses Endpoint", False, f"House {i} missing fields: {missing_fields}", house)
                    return False
                    
            # Check specific demo houses
            addresses = [house['address'] for house in houses]
            expected_addresses = [
                'ул. Аллейная, д. 10',
                'ул. Аллейная, д. 6, п. 1', 
                'ул. Аэропортовская, д. 14',
                'пр. Ленина, д. 25',
                'ул. Советская, д. 8А'
            ]
            
            for expected_addr in expected_addresses:
                if expected_addr not in addresses:
                    self.log_test("Houses Endpoint", False, f"Missing expected address: {expected_addr}", addresses)
                    return False
                    
            self.log_test("Houses Endpoint", True, f"Successfully loaded {total} houses with correct structure")
            return True
            
        except Exception as e:
            self.log_test("Houses Endpoint", False, f"Exception: {str(e)}")
            return False

    def test_employees_endpoint(self) -> bool:
        """Test /api/dashboard/employees endpoint"""
        try:
            response = requests.get(f"{self.api_url}/dashboard/employees", timeout=30)
            
            if response.status_code != 200:
                self.log_test("Employees Endpoint", False, f"HTTP {response.status_code}", response.text)
                return False
                
            data = response.json()
            
            # Validate response structure
            if 'employees' not in data or 'total' not in data:
                self.log_test("Employees Endpoint", False, "Missing employees or total field", data)
                return False
                
            employees = data['employees']
            total = data['total']
            
            # Check if we have expected number of employees (should be 39)
            if total != 39:
                self.log_test("Employees Endpoint", False, f"Expected 39 employees, got {total}", data)
                return False
                
            # Validate employee structure
            required_employee_fields = ['id', 'name', 'email', 'position', 'department_id', 'active']
            for i, employee in enumerate(employees[:5]):  # Check first 5 employees
                missing_fields = [field for field in required_employee_fields if field not in employee]
                if missing_fields:
                    self.log_test("Employees Endpoint", False, f"Employee {i} missing fields: {missing_fields}", employee)
                    return False
                    
            self.log_test("Employees Endpoint", True, f"Successfully loaded {total} employees with correct structure")
            return True
            
        except Exception as e:
            self.log_test("Employees Endpoint", False, f"Exception: {str(e)}")
            return False

    def test_statistics_endpoint(self) -> bool:
        """Test /api/dashboard/statistics endpoint"""
        try:
            response = requests.get(f"{self.api_url}/dashboard/statistics", timeout=30)
            
            if response.status_code != 200:
                self.log_test("Statistics Endpoint", False, f"HTTP {response.status_code}", response.text)
                return False
                
            data = response.json()
            
            # Validate response structure
            if 'statistics' not in data:
                self.log_test("Statistics Endpoint", False, "Missing statistics field", data)
                return False
                
            stats = data['statistics']
            
            # Validate statistics structure
            required_sections = ['houses', 'employees', 'management_companies', 'departments']
            missing_sections = [section for section in required_sections if section not in stats]
            
            if missing_sections:
                self.log_test("Statistics Endpoint", False, f"Missing sections: {missing_sections}", stats)
                return False
                
            # Validate houses statistics
            houses_stats = stats['houses']
            expected_houses_fields = ['total', 'total_apartments', 'total_entrances', 'with_schedule']
            missing_houses_fields = [field for field in expected_houses_fields if field not in houses_stats]
            
            if missing_houses_fields:
                self.log_test("Statistics Endpoint", False, f"Missing houses fields: {missing_houses_fields}", houses_stats)
                return False
                
            # Check expected values
            if houses_stats['total'] != 5:
                self.log_test("Statistics Endpoint", False, f"Expected 5 houses, got {houses_stats['total']}", houses_stats)
                return False
                
            if houses_stats['total_apartments'] != 331:
                self.log_test("Statistics Endpoint", False, f"Expected 331 apartments, got {houses_stats['total_apartments']}", houses_stats)
                return False
                
            # Validate employees statistics
            employees_stats = stats['employees']
            if employees_stats['total'] != 39:
                self.log_test("Statistics Endpoint", False, f"Expected 39 employees, got {employees_stats['total']}", employees_stats)
                return False
                
            if employees_stats['brigades'] != 9:
                self.log_test("Statistics Endpoint", False, f"Expected 9 brigades, got {employees_stats['brigades']}", employees_stats)
                return False
                
            # Validate management companies
            mc_stats = stats['management_companies']
            if mc_stats['total'] != 4:
                self.log_test("Statistics Endpoint", False, f"Expected 4 management companies, got {mc_stats['total']}", mc_stats)
                return False
                
            expected_companies = ["ТСЖ \"Аллейная\"", "ТСЖ \"Советское\"", "ТСЖ \"Центральное\"", "УК \"Домоуправление\""]
            actual_companies = mc_stats.get('list', [])
            
            for expected_company in expected_companies:
                if expected_company not in actual_companies:
                    self.log_test("Statistics Endpoint", False, f"Missing expected company: {expected_company}", actual_companies)
                    return False
                    
            self.log_test("Statistics Endpoint", True, "All statistics validated successfully")
            return True
            
        except Exception as e:
            self.log_test("Statistics Endpoint", False, f"Exception: {str(e)}")
            return False

    def test_root_endpoint(self) -> bool:
        """Test /api/ root endpoint"""
        try:
            response = requests.get(f"{self.api_url}/", timeout=10)
            
            if response.status_code != 200:
                self.log_test("Root API Endpoint", False, f"HTTP {response.status_code}", response.text)
                return False
                
            data = response.json()
            
            if 'message' not in data:
                self.log_test("Root API Endpoint", False, "Missing message field", data)
                return False
                
            self.log_test("Root API Endpoint", True, f"Message: {data['message']}")
            return True
            
        except Exception as e:
            self.log_test("Root API Endpoint", False, f"Exception: {str(e)}")
            return False

    def run_all_tests(self) -> bool:
        """Run all API tests"""
        print("🧪 Starting AudioBot API Testing...")
        print(f"🔗 Testing against: {self.base_url}")
        print("=" * 60)
        
        # Run all tests
        tests = [
            self.test_root_endpoint,
            self.test_health_endpoint,
            self.test_houses_endpoint,
            self.test_employees_endpoint,
            self.test_statistics_endpoint
        ]
        
        all_passed = True
        for test in tests:
            try:
                result = test()
                if not result:
                    all_passed = False
            except Exception as e:
                print(f"❌ FAIL - {test.__name__}: Exception {str(e)}")
                all_passed = False
                
        # Print summary
        print("=" * 60)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} passed")
        
        if all_passed:
            print("🎉 ALL TESTS PASSED! AudioBot API is working correctly.")
        else:
            print("⚠️  SOME TESTS FAILED! Check the details above.")
            
        return all_passed

def main():
    """Main test execution"""
    tester = AudioBotAPITester()
    success = tester.run_all_tests()
    
    # Save detailed results
    with open('/app/test_results.json', 'w') as f:
        json.dump({
            'summary': {
                'total_tests': tester.tests_run,
                'passed_tests': tester.tests_passed,
                'success_rate': tester.tests_passed / tester.tests_run if tester.tests_run > 0 else 0,
                'all_passed': success
            },
            'detailed_results': tester.test_results,
            'timestamp': datetime.now().isoformat()
        }, f, indent=2)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())