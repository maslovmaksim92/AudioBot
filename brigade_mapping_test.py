#!/usr/bin/env python3
"""
Brigade Name Mapping Test
Focused testing for brigade name mapping functionality as per review request
"""

import requests
import sys
import json
from typing import Dict, Any, Optional

class BrigadeMappingTester:
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
    
    def make_request(self, method: str, endpoint: str, params: Optional[Dict] = None) -> tuple:
        """Make HTTP request and return (success, response_data, status_code)"""
        url = f"{self.base_url}{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params, timeout=30)
            else:
                return False, {}, 0
                
            return True, response.json() if response.content else {}, response.status_code
            
        except requests.exceptions.Timeout:
            return False, {"error": "Request timeout"}, 0
        except requests.exceptions.ConnectionError:
            return False, {"error": "Connection error"}, 0
        except Exception as e:
            return False, {"error": str(e)}, 0
    
    def test_houses_response_shape(self):
        """Test GET /api/cleaning/houses response shape matches HousesResponse"""
        print("\n🔍 Testing Houses Response Shape...")
        
        success, data, status = self.make_request('GET', '/api/cleaning/houses', {'limit': 10})
        
        if not success or status != 200:
            self.log_test("Houses Response Shape", False, f"Request failed - Status: {status}, Data: {data}")
            return False
        
        # Check top-level structure
        required_top_fields = ['houses', 'total', 'page', 'limit', 'pages']
        missing_top_fields = [field for field in required_top_fields if field not in data]
        
        if missing_top_fields:
            self.log_test("Houses Response Shape", False, f"Missing top-level fields: {missing_top_fields}")
            return False
        
        # Check pagination fields are integers
        pagination_fields = ['total', 'page', 'limit', 'pages']
        non_integer_fields = []
        for field in pagination_fields:
            if not isinstance(data[field], int):
                non_integer_fields.append(f"{field}={data[field]} ({type(data[field]).__name__})")
        
        if non_integer_fields:
            self.log_test("Houses Response Shape", False, f"Non-integer pagination fields: {non_integer_fields}")
            return False
        
        # Check houses array
        if not isinstance(data['houses'], list):
            self.log_test("Houses Response Shape", False, f"'houses' should be list, got {type(data['houses']).__name__}")
            return False
        
        self.log_test("Houses Response Shape", True, f"Valid HousesResponse structure with {len(data['houses'])} houses")
        return True, data
    
    def test_house_brigade_field(self):
        """Test each house has 'brigade' field as string with no raw ASSIGNED_BY_ID"""
        print("\n🔍 Testing House Brigade Field...")
        
        success, data, status = self.make_request('GET', '/api/cleaning/houses', {'limit': 20})
        
        if not success or status != 200 or 'houses' not in data:
            self.log_test("House Brigade Field", False, f"Failed to get houses data - Status: {status}")
            return False
        
        houses = data['houses']
        if not houses:
            self.log_test("House Brigade Field", False, "No houses returned to test")
            return False
        
        brigade_field_issues = []
        raw_id_leaks = []
        brigade_types = {}
        
        for i, house in enumerate(houses):
            # Check if brigade field exists
            if 'brigade' not in house:
                brigade_field_issues.append(f"House {house.get('id', i)} missing 'brigade' field")
                continue
            
            brigade_value = house['brigade']
            
            # Check if brigade is string
            if not isinstance(brigade_value, str):
                brigade_field_issues.append(f"House {house.get('id', i)} brigade is {type(brigade_value).__name__}, not string")
                continue
            
            # Track brigade value types
            if brigade_value == "":
                brigade_types['empty'] = brigade_types.get('empty', 0) + 1
            elif brigade_value.isdigit():
                raw_id_leaks.append(f"House {house.get('id', i)} has raw ID '{brigade_value}' as brigade")
            else:
                brigade_types['named'] = brigade_types.get('named', 0) + 1
        
        # Report results
        if brigade_field_issues:
            self.log_test("House Brigade Field", False, f"Brigade field issues: {brigade_field_issues[:3]}")
            return False
        
        if raw_id_leaks:
            self.log_test("House Brigade Field", False, f"Raw ASSIGNED_BY_ID leaks: {raw_id_leaks[:3]}")
            return False
        
        brigade_summary = f"Empty: {brigade_types.get('empty', 0)}, Named: {brigade_types.get('named', 0)}"
        self.log_test("House Brigade Field", True, f"All brigade fields are strings. {brigade_summary}")
        return True
    
    def test_house_details_brigade_field(self):
        """Test GET /api/cleaning/house/{id}/details returns house.brigade as string"""
        print("\n🔍 Testing House Details Brigade Field...")
        
        # First get a house ID to test with
        success, houses_data, status = self.make_request('GET', '/api/cleaning/houses', {'limit': 5})
        
        if not success or status != 200 or not houses_data.get('houses'):
            # Try with a known house ID
            test_house_id = 13112
        else:
            test_house_id = houses_data['houses'][0]['id']
        
        # Test house details endpoint
        success, data, status = self.make_request('GET', f'/api/cleaning/house/{test_house_id}/details')
        
        if not success or status != 200:
            self.log_test("House Details Brigade Field", False, f"Request failed - Status: {status}, Data: {data}")
            return False
        
        # Check response structure
        if 'house' not in data:
            self.log_test("House Details Brigade Field", False, "Response missing 'house' section")
            return False
        
        house = data['house']
        
        # Check brigade field exists
        if 'brigade' not in house:
            self.log_test("House Details Brigade Field", False, "House section missing 'brigade' field")
            return False
        
        brigade_value = house['brigade']
        
        # Check brigade is string
        if not isinstance(brigade_value, str):
            self.log_test("House Details Brigade Field", False, f"Brigade is {type(brigade_value).__name__}, not string")
            return False
        
        # Check it's not a raw ID
        if brigade_value.isdigit() and len(brigade_value) > 2:
            self.log_test("House Details Brigade Field", False, f"Brigade appears to be raw ID: '{brigade_value}'")
            return False
        
        brigade_info = f"House {test_house_id} brigade: '{brigade_value}'"
        self.log_test("House Details Brigade Field", True, brigade_info)
        return True
    
    def test_house_details_404_handling(self):
        """Test house details endpoint returns 404 for non-existent house, not 500"""
        print("\n🔍 Testing House Details 404 Handling...")
        
        # Test with clearly non-existent house ID
        non_existent_id = 999999
        success, data, status = self.make_request('GET', f'/api/cleaning/house/{non_existent_id}/details')
        
        if status == 404:
            self.log_test("House Details 404 Handling", True, f"Correctly returns 404 for house {non_existent_id}")
            return True
        elif status == 500:
            self.log_test("House Details 404 Handling", False, f"Returns 500 instead of 404 for non-existent house")
            return False
        else:
            self.log_test("House Details 404 Handling", False, f"Unexpected status {status} for non-existent house")
            return False
    
    def test_brigade_name_enrichment(self):
        """Test that brigade names are properly enriched (not just raw IDs)"""
        print("\n🔍 Testing Brigade Name Enrichment...")
        
        success, data, status = self.make_request('GET', '/api/cleaning/houses', {'limit': 10})
        
        if not success or status != 200 or not data.get('houses'):
            self.log_test("Brigade Name Enrichment", False, f"Failed to get houses data - Status: {status}")
            return False
        
        houses = data['houses']
        enriched_brigades = []
        raw_id_brigades = []
        empty_brigades = 0
        
        for house in houses:
            brigade = house.get('brigade', '')
            
            if brigade == '':
                empty_brigades += 1
            elif brigade.isdigit():
                raw_id_brigades.append(f"House {house.get('id')}: '{brigade}'")
            else:
                enriched_brigades.append(f"House {house.get('id')}: '{brigade}'")
        
        # Report findings
        total_houses = len(houses)
        enriched_count = len(enriched_brigades)
        raw_count = len(raw_id_brigades)
        
        if raw_count > 0:
            self.log_test("Brigade Name Enrichment", False, f"Found {raw_count} raw ID brigades: {raw_id_brigades[:2]}")
            return False
        
        if enriched_count == 0 and empty_brigades < total_houses:
            self.log_test("Brigade Name Enrichment", False, "No enriched brigade names found")
            return False
        
        enrichment_info = f"Enriched: {enriched_count}, Empty: {empty_brigades}, Total: {total_houses}"
        self.log_test("Brigade Name Enrichment", True, enrichment_info)
        
        # Show sample enriched names
        if enriched_brigades:
            print(f"   Sample enriched brigades: {enriched_brigades[:3]}")
        
        return True
    
    def run_brigade_mapping_tests(self):
        """Run all brigade mapping tests"""
        print("🚀 Starting Brigade Name Mapping Tests")
        print(f"📍 Testing URL: {self.base_url}")
        print("=" * 60)
        
        # Run all tests
        shape_success, houses_data = self.test_houses_response_shape() or (False, {})
        brigade_field_success = self.test_house_brigade_field()
        details_brigade_success = self.test_house_details_brigade_field()
        not_found_success = self.test_house_details_404_handling()
        enrichment_success = self.test_brigade_name_enrichment()
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 BRIGADE MAPPING TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {len(self.failed_tests)}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if self.failed_tests:
            print("\n❌ FAILED TESTS:")
            for test in self.failed_tests:
                print(f"  - {test['name']}: {test['details']}")
        
        # Overall assessment
        critical_tests_passed = shape_success and brigade_field_success and details_brigade_success
        
        if critical_tests_passed:
            print("\n✅ CRITICAL BRIGADE MAPPING TESTS PASSED")
            print("   - Houses response has correct shape")
            print("   - Brigade fields are strings without raw IDs")
            print("   - House details brigade field works correctly")
        else:
            print("\n❌ CRITICAL BRIGADE MAPPING TESTS FAILED")
            print("   Brigade name mapping implementation needs fixes")
        
        return len(self.failed_tests) == 0

def main():
    """Main test execution"""
    tester = BrigadeMappingTester()
    success = tester.run_brigade_mapping_tests()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())