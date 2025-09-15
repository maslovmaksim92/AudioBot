#!/usr/bin/env python3
"""
VasDom AudioBot Backend API Testing
Comprehensive testing of all backend endpoints
"""

import requests
import sys
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional

class VasDomAPITester:
    def __init__(self, base_url="https://smartclean.preview.emergentagent.com"):
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
                
            return True, response.json() if response.content else {}, response.status_code
            
        except requests.exceptions.Timeout:
            return False, {"error": "Request timeout"}, 0
        except requests.exceptions.ConnectionError:
            return False, {"error": "Connection error"}, 0
        except Exception as e:
            return False, {"error": str(e)}, 0
    
    def test_root_endpoint(self):
        """Test root API endpoint"""
        success, data, status = self.make_request('GET', '/api/')
        
        if success and status == 200:
            if 'message' in data and 'VasDom AudioBot API' in data['message']:
                self.log_test("Root API Endpoint", True, f"Version: {data.get('version', 'N/A')}")
                return True
            else:
                self.log_test("Root API Endpoint", False, f"Unexpected response: {data}")
        else:
            self.log_test("Root API Endpoint", False, f"Status: {status}, Data: {data}")
        return False
    
    def test_dashboard_stats(self):
        """Test dashboard statistics endpoint"""
        success, data, status = self.make_request('GET', '/api/dashboard/stats')
        
        if success and status == 200:
            required_fields = ['total_houses', 'total_apartments', 'active_brigades', 'employees']
            missing_fields = [field for field in required_fields if field not in data]
            
            if not missing_fields:
                stats_info = f"Houses: {data['total_houses']}, Apartments: {data['total_apartments']}, Brigades: {data['active_brigades']}, Employees: {data['employees']}"
                self.log_test("Dashboard Stats", True, stats_info)
                return True, data
            else:
                self.log_test("Dashboard Stats", False, f"Missing fields: {missing_fields}")
        else:
            self.log_test("Dashboard Stats", False, f"Status: {status}, Data: {data}")
        return False, {}
    
    def test_cleaning_houses(self):
        """Test houses endpoint with various filters"""
        # Test basic houses endpoint
        success, data, status = self.make_request('GET', '/api/cleaning/houses')
        
        if success and status == 200:
            # Check if response has the expected structure
            if isinstance(data, dict) and 'houses' in data:
                houses = data['houses']
                houses_count = len(houses)
                if houses_count > 0:
                    # Check first house structure
                    first_house = houses[0]
                    required_fields = ['id', 'title', 'address', 'brigade', 'management_company', 'status']
                    missing_fields = [field for field in required_fields if field not in first_house]
                    
                    if not missing_fields:
                        self.log_test("Houses List", True, f"Retrieved {houses_count} houses, Total: {data.get('total', 'N/A')}")
                        
                        # Test with filters
                        self.test_houses_with_filters()
                        return True, houses
                    else:
                        self.log_test("Houses List", False, f"Missing fields in house data: {missing_fields}")
                else:
                    self.log_test("Houses List", False, "No houses returned")
            else:
                self.log_test("Houses List", False, f"Expected dict with 'houses' key, got: {type(data)}")
        else:
            self.log_test("Houses List", False, f"Status: {status}, Data: {data}")
        return False, []
    
    def test_houses_with_filters(self):
        """Test houses endpoint with filters"""
        # Test with limit
        success, data, status = self.make_request('GET', '/api/cleaning/houses', params={'limit': 5})
        if success and status == 200 and isinstance(data, dict) and 'houses' in data:
            houses = data['houses']
            self.log_test("Houses with Limit Filter", True, f"Retrieved {len(houses)} houses (limit=5)")
        else:
            self.log_test("Houses with Limit Filter", False, f"Status: {status}")
        
        # Test with offset
        success, data, status = self.make_request('GET', '/api/cleaning/houses', params={'offset': 10, 'limit': 5})
        if success and status == 200 and isinstance(data, dict) and 'houses' in data:
            houses = data['houses']
            self.log_test("Houses with Offset Filter", True, f"Retrieved {len(houses)} houses (offset=10)")
        else:
            self.log_test("Houses with Offset Filter", False, f"Status: {status}")
    
    def test_cleaning_filters(self):
        """Test filters endpoint"""
        success, data, status = self.make_request('GET', '/api/cleaning/filters')
        
        if success and status == 200:
            required_fields = ['brigades', 'management_companies', 'statuses']
            missing_fields = [field for field in required_fields if field not in data]
            
            if not missing_fields:
                filter_info = f"Brigades: {len(data['brigades'])}, Companies: {len(data['management_companies'])}, Statuses: {len(data['statuses'])}"
                self.log_test("Cleaning Filters", True, filter_info)
                return True, data
            else:
                self.log_test("Cleaning Filters", False, f"Missing fields: {missing_fields}")
        else:
            self.log_test("Cleaning Filters", False, f"Status: {status}, Data: {data}")
        return False, {}
    
    def test_ai_chat(self):
        """Test AI chat endpoint"""
        test_message = "Привет! Расскажи о системе VasDom AudioBot"
        
        success, data, status = self.make_request('POST', '/api/ai/chat', {
            'message': test_message,
            'user_id': 'test_user_123'
        })
        
        if success and status == 200:
            if 'response' in data and 'success' in data:
                if data['success'] and data['response']:
                    response_length = len(data['response'])
                    self.log_test("AI Chat", True, f"Response length: {response_length} chars")
                    return True, data['response']
                else:
                    self.log_test("AI Chat", False, f"AI returned unsuccessful response: {data}")
            else:
                self.log_test("AI Chat", False, f"Missing response fields: {data}")
        else:
            self.log_test("AI Chat", False, f"Status: {status}, Data: {data}")
        return False, ""
    
    def test_house_details_endpoint(self):
        """Test the new house details endpoint"""
        print("\n🔍 Testing House Details Endpoint...")
        
        # Test with the specific house mentioned in requirements: ID 13112
        test_house_id = 13112
        success, data, status = self.make_request('GET', f'/api/cleaning/house/{test_house_id}/details')
        
        if success and status == 200:
            # Check if response has the expected structure
            required_sections = ['house', 'management_company', 'senior_resident']
            missing_sections = [section for section in required_sections if section not in data]
            
            if not missing_sections:
                # Check house section
                house = data.get('house', {})
                house_fields = ['id', 'title', 'address', 'apartments', 'entrances', 'floors', 'brigade', 'status']
                missing_house_fields = [field for field in house_fields if field not in house]
                
                # Check management company section
                mc = data.get('management_company', {})
                mc_fields = ['title', 'phone', 'email']
                missing_mc_fields = [field for field in mc_fields if field not in mc]
                
                # Check senior resident section
                sr = data.get('senior_resident', {})
                sr_fields = ['full_name', 'phone', 'email']
                missing_sr_fields = [field for field in sr_fields if field not in sr]
                
                if not missing_house_fields and not missing_mc_fields and not missing_sr_fields:
                    # Verify specific data for house 13112
                    house_info = f"House: {house.get('title', 'N/A')}, Address: {house.get('address', 'N/A')}"
                    mc_info = f"MC: {mc.get('title', 'N/A')}, Email: {mc.get('email', 'N/A')}"
                    apartments = house.get('apartments', 0)
                    entrances = house.get('entrances', 0)
                    floors = house.get('floors', 0)
                    
                    details_info = f"{house_info}, {mc_info}, Apt: {apartments}, Ent: {entrances}, Fl: {floors}"
                    self.log_test("House Details Endpoint", True, details_info)
                    
                    # Verify expected data for house 13112
                    self.verify_house_13112_data(data)
                    return True, data
                else:
                    all_missing = missing_house_fields + missing_mc_fields + missing_sr_fields
                    self.log_test("House Details Endpoint", False, f"Missing fields: {all_missing}")
            else:
                self.log_test("House Details Endpoint", False, f"Missing sections: {missing_sections}")
        else:
            self.log_test("House Details Endpoint", False, f"Status: {status}, Data: {data}")
        
        # Test with invalid house ID
        success, data, status = self.make_request('GET', '/api/cleaning/house/99999/details')
        if status == 404:
            self.log_test("House Details - Invalid ID", True, "Correctly returns 404 for invalid house ID")
        else:
            self.log_test("House Details - Invalid ID", False, f"Expected 404, got {status}")
        
        return False, {}
    
    def verify_house_13112_data(self, data):
        """Verify specific data for house 13112 as mentioned in requirements"""
        house = data.get('house', {})
        mc = data.get('management_company', {})
        
        # Expected data from requirements
        expected_address = "Аллейная 6 п.1"
        expected_mc = "ООО УК Новый город"
        expected_email = "yk.novo-gorod@mail.ru"
        expected_apartments = 119
        expected_entrances = 1
        expected_floors = 14
        
        # Check address
        address = house.get('address', '')
        if expected_address in address or address in expected_address:
            self.log_test("House 13112 - Address Verification", True, f"Address contains: {expected_address}")
        else:
            self.log_test("House 13112 - Address Verification", False, f"Expected '{expected_address}', got '{address}'")
        
        # Check management company
        mc_title = mc.get('title', '')
        if expected_mc in mc_title or mc_title in expected_mc:
            self.log_test("House 13112 - MC Verification", True, f"MC: {mc_title}")
        else:
            self.log_test("House 13112 - MC Verification", False, f"Expected '{expected_mc}', got '{mc_title}'")
        
        # Check email
        mc_email = mc.get('email', '')
        if expected_email in mc_email or mc_email in expected_email:
            self.log_test("House 13112 - Email Verification", True, f"Email: {mc_email}")
        else:
            self.log_test("House 13112 - Email Verification", False, f"Expected '{expected_email}', got '{mc_email}'")
        
        # Check apartment count
        apartments = house.get('apartments', 0)
        if apartments == expected_apartments:
            self.log_test("House 13112 - Apartments Count", True, f"Apartments: {apartments}")
        else:
            self.log_test("House 13112 - Apartments Count", False, f"Expected {expected_apartments}, got {apartments}")
    
    def test_houses_display_requirements(self):
        """Test houses display requirements from the review request"""
        print("\n🔍 Testing Houses Display Requirements...")
        
        success, data, status = self.make_request('GET', '/api/cleaning/houses', params={'limit': 10})
        
        if success and status == 200 and data and 'houses' in data:
            houses = data['houses']
            
            # Check if houses have management company displayed
            houses_with_mc = [h for h in houses if h.get('management_company')]
            mc_percentage = (len(houses_with_mc) / len(houses)) * 100 if houses else 0
            
            if mc_percentage > 50:
                self.log_test("Houses - Management Company Display", True, f"{mc_percentage:.1f}% houses have MC")
            else:
                self.log_test("Houses - Management Company Display", False, f"Only {mc_percentage:.1f}% houses have MC")
            
            # Check if houses have brigade numbers instead of schedule
            houses_with_brigade = [h for h in houses if h.get('brigade')]
            brigade_percentage = (len(houses_with_brigade) / len(houses)) * 100 if houses else 0
            
            if brigade_percentage > 50:
                self.log_test("Houses - Brigade Number Display", True, f"{brigade_percentage:.1f}% houses have brigade")
            else:
                self.log_test("Houses - Brigade Number Display", False, f"Only {brigade_percentage:.1f}% houses have brigade")
            
            # Sample some house data
            if houses:
                sample_house = houses[0]
                sample_info = f"ID: {sample_house.get('id')}, MC: {sample_house.get('management_company', 'N/A')}, Brigade: {sample_house.get('brigade', 'N/A')}"
                self.log_test("Houses - Sample Data", True, sample_info)
            
            return True
        else:
            self.log_test("Houses Display Requirements", False, f"Failed to get houses data")
            return False
    
    def test_bitrix24_integration(self):
        """Test Bitrix24 integration by checking if real data is returned"""
        print("\n🔍 Testing Bitrix24 Integration...")
        
        # Get houses and check if they contain real Bitrix24 data
        success, data, status = self.make_request('GET', '/api/cleaning/houses', params={'limit': 10})
        
        if success and status == 200 and data and 'houses' in data:
            houses = data['houses']
            # Check for signs of real Bitrix24 data
            real_data_indicators = 0
            
            for house in houses[:5]:  # Check first 5 houses
                # Check if house has real ID (not just sequential)
                if house.get('id', 0) > 1000:
                    real_data_indicators += 1
                
                # Check if house has meaningful title/address
                title = house.get('title', '')
                address = house.get('address', '')
                if title and len(title) > 10 and 'дом' in title.lower():
                    real_data_indicators += 1
                
                # Check if house has brigade assigned
                if house.get('brigade'):
                    real_data_indicators += 1
            
            if real_data_indicators >= 3:
                self.log_test("Bitrix24 Integration", True, f"Real data indicators: {real_data_indicators}/15")
                return True
            else:
                self.log_test("Bitrix24 Integration", False, f"Insufficient real data indicators: {real_data_indicators}/15")
        else:
            self.log_test("Bitrix24 Integration", False, f"Failed to get houses data")
        
        return False
    
    def run_comprehensive_test(self):
        """Run all tests"""
        print("🚀 Starting VasDom AudioBot API Testing")
        print(f"📍 Testing URL: {self.base_url}")
        print("=" * 60)
        
        # Test all endpoints
        self.test_root_endpoint()
        stats_success, stats_data = self.test_dashboard_stats()
        houses_success, houses_data = self.test_cleaning_houses()
        filters_success, filters_data = self.test_cleaning_filters()
        ai_success, ai_response = self.test_ai_chat()
        bitrix_success = self.test_bitrix24_integration()
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {len(self.failed_tests)}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if self.failed_tests:
            print("\n❌ FAILED TESTS:")
            for test in self.failed_tests:
                print(f"  - {test['name']}: {test['details']}")
        
        # Print key findings
        if stats_success:
            print(f"\n📈 SYSTEM STATS:")
            print(f"  - Houses: {stats_data.get('total_houses', 'N/A')}")
            print(f"  - Apartments: {stats_data.get('total_apartments', 'N/A')}")
            print(f"  - Brigades: {stats_data.get('active_brigades', 'N/A')}")
            print(f"  - Employees: {stats_data.get('employees', 'N/A')}")
        
        if ai_success:
            print(f"\n🤖 AI RESPONSE SAMPLE:")
            print(f"  {ai_response[:100]}..." if len(ai_response) > 100 else f"  {ai_response}")
        
        return len(self.failed_tests) == 0

def main():
    """Main test execution"""
    tester = VasDomAPITester()
    success = tester.run_comprehensive_test()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())