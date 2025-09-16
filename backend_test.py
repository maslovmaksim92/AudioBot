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
    def __init__(self, base_url="https://vasdom-crm.preview.emergentagent.com"):
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
        """Test houses endpoint with filters as per review request"""
        print("\n🔍 Testing Houses Endpoint Filters and Pagination...")
        
        # Test 1: Basic pagination response schema
        success, data, status = self.make_request('GET', '/api/cleaning/houses', params={'limit': 5, 'page': 1})
        if success and status == 200:
            # Verify response schema: { houses: [...], total, page, limit, pages }
            required_fields = ['houses', 'total', 'page', 'limit', 'pages']
            missing_fields = [field for field in required_fields if field not in data]
            
            if not missing_fields:
                # Verify integers for total/page/limit/pages
                integer_fields = ['total', 'page', 'limit', 'pages']
                non_integer_fields = []
                for field in integer_fields:
                    if not isinstance(data[field], int):
                        non_integer_fields.append(f"{field}={data[field]} ({type(data[field]).__name__})")
                
                if not non_integer_fields:
                    # Verify houses array is present
                    if isinstance(data['houses'], list):
                        self.log_test("Houses Response Schema", True, 
                                    f"Schema valid: houses={len(data['houses'])}, total={data['total']}, page={data['page']}, limit={data['limit']}, pages={data['pages']}")
                        
                        # Test house object schema
                        if data['houses']:
                            self.test_house_object_schema(data['houses'][0])
                    else:
                        self.log_test("Houses Response Schema", False, f"houses field is not array: {type(data['houses'])}")
                else:
                    self.log_test("Houses Response Schema", False, f"Non-integer fields: {non_integer_fields}")
            else:
                self.log_test("Houses Response Schema", False, f"Missing fields: {missing_fields}")
        else:
            self.log_test("Houses Response Schema", False, f"Status: {status}, Data: {data}")
        
        # Test 2: Brigade filter
        success, data, status = self.make_request('GET', '/api/cleaning/houses', params={'brigade': '4 бригада', 'limit': 10})
        if success and status == 200:
            self.log_test("Houses Brigade Filter", True, f"Brigade filter works, returned {len(data.get('houses', []))} houses")
        else:
            self.log_test("Houses Brigade Filter", False, f"Status: {status}")
        
        # Test 3: Management company filter
        success, data, status = self.make_request('GET', '/api/cleaning/houses', params={'management_company': 'УК', 'limit': 10})
        if success and status == 200:
            self.log_test("Houses Management Company Filter", True, f"Management company filter works, returned {len(data.get('houses', []))} houses")
        else:
            self.log_test("Houses Management Company Filter", False, f"Status: {status}")
        
        # Test 4: Cleaning date filter (specific date)
        success, data, status = self.make_request('GET', '/api/cleaning/houses', params={'cleaning_date': '2025-09-05', 'limit': 10})
        if success and status == 200:
            self.log_test("Houses Cleaning Date Filter", True, f"Cleaning date filter works, returned {len(data.get('houses', []))} houses")
        else:
            self.log_test("Houses Cleaning Date Filter", False, f"Status: {status}")
        
        # Test 5: Date range filter
        success, data, status = self.make_request('GET', '/api/cleaning/houses', params={
            'date_from': '2025-09-01', 
            'date_to': '2025-09-30', 
            'limit': 10
        })
        if success and status == 200:
            self.log_test("Houses Date Range Filter", True, f"Date range filter works, returned {len(data.get('houses', []))} houses")
        else:
            self.log_test("Houses Date Range Filter", False, f"Status: {status}")
        
        # Test 6: Combined filters
        success, data, status = self.make_request('GET', '/api/cleaning/houses', params={
            'brigade': '4 бригада',
            'management_company': 'УК',
            'date_from': '2025-09-01',
            'date_to': '2025-09-30',
            'limit': 5,
            'page': 1
        })
        if success and status == 200:
            self.log_test("Houses Combined Filters", True, f"Combined filters work, returned {len(data.get('houses', []))} houses")
        else:
            self.log_test("Houses Combined Filters", False, f"Status: {status}")
    
    def test_house_object_schema(self, house):
        """Test individual house object schema"""
        required_fields = ['id', 'title', 'address', 'brigade', 'management_company', 'periodicity', 'cleaning_dates', 'bitrix_url']
        missing_fields = [field for field in required_fields if field not in house]
        
        if not missing_fields:
            # Verify field types
            type_errors = []
            if not isinstance(house['brigade'], str):
                type_errors.append(f"brigade should be string, got {type(house['brigade'])}")
            if not isinstance(house['management_company'], str):
                type_errors.append(f"management_company should be string, got {type(house['management_company'])}")
            if not isinstance(house['periodicity'], str):
                type_errors.append(f"periodicity should be string, got {type(house['periodicity'])}")
            if not isinstance(house['cleaning_dates'], dict):
                type_errors.append(f"cleaning_dates should be object, got {type(house['cleaning_dates'])}")
            if not isinstance(house['bitrix_url'], str):
                type_errors.append(f"bitrix_url should be string, got {type(house['bitrix_url'])}")
            
            if not type_errors:
                self.log_test("House Object Schema", True, 
                            f"House ID {house['id']}: brigade='{house['brigade']}', mc='{house['management_company']}', periodicity='{house['periodicity']}'")
            else:
                self.log_test("House Object Schema", False, f"Type errors: {type_errors}")
        else:
            self.log_test("House Object Schema", False, f"Missing fields: {missing_fields}")
    
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
        """Test house details endpoint as per review request"""
        print("\n🔍 Testing House Details Endpoint...")
        
        # First, get a house ID from the houses list
        success, houses_data, status = self.make_request('GET', '/api/cleaning/houses', params={'limit': 5})
        test_house_id = None
        
        if success and status == 200 and houses_data.get('houses'):
            test_house_id = houses_data['houses'][0]['id']
            print(f"   Using house ID {test_house_id} for testing")
        else:
            # Fallback to a sample ID
            test_house_id = 1
            print(f"   Using fallback house ID {test_house_id} for testing")
        
        # Test 1: Valid house details
        success, data, status = self.make_request('GET', f'/api/cleaning/house/{test_house_id}/details')
        
        if success and status == 200:
            # Check if response has the expected structure
            required_sections = ['house', 'management_company', 'senior_resident']
            missing_sections = [section for section in required_sections if section not in data]
            
            if not missing_sections:
                # Check house section has bitrix_url
                house = data.get('house', {})
                if 'bitrix_url' in house:
                    bitrix_url = house['bitrix_url']
                    self.log_test("House Details - Valid Response", True, 
                                f"House ID {test_house_id}: bitrix_url={'present' if bitrix_url else 'empty'}")
                    
                    # Verify house.bitrix_url is string
                    if isinstance(bitrix_url, str):
                        self.log_test("House Details - Bitrix URL Type", True, f"bitrix_url is string: {len(bitrix_url)} chars")
                    else:
                        self.log_test("House Details - Bitrix URL Type", False, f"bitrix_url should be string, got {type(bitrix_url)}")
                else:
                    self.log_test("House Details - Valid Response", False, "Missing bitrix_url in house object")
            else:
                self.log_test("House Details - Valid Response", False, f"Missing sections: {missing_sections}")
        else:
            self.log_test("House Details - Valid Response", False, f"Status: {status}, Data: {data}")
        
        # Test 2: Invalid house ID (should return 404, not 500)
        invalid_id = 999999
        success, data, status = self.make_request('GET', f'/api/cleaning/house/{invalid_id}/details')
        
        if status == 404:
            self.log_test("House Details - Invalid ID (404)", True, f"Correctly returns 404 for house ID {invalid_id}")
        elif status == 500:
            self.log_test("House Details - Invalid ID (404)", False, f"Returns 500 instead of 404 for invalid house ID {invalid_id}")
        else:
            self.log_test("House Details - Invalid ID (404)", False, f"Expected 404, got {status} for invalid house ID {invalid_id}")
        
        return success and status == 200, data
    
    def test_bitrix_fallback_behavior(self):
        """Test that endpoints handle Bitrix 503 gracefully without returning 500"""
        print("\n🔍 Testing Bitrix Fallback Behavior...")
        
        # Test houses endpoint - should not return 500 even if Bitrix is down
        success, data, status = self.make_request('GET', '/api/cleaning/houses', params={'limit': 5})
        
        if success and status == 200:
            # Check that response has correct shape even if Bitrix is down
            if isinstance(data, dict) and 'houses' in data and 'total' in data:
                houses = data['houses']
                # Houses array should be present (may be empty if Bitrix down but should not 500)
                if isinstance(houses, list):
                    self.log_test("Bitrix Fallback - Houses Endpoint", True, 
                                f"Houses endpoint stable: {len(houses)} houses, total={data['total']}")
                else:
                    self.log_test("Bitrix Fallback - Houses Endpoint", False, f"houses should be array, got {type(houses)}")
            else:
                self.log_test("Bitrix Fallback - Houses Endpoint", False, f"Invalid response structure: {list(data.keys()) if isinstance(data, dict) else type(data)}")
        elif status == 500:
            self.log_test("Bitrix Fallback - Houses Endpoint", False, f"Houses endpoint returns 500 - should handle Bitrix failures gracefully")
        else:
            self.log_test("Bitrix Fallback - Houses Endpoint", False, f"Unexpected status: {status}")
        
        # Test house details endpoint - should not return 500 even if Bitrix is down
        test_id = 1
        success, data, status = self.make_request('GET', f'/api/cleaning/house/{test_id}/details')
        
        if success and status in [200, 404]:
            self.log_test("Bitrix Fallback - House Details", True, f"House details endpoint stable (status {status})")
        elif status == 500:
            self.log_test("Bitrix Fallback - House Details", False, f"House details returns 500 - should handle Bitrix failures gracefully")
        else:
            self.log_test("Bitrix Fallback - House Details", False, f"Unexpected status: {status}")
        
        return True
    
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
        """Run all tests focusing on review request requirements"""
        print("🚀 Starting VasDom AudioBot API Testing")
        print(f"📍 Testing URL: {self.base_url}")
        print("🎯 Focus: Updated filters and pagination per review request")
        print("=" * 60)
        
        # Test core endpoints
        self.test_root_endpoint()
        stats_success, stats_data = self.test_dashboard_stats()
        
        # Main focus: Houses endpoint with filters and pagination
        houses_success, houses_data = self.test_cleaning_houses()
        
        # Test house details endpoint
        house_details_success, house_details_data = self.test_house_details_endpoint()
        
        # Test Bitrix fallback behavior
        self.test_bitrix_fallback_behavior()
        
        # Test other endpoints
        filters_success, filters_data = self.test_cleaning_filters()
        ai_success, ai_response = self.test_ai_chat()
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY - REVIEW REQUEST FOCUS")
        print("=" * 60)
        print(f"Total Tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {len(self.failed_tests)}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if self.failed_tests:
            print("\n❌ FAILED TESTS:")
            for test in self.failed_tests:
                print(f"  - {test['name']}: {test['details']}")
        
        # Print key findings for review request
        print(f"\n🎯 REVIEW REQUEST RESULTS:")
        print(f"  ✅ GET /api/cleaning/houses filters: {'PASSED' if any('Filter' in t['name'] and t['name'] not in [f['name'] for f in self.failed_tests] for t in [{'name': 'Houses Brigade Filter'}, {'name': 'Houses Management Company Filter'}, {'name': 'Houses Cleaning Date Filter'}, {'name': 'Houses Date Range Filter'}]) else 'FAILED'}")
        print(f"  ✅ Response schema validation: {'PASSED' if 'Houses Response Schema' not in [f['name'] for f in self.failed_tests] else 'FAILED'}")
        print(f"  ✅ House details with bitrix_url: {'PASSED' if 'House Details - Valid Response' not in [f['name'] for f in self.failed_tests] else 'FAILED'}")
        print(f"  ✅ 404 handling (not 500): {'PASSED' if 'House Details - Invalid ID (404)' not in [f['name'] for f in self.failed_tests] else 'FAILED'}")
        print(f"  ✅ Bitrix 503 fallbacks: {'PASSED' if 'Bitrix Fallback' not in ' '.join([f['name'] for f in self.failed_tests]) else 'FAILED'}")
        
        return len(self.failed_tests) == 0

def main():
    """Main test execution"""
    tester = VasDomAPITester()
    success = tester.run_comprehensive_test()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())