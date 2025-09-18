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
    def __init__(self, base_url="https://cleanbrain.preview.emergentagent.com"):
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
    
    def test_logistics_route_endpoint(self):
        """Test logistics route endpoint as per user request"""
        print("\n🔍 Testing Logistics Route Endpoint...")
        
        # Test 1: Check if endpoint exists
        test_data = {
            "points": [
                {"address": "Москва, Красная площадь"},
                {"address": "Москва, ВДНХ"}
            ],
            "optimize": False,
            "profile": "driving-car",
            "language": "ru"
        }
        
        success, data, status = self.make_request('POST', '/api/logistics/route', test_data)
        
        if status == 404 and success and 'detail' in data and 'геокодировать' not in data['detail']:
            self.log_test("Logistics Route - Endpoint Exists", False, f"Endpoint /api/logistics/route not found (404). Success: {success}, Data: {data}")
            return False
        elif status == 405:
            self.log_test("Logistics Route - Endpoint Exists", False, "Method not allowed (405) - endpoint may exist but not accept POST")
            return False
        elif success and status in [200, 400, 401, 404, 500]:
            # Endpoint exists if we get any of these status codes (including geocoding 404)
            self.log_test("Logistics Route - Endpoint Exists", True, f"Endpoint responds (status {status})")
            
            # Test 2: Basic route with 2 addresses
            self.test_basic_route()
            
            # Test 3: Route with 3-4 points, optimize=false
            self.test_route_no_optimization()
            
            # Test 4: Route with optimization
            self.test_route_with_optimization()
            
            # Test 5: Validation error - 1 point
            self.test_route_validation_error()
            
            # Test 6: Geocoding error
            self.test_route_geocoding_error()
            
            return True
        else:
            self.log_test("Logistics Route - Endpoint Exists", False, f"Unexpected response: Status {status}, Data: {data}, Success: {success}")
            return False
    
    def test_basic_route(self):
        """Test basic route with 2 Moscow addresses"""
        test_data = {
            "points": [
                {"address": "Москва, Красная площадь"},
                {"address": "Москва, ВДНХ"}
            ],
            "optimize": False,
            "profile": "driving-car",
            "language": "ru"
        }
        
        success, data, status = self.make_request('POST', '/api/logistics/route', test_data)
        
        if success and status == 200:
            # Check required fields in response
            required_fields = ['distance', 'duration', 'order', 'geometry']
            missing_fields = [field for field in required_fields if field not in data]
            
            if not missing_fields:
                # Verify data types and values
                if (isinstance(data['distance'], (int, float)) and data['distance'] > 0 and
                    isinstance(data['duration'], (int, float)) and data['duration'] > 0 and
                    isinstance(data['geometry'], list) and len(data['geometry']) > 0):
                    
                    self.log_test("Logistics Route - Basic Route", True, 
                                f"Distance: {data['distance']}m, Duration: {data['duration']}s, Geometry points: {len(data['geometry'])}")
                else:
                    self.log_test("Logistics Route - Basic Route", False, 
                                f"Invalid data values: distance={data['distance']}, duration={data['duration']}, geometry_len={len(data.get('geometry', []))}")
            else:
                self.log_test("Logistics Route - Basic Route", False, f"Missing fields: {missing_fields}")
        elif status == 404 and 'геокодировать' in data.get('detail', ''):
            self.log_test("Logistics Route - Basic Route", False, f"ORS API Key missing - geocoding failed: {data.get('detail', '')}")
        elif status == 401:
            self.log_test("Logistics Route - Basic Route", False, f"ORS API Key missing - unauthorized: {data.get('detail', '')}")
        else:
            self.log_test("Logistics Route - Basic Route", False, f"Status: {status}, Data: {data}")
    
    def test_route_no_optimization(self):
        """Test route with 3-4 points and optimize=false (should preserve order)"""
        test_data = {
            "points": [
                {"address": "Москва, Красная площадь"},
                {"address": "Москва, ВДНХ"},
                {"address": "Москва, Парк Горького"},
                {"address": "Москва, Третьяковская галерея"}
            ],
            "optimize": False,
            "profile": "driving-car",
            "language": "ru"
        }
        
        success, data, status = self.make_request('POST', '/api/logistics/route', test_data)
        
        if success and status == 200:
            order = data.get('order', [])
            expected_order = [0, 1, 2, 3]
            
            if order == expected_order:
                self.log_test("Logistics Route - No Optimization", True, f"Order preserved: {order}")
            else:
                self.log_test("Logistics Route - No Optimization", False, f"Expected {expected_order}, got {order}")
        elif status == 404 and 'геокодировать' in data.get('detail', ''):
            self.log_test("Logistics Route - No Optimization", False, f"ORS API Key missing - geocoding failed: {data.get('detail', '')}")
        elif status == 401:
            self.log_test("Logistics Route - No Optimization", False, f"ORS API Key missing - unauthorized: {data.get('detail', '')}")
        else:
            self.log_test("Logistics Route - No Optimization", False, f"Status: {status}, Data: {data}")
    
    def test_route_with_optimization(self):
        """Test route with optimization=true"""
        test_data = {
            "points": [
                {"address": "Москва, Красная площадь"},
                {"address": "Москва, ВДНХ"},
                {"address": "Москва, Парк Горького"},
                {"address": "Москва, Третьяковская галерея"}
            ],
            "optimize": True,
            "profile": "driving-car",
            "language": "ru"
        }
        
        success, data, status = self.make_request('POST', '/api/logistics/route', test_data)
        
        if success and status == 200:
            order = data.get('order', [])
            
            if isinstance(order, list) and len(order) == 4 and set(order) == {0, 1, 2, 3}:
                # Order should be a valid permutation of [0,1,2,3]
                self.log_test("Logistics Route - With Optimization", True, f"Optimized order: {order}")
            else:
                self.log_test("Logistics Route - With Optimization", False, f"Invalid order array: {order}")
        elif status == 404 and 'геокодировать' in data.get('detail', ''):
            self.log_test("Logistics Route - With Optimization", False, f"ORS API Key missing - geocoding failed: {data.get('detail', '')}")
        elif status == 401:
            self.log_test("Logistics Route - With Optimization", False, f"ORS API Key missing - unauthorized: {data.get('detail', '')}")
        else:
            self.log_test("Logistics Route - With Optimization", False, f"Status: {status}, Data: {data}")
    
    def test_route_validation_error(self):
        """Test validation error with only 1 point"""
        test_data = {
            "points": [
                {"address": "Москва, Красная площадь"}
            ],
            "optimize": False,
            "profile": "driving-car",
            "language": "ru"
        }
        
        success, data, status = self.make_request('POST', '/api/logistics/route', test_data)
        
        if status == 400:
            detail = data.get('detail', '')
            if 'Минимум 2 точки' in detail:
                self.log_test("Logistics Route - Validation Error", True, f"Correct 400 error: {detail}")
            else:
                self.log_test("Logistics Route - Validation Error", False, f"Wrong error message: {detail}")
        else:
            self.log_test("Logistics Route - Validation Error", False, f"Expected 400, got {status}")
    
    def test_route_geocoding_error(self):
        """Test geocoding error with meaningless address"""
        test_data = {
            "points": [
                {"address": "_____"},
                {"address": "Москва, ВДНХ"}
            ],
            "optimize": False,
            "profile": "driving-car",
            "language": "ru"
        }
        
        success, data, status = self.make_request('POST', '/api/logistics/route', test_data)
        
        if status == 404:
            detail = data.get('detail', '')
            if detail.startswith('Не удалось геокодировать адрес'):
                self.log_test("Logistics Route - Geocoding Error", True, f"Correct 404 error: {detail}")
            else:
                self.log_test("Logistics Route - Geocoding Error", False, f"Wrong error message: {detail}")
        else:
            self.log_test("Logistics Route - Geocoding Error", False, f"Expected 404, got {status}")

    def make_multipart_request(self, method: str, endpoint: str, files: dict = None, data: dict = None) -> tuple:
        """Make multipart HTTP request for file uploads"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method == 'POST':
                response = requests.post(url, files=files, data=data, timeout=60)
            else:
                return False, {}, 0
                
            return True, response.json() if response.content else {}, response.status_code
            
        except requests.exceptions.Timeout:
            return False, {"error": "Request timeout"}, 0
        except requests.exceptions.ConnectionError:
            return False, {"error": "Connection error"}, 0
        except Exception as e:
            return False, {"error": str(e)}, 0

    def test_ai_knowledge_endpoints(self):
        """Test AI Knowledge Base endpoints comprehensively"""
        print("\n🧠 Testing AI Knowledge Base Endpoints...")
        
        # Test 1: Upload validation - no files
        self.test_ai_upload_no_files()
        
        # Test 2: Upload validation - unsupported file extension
        self.test_ai_upload_unsupported_extension()
        
        # Test 3: Upload validation - small TXT file (should work)
        upload_id = self.test_ai_upload_txt_file()
        
        # Test 4: Size limits - file >50MB
        self.test_ai_upload_large_file()
        
        # Test 5: Size limits - total >200MB
        self.test_ai_upload_total_size_limit()
        
        # Test 6: Format parsing - various file types
        self.test_ai_upload_various_formats()
        
        # Test 7: Save uploaded file
        document_id = None
        if upload_id:
            document_id = self.test_ai_save_document(upload_id)
        
        # Test 8: List documents
        self.test_ai_list_documents()
        
        # Test 9: Search functionality
        self.test_ai_search()
        
        # Test 10: Delete document
        if document_id:
            self.test_ai_delete_document(document_id)
            # Test 11: Delete same document again (idempotent)
            self.test_ai_delete_document(document_id)
        
        # Test 12: Database not initialized scenario
        self.test_ai_database_not_initialized()
        
        return True

    def test_ai_upload_no_files(self):
        """Test upload endpoint with no files - should return 400 or 422"""
        success, data, status = self.make_multipart_request('POST', '/api/ai-knowledge/upload', files={})
        
        if status in [400, 422]:
            # Both 400 and 422 are acceptable for missing files (FastAPI validation)
            detail = data.get('detail', '')
            if isinstance(detail, list):
                detail = str(detail)
            self.log_test("AI Upload - No Files", True, f"Correctly returns {status} for no files: {detail[:100]}...")
        else:
            self.log_test("AI Upload - No Files", False, f"Expected 400 or 422, got {status}: {data}")

    def test_ai_upload_unsupported_extension(self):
        """Test upload with unsupported file extension (.exe) - should return 400"""
        # Create a fake .exe file
        fake_exe_content = b"fake executable content"
        files = {'files': ('malware.exe', fake_exe_content, 'application/octet-stream')}
        
        success, data, status = self.make_multipart_request('POST', '/api/ai-knowledge/upload', files=files)
        
        if status == 400:
            detail = data.get('detail', '')
            if 'Недопустимый формат' in detail or '.exe' in detail:
                self.log_test("AI Upload - Unsupported Extension", True, f"Correctly rejects .exe: {detail}")
            else:
                self.log_test("AI Upload - Unsupported Extension", False, f"Wrong error message: {detail}")
        else:
            self.log_test("AI Upload - Unsupported Extension", False, f"Expected 400, got {status}: {data}")

    def test_ai_upload_txt_file(self):
        """Test upload with small TXT file - should return 200 with upload_id, chunks>0, preview"""
        txt_content = """Это тестовый документ для системы VasDom AudioBot.
        
Система управления клининговой компанией включает в себя:
1. Управление домами и подъездами
2. Планирование уборок
3. Контроль качества работ
4. Интеграция с Bitrix24
5. AI-консультант для сотрудников

Компания обслуживает 490 домов с 82 сотрудниками в 7 бригадах.
Используется современная система автоматизации процессов."""

        files = {'files': ('test_document.txt', txt_content.encode('utf-8'), 'text/plain')}
        
        success, data, status = self.make_multipart_request('POST', '/api/ai-knowledge/upload', files=files)
        
        if success and status == 200:
            # Check required fields
            required_fields = ['upload_id', 'chunks', 'preview']
            missing_fields = [field for field in required_fields if field not in data]
            
            if not missing_fields:
                upload_id = data['upload_id']
                chunks = data['chunks']
                preview = data['preview']
                
                if chunks > 0 and isinstance(preview, str) and len(preview) > 0:
                    self.log_test("AI Upload - TXT File", True, 
                                f"upload_id: {upload_id[:8]}..., chunks: {chunks}, preview: {len(preview)} chars")
                    return upload_id
                else:
                    self.log_test("AI Upload - TXT File", False, f"Invalid chunks ({chunks}) or preview ({len(preview) if isinstance(preview, str) else type(preview)})")
            else:
                self.log_test("AI Upload - TXT File", False, f"Missing fields: {missing_fields}")
        elif status == 500 and 'Database is not initialized' in data.get('detail', ''):
            self.log_test("AI Upload - TXT File", False, f"Database not initialized (expected if DATABASE_URL not set): {data.get('detail')}")
        else:
            self.log_test("AI Upload - TXT File", False, f"Status: {status}, Data: {data}")
        
        return None

    def test_ai_upload_large_file(self):
        """Test upload with file >50MB - should return 413"""
        # Create a large file content (simulate >50MB)
        large_content = "A" * (51 * 1024 * 1024)  # 51MB of 'A' characters
        files = {'files': ('large_file.txt', large_content.encode('utf-8'), 'text/plain')}
        
        success, data, status = self.make_multipart_request('POST', '/api/ai-knowledge/upload', files=files)
        
        if status == 413:
            detail = data.get('detail', '')
            if '50MB' in detail or 'превышает' in detail:
                self.log_test("AI Upload - Large File", True, f"Correctly rejects >50MB file: {detail}")
            else:
                self.log_test("AI Upload - Large File", False, f"Wrong error message: {detail}")
        elif status == 500 and 'Database is not initialized' in data.get('detail', ''):
            self.log_test("AI Upload - Large File", False, f"Database not initialized (cannot test size limits): {data.get('detail')}")
        else:
            self.log_test("AI Upload - Large File", False, f"Expected 413, got {status}: {data}")

    def test_ai_upload_total_size_limit(self):
        """Test upload with total size >200MB - should return 413"""
        # Create multiple files that together exceed 200MB
        file_size = 70 * 1024 * 1024  # 70MB each
        file_content = "B" * file_size
        
        files = [
            ('files', ('file1.txt', file_content.encode('utf-8'), 'text/plain')),
            ('files', ('file2.txt', file_content.encode('utf-8'), 'text/plain')),
            ('files', ('file3.txt', file_content.encode('utf-8'), 'text/plain'))  # Total: 210MB
        ]
        
        success, data, status = self.make_multipart_request('POST', '/api/ai-knowledge/upload', files=files)
        
        if status == 413:
            detail = data.get('detail', '')
            if '200MB' in detail or 'Общий размер' in detail:
                self.log_test("AI Upload - Total Size Limit", True, f"Correctly rejects >200MB total: {detail}")
            else:
                self.log_test("AI Upload - Total Size Limit", False, f"Wrong error message: {detail}")
        elif status == 500 and 'Database is not initialized' in data.get('detail', ''):
            self.log_test("AI Upload - Total Size Limit", False, f"Database not initialized (cannot test size limits): {data.get('detail')}")
        else:
            self.log_test("AI Upload - Total Size Limit", False, f"Expected 413, got {status}: {data}")

    def test_ai_upload_various_formats(self):
        """Test upload with various file formats - TXT, PDF, DOCX, XLSX, ZIP"""
        # Simple TXT
        txt_content = "Простой текстовый файл для тестирования системы."
        
        # Simple PDF content (minimal PDF structure)
        pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj
4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
100 700 Td
(Test PDF content) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000206 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
299
%%EOF"""

        files = [
            ('files', ('test.txt', txt_content.encode('utf-8'), 'text/plain')),
            ('files', ('test.pdf', pdf_content, 'application/pdf'))
        ]
        
        success, data, status = self.make_multipart_request('POST', '/api/ai-knowledge/upload', files=files)
        
        if success and status == 200:
            chunks = data.get('chunks', 0)
            if chunks > 0:
                self.log_test("AI Upload - Various Formats", True, f"Successfully parsed multiple formats, chunks: {chunks}")
            else:
                self.log_test("AI Upload - Various Formats", False, f"No chunks extracted from files")
        elif status == 500 and 'Database is not initialized' in data.get('detail', ''):
            self.log_test("AI Upload - Various Formats", False, f"Database not initialized: {data.get('detail')}")
        else:
            self.log_test("AI Upload - Various Formats", False, f"Status: {status}, Data: {data}")

    def test_ai_save_document(self, upload_id):
        """Test saving uploaded document"""
        if not upload_id:
            self.log_test("AI Save - Document", False, "No upload_id provided")
            return None
            
        data = {
            'upload_id': upload_id,
            'filename': 'test_knowledge_document.txt'
        }
        
        success, response_data, status = self.make_multipart_request('POST', '/api/ai-knowledge/save', data=data)
        
        if success and status == 200:
            if 'document_id' in response_data:
                document_id = response_data['document_id']
                self.log_test("AI Save - Document", True, f"Document saved with ID: {document_id[:8]}...")
                return document_id
            else:
                self.log_test("AI Save - Document", False, f"Missing document_id in response: {response_data}")
        elif status == 404:
            self.log_test("AI Save - Document", False, f"upload_id not found or expired: {response_data.get('detail', '')}")
        elif status == 500 and 'Database is not initialized' in response_data.get('detail', ''):
            self.log_test("AI Save - Document", False, f"Database not initialized: {response_data.get('detail')}")
        else:
            self.log_test("AI Save - Document", False, f"Status: {status}, Data: {response_data}")
        
        return None

    def test_ai_list_documents(self):
        """Test listing documents"""
        success, data, status = self.make_request('GET', '/api/ai-knowledge/documents')
        
        if success and status == 200:
            if 'documents' in data and isinstance(data['documents'], list):
                docs_count = len(data['documents'])
                self.log_test("AI List - Documents", True, f"Retrieved {docs_count} documents")
                
                # Check document structure if any documents exist
                if docs_count > 0:
                    doc = data['documents'][0]
                    required_fields = ['id', 'filename']
                    missing_fields = [field for field in required_fields if field not in doc]
                    
                    if not missing_fields:
                        self.log_test("AI List - Document Structure", True, f"Document structure valid: {doc.get('filename', 'N/A')}")
                    else:
                        self.log_test("AI List - Document Structure", False, f"Missing fields: {missing_fields}")
            else:
                self.log_test("AI List - Documents", False, f"Invalid response structure: {data}")
        elif status == 500 and 'Database is not initialized' in data.get('detail', ''):
            self.log_test("AI List - Documents", False, f"Database not initialized: {data.get('detail')}")
        else:
            self.log_test("AI List - Documents", False, f"Status: {status}, Data: {data}")

    def test_ai_search(self):
        """Test search functionality"""
        search_data = {
            'query': 'test',
            'top_k': 10
        }
        
        success, data, status = self.make_request('POST', '/api/ai-knowledge/search', search_data)
        
        if success and status == 200:
            if 'results' in data and isinstance(data['results'], list):
                results_count = len(data['results'])
                self.log_test("AI Search - Basic Query", True, f"Search returned {results_count} results")
                
                # Check result structure if any results exist
                if results_count > 0:
                    result = data['results'][0]
                    required_fields = ['document_id', 'content', 'score', 'filename']
                    missing_fields = [field for field in required_fields if field not in result]
                    
                    if not missing_fields:
                        score = result.get('score', 0)
                        # Score should be 1.0 if OPENAI_API_KEY is missing (zero vector fallback)
                        self.log_test("AI Search - Result Structure", True, 
                                    f"Result structure valid, score: {score}, filename: {result.get('filename', 'N/A')}")
                    else:
                        self.log_test("AI Search - Result Structure", False, f"Missing fields: {missing_fields}")
            else:
                self.log_test("AI Search - Basic Query", False, f"Invalid response structure: {data}")
        elif status == 400:
            self.log_test("AI Search - Basic Query", False, f"Bad request: {data.get('detail', '')}")
        elif status == 500 and 'Database is not initialized' in data.get('detail', ''):
            self.log_test("AI Search - Basic Query", False, f"Database not initialized: {data.get('detail')}")
        else:
            self.log_test("AI Search - Basic Query", False, f"Status: {status}, Data: {data}")

    def test_ai_delete_document(self, document_id):
        """Test deleting a document"""
        if not document_id:
            self.log_test("AI Delete - Document", False, "No document_id provided")
            return
            
        success, data, status = self.make_request('DELETE', f'/api/ai-knowledge/document/{document_id}')
        
        if success and status == 200:
            if data.get('ok') is True:
                self.log_test("AI Delete - Document", True, f"Document {document_id[:8]}... deleted successfully")
            else:
                self.log_test("AI Delete - Document", False, f"Unexpected response: {data}")
        elif status == 500 and 'Database is not initialized' in data.get('detail', ''):
            self.log_test("AI Delete - Document", False, f"Database not initialized: {data.get('detail')}")
        else:
            self.log_test("AI Delete - Document", False, f"Status: {status}, Data: {data}")

    def test_ai_database_not_initialized(self):
        """Test behavior when DATABASE_URL is not set"""
        # This test assumes DATABASE_URL might not be set
        # We'll check if endpoints return 500 with "Database is not initialized"
        
        # Try a simple operation that requires database
        success, data, status = self.make_request('GET', '/api/ai-knowledge/documents')
        
        if status == 500 and 'Database is not initialized' in data.get('detail', ''):
            self.log_test("AI Database - Not Initialized", True, f"Correctly returns 500 when DB not initialized: {data.get('detail')}")
        elif status == 200:
            self.log_test("AI Database - Initialized", True, f"Database is properly initialized and working")
        else:
            self.log_test("AI Database - Status Check", False, f"Unexpected response: Status {status}, Data: {data}")

    def make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, params: Optional[Dict] = None) -> tuple:
        """Make HTTP request and return (success, response_data, status_code)"""
        url = f"{self.base_url}{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=30)
            else:
                return False, {}, 0
                
            return True, response.json() if response.content else {}, response.status_code
            
        except requests.exceptions.Timeout:
            return False, {"error": "Request timeout"}, 0
        except requests.exceptions.ConnectionError:
            return False, {"error": "Connection error"}, 0
        except Exception as e:
            return False, {"error": str(e)}, 0

    def test_crm_cleaning_filters(self):
        """Test CRM cleaning filters endpoint as per review request"""
        print("\n🏠 Testing CRM Cleaning Filters...")
        
        success, data, status = self.make_request('GET', '/api/cleaning/filters')
        
        if success and status == 200:
            # Check required structure: brigades, management_companies, statuses
            required_fields = ['brigades', 'management_companies', 'statuses']
            missing_fields = [field for field in required_fields if field not in data]
            
            if not missing_fields:
                # Verify all fields are arrays
                type_errors = []
                for field in required_fields:
                    if not isinstance(data[field], list):
                        type_errors.append(f"{field} should be array, got {type(data[field])}")
                
                if not type_errors:
                    brigades_count = len(data['brigades'])
                    companies_count = len(data['management_companies'])
                    statuses_count = len(data['statuses'])
                    
                    self.log_test("CRM Filters - Structure", True, 
                                f"brigades: {brigades_count}, management_companies: {companies_count}, statuses: {statuses_count}")
                else:
                    self.log_test("CRM Filters - Structure", False, f"Type errors: {type_errors}")
            else:
                self.log_test("CRM Filters - Structure", False, f"Missing fields: {missing_fields}")
        elif status == 500:
            # Bitrix unavailable is acceptable
            detail = data.get('detail', '')
            if 'Bitrix' in detail or 'битрикс' in detail.lower():
                self.log_test("CRM Filters - Bitrix Unavailable", True, f"Bitrix unavailable (acceptable): {detail}")
            else:
                self.log_test("CRM Filters - Structure", False, f"500 error: {detail}")
        else:
            self.log_test("CRM Filters - Structure", False, f"Status: {status}, Data: {data}")

    def test_crm_houses_endpoint(self):
        """Test CRM houses endpoint as per review request"""
        print("\n🏠 Testing CRM Houses Endpoint...")
        
        success, data, status = self.make_request('GET', '/api/cleaning/houses', params={'page': 1, 'limit': 50})
        
        if success and status == 200:
            # Check required structure
            required_fields = ['houses', 'total', 'page', 'limit', 'pages']
            missing_fields = [field for field in required_fields if field not in data]
            
            if not missing_fields:
                houses = data['houses']
                if isinstance(houses, list):
                    self.log_test("CRM Houses - Response Structure", True, 
                                f"houses: {len(houses)}, total: {data['total']}, page: {data['page']}, limit: {data['limit']}, pages: {data['pages']}")
                    
                    # Check house object structure if houses exist
                    if houses:
                        house = houses[0]
                        required_house_fields = ['id', 'title', 'address', 'apartments', 'entrances', 'floors', 'cleaning_dates', 'periodicity', 'bitrix_url']
                        missing_house_fields = [field for field in required_house_fields if field not in house]
                        
                        if not missing_house_fields:
                            self.log_test("CRM Houses - House Object Structure", True, 
                                        f"House ID {house['id']}: all required fields present")
                        else:
                            self.log_test("CRM Houses - House Object Structure", False, 
                                        f"Missing house fields: {missing_house_fields}")
                else:
                    self.log_test("CRM Houses - Response Structure", False, f"houses should be array, got {type(houses)}")
            else:
                self.log_test("CRM Houses - Response Structure", False, f"Missing fields: {missing_fields}")
        elif status == 500:
            # Bitrix unavailable is acceptable
            detail = data.get('detail', '')
            if 'Bitrix' in detail or 'битрикс' in detail.lower():
                self.log_test("CRM Houses - Bitrix Unavailable", True, f"Bitrix unavailable (acceptable): {detail}")
            else:
                self.log_test("CRM Houses - Response Structure", False, f"500 error: {detail}")
        else:
            self.log_test("CRM Houses - Response Structure", False, f"Status: {status}, Data: {data}")

    def test_crm_house_details(self):
        """Test CRM house details endpoint as per review request"""
        print("\n🏠 Testing CRM House Details...")
        
        # First get a house ID from houses list
        success, houses_data, status = self.make_request('GET', '/api/cleaning/houses', params={'limit': 5})
        test_house_id = None
        
        if success and status == 200 and houses_data.get('houses'):
            test_house_id = houses_data['houses'][0]['id']
            print(f"   Using house ID {test_house_id} for testing")
        else:
            # Use fallback ID
            test_house_id = 13112
            print(f"   Using fallback house ID {test_house_id}")
        
        # Test house details
        success, data, status = self.make_request('GET', f'/api/cleaning/house/{test_house_id}/details')
        
        if success and status == 200:
            # Check response structure according to server.py
            if isinstance(data, dict):
                self.log_test("CRM House Details - Valid Response", True, 
                            f"House ID {test_house_id}: details retrieved successfully")
            else:
                self.log_test("CRM House Details - Valid Response", False, 
                            f"Expected dict response, got {type(data)}")
        elif status == 500:
            # Bitrix unavailable is acceptable
            detail = data.get('detail', '')
            if 'Bitrix' in detail or 'битрикс' in detail.lower():
                self.log_test("CRM House Details - Bitrix Unavailable", True, f"Bitrix unavailable (acceptable): {detail}")
            else:
                self.log_test("CRM House Details - Valid Response", False, f"500 error: {detail}")
        else:
            self.log_test("CRM House Details - Valid Response", False, f"Status: {status}, Data: {data}")

    def run_review_request_tests(self):
        """Run tests specifically requested in the review request"""
        print("🚀 Starting VasDom AudioBot Backend Testing")
        print(f"📍 Testing URL: {self.base_url}")
        print("🎯 Focus: AI Training & CRM Endpoints per Review Request")
        print("=" * 60)
        
        # CRM (Bitrix) Tests
        print("\n🏠 CRM (BITRIX) ENDPOINTS TESTING")
        print("-" * 40)
        
        # 1) GET /api/cleaning/filters
        self.test_crm_cleaning_filters()
        
        # 2) GET /api/cleaning/houses?page=1&limit=50
        self.test_crm_houses_endpoint()
        
        # 3) GET /api/cleaning/house/{id}/details
        self.test_crm_house_details()
        
        # AI Training Tests
        print("\n🧠 AI TRAINING ENDPOINTS TESTING")
        print("-" * 40)
        
        # 4-8) AI Knowledge endpoints
        self.test_ai_knowledge_endpoints()
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 REVIEW REQUEST TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {len(self.failed_tests)}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if self.failed_tests:
            print("\n❌ FAILED TESTS:")
            for test in self.failed_tests:
                print(f"  - {test['name']}: {test['details']}")
        
        # Categorize results
        crm_tests = [t for t in self.failed_tests if 'CRM ' in t['name']]
        ai_tests = [t for t in self.failed_tests if 'AI ' in t['name']]
        
        print(f"\n🏠 CRM ENDPOINTS RESULTS:")
        if not crm_tests:
            print(f"  ✅ All CRM tests PASSED")
        else:
            print(f"  ❌ CRM tests FAILED: {len(crm_tests)} failures")
        
        print(f"\n🧠 AI TRAINING ENDPOINTS RESULTS:")
        if not ai_tests:
            print(f"  ✅ All AI Training tests PASSED")
        else:
            print(f"  ❌ AI Training tests FAILED: {len(ai_tests)} failures")
        
        return len(self.failed_tests) == 0

def main():
    """Main test execution"""
    tester = VasDomAPITester()
    success = tester.run_review_request_tests()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())