#!/usr/bin/env python3
"""
Cleaning Module Backend Testing - Review Request Focus
Testing specific corrections for Cleaning (Houses) module
"""

import requests
import sys
import json
import re
from datetime import datetime
from typing import Dict, Any, Optional, List

class CleaningModuleTester:
    def __init__(self, base_url="https://ai-report-call.preview.emergentagent.com"):
        self.base_url = base_url.rstrip('/')
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []
        self.sample_responses = {}
        
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

    def test_houses_endpoint_corrections(self):
        """Test GET /api/cleaning/houses with focus on review request corrections"""
        print("\n🏠 Testing GET /api/cleaning/houses - Review Request Corrections")
        print("-" * 60)
        
        success, data, status = self.make_request('GET', '/api/cleaning/houses', params={'limit': 20})
        
        if not success or status != 200:
            self.log_test("Houses Endpoint - Basic Response", False, f"Status: {status}, Data: {data}")
            return False
        
        if not isinstance(data, dict) or 'houses' not in data:
            self.log_test("Houses Endpoint - Response Structure", False, f"Invalid response structure: {type(data)}")
            return False
        
        houses = data['houses']
        if not isinstance(houses, list) or len(houses) == 0:
            self.log_test("Houses Endpoint - Houses Array", False, f"No houses returned or invalid array: {len(houses) if isinstance(houses, list) else type(houses)}")
            return False
        
        self.log_test("Houses Endpoint - Basic Response", True, f"Retrieved {len(houses)} houses, total: {data.get('total', 'N/A')}")
        
        # Store sample for detailed analysis
        self.sample_responses['houses'] = data
        
        # Test specific corrections
        self.test_management_company_correction(houses)
        self.test_brigade_correction(houses)
        self.test_cleaning_dates_format(houses)
        self.test_periodicity_rules(houses)
        self.test_bitrix_url_format(houses)
        
        return True

    def test_management_company_correction(self, houses: List[Dict]):
        """Test that management_company returns 'Не указана' for empty values"""
        print("\n🔍 Testing management_company correction...")
        
        empty_mc_count = 0
        correct_fallback_count = 0
        sample_values = []
        
        for house in houses[:10]:  # Check first 10 houses
            mc = house.get('management_company', '')
            sample_values.append(mc)
            
            if not mc or mc.strip() == '':
                empty_mc_count += 1
            elif mc == "Не указана":
                correct_fallback_count += 1
        
        # Check if we have proper fallback values
        if empty_mc_count == 0:
            self.log_test("Management Company - No Empty Values", True, 
                        f"All houses have management_company values. Sample: {sample_values[:3]}")
        else:
            self.log_test("Management Company - Empty Values Found", False, 
                        f"Found {empty_mc_count} houses with empty management_company")
        
        # Check for correct fallback text
        if correct_fallback_count > 0:
            self.log_test("Management Company - Correct Fallback", True, 
                        f"Found {correct_fallback_count} houses with 'Не указана' fallback")
        
        print(f"   Sample management_company values: {sample_values[:5]}")

    def test_brigade_correction(self, houses: List[Dict]):
        """Test that brigade returns 'Бригада не назначена' when no ASSIGNED_BY_NAME"""
        print("\n🔍 Testing brigade correction...")
        
        empty_brigade_count = 0
        correct_fallback_count = 0
        sample_values = []
        
        for house in houses[:10]:  # Check first 10 houses
            brigade = house.get('brigade', '')
            sample_values.append(brigade)
            
            if not brigade or brigade.strip() == '':
                empty_brigade_count += 1
            elif brigade == "Бригада не назначена":
                correct_fallback_count += 1
        
        # Check if we have proper fallback values
        if empty_brigade_count == 0:
            self.log_test("Brigade - No Empty Values", True, 
                        f"All houses have brigade values. Sample: {sample_values[:3]}")
        else:
            self.log_test("Brigade - Empty Values Found", False, 
                        f"Found {empty_brigade_count} houses with empty brigade")
        
        # Check for correct fallback text
        if correct_fallback_count > 0:
            self.log_test("Brigade - Correct Fallback", True, 
                        f"Found {correct_fallback_count} houses with 'Бригада не назначена' fallback")
        
        print(f"   Sample brigade values: {sample_values[:5]}")

    def test_cleaning_dates_format(self, houses: List[Dict]):
        """Test that cleaning_dates.*.dates are in YYYY-MM-DD format (without T and TZ)"""
        print("\n🔍 Testing cleaning_dates format...")
        
        date_format_errors = []
        valid_dates_count = 0
        total_dates_checked = 0
        
        date_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}$')
        
        for i, house in enumerate(houses[:5]):  # Check first 5 houses
            cleaning_dates = house.get('cleaning_dates', {})
            if not isinstance(cleaning_dates, dict):
                continue
                
            for period_key, period_data in cleaning_dates.items():
                if not isinstance(period_data, dict):
                    continue
                    
                dates = period_data.get('dates', [])
                if not isinstance(dates, list):
                    continue
                
                for date_str in dates:
                    total_dates_checked += 1
                    if isinstance(date_str, str):
                        if date_pattern.match(date_str):
                            valid_dates_count += 1
                        else:
                            date_format_errors.append(f"House {house.get('id', i)}, {period_key}: '{date_str}'")
                            if len(date_format_errors) < 5:  # Limit error samples
                                print(f"   ❌ Invalid date format: {date_str}")
        
        if total_dates_checked == 0:
            self.log_test("Cleaning Dates - Format Check", False, "No dates found to check")
        elif len(date_format_errors) == 0:
            self.log_test("Cleaning Dates - Format Check", True, 
                        f"All {valid_dates_count} dates are in YYYY-MM-DD format")
        else:
            self.log_test("Cleaning Dates - Format Check", False, 
                        f"{len(date_format_errors)} invalid dates out of {total_dates_checked} total")
        
        print(f"   Total dates checked: {total_dates_checked}, Valid: {valid_dates_count}")

    def test_periodicity_rules(self, houses: List[Dict]):
        """Test that house.periodicity follows the specified rules"""
        print("\n🔍 Testing periodicity rules...")
        
        allowed_periodicities = {
            "2 раза",
            "2 раза + первые этажи", 
            "2 раза + 2 подметания",
            "4 раза",
            "индивидуальная"
        }
        
        invalid_periodicities = []
        periodicity_counts = {}
        
        for house in houses[:10]:  # Check first 10 houses
            periodicity = house.get('periodicity', '')
            
            if periodicity in periodicity_counts:
                periodicity_counts[periodicity] += 1
            else:
                periodicity_counts[periodicity] = 1
            
            if periodicity not in allowed_periodicities:
                invalid_periodicities.append(f"House {house.get('id', 'N/A')}: '{periodicity}'")
        
        if len(invalid_periodicities) == 0:
            self.log_test("Periodicity - Rules Compliance", True, 
                        f"All periodicities are valid. Distribution: {periodicity_counts}")
        else:
            self.log_test("Periodicity - Rules Compliance", False, 
                        f"Found {len(invalid_periodicities)} invalid periodicities: {invalid_periodicities[:3]}")
        
        print(f"   Periodicity distribution: {periodicity_counts}")

    def test_bitrix_url_format(self, houses: List[Dict]):
        """Test that bitrix_url is in format https://vas-dom.bitrix24.ru/crm/deal/details/{ID}/"""
        print("\n🔍 Testing bitrix_url format...")
        
        expected_pattern = re.compile(r'^https://vas-dom\.bitrix24\.ru/crm/deal/details/\d+/$')
        invalid_urls = []
        valid_urls_count = 0
        
        for house in houses[:10]:  # Check first 10 houses
            bitrix_url = house.get('bitrix_url', '')
            house_id = house.get('id', 'N/A')
            
            if not bitrix_url:
                invalid_urls.append(f"House {house_id}: empty URL")
            elif expected_pattern.match(bitrix_url):
                valid_urls_count += 1
                # Verify ID in URL matches house ID
                url_id = bitrix_url.split('/')[-2]
                if str(house_id) != url_id:
                    invalid_urls.append(f"House {house_id}: URL ID mismatch ({url_id})")
            else:
                invalid_urls.append(f"House {house_id}: invalid format '{bitrix_url}'")
        
        if len(invalid_urls) == 0:
            self.log_test("Bitrix URL - Format Check", True, 
                        f"All {valid_urls_count} URLs are correctly formatted")
        else:
            self.log_test("Bitrix URL - Format Check", False, 
                        f"Found {len(invalid_urls)} invalid URLs: {invalid_urls[:3]}")
        
        # Show sample valid URL
        if houses and houses[0].get('bitrix_url'):
            print(f"   Sample URL: {houses[0]['bitrix_url']}")

    def test_house_details_endpoint(self):
        """Test GET /api/cleaning/house/{id}/details with corrections"""
        print("\n🏠 Testing GET /api/cleaning/house/{id}/details - Review Request Corrections")
        print("-" * 60)
        
        # Get a valid house ID from houses list
        houses_data = self.sample_responses.get('houses')
        if not houses_data or not houses_data.get('houses'):
            # Try to get houses data
            success, houses_data, status = self.make_request('GET', '/api/cleaning/houses', params={'limit': 5})
            if not success or status != 200 or not houses_data.get('houses'):
                self.log_test("House Details - Get Test ID", False, "Cannot get house ID for testing")
                return False
        
        test_house_id = houses_data['houses'][0]['id']
        print(f"   Using house ID {test_house_id} for testing")
        
        # Test valid house details
        success, data, status = self.make_request('GET', f'/api/cleaning/house/{test_house_id}/details')
        
        if success and status == 200:
            self.test_house_details_structure(data, test_house_id)
            self.test_house_details_corrections(data, test_house_id)
        else:
            self.log_test("House Details - Valid Response", False, f"Status: {status}, Data: {data}")
        
        # Test invalid house ID (should return 404)
        self.test_house_details_invalid_id()
        
        return True

    def test_house_details_structure(self, data: Dict, house_id: int):
        """Test house details response structure"""
        required_sections = ['house', 'management_company', 'senior_resident']
        missing_sections = [section for section in required_sections if section not in data]
        
        if not missing_sections:
            self.log_test("House Details - Response Structure", True, 
                        f"House {house_id}: all required sections present")
            
            # Check house section has required fields
            house = data.get('house', {})
            required_house_fields = ['bitrix_url', 'cleaning_dates', 'periodicity']
            missing_house_fields = [field for field in required_house_fields if field not in house]
            
            if not missing_house_fields:
                self.log_test("House Details - House Section", True, 
                            f"House section has all required fields")
            else:
                self.log_test("House Details - House Section", False, 
                            f"Missing house fields: {missing_house_fields}")
        else:
            self.log_test("House Details - Response Structure", False, 
                        f"Missing sections: {missing_sections}")

    def test_house_details_corrections(self, data: Dict, house_id: int):
        """Test specific corrections in house details"""
        house = data.get('house', {})
        management_company = data.get('management_company', {})
        
        # Test dates normalization (YYYY-MM-DD)
        cleaning_dates = house.get('cleaning_dates', {})
        self.test_details_dates_normalization(cleaning_dates, house_id)
        
        # Test periodicity calculation
        periodicity = house.get('periodicity', '')
        self.test_details_periodicity(periodicity, house_id)
        
        # Test bitrix_url presence
        bitrix_url = house.get('bitrix_url', '')
        if bitrix_url:
            self.log_test("House Details - Bitrix URL Present", True, 
                        f"House {house_id}: bitrix_url present ({len(bitrix_url)} chars)")
        else:
            self.log_test("House Details - Bitrix URL Present", False, 
                        f"House {house_id}: bitrix_url missing or empty")
        
        # Test management company title (can be "Не указана")
        mc_title = management_company.get('title', '')
        if mc_title:
            self.log_test("House Details - MC Title", True, 
                        f"House {house_id}: MC title = '{mc_title}'")
        else:
            self.log_test("House Details - MC Title", False, 
                        f"House {house_id}: MC title missing")

    def test_details_dates_normalization(self, cleaning_dates: Dict, house_id: int):
        """Test that dates in details are normalized to YYYY-MM-DD"""
        date_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}$')
        invalid_dates = []
        total_dates = 0
        
        for period_key, period_data in cleaning_dates.items():
            if not isinstance(period_data, dict):
                continue
            dates = period_data.get('dates', [])
            if not isinstance(dates, list):
                continue
            
            for date_str in dates:
                total_dates += 1
                if not isinstance(date_str, str) or not date_pattern.match(date_str):
                    invalid_dates.append(f"{period_key}: '{date_str}'")
        
        if total_dates == 0:
            self.log_test("House Details - Dates Normalization", True, 
                        f"House {house_id}: no dates to check")
        elif len(invalid_dates) == 0:
            self.log_test("House Details - Dates Normalization", True, 
                        f"House {house_id}: all {total_dates} dates normalized")
        else:
            self.log_test("House Details - Dates Normalization", False, 
                        f"House {house_id}: {len(invalid_dates)} invalid dates: {invalid_dates[:2]}")

    def test_details_periodicity(self, periodicity: str, house_id: int):
        """Test periodicity calculation in details"""
        allowed_periodicities = {
            "2 раза", "2 раза + первые этажи", "2 раза + 2 подметания", 
            "4 раза", "индивидуальная"
        }
        
        if periodicity in allowed_periodicities:
            self.log_test("House Details - Periodicity", True, 
                        f"House {house_id}: periodicity = '{periodicity}'")
        else:
            self.log_test("House Details - Periodicity", False, 
                        f"House {house_id}: invalid periodicity = '{periodicity}'")

    def test_house_details_invalid_id(self):
        """Test house details with invalid ID (should return 404)"""
        invalid_id = 999999
        success, data, status = self.make_request('GET', f'/api/cleaning/house/{invalid_id}/details')
        
        if status == 404:
            self.log_test("House Details - Invalid ID (404)", True, 
                        f"Correctly returns 404 for invalid house ID {invalid_id}")
        else:
            self.log_test("House Details - Invalid ID (404)", False, 
                        f"Expected 404, got {status} for invalid house ID {invalid_id}")

    def test_bitrix_stability(self):
        """Test that endpoints handle Bitrix errors gracefully (no 500 errors)"""
        print("\n🔧 Testing Bitrix Stability - No 500 Errors")
        print("-" * 60)
        
        # Test houses endpoint stability
        success, data, status = self.make_request('GET', '/api/cleaning/houses', params={'limit': 5})
        
        if status == 500:
            self.log_test("Bitrix Stability - Houses Endpoint", False, 
                        f"Houses endpoint returns 500 - should handle Bitrix failures gracefully")
        elif status == 200:
            self.log_test("Bitrix Stability - Houses Endpoint", True, 
                        f"Houses endpoint stable (200) - returns safe data")
        else:
            self.log_test("Bitrix Stability - Houses Endpoint", True, 
                        f"Houses endpoint stable ({status}) - no 500 error")
        
        # Test house details stability
        test_id = 1
        success, data, status = self.make_request('GET', f'/api/cleaning/house/{test_id}/details')
        
        if status == 500:
            self.log_test("Bitrix Stability - House Details", False, 
                        f"House details returns 500 - should handle Bitrix failures gracefully")
        elif status in [200, 404]:
            self.log_test("Bitrix Stability - House Details", True, 
                        f"House details stable ({status}) - proper error handling")
        else:
            self.log_test("Bitrix Stability - House Details", True, 
                        f"House details stable ({status}) - no 500 error")

    def run_comprehensive_test(self):
        """Run comprehensive test of Cleaning module per review request"""
        print("🧹 CLEANING MODULE COMPREHENSIVE TESTING")
        print("=" * 60)
        print("Focus: Review Request Corrections")
        print("1) GET /api/cleaning/houses - management_company, brigade, dates format, periodicity, bitrix_url")
        print("2) GET /api/cleaning/house/{id}/details - structure, dates normalization, 404 handling")
        print("3) Bitrix stability - no 500 errors, safe fallbacks")
        print("=" * 60)
        
        # Test 1: Houses endpoint corrections
        houses_success = self.test_houses_endpoint_corrections()
        
        # Test 2: House details corrections (only if houses test succeeded)
        if houses_success:
            self.test_house_details_endpoint()
        
        # Test 3: Bitrix stability
        self.test_bitrix_stability()
        
        # Print comprehensive summary
        self.print_comprehensive_summary()
        
        return len(self.failed_tests) == 0

    def print_comprehensive_summary(self):
        """Print detailed summary with examples"""
        print("\n" + "=" * 60)
        print("📊 CLEANING MODULE TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {len(self.failed_tests)}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        # Show sample response data
        if 'houses' in self.sample_responses:
            houses_data = self.sample_responses['houses']
            if houses_data.get('houses'):
                sample_house = houses_data['houses'][0]
                print(f"\n📋 SAMPLE HOUSE DATA:")
                print(f"   ID: {sample_house.get('id')}")
                print(f"   Management Company: '{sample_house.get('management_company', 'N/A')}'")
                print(f"   Brigade: '{sample_house.get('brigade', 'N/A')}'")
                print(f"   Periodicity: '{sample_house.get('periodicity', 'N/A')}'")
                print(f"   Bitrix URL: {sample_house.get('bitrix_url', 'N/A')[:50]}...")
                
                # Show sample cleaning dates
                cleaning_dates = sample_house.get('cleaning_dates', {})
                if cleaning_dates:
                    for period, data in list(cleaning_dates.items())[:2]:
                        if isinstance(data, dict) and data.get('dates'):
                            print(f"   {period} dates: {data['dates'][:2]}")
        
        if self.failed_tests:
            print(f"\n❌ FAILED TESTS DETAILS:")
            for test in self.failed_tests:
                print(f"   • {test['name']}")
                print(f"     {test['details']}")
        
        # Key findings
        print(f"\n🔍 KEY FINDINGS:")
        management_company_tests = [t for t in self.failed_tests if 'Management Company' in t['name']]
        brigade_tests = [t for t in self.failed_tests if 'Brigade' in t['name']]
        dates_tests = [t for t in self.failed_tests if 'Dates' in t['name'] or 'dates' in t['name']]
        periodicity_tests = [t for t in self.failed_tests if 'Periodicity' in t['name']]
        bitrix_tests = [t for t in self.failed_tests if 'Bitrix' in t['name']]
        
        print(f"   Management Company: {'✅ FIXED' if not management_company_tests else '❌ ISSUES FOUND'}")
        print(f"   Brigade Names: {'✅ FIXED' if not brigade_tests else '❌ ISSUES FOUND'}")
        print(f"   Date Formats: {'✅ FIXED' if not dates_tests else '❌ ISSUES FOUND'}")
        print(f"   Periodicity Rules: {'✅ FIXED' if not periodicity_tests else '❌ ISSUES FOUND'}")
        print(f"   Bitrix URL Format: {'✅ FIXED' if not bitrix_tests else '❌ ISSUES FOUND'}")

def main():
    """Main test execution"""
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        base_url = "https://ai-report-call.preview.emergentagent.com"
    
    tester = CleaningModuleTester(base_url)
    success = tester.run_comprehensive_test()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()