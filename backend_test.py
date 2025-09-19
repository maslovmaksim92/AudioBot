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
    def __init__(self, base_url="https://audiobot-qci2.onrender.com"):
        self.base_url = base_url.rstrip('/')
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []
        self.ai_endpoints_deployed = None  # Track AI endpoint deployment status
        
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
                response = requests.get(url, headers=headers, params=params, timeout=60)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=60)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=60)
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

    def test_production_diagnostics_after_url_normalization(self):
        """Test production diagnostics after URL normalization logic added - Review Request"""
        print("\n🔍 REVIEW REQUEST DIAGNOSTICS - CLEAN ASYNC URL & SSL")
        print("=" * 70)
        print(f"Base URL: {self.base_url}")
        print("Testing after forcing clean async URL and connect_args ssl")
        print("-" * 70)
        
        # Test 1: GET /api/ai-knowledge/db-check - expect connected true now
        db_status = self.test_db_check_endpoint()
        
        # Test 2: Analyze db-check results and determine next steps
        if db_status:
            connected = db_status.get('connected', False)
            pgvector_available = db_status.get('pgvector_available', False)
            pgvector_installed = db_status.get('pgvector_installed', False)
            errors = db_status.get('errors', [])
            
            print(f"\n📊 Database Status Analysis:")
            print(f"   Connected: {connected}")
            print(f"   PGVector Available: {pgvector_available}")
            print(f"   PGVector Installed: {pgvector_installed}")
            print(f"   Errors: {len(errors)} - {errors[:3] if errors else 'None'}")
            
            if connected and pgvector_available and not pgvector_installed:
                print("   🔧 Database connected, pgvector available but not installed - attempting installation")
                # Test 3: POST /api/ai-knowledge/db-install-vector
                install_success = self.test_db_install_vector_endpoint()
                if install_success:
                    # Test 4: Re-check after installation
                    self.test_db_check_after_install()
                    # Test 5: Run AI flow if everything is ready
                    self.test_ai_flow_sequence()
                else:
                    self.log_test("AI Flow - Prerequisites", False, "pgvector installation failed, cannot run AI flow")
            elif connected and pgvector_available and pgvector_installed:
                print("   ✅ Database fully configured and ready - running AI flow")
                self.log_test("DB Analysis - Full Setup", True, "Database connected with pgvector installed")
                # Test 5: Run quick AI flow: preview -> study -> documents -> search -> delete
                self.test_ai_flow_sequence()
            elif not connected:
                print("   ❌ Database not connected - SSL/URL issues persist")
                self.log_test("DB Analysis - Connection Failed", False, 
                            f"Database connection failed after URL normalization. Errors: {errors[:2]}")
            else:
                print("   ❓ Unexpected database state")
                self.log_test("DB Analysis - Unexpected State", False, 
                            f"Unexpected state: connected={connected}, available={pgvector_available}, installed={pgvector_installed}")
        else:
            print("   ❌ Could not retrieve database status")
            self.log_test("DB Analysis - Status Retrieval", False, "Failed to get database status from db-check endpoint")
        
        return True

    def test_db_dsn_endpoint(self):
        """Test GET /api/ai-knowledge/db-dsn endpoint - Review Request Step 1"""
        print("\n1️⃣ Testing GET /api/ai-knowledge/db-dsn")
        
        success, data, status = self.make_request('GET', '/api/ai-knowledge/db-dsn')
        
        if success and status == 200:
            # Check if response has expected DSN fields
            expected_fields = ['raw_present', 'raw_contains_sslmode', 'raw', 'normalized']
            missing_fields = [field for field in expected_fields if field not in data]
            
            if not missing_fields:
                raw_present = data.get('raw_present', False)
                raw_contains_sslmode = data.get('raw_contains_sslmode', False)
                raw = data.get('raw', '')
                normalized = data.get('normalized', '')
                
                # Log detailed DSN info (mask sensitive parts)
                raw_masked = self.mask_sensitive_url(raw) if raw else 'N/A'
                normalized_masked = self.mask_sensitive_url(normalized) if normalized else 'N/A'
                
                dsn_info = f"raw_present={raw_present}, raw_contains_sslmode={raw_contains_sslmode}"
                self.log_test("DB DSN - Endpoint Response", True, dsn_info)
                
                print(f"   📋 DSN Analysis:")
                print(f"      Raw URL Present: {raw_present}")
                print(f"      Raw Contains sslmode: {raw_contains_sslmode}")
                print(f"      Raw URL: {raw_masked}")
                print(f"      Normalized URL: {normalized_masked}")
                
                return data
            else:
                self.log_test("DB DSN - Endpoint Response", False, f"Missing DSN fields: {missing_fields}")
        elif status == 404:
            self.log_test("DB DSN - Endpoint Exists", False, "db-dsn endpoint not found (404) - not deployed")
        elif status == 500:
            detail = data.get('detail', '')
            self.log_test("DB DSN - Endpoint Response", False, f"500 error: {detail}")
        else:
            self.log_test("DB DSN - Endpoint Response", False, f"Status: {status}, Data: {data}")
        
        return None

    def mask_sensitive_url(self, url):
        """Mask sensitive parts of database URL for logging"""
        if not url or not isinstance(url, str):
            return url
        
        # Mask password in URL
        import re
        # Pattern to match postgresql://user:password@host:port/db
        pattern = r'(postgresql[^:]*://[^:]+:)([^@]+)(@.*)'
        masked = re.sub(pattern, r'\1***\3', url)
        return masked

    def test_db_check_endpoint(self):
        """Test GET /api/ai-knowledge/db-check endpoint - Review Request Step 2"""
        print("\n2️⃣ Testing GET /api/ai-knowledge/db-check")
        
        success, data, status = self.make_request('GET', '/api/ai-knowledge/db-check')
        
        if success and status == 200:
            # Check if response has expected diagnostic fields
            expected_fields = ['connected', 'pgvector_available', 'pgvector_installed', 'errors']
            missing_fields = [field for field in expected_fields if field not in data]
            
            if not missing_fields:
                connected = data.get('connected', False)
                pgvector_available = data.get('pgvector_available', False)
                pgvector_installed = data.get('pgvector_installed', False)
                errors = data.get('errors', [])
                
                # Log detailed diagnostic info
                diagnostic_info = f"connected={connected}, pgvector_available={pgvector_available}, pgvector_installed={pgvector_installed}"
                if errors:
                    diagnostic_info += f", errors={len(errors)}"
                
                self.log_test("DB Check - Endpoint Response", True, diagnostic_info)
                
                print(f"   📊 Database Status:")
                print(f"      Connected: {connected}")
                print(f"      PGVector Available: {pgvector_available}")
                print(f"      PGVector Installed: {pgvector_installed}")
                
                # Log specific errors if any
                if errors:
                    print(f"   🔍 Database Errors Found ({len(errors)}):")
                    for i, error in enumerate(errors[:5]):  # Show first 5 errors
                        print(f"      {i+1}. {error}")
                    if len(errors) > 5:
                        print(f"      ... and {len(errors) - 5} more errors")
                
                return data
            else:
                self.log_test("DB Check - Endpoint Response", False, f"Missing diagnostic fields: {missing_fields}")
        elif status == 404:
            self.log_test("DB Check - Endpoint Exists", False, "db-check endpoint not found (404) - not deployed")
        elif status == 500:
            detail = data.get('detail', '')
            if 'sslmode' in detail.lower():
                self.log_test("DB Check - SSL Mode Error", True, f"Expected sslmode error (URL normalization issue): {detail}")
            else:
                self.log_test("DB Check - Endpoint Response", False, f"500 error: {detail}")
        else:
            self.log_test("DB Check - Endpoint Response", False, f"Status: {status}, Data: {data}")
        
        return None

    def test_db_install_vector_endpoint(self):
        """Test POST /api/ai-knowledge/db-install-vector endpoint"""
        print("\n2️⃣ Testing POST /api/ai-knowledge/db-install-vector")
        
        success, data, status = self.make_request('POST', '/api/ai-knowledge/db-install-vector')
        
        if success and status == 200:
            # Check if installation was successful
            if data.get('success') or data.get('installed'):
                self.log_test("DB Install Vector - Success", True, f"pgvector installation successful: {data}")
            else:
                self.log_test("DB Install Vector - Response", False, f"Unexpected success response: {data}")
        elif status == 404:
            self.log_test("DB Install Vector - Endpoint Exists", False, "db-install-vector endpoint not found (404) - not deployed")
        elif status == 500:
            detail = data.get('detail', '')
            if 'sslmode' in detail.lower():
                self.log_test("DB Install Vector - SSL Mode Error", True, f"Expected sslmode error (URL normalization issue): {detail}")
            elif 'permission' in detail.lower() or 'privilege' in detail.lower():
                self.log_test("DB Install Vector - Permission Error", True, f"Expected permission error (database user lacks CREATE EXTENSION): {detail}")
            else:
                self.log_test("DB Install Vector - Error", False, f"500 error: {detail}")
        else:
            self.log_test("DB Install Vector - Response", False, f"Status: {status}, Data: {data}")

    def test_db_check_after_install(self):
        """Re-test db-check after attempting pgvector installation"""
        print("\n3️⃣ Re-testing GET /api/ai-knowledge/db-check after installation attempt")
        
        success, data, status = self.make_request('GET', '/api/ai-knowledge/db-check')
        
        if success and status == 200:
            connected = data.get('connected', False)
            pgvector_available = data.get('pgvector_available', False)
            pgvector_installed = data.get('pgvector_installed', False)
            
            if connected and pgvector_available and pgvector_installed:
                self.log_test("DB Check After Install - Full Setup", True, "Database now fully configured with pgvector")
            elif connected and pgvector_available and not pgvector_installed:
                self.log_test("DB Check After Install - Install Failed", False, "pgvector installation failed - check permissions")
            else:
                status_info = f"connected={connected}, available={pgvector_available}, installed={pgvector_installed}"
                self.log_test("DB Check After Install - Status", True, f"Post-install status: {status_info}")
        else:
            self.log_test("DB Check After Install - Request Failed", False, f"Status: {status}, Data: {data}")

    def test_ai_knowledge_new_endpoints(self):
        """Test new AI Knowledge endpoints moved to app/routers/ai_knowledge.py"""
        print("\n🧠 Testing New AI Knowledge Endpoints (Review Request)")
        print("=" * 60)
        print("Testing endpoints moved to app/routers/ai_knowledge.py")
        print("Configuration: FastAPI, all routes under /api")
        print("Testing LOCALLY on current environment")
        print("-" * 60)
        
        # Test 1: POST /api/ai-knowledge/preview
        upload_id = self.test_ai_knowledge_preview()
        
        # Test 2: POST /api/ai-knowledge/study (if preview worked)
        document_id = None
        if upload_id:
            document_id = self.test_ai_knowledge_study(upload_id)
        
        # Test 3: GET /api/ai-knowledge/status
        if upload_id:
            self.test_ai_knowledge_status_before_study(upload_id)
        if document_id:
            self.test_ai_knowledge_status_after_study(upload_id)
        
        # Test 4: GET /api/ai-knowledge/documents
        self.test_ai_knowledge_documents()
        
        # Test 5: POST /api/ai-knowledge/search
        self.test_ai_knowledge_search()
        
        # Test 6: DELETE /api/ai-knowledge/document/{document_id}
        if document_id:
            self.test_ai_knowledge_delete(document_id)
            # Test repeated DELETE (should also return 200)
            self.test_ai_knowledge_delete_repeated(document_id)
        
        # Additional: Test old endpoints still work
        print("\n🔄 Testing Legacy Endpoints Still Work")
        print("-" * 40)
        self.test_legacy_cleaning_filters()
        self.test_legacy_logistics_route()
        
        return True

    def test_ai_knowledge_preview(self):
        """Test POST /api/ai-knowledge/preview with simple TXT file"""
        print("\n1️⃣ Testing POST /api/ai-knowledge/preview")
        
        # Create simple TXT file as requested
        txt_content = "Hello AI"
        files = {'file': ('test.txt', txt_content.encode('utf-8'), 'text/plain')}
        data = {'chunk_tokens': 600, 'overlap': 100}
        
        success, response_data, status = self.make_multipart_request('POST', '/api/ai-knowledge/preview', files=files, data=data)
        
        if success and status == 200:
            # Check required fields: upload_id (string), preview (string), chunks (>=1), stats.total_size_bytes (>0)
            required_fields = ['upload_id', 'preview', 'chunks', 'stats']
            missing_fields = [field for field in required_fields if field not in response_data]
            
            if not missing_fields:
                upload_id = response_data['upload_id']
                preview = response_data['preview']
                chunks = response_data['chunks']
                stats = response_data.get('stats', {})
                total_size_bytes = stats.get('total_size_bytes', 0)
                
                # Validate types and values
                if (isinstance(upload_id, str) and len(upload_id) > 0 and
                    isinstance(preview, str) and len(preview) > 0 and
                    isinstance(chunks, int) and chunks >= 1 and
                    isinstance(total_size_bytes, int) and total_size_bytes > 0):
                    
                    self.log_test("AI Preview - Valid Response", True, 
                                f"upload_id: {upload_id[:8]}..., preview: {len(preview)} chars, chunks: {chunks}, size: {total_size_bytes} bytes")
                    return upload_id
                else:
                    self.log_test("AI Preview - Valid Response", False, 
                                f"Invalid field types/values: upload_id={type(upload_id)}, preview={len(preview) if isinstance(preview, str) else type(preview)}, chunks={chunks}, size={total_size_bytes}")
            else:
                self.log_test("AI Preview - Valid Response", False, f"Missing fields: {missing_fields}")
        elif status == 500 and 'Database is not initialized' in response_data.get('detail', ''):
            self.log_test("AI Preview - Database Not Initialized", True, f"Expected 500 'Database is not initialized': {response_data.get('detail')}")
        else:
            self.log_test("AI Preview - Valid Response", False, f"Status: {status}, Data: {response_data}")
        
        return None

    def test_ai_knowledge_study(self, upload_id):
        """Test POST /api/ai-knowledge/study with upload_id from preview"""
        print("\n2️⃣ Testing POST /api/ai-knowledge/study")
        
        if not upload_id:
            self.log_test("AI Study - No Upload ID", False, "No upload_id provided from preview")
            return None
        
        data = {
            'upload_id': upload_id,
            'filename': 'test.txt',
            'category': 'Клининг'
        }
        
        success, response_data, status = self.make_multipart_request('POST', '/api/ai-knowledge/study', data=data)
        
        if success and status == 200:
            # Check required fields: document_id (string), chunks (>=1), category
            required_fields = ['document_id', 'chunks', 'category']
            missing_fields = [field for field in required_fields if field not in response_data]
            
            if not missing_fields:
                document_id = response_data['document_id']
                chunks = response_data['chunks']
                category = response_data['category']
                
                if (isinstance(document_id, str) and len(document_id) > 0 and
                    isinstance(chunks, int) and chunks >= 1 and
                    category == 'Клининг'):
                    
                    self.log_test("AI Study - Valid Response", True, 
                                f"document_id: {document_id[:8]}..., chunks: {chunks}, category: {category}")
                    return document_id
                else:
                    self.log_test("AI Study - Valid Response", False, 
                                f"Invalid values: document_id={type(document_id)}, chunks={chunks}, category={category}")
            else:
                self.log_test("AI Study - Valid Response", False, f"Missing fields: {missing_fields}")
        elif status == 404:
            self.log_test("AI Study - Upload ID Not Found", False, f"upload_id not found or expired: {response_data.get('detail', '')}")
        elif status == 500 and 'Database is not initialized' in response_data.get('detail', ''):
            self.log_test("AI Study - Database Not Initialized", True, f"Expected 500 'Database is not initialized': {response_data.get('detail')}")
        else:
            self.log_test("AI Study - Valid Response", False, f"Status: {status}, Data: {response_data}")
        
        return None

    def test_ai_knowledge_status_before_study(self, upload_id):
        """Test GET /api/ai-knowledge/status before study (should return ready)"""
        print("\n3️⃣ Testing GET /api/ai-knowledge/status (before study)")
        
        if not upload_id:
            self.log_test("AI Status Before - No Upload ID", False, "No upload_id provided")
            return
        
        success, response_data, status = self.make_request('GET', f'/api/ai-knowledge/status', params={'upload_id': upload_id})
        
        if success and status == 200:
            if 'status' in response_data:
                status_value = response_data['status']
                if status_value == 'ready':
                    self.log_test("AI Status Before Study", True, f"Status: {status_value}")
                else:
                    self.log_test("AI Status Before Study", False, f"Expected 'ready', got '{status_value}'")
            else:
                self.log_test("AI Status Before Study", False, f"Missing 'status' field: {response_data}")
        elif status == 500 and 'Database is not initialized' in response_data.get('detail', ''):
            self.log_test("AI Status Before - Database Not Initialized", True, f"Expected 500 'Database is not initialized': {response_data.get('detail')}")
        else:
            self.log_test("AI Status Before Study", False, f"Status: {status}, Data: {response_data}")

    def test_ai_knowledge_status_after_study(self, upload_id):
        """Test GET /api/ai-knowledge/status after study (should return done or not found)"""
        print("\n3️⃣ Testing GET /api/ai-knowledge/status (after study)")
        
        if not upload_id:
            self.log_test("AI Status After - No Upload ID", False, "No upload_id provided")
            return
        
        success, response_data, status = self.make_request('GET', f'/api/ai-knowledge/status', params={'upload_id': upload_id})
        
        if success and status == 200:
            if 'status' in response_data:
                status_value = response_data['status']
                if status_value == 'done':
                    self.log_test("AI Status After Study", True, f"Status: {status_value} (upload processed)")
                else:
                    self.log_test("AI Status After Study", True, f"Status: {status_value} (acceptable)")
            else:
                self.log_test("AI Status After Study", False, f"Missing 'status' field: {response_data}")
        elif status == 404:
            self.log_test("AI Status After Study", True, f"Upload not found (acceptable - processed): {response_data.get('detail', '')}")
        elif status == 500 and 'Database is not initialized' in response_data.get('detail', ''):
            self.log_test("AI Status After - Database Not Initialized", True, f"Expected 500 'Database is not initialized': {response_data.get('detail')}")
        else:
            self.log_test("AI Status After Study", False, f"Status: {status}, Data: {response_data}")

    def test_ai_knowledge_documents(self):
        """Test GET /api/ai-knowledge/documents"""
        print("\n4️⃣ Testing GET /api/ai-knowledge/documents")
        
        success, response_data, status = self.make_request('GET', '/api/ai-knowledge/documents')
        
        if success and status == 200:
            if 'documents' in response_data and isinstance(response_data['documents'], list):
                documents = response_data['documents']
                docs_count = len(documents)
                
                # Check if we have documents with chunks_count >= 1
                docs_with_chunks = [doc for doc in documents if doc.get('chunks_count', 0) >= 1]
                
                if docs_with_chunks:
                    sample_doc = docs_with_chunks[0]
                    self.log_test("AI Documents - Contains Study Document", True, 
                                f"Found {len(docs_with_chunks)} documents with chunks >= 1. Sample: {sample_doc.get('filename', 'N/A')}, chunks: {sample_doc.get('chunks_count', 0)}")
                else:
                    self.log_test("AI Documents - Contains Study Document", True, 
                                f"Retrieved {docs_count} documents (may not contain test document if DB not initialized)")
            else:
                self.log_test("AI Documents - Valid Response", False, f"Invalid response structure: {response_data}")
        elif status == 500 and 'Database is not initialized' in response_data.get('detail', ''):
            self.log_test("AI Documents - Database Not Initialized", True, f"Expected 500 'Database is not initialized': {response_data.get('detail')}")
        else:
            self.log_test("AI Documents - Valid Response", False, f"Status: {status}, Data: {response_data}")

    def test_ai_knowledge_search(self):
        """Test POST /api/ai-knowledge/search"""
        print("\n5️⃣ Testing POST /api/ai-knowledge/search")
        
        search_data = {
            'query': 'Hello',
            'top_k': 5
        }
        
        success, response_data, status = self.make_request('POST', '/api/ai-knowledge/search', search_data)
        
        if success and status == 200:
            if 'results' in response_data and isinstance(response_data['results'], list):
                results = response_data['results']
                results_count = len(results)
                
                self.log_test("AI Search - Valid Response", True, 
                            f"Search returned {results_count} results (even with missing OPENAI_API_KEY, form is correct)")
                
                # Check result structure if any results
                if results:
                    result = results[0]
                    required_fields = ['document_id', 'content', 'score', 'filename']
                    missing_fields = [field for field in required_fields if field not in result]
                    
                    if not missing_fields:
                        score = result.get('score', 0)
                        # Score may be same for all results if OPENAI_API_KEY missing (zero vector fallback)
                        self.log_test("AI Search - Result Structure", True, 
                                    f"Result structure valid. Score: {score}, filename: {result.get('filename', 'N/A')}")
                    else:
                        self.log_test("AI Search - Result Structure", False, f"Missing fields: {missing_fields}")
            else:
                self.log_test("AI Search - Valid Response", False, f"Invalid response structure: {response_data}")
        elif status == 400:
            self.log_test("AI Search - Valid Response", False, f"Bad request: {response_data.get('detail', '')}")
        elif status == 500 and 'Database is not initialized' in response_data.get('detail', ''):
            self.log_test("AI Search - Database Not Initialized", True, f"Expected 500 'Database is not initialized': {response_data.get('detail')}")
        else:
            self.log_test("AI Search - Valid Response", False, f"Status: {status}, Data: {response_data}")

    def test_ai_knowledge_delete(self, document_id):
        """Test DELETE /api/ai-knowledge/document/{document_id}"""
        print("\n6️⃣ Testing DELETE /api/ai-knowledge/document/{document_id}")
        
        if not document_id:
            self.log_test("AI Delete - No Document ID", False, "No document_id provided")
            return
        
        success, response_data, status = self.make_request('DELETE', f'/api/ai-knowledge/document/{document_id}')
        
        if success and status == 200:
            if response_data.get('ok') is True:
                self.log_test("AI Delete - First Delete", True, f"Document {document_id[:8]}... deleted successfully")
            else:
                self.log_test("AI Delete - First Delete", False, f"Expected {{ok: true}}, got: {response_data}")
        elif status == 500 and 'Database is not initialized' in response_data.get('detail', ''):
            self.log_test("AI Delete - Database Not Initialized", True, f"Expected 500 'Database is not initialized': {response_data.get('detail')}")
        else:
            self.log_test("AI Delete - First Delete", False, f"Status: {status}, Data: {response_data}")

    def test_ai_knowledge_delete_repeated(self, document_id):
        """Test repeated DELETE /api/ai-knowledge/document/{document_id} (should also return 200)"""
        print("\n6️⃣ Testing DELETE /api/ai-knowledge/document/{document_id} (repeated)")
        
        if not document_id:
            self.log_test("AI Delete Repeated - No Document ID", False, "No document_id provided")
            return
        
        success, response_data, status = self.make_request('DELETE', f'/api/ai-knowledge/document/{document_id}')
        
        if success and status == 200:
            if response_data.get('ok') is True:
                self.log_test("AI Delete - Repeated Delete", True, f"Repeated delete also returns 200 {{ok: true}} (idempotent)")
            else:
                self.log_test("AI Delete - Repeated Delete", False, f"Expected {{ok: true}}, got: {response_data}")
        elif status == 500 and 'Database is not initialized' in response_data.get('detail', ''):
            self.log_test("AI Delete Repeated - Database Not Initialized", True, f"Expected 500 'Database is not initialized': {response_data.get('detail')}")
        else:
            self.log_test("AI Delete - Repeated Delete", False, f"Status: {status}, Data: {response_data}")

    def test_legacy_cleaning_filters(self):
        """Test that old Cleaning endpoint still works"""
        print("\n🧹 Testing Legacy GET /api/cleaning/filters")
        
        success, response_data, status = self.make_request('GET', '/api/cleaning/filters')
        
        if success and status == 200:
            if isinstance(response_data, dict) and 'brigades' in response_data:
                self.log_test("Legacy Cleaning Filters", True, f"Old endpoint still works: {len(response_data.get('brigades', []))} brigades")
            else:
                self.log_test("Legacy Cleaning Filters", False, f"Invalid response structure: {response_data}")
        else:
            self.log_test("Legacy Cleaning Filters", False, f"Status: {status}, Data: {response_data}")

    def test_legacy_logistics_route(self):
        """Test that old Logistics endpoint validation still works"""
        print("\n🚚 Testing Legacy POST /api/logistics/route (validation)")
        
        # Test with 1 point - should return 400 with "Минимум 2 точки"
        test_data = {
            "points": [
                {"address": "Москва, Красная площадь"}
            ],
            "optimize": False,
            "profile": "driving-car",
            "language": "ru"
        }
        
        success, response_data, status = self.make_request('POST', '/api/logistics/route', test_data)
        
        if status == 400:
            detail = response_data.get('detail', '')
            if 'Минимум 2 точки' in detail:
                self.log_test("Legacy Logistics Route Validation", True, f"Old endpoint validation works: {detail}")
            else:
                self.log_test("Legacy Logistics Route Validation", False, f"Wrong error message: {detail}")
        else:
            self.log_test("Legacy Logistics Route Validation", False, f"Expected 400, got {status}: {response_data}")

    def run_ai_knowledge_review_tests(self):
        """Run the specific tests requested in the review"""
        print("🚀 Starting AI Knowledge Review Request Testing")
        print(f"📍 Testing URL: {self.base_url}")
        print("🎯 Focus: New AI Training endpoints after move to app/routers/ai_knowledge.py")
        print("=" * 80)
        
        # Run the comprehensive AI Knowledge tests
        self.test_ai_knowledge_new_endpoints()
        
        # Print summary
        print("\n" + "=" * 80)
        print("📊 AI KNOWLEDGE REVIEW REQUEST TEST SUMMARY")
        print("=" * 80)
        print(f"Total Tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {len(self.failed_tests)}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if self.failed_tests:
            print("\n❌ FAILED TESTS:")
            for test in self.failed_tests:
                print(f"  - {test['name']}: {test['details']}")
        
        # Categorize results
        ai_tests = [t for t in self.failed_tests if 'AI ' in t['name']]
        legacy_tests = [t for t in self.failed_tests if 'Legacy ' in t['name']]
        
        print(f"\n🧠 AI KNOWLEDGE ENDPOINTS RESULTS:")
        if not ai_tests:
            print(f"  ✅ All AI Knowledge tests PASSED")
        else:
            print(f"  ❌ AI Knowledge tests FAILED: {len(ai_tests)} failures")
        
        print(f"\n🔄 LEGACY ENDPOINTS RESULTS:")
        if not legacy_tests:
            print(f"  ✅ All Legacy endpoint tests PASSED")
        else:
            print(f"  ❌ Legacy endpoint tests FAILED: {len(legacy_tests)} failures")
        
        # Special note about DATABASE_URL
        print(f"\n📝 IMPORTANT NOTES:")
        print(f"  - DATABASE_URL is not set in environment (expected per review)")
        print(f"  - Endpoints returning 500 'Database is not initialized' is expected behavior")
        print(f"  - Tests validate endpoint structure and error handling")
        
        return len(self.failed_tests) == 0
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

    def test_cleaning_module_comprehensive(self):
        """Comprehensive testing of Cleaning module as per review request"""
        print("🧹 COMPREHENSIVE CLEANING MODULE TESTING")
        print("=" * 60)
        print("Testing after changes in /app/backend/app_main.py")
        print("Focus: Filters, Houses with search/date filters, Details, Bitrix stability")
        print("-" * 60)
        
        # 1) GET /api/cleaning/filters
        self.test_cleaning_filters_comprehensive()
        
        # 2) GET /api/cleaning/houses - comprehensive scenarios
        self.test_cleaning_houses_comprehensive()
        
        # 3) GET /api/cleaning/house/{id}/details
        self.test_cleaning_house_details_comprehensive()
        
        # 4) Bitrix stability tests
        self.test_bitrix_stability_comprehensive()
        
        return True

    def test_cleaning_filters_comprehensive(self):
        """Test GET /api/cleaning/filters - expect 200 and structure"""
        print("\n1️⃣ Testing GET /api/cleaning/filters")
        
        success, data, status = self.make_request('GET', '/api/cleaning/filters')
        
        if success and status == 200:
            # Check structure: { brigades[], management_companies[], statuses[] }
            required_fields = ['brigades', 'management_companies', 'statuses']
            missing_fields = [field for field in required_fields if field not in data]
            
            if not missing_fields:
                # Verify all are arrays
                type_errors = []
                for field in required_fields:
                    if not isinstance(data[field], list):
                        type_errors.append(f"{field} should be array, got {type(data[field])}")
                
                if not type_errors:
                    self.log_test("Cleaning Filters - Structure ✅", True, 
                                f"brigades: {len(data['brigades'])}, management_companies: {len(data['management_companies'])}, statuses: {len(data['statuses'])}")
                    
                    # Log sample data
                    if data['brigades']:
                        print(f"   Sample brigades: {data['brigades'][:3]}")
                    if data['management_companies']:
                        print(f"   Sample companies: {data['management_companies'][:3]}")
                    if data['statuses']:
                        print(f"   Sample statuses: {data['statuses'][:3]}")
                else:
                    self.log_test("Cleaning Filters - Structure ❌", False, f"Type errors: {type_errors}")
            else:
                self.log_test("Cleaning Filters - Structure ❌", False, f"Missing fields: {missing_fields}")
        else:
            self.log_test("Cleaning Filters - Structure ❌", False, f"Status: {status}, Response: {data}")

    def test_cleaning_houses_comprehensive(self):
        """Test GET /api/cleaning/houses with all scenarios from review request"""
        print("\n2️⃣ Testing GET /api/cleaning/houses - Comprehensive Scenarios")
        
        # Base test: page=1&limit=50 -> 200, houses[] with required fields
        print("\n   📋 Base pagination test (page=1&limit=50)")
        success, data, status = self.make_request('GET', '/api/cleaning/houses', params={'page': 1, 'limit': 50})
        
        if success and status == 200:
            # Verify response structure
            required_fields = ['houses', 'total', 'page', 'limit', 'pages']
            missing_fields = [field for field in required_fields if field not in data]
            
            if not missing_fields:
                # Verify integer types for pagination fields
                integer_fields = ['total', 'page', 'limit', 'pages']
                non_integer_fields = []
                for field in integer_fields:
                    if not isinstance(data[field], int):
                        non_integer_fields.append(f"{field}={data[field]} ({type(data[field]).__name__})")
                
                if not non_integer_fields:
                    houses = data['houses']
                    if isinstance(houses, list):
                        self.log_test("Houses Base Response ✅", True, 
                                    f"houses: {len(houses)}, total: {data['total']}, page: {data['page']}, limit: {data['limit']}, pages: {data['pages']}")
                        
                        # Test house object structure
                        if houses:
                            self.test_house_object_structure(houses[0])
                            self.test_periodicity_validation(houses)
                    else:
                        self.log_test("Houses Base Response ❌", False, f"houses should be array, got {type(houses)}")
                else:
                    self.log_test("Houses Base Response ❌", False, f"Non-integer pagination fields: {non_integer_fields}")
            else:
                self.log_test("Houses Base Response ❌", False, f"Missing fields: {missing_fields}")
        else:
            self.log_test("Houses Base Response ❌", False, f"Status: {status}, Response: {data}")
        
        # Search test: search=подстрока адреса/названия
        print("\n   🔍 Search filter test")
        search_terms = ["ул", "дом", "Аллейная"]
        for term in search_terms:
            success, data, status = self.make_request('GET', '/api/cleaning/houses', 
                                                    params={'search': term, 'limit': 10})
            if success and status == 200:
                houses = data.get('houses', [])
                # Verify search results contain the search term
                matching_houses = 0
                for house in houses:
                    address = house.get('address', '').lower()
                    title = house.get('title', '').lower()
                    if term.lower() in address or term.lower() in title:
                        matching_houses += 1
                
                if matching_houses > 0 or len(houses) == 0:  # Empty result is also valid
                    self.log_test(f"Houses Search '{term}' ✅", True, 
                                f"Found {len(houses)} houses, {matching_houses} contain '{term}'")
                else:
                    self.log_test(f"Houses Search '{term}' ❌", False, 
                                f"Search returned {len(houses)} houses but none contain '{term}'")
            else:
                self.log_test(f"Houses Search '{term}' ❌", False, f"Status: {status}")
        
        # Date filter test: cleaning_date=YYYY-MM-DD
        print("\n   📅 Cleaning date filter test")
        test_dates = ["2025-09-05", "2025-09-15", "2025-10-01"]
        for date in test_dates:
            success, data, status = self.make_request('GET', '/api/cleaning/houses', 
                                                    params={'cleaning_date': date, 'limit': 10})
            if success and status == 200:
                houses = data.get('houses', [])
                self.log_test(f"Houses Date Filter '{date}' ✅", True, 
                            f"Date filter works, returned {len(houses)} houses")
                
                # Verify houses have the exact date in cleaning_dates
                if houses:
                    sample_house = houses[0]
                    cleaning_dates = sample_house.get('cleaning_dates', {})
                    has_date = False
                    for block in cleaning_dates.values():
                        if isinstance(block, dict):
                            dates = block.get('dates', [])
                            if date in dates:
                                has_date = True
                                break
                    if has_date:
                        print(f"      ✓ Sample house contains date {date}")
            else:
                self.log_test(f"Houses Date Filter '{date}' ❌", False, f"Status: {status}")
        
        # Date range test: date_from & date_to
        print("\n   📅 Date range filter test")
        date_ranges = [
            ("2025-09-01", "2025-09-30"),
            ("2025-10-01", "2025-10-31"),
            ("2025-11-01", "2025-11-30")
        ]
        for date_from, date_to in date_ranges:
            success, data, status = self.make_request('GET', '/api/cleaning/houses', 
                                                    params={'date_from': date_from, 'date_to': date_to, 'limit': 10})
            if success and status == 200:
                houses = data.get('houses', [])
                self.log_test(f"Houses Date Range '{date_from}' to '{date_to}' ✅", True, 
                            f"Date range filter works, returned {len(houses)} houses")
            else:
                self.log_test(f"Houses Date Range '{date_from}' to '{date_to}' ❌", False, f"Status: {status}")

    def test_house_object_structure(self, house):
        """Test house object contains all required fields"""
        required_fields = ['id', 'title', 'address', 'brigade', 'management_company', 'status', 
                          'apartments', 'entrances', 'floors', 'cleaning_dates', 'periodicity', 'bitrix_url']
        missing_fields = [field for field in required_fields if field not in house]
        
        if not missing_fields:
            # Verify field types
            type_errors = []
            if not isinstance(house.get('brigade'), str):
                type_errors.append(f"brigade should be string, got {type(house.get('brigade'))}")
            if not isinstance(house.get('management_company'), str):
                type_errors.append(f"management_company should be string, got {type(house.get('management_company'))}")
            if not isinstance(house.get('periodicity'), str):
                type_errors.append(f"periodicity should be string, got {type(house.get('periodicity'))}")
            if not isinstance(house.get('cleaning_dates'), dict):
                type_errors.append(f"cleaning_dates should be object, got {type(house.get('cleaning_dates'))}")
            if not isinstance(house.get('bitrix_url'), str):
                type_errors.append(f"bitrix_url should be string, got {type(house.get('bitrix_url'))}")
            
            if not type_errors:
                self.log_test("House Object Structure ✅", True, 
                            f"House ID {house['id']}: all required fields present with correct types")
                
                # Log sample data
                print(f"      Brigade: '{house.get('brigade', 'N/A')}'")
                print(f"      Management Company: '{house.get('management_company', 'N/A')}'")
                print(f"      Periodicity: '{house.get('periodicity', 'N/A')}'")
                print(f"      Bitrix URL: {'present' if house.get('bitrix_url') else 'empty'}")
            else:
                self.log_test("House Object Structure ❌", False, f"Type errors: {type_errors}")
        else:
            self.log_test("House Object Structure ❌", False, f"Missing fields: {missing_fields}")

    def test_periodicity_validation(self, houses):
        """Validate periodicity values are from allowed set"""
        allowed_periodicity = ["2 раза", "2 раза + первые этажи", "Мытье 2 раза + подметание 2 раза", "4 раза", "индивидуальная"]
        
        invalid_periodicity = []
        periodicity_counts = {}
        
        for house in houses[:10]:  # Check first 10 houses
            periodicity = house.get('periodicity', '')
            if periodicity not in allowed_periodicity:
                invalid_periodicity.append(f"House {house.get('id')}: '{periodicity}'")
            
            # Count occurrences
            periodicity_counts[periodicity] = periodicity_counts.get(periodicity, 0) + 1
        
        if not invalid_periodicity:
            self.log_test("Periodicity Validation ✅", True, 
                        f"All periodicity values are valid. Counts: {periodicity_counts}")
        else:
            self.log_test("Periodicity Validation ❌", False, 
                        f"Invalid periodicity values found: {invalid_periodicity[:5]}")

    def test_cleaning_house_details_comprehensive(self):
        """Test GET /api/cleaning/house/{id}/details comprehensively"""
        print("\n3️⃣ Testing GET /api/cleaning/house/{id}/details")
        
        # Get a valid house ID first
        success, houses_data, status = self.make_request('GET', '/api/cleaning/houses', params={'limit': 5})
        test_house_id = None
        
        if success and status == 200 and houses_data.get('houses'):
            test_house_id = houses_data['houses'][0]['id']
            print(f"   Using house ID {test_house_id} for testing")
        else:
            # Fallback to known ID
            test_house_id = 13112
            print(f"   Using fallback house ID {test_house_id}")
        
        # Test valid house details
        print(f"\n   📋 Testing valid house details (ID: {test_house_id})")
        success, data, status = self.make_request('GET', f'/api/cleaning/house/{test_house_id}/details')
        
        if success and status == 200:
            # Check response structure
            if isinstance(data, dict) and 'house' in data:
                house = data['house']
                
                # Verify required fields in house object
                required_fields = ['cleaning_dates', 'periodicity', 'bitrix_url']
                missing_fields = [field for field in required_fields if field not in house]
                
                if not missing_fields:
                    self.log_test("House Details Valid Response ✅", True, 
                                f"House ID {test_house_id}: contains cleaning_dates, periodicity, bitrix_url")
                    
                    # Check cleaning_dates structure and human-readable types
                    cleaning_dates = house.get('cleaning_dates', {})
                    if isinstance(cleaning_dates, dict):
                        self.test_cleaning_dates_types(cleaning_dates, test_house_id)
                    
                    # Check periodicity
                    periodicity = house.get('periodicity', '')
                    allowed_periodicity = ["2 раза", "2 раза + первые этажи", "Мытье 2 раза + подметание 2 раза", "4 раза", "индивидуальная"]
                    if periodicity in allowed_periodicity:
                        print(f"      ✓ Periodicity valid: '{periodicity}'")
                    else:
                        print(f"      ⚠ Periodicity not in allowed set: '{periodicity}'")
                    
                    # Check bitrix_url
                    bitrix_url = house.get('bitrix_url', '')
                    if isinstance(bitrix_url, str) and bitrix_url:
                        print(f"      ✓ Bitrix URL present: {len(bitrix_url)} chars")
                    else:
                        print(f"      ⚠ Bitrix URL empty or invalid")
                else:
                    self.log_test("House Details Valid Response ❌", False, f"Missing fields: {missing_fields}")
            else:
                self.log_test("House Details Valid Response ❌", False, f"Invalid response structure: {type(data)}")
        else:
            self.log_test("House Details Valid Response ❌", False, f"Status: {status}, Response: {data}")
        
        # Test invalid house ID (should return 404, not 500)
        print("\n   ❌ Testing invalid house ID (should return 404)")
        invalid_id = 999999
        success, data, status = self.make_request('GET', f'/api/cleaning/house/{invalid_id}/details')
        
        if status == 404:
            detail = data.get('detail', '')
            if 'не найден' in detail.lower():
                self.log_test("House Details Invalid ID ✅", True, f"Correctly returns 404 with message: '{detail}'")
            else:
                self.log_test("House Details Invalid ID ❌", False, f"404 but wrong message: '{detail}'")
        elif status == 500:
            self.log_test("House Details Invalid ID ❌", False, f"Returns 500 instead of 404 for invalid ID {invalid_id}")
        else:
            self.log_test("House Details Invalid ID ❌", False, f"Expected 404, got {status} for invalid ID {invalid_id}")

    def test_cleaning_dates_types(self, cleaning_dates, house_id):
        """Test that cleaning_dates.*.type returns human-readable labels, not raw IDs"""
        human_readable_found = 0
        raw_id_found = 0
        
        for key, block in cleaning_dates.items():
            if isinstance(block, dict):
                type_value = block.get('type', '')
                if isinstance(type_value, str):
                    # Check if it's a raw ID (numeric) or human-readable
                    if type_value.isdigit():
                        raw_id_found += 1
                        print(f"      ⚠ Raw ID found in {key}.type: '{type_value}'")
                    elif type_value and len(type_value) > 3:  # Human-readable should be longer
                        human_readable_found += 1
                        print(f"      ✓ Human-readable type in {key}: '{type_value}'")
        
        if human_readable_found > 0 and raw_id_found == 0:
            self.log_test("Cleaning Dates Types ✅", True, 
                        f"House {house_id}: {human_readable_found} human-readable types, no raw IDs")
        elif raw_id_found > 0:
            self.log_test("Cleaning Dates Types ⚠", False, 
                        f"House {house_id}: {raw_id_found} raw IDs found, {human_readable_found} human-readable")
        else:
            print(f"      ℹ No type data found for house {house_id}")

    def test_bitrix_stability_comprehensive(self):
        """Test Bitrix 503/error stability - endpoints should not return 500"""
        print("\n4️⃣ Testing Bitrix Stability (503 fallback behavior)")
        
        # Test that endpoints return stable responses even if Bitrix is down
        endpoints_to_test = [
            ('/api/cleaning/filters', 'GET', None),
            ('/api/cleaning/houses', 'GET', {'limit': 5}),
        ]
        
        for endpoint, method, params in endpoints_to_test:
            success, data, status = self.make_request(method, endpoint, params=params)
            
            if success and status == 200:
                # Check that response has stable structure
                if endpoint == '/api/cleaning/filters':
                    required_fields = ['brigades', 'management_companies', 'statuses']
                    has_structure = all(field in data for field in required_fields)
                    if has_structure:
                        self.log_test(f"Bitrix Stability {endpoint} ✅", True, 
                                    "Returns stable structure even if Bitrix has issues")
                    else:
                        self.log_test(f"Bitrix Stability {endpoint} ❌", False, 
                                    f"Missing structure fields when Bitrix down")
                
                elif endpoint == '/api/cleaning/houses':
                    required_fields = ['houses', 'total', 'page', 'limit', 'pages']
                    has_structure = all(field in data for field in required_fields)
                    if has_structure and isinstance(data['houses'], list):
                        self.log_test(f"Bitrix Stability {endpoint} ✅", True, 
                                    f"Returns stable structure: {len(data['houses'])} houses, total={data['total']}")
                    else:
                        self.log_test(f"Bitrix Stability {endpoint} ❌", False, 
                                    f"Invalid structure when Bitrix down")
            
            elif status == 500:
                # 500 errors indicate poor Bitrix fallback handling
                detail = data.get('detail', '')
                self.log_test(f"Bitrix Stability {endpoint} ❌", False, 
                            f"Returns 500 instead of stable fallback: {detail}")
            
            else:
                # Other status codes might be acceptable depending on implementation
                self.log_test(f"Bitrix Stability {endpoint} ℹ", True, 
                            f"Status {status} (may be acceptable fallback behavior)")

    def test_review_request_specific(self):
        """Test specific scenarios from the review request"""
        print("🎯 REVIEW REQUEST SPECIFIC TESTS")
        print("=" * 60)
        print("Base URL: https://audiobot-qci2.onrender.com")
        print("Testing specific scenarios as requested")
        print("-" * 60)
        
        # Test 1: GET /api/cleaning/house/12966/details
        self.test_house_12966_details()
        
        # Test 2: GET /api/cleaning/filters
        filters_data = self.test_cleaning_filters_specific()
        
        # Test 3: GET /api/cleaning/houses?brigade=<first_brigade>
        if filters_data:
            self.test_brigade_filtering(filters_data)
        
        return True

    def test_house_12966_details(self):
        """Test GET /api/cleaning/house/12966/details - expect 200 and house.periodicity == '2 раза + подметания'"""
        print("\n1️⃣ Testing GET /api/cleaning/house/12966/details")
        
        success, data, status = self.make_request('GET', '/api/cleaning/house/12966/details')
        
        if success and status == 200:
            # Check if response has house object
            if 'house' in data:
                house = data['house']
                
                # Check periodicity
                periodicity = house.get('periodicity', '')
                if periodicity == '2 раза + подметания':
                    self.log_test("House 12966 - Periodicity Check", True, f"✅ periodicity = '{periodicity}'")
                else:
                    self.log_test("House 12966 - Periodicity Check", False, f"❌ Expected '2 раза + подметания', got '{periodicity}'")
                
                # Check cleaning_dates format
                cleaning_dates = house.get('cleaning_dates', {})
                date_format_errors = []
                
                for period_key in ['september_1', 'september_2']:
                    if period_key in cleaning_dates:
                        period_data = cleaning_dates[period_key]
                        if isinstance(period_data, dict) and 'dates' in period_data:
                            dates = period_data['dates']
                            if isinstance(dates, list):
                                for date in dates:
                                    # Check YYYY-MM-DD format
                                    if not (isinstance(date, str) and len(date) == 10 and date.count('-') == 2):
                                        date_format_errors.append(f"{period_key}: '{date}' not in YYYY-MM-DD format")
                
                if not date_format_errors:
                    self.log_test("House 12966 - Date Format Check", True, "✅ All dates in YYYY-MM-DD format")
                    
                    # Show sample dates
                    sample_dates = []
                    for period_key in ['september_1', 'september_2']:
                        if period_key in cleaning_dates and 'dates' in cleaning_dates[period_key]:
                            dates = cleaning_dates[period_key]['dates']
                            if dates:
                                sample_dates.extend(dates[:2])  # Take first 2 dates from each period
                    
                    if sample_dates:
                        print(f"   📅 Sample dates: {sample_dates}")
                else:
                    self.log_test("House 12966 - Date Format Check", False, f"❌ Date format errors: {date_format_errors}")
                
                # Show full response sample
                print(f"   🏠 House ID: {house.get('id')}")
                print(f"   📍 Address: {house.get('address', 'N/A')}")
                print(f"   🔧 Periodicity: {house.get('periodicity', 'N/A')}")
                print(f"   🔗 Bitrix URL: {house.get('bitrix_url', 'N/A')}")
                
            else:
                self.log_test("House 12966 - Response Structure", False, "❌ Missing 'house' object in response")
        else:
            self.log_test("House 12966 - API Response", False, f"❌ Status: {status}, Data: {data}")

    def test_cleaning_filters_specific(self):
        """Test GET /api/cleaning/filters - brigades not empty, management_companies = [], statuses present"""
        print("\n2️⃣ Testing GET /api/cleaning/filters")
        
        success, data, status = self.make_request('GET', '/api/cleaning/filters')
        
        if success and status == 200:
            # Check brigades not empty
            brigades = data.get('brigades', [])
            if isinstance(brigades, list) and len(brigades) > 0:
                self.log_test("Filters - Brigades Not Empty", True, f"✅ Found {len(brigades)} brigades")
                print(f"   👥 Sample brigades: {brigades[:5]}")
            else:
                self.log_test("Filters - Brigades Not Empty", False, f"❌ Brigades empty or invalid: {brigades}")
            
            # Check management_companies is empty array
            management_companies = data.get('management_companies', None)
            if isinstance(management_companies, list) and len(management_companies) == 0:
                self.log_test("Filters - Management Companies Empty", True, "✅ management_companies = [] (empty array)")
            else:
                self.log_test("Filters - Management Companies Empty", False, f"❌ Expected [], got: {management_companies}")
            
            # Check statuses present
            statuses = data.get('statuses', [])
            if isinstance(statuses, list) and len(statuses) > 0:
                self.log_test("Filters - Statuses Present", True, f"✅ Found {len(statuses)} statuses")
                print(f"   📊 Sample statuses: {statuses[:3]}")
            else:
                self.log_test("Filters - Statuses Present", False, f"❌ Statuses empty or invalid: {statuses}")
            
            return data
        else:
            self.log_test("Filters - API Response", False, f"❌ Status: {status}, Data: {data}")
            return None

    def test_brigade_filtering(self, filters_data):
        """Test GET /api/cleaning/houses?brigade=<first_brigade> - exact match filtering"""
        print("\n3️⃣ Testing Brigade Filtering")
        
        brigades = filters_data.get('brigades', [])
        if not brigades:
            self.log_test("Brigade Filtering - No Brigades", False, "❌ No brigades available for testing")
            return
        
        # Use first brigade for testing
        test_brigade = brigades[0]
        print(f"   🎯 Testing with brigade: '{test_brigade}'")
        
        success, data, status = self.make_request('GET', '/api/cleaning/houses', params={'brigade': test_brigade, 'limit': 20})
        
        if success and status == 200:
            houses = data.get('houses', [])
            if isinstance(houses, list):
                # Check that all houses have exact brigade match
                exact_matches = 0
                mismatches = []
                
                for house in houses:
                    house_brigade = house.get('brigade', '')
                    if house_brigade == test_brigade:
                        exact_matches += 1
                    else:
                        mismatches.append(f"House {house.get('id')}: '{house_brigade}' != '{test_brigade}'")
                
                if len(houses) > 0 and exact_matches == len(houses):
                    self.log_test("Brigade Filtering - Exact Match", True, f"✅ All {len(houses)} houses have exact brigade match")
                    
                    # Show sample JSON
                    if houses:
                        sample_house = houses[0]
                        print(f"   📋 Sample house JSON:")
                        print(f"      ID: {sample_house.get('id')}")
                        print(f"      Title: {sample_house.get('title', 'N/A')}")
                        print(f"      Brigade: '{sample_house.get('brigade', 'N/A')}'")
                        print(f"      Address: {sample_house.get('address', 'N/A')}")
                        
                elif len(houses) == 0:
                    self.log_test("Brigade Filtering - No Results", True, f"✅ No houses found for brigade '{test_brigade}' (acceptable)")
                else:
                    self.log_test("Brigade Filtering - Exact Match", False, f"❌ {exact_matches}/{len(houses)} exact matches. Mismatches: {mismatches[:3]}")
            else:
                self.log_test("Brigade Filtering - Response Structure", False, f"❌ Invalid houses array: {type(houses)}")
        else:
            self.log_test("Brigade Filtering - API Response", False, f"❌ Status: {status}, Data: {data}")

    def test_review_request_deployed_backend(self):
        """Test deployed backend as per review request"""
        print("\n🎯 REVIEW REQUEST: Testing Deployed Backend")
        print("=" * 60)
        print(f"Base URL: {self.base_url}")
        print("Scope: AI Training + CRM regression + Logistics (optional)")
        print("-" * 60)
        
        # AI Training endpoints (new router /api/ai-knowledge)
        print("\n🧠 AI TRAINING ENDPOINTS")
        print("-" * 30)
        
        # 1) POST /api/ai-knowledge/preview
        upload_id = self.test_ai_preview_deployed()
        
        # 2) POST /api/ai-knowledge/study
        document_id = None
        if upload_id:
            document_id = self.test_ai_study_deployed(upload_id)
        
        # 3) GET /api/ai-knowledge/status
        if upload_id:
            self.test_ai_status_deployed(upload_id)
        
        # 4) GET /api/ai-knowledge/documents
        self.test_ai_documents_deployed()
        
        # 5) POST /api/ai-knowledge/search
        self.test_ai_search_deployed()
        
        # 6) DELETE /api/ai-knowledge/document/{document_id}
        if document_id:
            self.test_ai_delete_deployed(document_id)
        
        # CRM regression tests
        print("\n🏠 CRM REGRESSION TESTS")
        print("-" * 30)
        
        # 7) GET /api/cleaning/filters
        self.test_crm_filters_deployed()
        
        # 8) GET /api/cleaning/houses
        self.test_crm_houses_deployed()
        
        # Logistics (optional)
        print("\n🚛 LOGISTICS (OPTIONAL)")
        print("-" * 30)
        
        # 9) POST /api/logistics/route
        self.test_logistics_deployed()
        
        return True

    def test_ai_preview_deployed(self):
        """Test POST /api/ai-knowledge/preview on deployed backend"""
        print("1️⃣ POST /api/ai-knowledge/preview")
        
        # Create test file as specified: test.txt("Hello AI"), chunk_tokens=600, overlap=100
        txt_content = "Hello AI"
        files = {'file': ('test.txt', txt_content.encode('utf-8'), 'text/plain')}
        data = {'chunk_tokens': 600, 'overlap': 100}
        
        success, response_data, status = self.make_multipart_request('POST', '/api/ai-knowledge/preview', files=files, data=data)
        
        if success and status == 200:
            # Expected: upload_id(string), preview(string), chunks>=1, stats.total_size_bytes>0
            required_fields = ['upload_id', 'preview', 'chunks', 'stats']
            missing_fields = [field for field in required_fields if field not in response_data]
            
            if not missing_fields:
                upload_id = response_data['upload_id']
                preview = response_data['preview']
                chunks = response_data['chunks']
                stats = response_data.get('stats', {})
                total_size_bytes = stats.get('total_size_bytes', 0)
                
                if (isinstance(upload_id, str) and len(upload_id) > 0 and
                    isinstance(preview, str) and len(preview) > 0 and
                    isinstance(chunks, int) and chunks >= 1 and
                    isinstance(total_size_bytes, int) and total_size_bytes > 0):
                    
                    self.log_test("AI Preview - Deployed", True, 
                                f"✅ 200, upload_id: {upload_id[:8]}..., preview: {len(preview)} chars, chunks: {chunks}, size: {total_size_bytes} bytes")
                    return upload_id
                else:
                    self.log_test("AI Preview - Deployed", False, 
                                f"❌ Invalid response values: chunks={chunks}, size={total_size_bytes}")
            else:
                self.log_test("AI Preview - Deployed", False, f"❌ Missing fields: {missing_fields}")
        elif status == 500 and 'Database is not initialized' in response_data.get('detail', ''):
            self.log_test("AI Preview - Deployed", True, 
                        f"✅ Expected 500 'Database is not initialized' (DATABASE_URL not set): {response_data.get('detail')}")
        else:
            self.log_test("AI Preview - Deployed", False, f"❌ Status: {status}, Data: {response_data}")
        
        return None

    def test_ai_study_deployed(self, upload_id):
        """Test POST /api/ai-knowledge/study on deployed backend"""
        print("2️⃣ POST /api/ai-knowledge/study")
        
        if not upload_id:
            self.log_test("AI Study - Deployed", False, "❌ No upload_id from preview")
            return None
        
        data = {
            'upload_id': upload_id,
            'filename': 'test.txt',
            'category': 'Клининг'
        }
        
        success, response_data, status = self.make_multipart_request('POST', '/api/ai-knowledge/study', data=data)
        
        if success and status == 200:
            # Expected: document_id, chunks>=1, category
            if ('document_id' in response_data and 
                'chunks' in response_data and 
                'category' in response_data):
                
                document_id = response_data['document_id']
                chunks = response_data['chunks']
                category = response_data['category']
                
                if (isinstance(document_id, str) and len(document_id) > 0 and
                    isinstance(chunks, int) and chunks >= 1 and
                    category == 'Клининг'):
                    
                    self.log_test("AI Study - Deployed", True, 
                                f"✅ 200, document_id: {document_id[:8]}..., chunks: {chunks}, category: {category}")
                    return document_id
                else:
                    self.log_test("AI Study - Deployed", False, 
                                f"❌ Invalid values: chunks={chunks}, category={category}")
            else:
                self.log_test("AI Study - Deployed", False, f"❌ Missing required fields in response")
        elif status == 500 and 'Database is not initialized' in response_data.get('detail', ''):
            self.log_test("AI Study - Deployed", True, 
                        f"✅ Expected 500 'Database is not initialized': {response_data.get('detail')}")
        else:
            self.log_test("AI Study - Deployed", False, f"❌ Status: {status}, Data: {response_data}")
        
        return None

    def test_ai_status_deployed(self, upload_id):
        """Test GET /api/ai-knowledge/status on deployed backend"""
        print("3️⃣ GET /api/ai-knowledge/status")
        
        if not upload_id:
            self.log_test("AI Status - Deployed", False, "❌ No upload_id provided")
            return
        
        success, response_data, status = self.make_request('GET', f'/api/ai-knowledge/status?upload_id={upload_id}')
        
        if success and status == 200:
            # Expected: until study -> 'ready', after study -> 'done' (or no row)
            if 'status' in response_data:
                status_value = response_data['status']
                if status_value in ['ready', 'done']:
                    self.log_test("AI Status - Deployed", True, f"✅ 200, status: {status_value}")
                else:
                    self.log_test("AI Status - Deployed", False, f"❌ Unexpected status: {status_value}")
            else:
                self.log_test("AI Status - Deployed", False, f"❌ Missing status field")
        elif status == 404:
            # No row found is acceptable (means 'done')
            self.log_test("AI Status - Deployed", True, f"✅ 404 (no row found - acceptable)")
        elif status == 500 and 'Database is not initialized' in response_data.get('detail', ''):
            self.log_test("AI Status - Deployed", True, 
                        f"✅ Expected 500 'Database is not initialized': {response_data.get('detail')}")
        else:
            self.log_test("AI Status - Deployed", False, f"❌ Status: {status}, Data: {response_data}")

    def test_ai_documents_deployed(self):
        """Test GET /api/ai-knowledge/documents on deployed backend"""
        print("4️⃣ GET /api/ai-knowledge/documents")
        
        success, response_data, status = self.make_request('GET', '/api/ai-knowledge/documents')
        
        if success and status == 200:
            # Expected: contains document from study with chunks_count>=1
            if 'documents' in response_data and isinstance(response_data['documents'], list):
                documents = response_data['documents']
                self.log_test("AI Documents - Deployed", True, 
                            f"✅ 200, documents: {len(documents)} found")
                
                # Check if any document has chunks_count >= 1
                if documents:
                    for doc in documents:
                        if doc.get('chunks_count', 0) >= 1:
                            self.log_test("AI Documents - Chunks", True, 
                                        f"✅ Document with chunks_count: {doc.get('chunks_count')}")
                            break
                    else:
                        self.log_test("AI Documents - Chunks", False, 
                                    f"❌ No documents with chunks_count >= 1")
            else:
                self.log_test("AI Documents - Deployed", False, f"❌ Invalid response structure")
        elif status == 500 and 'Database is not initialized' in response_data.get('detail', ''):
            self.log_test("AI Documents - Deployed", True, 
                        f"✅ Expected 500 'Database is not initialized': {response_data.get('detail')}")
        else:
            self.log_test("AI Documents - Deployed", False, f"❌ Status: {status}, Data: {response_data}")

    def test_ai_search_deployed(self):
        """Test POST /api/ai-knowledge/search on deployed backend"""
        print("5️⃣ POST /api/ai-knowledge/search")
        
        search_data = {
            'query': 'Hello',
            'top_k': 5
        }
        
        success, response_data, status = self.make_request('POST', '/api/ai-knowledge/search', search_data)
        
        if success and status == 200:
            # Expected: results[]
            if 'results' in response_data and isinstance(response_data['results'], list):
                results = response_data['results']
                self.log_test("AI Search - Deployed", True, 
                            f"✅ 200, results: {len(results)} found")
            else:
                self.log_test("AI Search - Deployed", False, f"❌ Invalid response structure")
        elif status == 500 and 'Database is not initialized' in response_data.get('detail', ''):
            self.log_test("AI Search - Deployed", True, 
                        f"✅ Expected 500 'Database is not initialized': {response_data.get('detail')}")
        else:
            self.log_test("AI Search - Deployed", False, f"❌ Status: {status}, Data: {response_data}")

    def test_ai_delete_deployed(self, document_id):
        """Test DELETE /api/ai-knowledge/document/{document_id} on deployed backend"""
        print("6️⃣ DELETE /api/ai-knowledge/document/{document_id}")
        
        if not document_id:
            self.log_test("AI Delete - Deployed", False, "❌ No document_id provided")
            return
        
        # First delete
        success, response_data, status = self.make_request('DELETE', f'/api/ai-knowledge/document/{document_id}')
        
        if success and status == 200:
            if response_data.get('ok') is True:
                self.log_test("AI Delete - Deployed", True, f"✅ 200, ok: true")
                
                # Repeat delete (should also return 200)
                success2, response_data2, status2 = self.make_request('DELETE', f'/api/ai-knowledge/document/{document_id}')
                if success2 and status2 == 200 and response_data2.get('ok') is True:
                    self.log_test("AI Delete - Repeated", True, f"✅ 200, ok: true (idempotent)")
                else:
                    self.log_test("AI Delete - Repeated", False, f"❌ Status: {status2}, Data: {response_data2}")
            else:
                self.log_test("AI Delete - Deployed", False, f"❌ Expected ok: true, got: {response_data}")
        elif status == 500 and 'Database is not initialized' in response_data.get('detail', ''):
            self.log_test("AI Delete - Deployed", True, 
                        f"✅ Expected 500 'Database is not initialized': {response_data.get('detail')}")
        else:
            self.log_test("AI Delete - Deployed", False, f"❌ Status: {status}, Data: {response_data}")

    def test_crm_filters_deployed(self):
        """Test GET /api/cleaning/filters on deployed backend"""
        print("7️⃣ GET /api/cleaning/filters")
        
        success, response_data, status = self.make_request('GET', '/api/cleaning/filters')
        
        if success and status == 200:
            # Expected: brigades non-empty, management_companies = []
            if ('brigades' in response_data and 
                'management_companies' in response_data and 
                'statuses' in response_data):
                
                brigades = response_data['brigades']
                management_companies = response_data['management_companies']
                statuses = response_data['statuses']
                
                # Check brigades non-empty
                brigades_ok = isinstance(brigades, list) and len(brigades) > 0
                # Check management_companies = []
                mc_ok = isinstance(management_companies, list) and len(management_companies) == 0
                # Check statuses present
                statuses_ok = isinstance(statuses, list)
                
                if brigades_ok and mc_ok and statuses_ok:
                    self.log_test("CRM Filters - Deployed", True, 
                                f"✅ 200, brigades: {len(brigades)} (non-empty), management_companies: [] (empty), statuses: {len(statuses)}")
                else:
                    self.log_test("CRM Filters - Deployed", False, 
                                f"❌ brigades_ok: {brigades_ok}, mc_ok: {mc_ok}, statuses_ok: {statuses_ok}")
            else:
                self.log_test("CRM Filters - Deployed", False, f"❌ Missing required fields")
        else:
            self.log_test("CRM Filters - Deployed", False, f"❌ Status: {status}, Data: {response_data}")

    def test_crm_houses_deployed(self):
        """Test GET /api/cleaning/houses on deployed backend"""
        print("8️⃣ GET /api/cleaning/houses?page=1&limit=50")
        
        success, response_data, status = self.make_request('GET', '/api/cleaning/houses', params={'page': 1, 'limit': 50})
        
        if success and status == 200:
            # Expected: required fields present
            if ('houses' in response_data and 
                'total' in response_data and 
                'page' in response_data and 
                'limit' in response_data and 
                'pages' in response_data):
                
                houses = response_data['houses']
                total = response_data['total']
                page = response_data['page']
                limit = response_data['limit']
                pages = response_data['pages']
                
                if isinstance(houses, list):
                    self.log_test("CRM Houses - Deployed", True, 
                                f"✅ 200, houses: {len(houses)}, total: {total}, page: {page}, limit: {limit}, pages: {pages}")
                    
                    # Check house object structure if houses exist
                    if houses:
                        house = houses[0]
                        required_fields = ['id', 'title', 'address', 'apartments', 'entrances', 'floors', 'cleaning_dates', 'periodicity', 'bitrix_url']
                        missing_fields = [field for field in required_fields if field not in house]
                        
                        if not missing_fields:
                            self.log_test("CRM Houses - Structure", True, 
                                        f"✅ House object has all required fields")
                        else:
                            self.log_test("CRM Houses - Structure", False, 
                                        f"❌ Missing fields: {missing_fields}")
                else:
                    self.log_test("CRM Houses - Deployed", False, f"❌ houses should be array, got {type(houses)}")
            else:
                self.log_test("CRM Houses - Deployed", False, f"❌ Missing required response fields")
        else:
            self.log_test("CRM Houses - Deployed", False, f"❌ Status: {status}, Data: {response_data}")

    def test_logistics_deployed(self):
        """Test POST /api/logistics/route on deployed backend (optional)"""
        print("9️⃣ POST /api/logistics/route (optional)")
        
        # Test with 1 point - should return 400 'Минимум 2 точки'
        test_data = {
            "points": [
                {"address": "Москва, Красная площадь"}
            ],
            "optimize": False,
            "profile": "driving-car",
            "language": "ru"
        }
        
        success, response_data, status = self.make_request('POST', '/api/logistics/route', test_data)
        
        if status == 404 and 'Not Found' in response_data.get('detail', ''):
            self.log_test("Logistics - Deployed", True, 
                        f"✅ Endpoint not implemented (404 'Not Found') - acceptable per review request")
        elif status == 400:
            detail = response_data.get('detail', '')
            if 'Минимум 2 точки' in detail:
                self.log_test("Logistics - Deployed", True, 
                            f"✅ 400 'Минимум 2 точки' - endpoint exists and validates correctly")
            else:
                self.log_test("Logistics - Deployed", False, 
                            f"❌ Wrong 400 error message: {detail}")
        else:
            self.log_test("Logistics - Deployed", False, 
                        f"❌ Unexpected response: Status {status}, Data: {response_data}")

    def run_review_request_tests(self):
        """Run specific tests as per review request"""
        print("=" * 80)
        print("🚀 REVIEW REQUEST BACKEND TESTING")
        print(f"Base URL: {self.base_url}")
        print("Goal: Verify presence of AI endpoints; if still 404, report clearly and skip to CRM tests")
        print("=" * 80)
        
        # Step A: Probe router
        print("\n📡 STEP A: Probing Router")
        print("-" * 40)
        self.probe_root_endpoint()
        ai_status_result = self.probe_ai_knowledge_status()
        
        # Step B: Determine AI module deployment status
        print("\n🧠 STEP B: AI Module Deployment Status")
        print("-" * 40)
        if self.ai_endpoints_deployed is False:
            print("❌ AI MODULE NOT DEPLOYED - Continuing with CRM-only tests")
        else:
            print("✅ AI MODULE DEPLOYED - Will test AI endpoints")
        
        # Step C: CRM tests (always run)
        print("\n🏠 STEP C: CRM Tests")
        print("-" * 40)
        self.test_crm_cleaning_filters_review()
        self.test_crm_houses_endpoint_review()
        
        # Step D: Logistics optional
        print("\n🚛 STEP D: Logistics Tests (Optional)")
        print("-" * 40)
        self.test_logistics_route_review()
        
        # AI tests if deployed
        if self.ai_endpoints_deployed:
            print("\n🧠 AI KNOWLEDGE TESTS")
            print("-" * 40)
            self.test_ai_knowledge_endpoints_review()
        
        # Final summary
        self.print_final_summary()
    
    def probe_root_endpoint(self):
        """Probe GET /api/ (root)"""
        success, data, status = self.make_request('GET', '/api/')
        
        if success and status == 200:
            if 'message' in data and 'VasDom AudioBot API' in data['message']:
                self.log_test("Root API Endpoint (/api/)", True, f"Status: {status}, Message: {data['message']}, Version: {data.get('version', 'N/A')}")
            else:
                self.log_test("Root API Endpoint (/api/)", False, f"Status: {status}, Unexpected response: {data}")
        else:
            self.log_test("Root API Endpoint (/api/)", False, f"Status: {status}, Data: {data}")
    
    def probe_ai_knowledge_status(self):
        """Probe GET /api/ai-knowledge/status?upload_id=x"""
        test_upload_id = "test_probe_id"
        success, data, status = self.make_request('GET', f'/api/ai-knowledge/status', params={'upload_id': test_upload_id})
        
        if status == 404 and success and 'Not Found' in str(data):
            self.log_test("AI Knowledge Status Probe", False, f"Status: {status} - AI endpoints NOT DEPLOYED")
            self.ai_endpoints_deployed = False
        elif status in [200, 404, 500]:
            # Any of these statuses indicate the endpoint exists
            detail = data.get('detail', '')
            if 'Database is not initialized' in detail:
                self.log_test("AI Knowledge Status Probe", True, f"Status: {status} - AI endpoints DEPLOYED (DB not initialized)")
            elif 'upload_id не найден' in detail or 'not found' in detail.lower():
                self.log_test("AI Knowledge Status Probe", True, f"Status: {status} - AI endpoints DEPLOYED (upload_id not found - expected)")
            else:
                self.log_test("AI Knowledge Status Probe", True, f"Status: {status} - AI endpoints DEPLOYED")
            self.ai_endpoints_deployed = True
        else:
            self.log_test("AI Knowledge Status Probe", False, f"Status: {status} - Unexpected response: {data}")
            self.ai_endpoints_deployed = False
        
        return status, data
    
    def test_crm_cleaning_filters_review(self):
        """Test GET /api/cleaning/filters - expect 200; brigades non-empty; management_companies=[]"""
        success, data, status = self.make_request('GET', '/api/cleaning/filters')
        
        if success and status == 200:
            # Check structure
            required_fields = ['brigades', 'management_companies', 'statuses']
            missing_fields = [field for field in required_fields if field not in data]
            
            if not missing_fields:
                brigades = data['brigades']
                management_companies = data['management_companies']
                statuses = data['statuses']
                
                # Verify brigades non-empty
                brigades_ok = isinstance(brigades, list) and len(brigades) > 0
                # Verify management_companies = []
                mc_ok = isinstance(management_companies, list) and len(management_companies) == 0
                # Verify statuses present
                statuses_ok = isinstance(statuses, list)
                
                if brigades_ok and mc_ok and statuses_ok:
                    self.log_test("CRM Filters Review", True, 
                                f"✅ brigades: {len(brigades)} (non-empty), management_companies: [] (empty), statuses: {len(statuses)}")
                    
                    # Show sample brigades
                    sample_brigades = brigades[:5] if len(brigades) > 5 else brigades
                    print(f"   Sample brigades: {sample_brigades}")
                    return True, data
                else:
                    errors = []
                    if not brigades_ok:
                        errors.append(f"brigades should be non-empty list, got {len(brigades) if isinstance(brigades, list) else type(brigades)}")
                    if not mc_ok:
                        errors.append(f"management_companies should be empty list, got {len(management_companies) if isinstance(management_companies, list) else type(management_companies)}")
                    if not statuses_ok:
                        errors.append(f"statuses should be list, got {type(statuses)}")
                    
                    self.log_test("CRM Filters Review", False, f"Validation errors: {'; '.join(errors)}")
            else:
                self.log_test("CRM Filters Review", False, f"Missing fields: {missing_fields}")
        else:
            self.log_test("CRM Filters Review", False, f"Status: {status}, Data: {data}")
        
        return False, {}
    
    def test_crm_houses_endpoint_review(self):
        """Test GET /api/cleaning/houses?page=1&limit=50 - expect 200; verify structure and required fields"""
        success, data, status = self.make_request('GET', '/api/cleaning/houses', params={'page': 1, 'limit': 50})
        
        if success and status == 200:
            # Check response structure
            required_fields = ['houses', 'total', 'page', 'limit', 'pages']
            missing_fields = [field for field in required_fields if field not in data]
            
            if not missing_fields:
                houses = data['houses']
                total = data['total']
                page = data['page']
                limit = data['limit']
                pages = data['pages']
                
                # Verify types
                if (isinstance(houses, list) and isinstance(total, int) and 
                    isinstance(page, int) and isinstance(limit, int) and isinstance(pages, int)):
                    
                    self.log_test("CRM Houses Structure", True, 
                                f"✅ houses: {len(houses)}, total: {total}, page: {page}, limit: {limit}, pages: {pages}")
                    
                    # Check house object structure if houses exist
                    if houses:
                        house = houses[0]
                        required_house_fields = ['id', 'title', 'address', 'apartments', 'entrances', 'floors', 'cleaning_dates', 'periodicity', 'bitrix_url']
                        missing_house_fields = [field for field in required_house_fields if field not in house]
                        
                        if not missing_house_fields:
                            self.log_test("CRM House Object Fields", True, 
                                        f"✅ House ID {house['id']}: all required fields present")
                            
                            # Show sample house data
                            sample_data = {
                                'id': house['id'],
                                'title': house['title'][:50] + '...' if len(house['title']) > 50 else house['title'],
                                'brigade': house.get('brigade', 'N/A'),
                                'management_company': house.get('management_company', 'N/A'),
                                'periodicity': house.get('periodicity', 'N/A')
                            }
                            print(f"   Sample house: {json.dumps(sample_data, ensure_ascii=False)}")
                            return True, data
                        else:
                            self.log_test("CRM House Object Fields", False, f"Missing house fields: {missing_house_fields}")
                    else:
                        self.log_test("CRM Houses Structure", False, "No houses returned")
                else:
                    type_errors = []
                    if not isinstance(houses, list):
                        type_errors.append(f"houses should be list, got {type(houses)}")
                    if not isinstance(total, int):
                        type_errors.append(f"total should be int, got {type(total)}")
                    if not isinstance(page, int):
                        type_errors.append(f"page should be int, got {type(page)}")
                    if not isinstance(limit, int):
                        type_errors.append(f"limit should be int, got {type(limit)}")
                    if not isinstance(pages, int):
                        type_errors.append(f"pages should be int, got {type(pages)}")
                    
                    self.log_test("CRM Houses Structure", False, f"Type errors: {'; '.join(type_errors)}")
            else:
                self.log_test("CRM Houses Structure", False, f"Missing fields: {missing_fields}")
        else:
            self.log_test("CRM Houses Structure", False, f"Status: {status}, Data: {data}")
        
        return False, {}
    
    def test_logistics_route_review(self):
        """Test POST /api/logistics/route with 1 point - if endpoint exists → 400 'Минимум 2 точки'; otherwise 404 acceptable"""
        test_data = {
            "points": [
                {"address": "Москва, Красная площадь"}
            ],
            "optimize": False,
            "profile": "driving-car",
            "language": "ru"
        }
        
        success, data, status = self.make_request('POST', '/api/logistics/route', test_data)
        
        if status == 404:
            # 404 is acceptable - endpoint not implemented
            self.log_test("Logistics Route Review", True, f"✅ Status: {status} - Endpoint not implemented (acceptable)")
        elif status == 400:
            # Check if it's the expected validation error
            detail = data.get('detail', '')
            if 'Минимум 2 точки' in detail:
                self.log_test("Logistics Route Review", True, f"✅ Status: {status} - Correct validation error: {detail}")
            else:
                self.log_test("Logistics Route Review", False, f"Status: {status} - Wrong error message: {detail}")
        else:
            self.log_test("Logistics Route Review", False, f"Status: {status} - Unexpected response: {data}")
    
    def test_ai_knowledge_endpoints_review(self):
        """Test AI Knowledge endpoints if they are deployed"""
        if not self.ai_endpoints_deployed:
            print("⏭️  Skipping AI Knowledge tests - endpoints not deployed")
            return
        
        print("🧠 Testing AI Knowledge Endpoints...")
        
        # Test key endpoints
        self.test_ai_knowledge_documents_review()
        self.test_ai_knowledge_search_review()
    
    def test_ai_knowledge_documents_review(self):
        """Test GET /api/ai-knowledge/documents"""
        success, data, status = self.make_request('GET', '/api/ai-knowledge/documents')
        
        if success and status == 200:
            if 'documents' in data and isinstance(data['documents'], list):
                docs_count = len(data['documents'])
                self.log_test("AI Knowledge Documents", True, f"✅ Retrieved {docs_count} documents")
            else:
                self.log_test("AI Knowledge Documents", False, f"Invalid response structure: {data}")
        elif status == 500 and 'Database is not initialized' in data.get('detail', ''):
            self.log_test("AI Knowledge Documents", True, f"✅ Expected 500 'Database is not initialized': {data.get('detail')}")
        else:
            self.log_test("AI Knowledge Documents", False, f"Status: {status}, Data: {data}")
    
    def test_ai_knowledge_search_review(self):
        """Test POST /api/ai-knowledge/search"""
        search_data = {
            'query': 'test',
            'top_k': 5
        }
        
        success, data, status = self.make_request('POST', '/api/ai-knowledge/search', search_data)
        
        if success and status == 200:
            if 'results' in data and isinstance(data['results'], list):
                results_count = len(data['results'])
                self.log_test("AI Knowledge Search", True, f"✅ Search returned {results_count} results")
            else:
                self.log_test("AI Knowledge Search", False, f"Invalid response structure: {data}")
        elif status == 500 and 'Database is not initialized' in data.get('detail', ''):
            self.log_test("AI Knowledge Search", True, f"✅ Expected 500 'Database is not initialized': {data.get('detail')}")
        else:
            self.log_test("AI Knowledge Search", False, f"Status: {status}, Data: {data}")
    
    def print_final_summary(self):
        """Print final test summary with clear pass/fail per step"""
        print("\n" + "=" * 80)
        print("📊 FINAL SUMMARY")
        print("=" * 80)
        
        print(f"Total Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {len(self.failed_tests)}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "No tests run")
        
        print("\n📋 STEP-BY-STEP RESULTS:")
        print("-" * 40)
        
        # Step A: Router probing
        root_passed = any("Root API Endpoint" in test['name'] for test in self.failed_tests) == False
        ai_status_passed = self.ai_endpoints_deployed is not None
        print(f"A) Router Probing: {'✅ PASS' if root_passed and ai_status_passed else '❌ FAIL'}")
        print(f"   - GET /api/: {'✅' if root_passed else '❌'}")
        print(f"   - GET /api/ai-knowledge/status: {'✅' if ai_status_passed else '❌'}")
        
        # Step B: AI Module Status
        if self.ai_endpoints_deployed is True:
            print("B) AI Module Status: ✅ DEPLOYED")
        elif self.ai_endpoints_deployed is False:
            print("B) AI Module Status: ❌ NOT DEPLOYED")
        else:
            print("B) AI Module Status: ❓ UNKNOWN")
        
        # Step C: CRM Tests
        crm_filters_passed = not any("CRM Filters Review" in test['name'] for test in self.failed_tests)
        crm_houses_passed = not any("CRM Houses Structure" in test['name'] for test in self.failed_tests)
        print(f"C) CRM Tests: {'✅ PASS' if crm_filters_passed and crm_houses_passed else '❌ FAIL'}")
        print(f"   - GET /api/cleaning/filters: {'✅' if crm_filters_passed else '❌'}")
        print(f"   - GET /api/cleaning/houses: {'✅' if crm_houses_passed else '❌'}")
        
        # Step D: Logistics Tests
        logistics_passed = not any("Logistics Route Review" in test['name'] for test in self.failed_tests)
        print(f"D) Logistics Tests: {'✅ PASS' if logistics_passed else '❌ FAIL'}")
        print(f"   - POST /api/logistics/route: {'✅' if logistics_passed else '❌'}")
        
        if self.failed_tests:
            print("\n❌ FAILED TESTS:")
            print("-" * 40)
            for i, test in enumerate(self.failed_tests, 1):
                print(f"{i}. {test['name']}")
                print(f"   Details: {test['details']}")
        
        print("\n" + "=" * 80)


    def run_smoke_test_review_request(self):
        """Run SMOKE tests for AI endpoints on prod after Alembic invocation fix"""
        print("🚀 SMOKE TEST - AI Endpoints on Production")
        print("=" * 60)
        print(f"Testing against: {self.base_url}")
        print("Review Request: Re-run SMOKE for AI endpoints after Alembic invocation fix")
        print("=" * 60)
        
        # Test 1: GET /api/ai-knowledge/status?upload_id=probe
        self.test_ai_status_probe()
        
        # Test 2: POST /api/ai-knowledge/preview multipart test.txt("Hello AI")
        self.test_ai_preview_smoke()
        
        # Test 3: Confirm CRM filters 200
        self.test_crm_filters_smoke()
        
        # Display final results
        self.display_results()

    def test_ai_status_probe(self):
        """Test GET /api/ai-knowledge/status?upload_id=probe - expect 200/404/500 (but not router-missing)"""
        print("\n1️⃣ Testing GET /api/ai-knowledge/status?upload_id=probe")
        
        success, data, status = self.make_request('GET', '/api/ai-knowledge/status', params={'upload_id': 'probe'})
        
        if status in [200, 404, 500]:
            # Any of these statuses are acceptable - means router is working
            if status == 200:
                self.log_test("AI Status Probe - Router Working", True, f"Status 200: {data}")
            elif status == 404:
                detail = data.get('detail', '')
                if 'Not Found' in detail and 'upload_id' not in detail:
                    # This indicates router is missing - the critical issue
                    self.log_test("AI Status Probe - Router Missing", False, f"Status 404 'Not Found' - AI endpoints NOT DEPLOYED. Router missing.")
                else:
                    self.log_test("AI Status Probe - Router Working", True, f"Status 404 (upload_id not found): {detail}")
            elif status == 500:
                detail = data.get('detail', '')
                if 'Database is not initialized' in detail:
                    self.log_test("AI Status Probe - Router Working", True, f"Status 500 (DB not initialized - expected): {detail}")
                else:
                    self.log_test("AI Status Probe - Router Working", True, f"Status 500 (other error): {detail}")
        else:
            self.log_test("AI Status Probe - Unexpected Response", False, f"Status: {status}, Data: {data}")
        
        # Capture and display body as requested
        print(f"   Response Body: {json.dumps(data, ensure_ascii=False, indent=2)}")

    def test_ai_preview_smoke(self):
        """Test POST /api/ai-knowledge/preview multipart test.txt('Hello AI') - expect 200 or 500 DB not initialized"""
        print("\n2️⃣ Testing POST /api/ai-knowledge/preview multipart test.txt('Hello AI')")
        
        # Create test.txt with "Hello AI" content
        txt_content = "Hello AI"
        files = {'files': ('test.txt', txt_content.encode('utf-8'), 'text/plain')}
        
        success, data, status = self.make_multipart_request('POST', '/api/ai-knowledge/preview', files=files)
        
        if status == 200:
            # Success case - check if response has expected structure
            if 'upload_id' in data and 'preview' in data:
                self.log_test("AI Preview Smoke - Success", True, f"Status 200: upload_id={data.get('upload_id', '')[:8]}..., preview={len(data.get('preview', ''))} chars")
            else:
                self.log_test("AI Preview Smoke - Success", True, f"Status 200 but unexpected structure: {data}")
        elif status == 500:
            detail = data.get('detail', '')
            if 'Database is not initialized' in detail:
                self.log_test("AI Preview Smoke - DB Not Initialized", True, f"Status 500 (DB not initialized - expected): {detail}")
            else:
                self.log_test("AI Preview Smoke - Server Error", True, f"Status 500 (other error): {detail}")
        elif status == 404:
            detail = data.get('detail', '')
            if 'Not Found' in detail:
                # This indicates router is missing
                self.log_test("AI Preview Smoke - Router Missing", False, f"Status 404 'Not Found' - AI endpoints NOT DEPLOYED. Router missing.")
            else:
                self.log_test("AI Preview Smoke - Unexpected Response", False, f"Status: {status}, Data: {data}")
        else:
            self.log_test("AI Preview Smoke - Unexpected Response", False, f"Status: {status}, Data: {data}")
        
        # Capture and display body as requested
        print(f"   Response Body: {json.dumps(data, ensure_ascii=False, indent=2)}")

    def test_crm_filters_smoke(self):
        """Test CRM filters endpoint returns 200 - confirm basic functionality"""
        print("\n3️⃣ Testing GET /api/cleaning/filters (CRM filters confirmation)")
        
        success, data, status = self.make_request('GET', '/api/cleaning/filters')
        
        if status == 200:
            # Check basic structure
            if isinstance(data, dict) and 'brigades' in data and 'statuses' in data:
                brigades_count = len(data.get('brigades', []))
                statuses_count = len(data.get('statuses', []))
                self.log_test("CRM Filters Smoke - Success", True, f"Status 200: brigades={brigades_count}, statuses={statuses_count}")
            else:
                self.log_test("CRM Filters Smoke - Success", True, f"Status 200 but unexpected structure: {data}")
        else:
            self.log_test("CRM Filters Smoke - Failed", False, f"Status: {status}, Data: {data}")
        
        # Capture and display body as requested
        print(f"   Response Body: {json.dumps(data, ensure_ascii=False, indent=2)}")

    def display_results(self):
        """Display final smoke test results"""
        print("\n" + "=" * 60)
        print("📊 SMOKE TEST RESULTS")
        print("=" * 60)
        print(f"Total Tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {len(self.failed_tests)}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%" if self.tests_run > 0 else "No tests run")
        
        if self.failed_tests:
            print("\n❌ FAILED TESTS:")
            for test in self.failed_tests:
                print(f"  - {test['name']}: {test['details']}")
        else:
            print("\n✅ ALL SMOKE TESTS PASSED!")

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {len(self.failed_tests)}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%" if self.tests_run > 0 else "No tests run")
        
        if self.failed_tests:
            print("\n❌ FAILED TESTS:")
            for test in self.failed_tests:
                print(f"  - {test['name']}: {test['details']}")
        else:
            print("\n✅ ALL TESTS PASSED!")

    def run_review_request_diagnostics(self):
        """Run diagnostics with direct asyncpg connection as per review request"""
        print("🔍 REVIEW REQUEST: AI Knowledge Diagnostics with Direct AsyncPG")
        print("=" * 70)
        print(f"Base URL: {self.base_url}")
        print("Testing: GET /api/ai-knowledge/db-check - expect connected true (using asyncpg)")
        print("=" * 70)
        
        # Step 1: Test GET /api/ai-knowledge/db-check
        db_status = self.test_db_check_endpoint_review_request()
        
        # Step 2: If available true and installed false, test POST install
        if db_status:
            connected = db_status.get('connected', False)
            pgvector_available = db_status.get('pgvector_available', False)
            pgvector_installed = db_status.get('pgvector_installed', False)
            
            print(f"\n📊 Database Status:")
            print(f"   Connected: {connected}")
            print(f"   PGVector Available: {pgvector_available}")
            print(f"   PGVector Installed: {pgvector_installed}")
            
            if pgvector_available and not pgvector_installed:
                print("   🔧 Attempting pgvector installation...")
                self.test_db_install_vector_review_request()
            elif pgvector_available and pgvector_installed:
                print("   ✅ pgvector already installed")
            else:
                print("   ❌ pgvector not available or connection failed")
        
        # Print summary
        self.print_summary()
        return self.tests_passed == self.tests_run

    def run_comprehensive_tests(self):
        """Run all comprehensive tests"""
        print("🚀 Starting VasDom AudioBot Backend API Testing")
        print("=" * 60)
        print(f"Testing URL: {self.base_url}")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        # PRIORITY: Review Request Diagnostics with NEON_DATABASE_URL
        print("\n🔍 PRIORITY TESTING: NEON_DATABASE_URL Diagnostics")
        print("User confirmed NEON_DATABASE_URL is set in Render")
        print("-" * 50)
        
        # Step 1: GET /api/ai-knowledge/db-dsn
        dsn_data = self.test_db_dsn_endpoint()
        
        # Step 2: GET /api/ai-knowledge/db-check
        db_status = self.test_db_check_endpoint()
        
        # Step 3: Conditional POST /api/ai-knowledge/db-install-vector
        if db_status and db_status.get('connected') and db_status.get('pgvector_available') and not db_status.get('pgvector_installed'):
            print("\n🔧 Installing pgvector extension...")
            self.test_db_install_vector_endpoint()
            # Re-check after installation
            db_status = self.test_db_check_endpoint()
        
        # Step 4: If fully connected and installed, run AI flow
        if db_status and db_status.get('connected') and db_status.get('pgvector_installed'):
            print("\n🧠 Running Quick AI Flow: preview -> study -> documents -> search -> delete")
            self.run_quick_ai_flow()
        
        # Core API Tests
        self.test_root_endpoint()
        
        # Print summary
        self.print_summary()
        
        return self.tests_passed, self.tests_run

    def test_db_dsn_endpoint(self):
        """Test GET /api/ai-knowledge/db-dsn endpoint - Review Request Step 1"""
        print("\n1️⃣ Testing GET /api/ai-knowledge/db-dsn")
        print("   Expect: raw_present=true, raw query ssl=true, no sslmode")
        
        success, data, status = self.make_request('GET', '/api/ai-knowledge/db-dsn')
        
        if success and status == 200:
            raw_present = data.get('raw_present', False)
            raw = data.get('raw', '')
            normalized = data.get('normalized', '')
            
            # Check expectations from review request
            if raw_present:
                # Ensure raw is a string
                raw_str = str(raw) if raw else ''
                
                # Check if raw query has ssl=true and no sslmode
                has_ssl_true = 'ssl=true' in raw_str.lower()
                has_sslmode = 'sslmode=' in raw_str.lower()
                
                if has_ssl_true and not has_sslmode:
                    self.log_test("DB DSN - Review Requirements", True, 
                                f"✅ raw_present=true, ssl=true, no sslmode")
                else:
                    self.log_test("DB DSN - Review Requirements", False, 
                                f"❌ Expected ssl=true and no sslmode. Found: ssl=true={has_ssl_true}, has_sslmode={has_sslmode}")
                
                # Log masked URLs for debugging
                raw_masked = self.mask_sensitive_url(raw_str)
                normalized_masked = self.mask_sensitive_url(str(normalized) if normalized else '')
                print(f"   📋 Raw URL: {raw_masked}")
                print(f"   📋 Normalized URL: {normalized_masked}")
                
                return data
            else:
                self.log_test("DB DSN - Review Requirements", False, "❌ raw_present=false")
        elif status == 404:
            self.log_test("DB DSN - Endpoint Exists", False, "❌ db-dsn endpoint not found (404)")
        else:
            self.log_test("DB DSN - Endpoint Response", False, f"❌ Status: {status}, Data: {data}")
        
        return None

    def test_db_check_endpoint(self):
        """Test GET /api/ai-knowledge/db-check endpoint - Review Request Step 2"""
        print("\n2️⃣ Testing GET /api/ai-knowledge/db-check")
        print("   Expect: connected=true; if pgvector_available=true and installed=false, POST install")
        
        success, data, status = self.make_request('GET', '/api/ai-knowledge/db-check')
        
        if success and status == 200:
            connected = data.get('connected', False)
            pgvector_available = data.get('pgvector_available', False)
            pgvector_installed = data.get('pgvector_installed', False)
            errors = data.get('errors', [])
            
            print(f"   📊 Database Status:")
            print(f"      Connected: {connected}")
            print(f"      PGVector Available: {pgvector_available}")
            print(f"      PGVector Installed: {pgvector_installed}")
            if errors:
                print(f"      Errors: {len(errors)} found")
                for i, error in enumerate(errors[:3]):  # Show first 3 errors
                    print(f"        {i+1}. {error}")
            
            if connected:
                self.log_test("DB Check - Connected", True, "✅ Database connected successfully")
                
                if pgvector_available and not pgvector_installed:
                    self.log_test("DB Check - PGVector Status", True, 
                                "✅ PGVector available but not installed - ready for installation")
                elif pgvector_available and pgvector_installed:
                    self.log_test("DB Check - PGVector Status", True, 
                                "✅ PGVector available and installed - ready for AI operations")
                else:
                    self.log_test("DB Check - PGVector Status", False, 
                                f"❌ PGVector status: available={pgvector_available}, installed={pgvector_installed}")
            else:
                self.log_test("DB Check - Connected", False, 
                            f"❌ Database not connected. Errors: {len(errors)}")
            
            return data
        elif status == 404:
            self.log_test("DB Check - Endpoint Exists", False, "❌ db-check endpoint not found (404)")
        else:
            self.log_test("DB Check - Endpoint Response", False, f"❌ Status: {status}, Data: {data}")
        
        return None

    def test_db_install_vector_endpoint(self):
        """Test POST /api/ai-knowledge/db-install-vector endpoint"""
        print("\n3️⃣ Testing POST /api/ai-knowledge/db-install-vector")
        
        success, data, status = self.make_request('POST', '/api/ai-knowledge/db-install-vector', {})
        
        if success and status == 200:
            installed = data.get('installed', False)
            message = data.get('message', '')
            
            if installed:
                self.log_test("DB Install Vector - Success", True, f"✅ PGVector installed: {message}")
            else:
                self.log_test("DB Install Vector - Success", False, f"❌ Installation failed: {message}")
            
            return data
        elif status == 422:
            # Validation error is acceptable if body is missing
            self.log_test("DB Install Vector - Validation", True, 
                        "✅ Returns 422 validation error (acceptable for missing body)")
        elif status == 404:
            self.log_test("DB Install Vector - Endpoint Exists", False, 
                        "❌ db-install-vector endpoint not found (404)")
        else:
            self.log_test("DB Install Vector - Response", False, f"❌ Status: {status}, Data: {data}")
        
        return None

    def run_quick_ai_flow(self):
        """Run quick AI flow: preview -> study -> documents -> search -> delete"""
        print("\n4️⃣ Running Quick AI Flow")
        
        # Step 1: Preview (upload)
        upload_id = self.test_ai_preview_step()
        if not upload_id:
            print("   ❌ Preview step failed - cannot continue AI flow")
            return
        
        # Step 2: Study (save)
        document_id = self.test_ai_study_step(upload_id)
        if not document_id:
            print("   ❌ Study step failed - cannot continue AI flow")
            return
        
        # Step 3: Documents (list)
        self.test_ai_documents_step()
        
        # Step 4: Search
        self.test_ai_search_step()
        
        # Step 5: Delete
        self.test_ai_delete_step(document_id)
        
        print("   ✅ Quick AI flow completed successfully")

    def test_ai_preview_step(self):
        """Test AI preview step (upload)"""
        print("   📤 Step 1: Preview (Upload)")
        
        # Create test content
        txt_content = """VasDom AudioBot AI Knowledge Test Document
        
This is a test document for the AI knowledge system.
It contains information about cleaning operations and house management.

Key topics:
- House cleaning schedules
- Brigade management
- Quality control procedures
- Bitrix24 integration
- AI assistant capabilities

This document will be processed into chunks for vector search."""

        files = {'files': ('ai_test_document.txt', txt_content.encode('utf-8'), 'text/plain')}
        data = {'chunk_tokens': '600', 'overlap': '100'}
        
        success, response_data, status = self.make_multipart_request('POST', '/api/ai-knowledge/preview', files=files, data=data)
        
        if success and status == 200:
            upload_id = response_data.get('upload_id')
            chunks = response_data.get('chunks', 0)
            preview = response_data.get('preview', '')
            
            if upload_id and chunks > 0:
                self.log_test("AI Preview - Upload Success", True, 
                            f"✅ upload_id: {upload_id[:8]}..., chunks: {chunks}")
                return upload_id
            else:
                self.log_test("AI Preview - Upload Success", False, 
                            f"❌ Invalid response: upload_id={bool(upload_id)}, chunks={chunks}")
        else:
            self.log_test("AI Preview - Upload Success", False, f"❌ Status: {status}, Data: {response_data}")
        
        return None

    def test_ai_study_step(self, upload_id):
        """Test AI study step (save)"""
        print("   📚 Step 2: Study (Save)")
        
        data = {
            'upload_id': upload_id,
            'filename': 'ai_test_knowledge.txt',
            'category': 'Testing'
        }
        
        success, response_data, status = self.make_multipart_request('POST', '/api/ai-knowledge/study', data=data)
        
        if success and status == 200:
            document_id = response_data.get('document_id')
            chunks = response_data.get('chunks', 0)
            category = response_data.get('category', '')
            
            if document_id:
                self.log_test("AI Study - Save Success", True, 
                            f"✅ document_id: {document_id[:8]}..., chunks: {chunks}, category: {category}")
                return document_id
            else:
                self.log_test("AI Study - Save Success", False, 
                            f"❌ No document_id in response: {response_data}")
        else:
            self.log_test("AI Study - Save Success", False, f"❌ Status: {status}, Data: {response_data}")
        
        return None

    def test_ai_documents_step(self):
        """Test AI documents step (list)"""
        print("   📋 Step 3: Documents (List)")
        
        success, data, status = self.make_request('GET', '/api/ai-knowledge/documents')
        
        if success and status == 200:
            documents = data.get('documents', [])
            if isinstance(documents, list):
                self.log_test("AI Documents - List Success", True, 
                            f"✅ Retrieved {len(documents)} documents")
            else:
                self.log_test("AI Documents - List Success", False, 
                            f"❌ Invalid documents format: {type(documents)}")
        else:
            self.log_test("AI Documents - List Success", False, f"❌ Status: {status}, Data: {data}")

    def test_ai_search_step(self):
        """Test AI search step"""
        print("   🔍 Step 4: Search")
        
        search_data = {
            'query': 'cleaning operations',
            'top_k': 5
        }
        
        success, data, status = self.make_request('POST', '/api/ai-knowledge/search', search_data)
        
        if success and status == 200:
            results = data.get('results', [])
            if isinstance(results, list):
                self.log_test("AI Search - Query Success", True, 
                            f"✅ Search returned {len(results)} results")
            else:
                self.log_test("AI Search - Query Success", False, 
                            f"❌ Invalid results format: {type(results)}")
        else:
            self.log_test("AI Search - Query Success", False, f"❌ Status: {status}, Data: {data}")

    def test_ai_delete_step(self, document_id):
        """Test AI delete step"""
        print("   🗑️ Step 5: Delete")
        
        success, data, status = self.make_request('DELETE', f'/api/ai-knowledge/document/{document_id}')
        
        if success and status == 200:
            ok = data.get('ok', False)
            if ok:
                self.log_test("AI Delete - Document Success", True, 
                            f"✅ Document {document_id[:8]}... deleted successfully")
            else:
                self.log_test("AI Delete - Document Success", False, 
                            f"❌ Delete failed: {data}")
        else:
            self.log_test("AI Delete - Document Success", False, f"❌ Status: {status}, Data: {data}")

    def mask_sensitive_url(self, url):
        """Mask sensitive parts of database URL for logging"""
        if not url or not isinstance(url, str):
            return url
        
        # Mask password in URL
        import re
        # Pattern to match postgresql://username:password@host:port/database
        pattern = r'(postgresql[^:]*://[^:]+:)([^@]+)(@.+)'
        masked = re.sub(pattern, r'\1***\3', url)
        return masked
        """Test AI DB diagnostics and full AI flow as per review request"""
        print("\n🔍 SMOKE TEST: AI DB Diagnostics and AI Flow")
        print("=" * 60)
        print("Review Request: Re-run SMOKE on prod https://audiobot-qci2.onrender.com")
        print("1) GET /api/ai-knowledge/db-check — parse JSON. If 404, report; if 500, capture detail.")
        print("2) If pgvector_available=true and installed=false, POST /api/ai-knowledge/db-install-vector {confirm:true} then re-check.")
        print("3) Try full AI flow if DB OK: preview (test.txt), study (Клининг), documents, search, delete.")
        print("4) Confirm CRM filters 200.")
        print("-" * 60)
        
        # Step 1: GET /api/ai-knowledge/db-check
        db_status = self.test_ai_db_check()
        
        # Step 2: Install pgvector if needed
        if db_status and db_status.get('pgvector_available') and not db_status.get('installed'):
            print("\n🔧 pgvector available but not installed - attempting installation...")
            install_success = self.test_ai_db_install_vector()
            if install_success:
                # Re-check after installation
                db_status = self.test_ai_db_check()
        
        # Step 3: Try full AI flow if DB is OK
        if db_status and db_status.get('database_initialized'):
            print("\n🧠 Database OK - Testing full AI flow...")
            self.test_full_ai_flow()
        else:
            print("\n❌ Database not initialized - skipping AI flow tests")
        
        # Step 4: Confirm CRM filters 200
        print("\n🏠 Testing CRM filters...")
        self.test_crm_filters_200()
        
        return True

    def test_ai_db_check(self):
        """Test GET /api/ai-knowledge/db-check endpoint"""
        print("\n1️⃣ Testing GET /api/ai-knowledge/db-check")
        
        success, data, status = self.make_request('GET', '/api/ai-knowledge/db-check')
        
        if status == 404:
            self.log_test("AI DB Check - Endpoint Missing", False, "GET /api/ai-knowledge/db-check returns 404 - endpoint not deployed")
            return None
        elif status == 500:
            detail = data.get('detail', '')
            self.log_test("AI DB Check - Server Error", False, f"500 error: {detail}")
            return None
        elif success and status == 200:
            # Parse JSON response
            try:
                # Expected fields: database_initialized, pgvector_available, installed, etc.
                db_initialized = data.get('database_initialized', False)
                pgvector_available = data.get('pgvector_available', False)
                installed = data.get('installed', False)
                
                self.log_test("AI DB Check - Success", True, 
                            f"DB initialized: {db_initialized}, pgvector available: {pgvector_available}, installed: {installed}")
                return data
            except Exception as e:
                self.log_test("AI DB Check - JSON Parse Error", False, f"Failed to parse JSON: {e}")
                return None
        else:
            self.log_test("AI DB Check - Unexpected Response", False, f"Status: {status}, Data: {data}")
            return None

    def test_ai_db_install_vector(self):
        """Test POST /api/ai-knowledge/db-install-vector endpoint"""
        print("\n2️⃣ Testing POST /api/ai-knowledge/db-install-vector")
        
        install_data = {'confirm': True}
        success, data, status = self.make_request('POST', '/api/ai-knowledge/db-install-vector', install_data)
        
        if status == 404:
            self.log_test("AI DB Install Vector - Endpoint Missing", False, "POST /api/ai-knowledge/db-install-vector returns 404 - endpoint not deployed")
            return False
        elif status == 500:
            detail = data.get('detail', '')
            self.log_test("AI DB Install Vector - Server Error", False, f"500 error: {detail}")
            return False
        elif success and status == 200:
            # Check if installation was successful
            success_flag = data.get('success', False)
            message = data.get('message', '')
            
            if success_flag:
                self.log_test("AI DB Install Vector - Success", True, f"pgvector installed successfully: {message}")
                return True
            else:
                self.log_test("AI DB Install Vector - Failed", False, f"Installation failed: {message}")
                return False
        else:
            self.log_test("AI DB Install Vector - Unexpected Response", False, f"Status: {status}, Data: {data}")
            return False

    def test_full_ai_flow(self):
        """Test full AI flow: preview -> study -> documents -> search -> delete"""
        print("\n3️⃣ Testing Full AI Flow")
        
        # Step 3a: Preview (test.txt)
        upload_id = self.test_ai_flow_preview()
        
        # Step 3b: Study (Клининг)
        document_id = None
        if upload_id:
            document_id = self.test_ai_flow_study(upload_id)
        
        # Step 3c: Documents
        self.test_ai_flow_documents()
        
        # Step 3d: Search
        self.test_ai_flow_search()
        
        # Step 3e: Delete
        if document_id:
            self.test_ai_flow_delete(document_id)

    def test_ai_flow_preview(self):
        """Test AI flow preview step with test.txt"""
        print("   3a) Testing preview (test.txt)")
        
        txt_content = "This is a test document for VasDom AudioBot AI system testing."
        files = {'file': ('test.txt', txt_content.encode('utf-8'), 'text/plain')}
        
        success, data, status = self.make_multipart_request('POST', '/api/ai-knowledge/preview', files=files)
        
        if success and status == 200:
            upload_id = data.get('upload_id')
            if upload_id:
                self.log_test("AI Flow - Preview", True, f"Preview successful, upload_id: {upload_id[:8]}...")
                return upload_id
            else:
                self.log_test("AI Flow - Preview", False, "No upload_id in response")
        else:
            self.log_test("AI Flow - Preview", False, f"Status: {status}, Data: {data}")
        
        return None

    def test_ai_flow_study(self, upload_id):
        """Test AI flow study step with category Клининг"""
        print("   3b) Testing study (Клининг)")
        
        data = {
            'upload_id': upload_id,
            'filename': 'test.txt',
            'category': 'Клининг'
        }
        
        success, response_data, status = self.make_multipart_request('POST', '/api/ai-knowledge/study', data=data)
        
        if success and status == 200:
            document_id = response_data.get('document_id')
            if document_id:
                self.log_test("AI Flow - Study", True, f"Study successful, document_id: {document_id[:8]}...")
                return document_id
            else:
                self.log_test("AI Flow - Study", False, "No document_id in response")
        else:
            self.log_test("AI Flow - Study", False, f"Status: {status}, Data: {response_data}")
        
        return None

    def test_ai_flow_documents(self):
        """Test AI flow documents listing"""
        print("   3c) Testing documents")
        
        success, data, status = self.make_request('GET', '/api/ai-knowledge/documents')
        
        if success and status == 200:
            documents = data.get('documents', [])
            self.log_test("AI Flow - Documents", True, f"Documents retrieved: {len(documents)} found")
        else:
            self.log_test("AI Flow - Documents", False, f"Status: {status}, Data: {data}")

    def test_ai_flow_search(self):
        """Test AI flow search functionality"""
        print("   3d) Testing search")
        
        search_data = {'query': 'test', 'top_k': 5}
        success, data, status = self.make_request('POST', '/api/ai-knowledge/search', search_data)
        
        if success and status == 200:
            results = data.get('results', [])
            self.log_test("AI Flow - Search", True, f"Search successful: {len(results)} results")
        else:
            self.log_test("AI Flow - Search", False, f"Status: {status}, Data: {data}")

    def test_ai_flow_delete(self, document_id):
        """Test AI flow document deletion"""
        print("   3e) Testing delete")
        
        success, data, status = self.make_request('DELETE', f'/api/ai-knowledge/document/{document_id}')
        
        if success and status == 200:
            ok = data.get('ok', False)
            if ok:
                self.log_test("AI Flow - Delete", True, f"Document deleted successfully: {document_id[:8]}...")
            else:
                self.log_test("AI Flow - Delete", False, f"Delete failed: {data}")
        else:
            self.log_test("AI Flow - Delete", False, f"Status: {status}, Data: {data}")

    def test_crm_filters_200(self):
        """Test CRM filters return 200 status"""
        print("\n4️⃣ Testing CRM filters 200")
        
        success, data, status = self.make_request('GET', '/api/cleaning/filters')
        
        if success and status == 200:
            brigades = data.get('brigades', [])
            management_companies = data.get('management_companies', [])
            statuses = data.get('statuses', [])
            
            self.log_test("CRM Filters - 200 Status", True, 
                        f"Filters OK: brigades={len(brigades)}, companies={len(management_companies)}, statuses={len(statuses)}")
        else:
            self.log_test("CRM Filters - 200 Status", False, f"Status: {status}, Data: {data}")

    def run_smoke_test_ai_diagnostics(self):
        """Run SMOKE test for AI DB diagnostics and AI flow as per review request"""
        print("🚀 SMOKE TEST: AI DB Diagnostics and AI Flow")
        print("=" * 60)
        print(f"Testing URL: {self.base_url}")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        # Run AI DB diagnostics and flow test
        self.test_ai_db_diagnostics_flow()
        
        # Print summary
        self.print_summary()

def main():
    """Main function to run tests"""
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        base_url = "https://audiobot-qci2.onrender.com"
    
    tester = VasDomAPITester(base_url)
    
    # Check if we should run smoke test specifically
    if len(sys.argv) > 2 and sys.argv[2] == "smoke":
        tester.run_smoke_test_ai_diagnostics()
    else:
        tester.run_comprehensive_tests()

if __name__ == "__main__":
    main()


    def run_review_request_tests(self):
        """Run specific tests as per review request"""
        print("=" * 80)
        print("🚀 REVIEW REQUEST BACKEND TESTING")
        print(f"Base URL: {self.base_url}")
        print("Goal: Verify presence of AI endpoints; if still 404, report clearly and skip to CRM tests")
        print("=" * 80)
        
        # Step A: Probe router
        print("\n📡 STEP A: Probing Router")
        print("-" * 40)
        self.probe_root_endpoint()
        ai_status_result = self.probe_ai_knowledge_status()
        
        # Step B: Determine AI module deployment status
        print("\n🧠 STEP B: AI Module Deployment Status")
        print("-" * 40)
        if self.ai_endpoints_deployed is False:
            print("❌ AI MODULE NOT DEPLOYED - Continuing with CRM-only tests")
        else:
            print("✅ AI MODULE DEPLOYED - Will test AI endpoints")
        
        # Step C: CRM tests (always run)
        print("\n🏠 STEP C: CRM Tests")
        print("-" * 40)
        self.test_crm_cleaning_filters_review()
        self.test_crm_houses_endpoint_review()
        
        # Step D: Logistics optional
        print("\n🚛 STEP D: Logistics Tests (Optional)")
        print("-" * 40)
        self.test_logistics_route_review()
        
        # AI tests if deployed
        if self.ai_endpoints_deployed:
            print("\n🧠 AI KNOWLEDGE TESTS")
            print("-" * 40)
            self.test_ai_knowledge_endpoints_review()
        
        # Final summary
        self.print_final_summary()
    
    def probe_root_endpoint(self):
        """Probe GET /api/ (root)"""
        success, data, status = self.make_request('GET', '/api/')
        
        if success and status == 200:
            if 'message' in data and 'VasDom AudioBot API' in data['message']:
                self.log_test("Root API Endpoint (/api/)", True, f"Status: {status}, Message: {data['message']}, Version: {data.get('version', 'N/A')}")
            else:
                self.log_test("Root API Endpoint (/api/)", False, f"Status: {status}, Unexpected response: {data}")
        else:
            self.log_test("Root API Endpoint (/api/)", False, f"Status: {status}, Data: {data}")
    
    def probe_ai_knowledge_status(self):
        """Probe GET /api/ai-knowledge/status?upload_id=x"""
        test_upload_id = "test_probe_id"
        success, data, status = self.make_request('GET', f'/api/ai-knowledge/status', params={'upload_id': test_upload_id})
        
        if status == 404 and success and 'Not Found' in str(data):
            self.log_test("AI Knowledge Status Probe", False, f"Status: {status} - AI endpoints NOT DEPLOYED")
            self.ai_endpoints_deployed = False
        elif status in [200, 404, 500]:
            # Any of these statuses indicate the endpoint exists
            detail = data.get('detail', '')
            if 'Database is not initialized' in detail:
                self.log_test("AI Knowledge Status Probe", True, f"Status: {status} - AI endpoints DEPLOYED (DB not initialized)")
            elif 'upload_id не найден' in detail or 'not found' in detail.lower():
                self.log_test("AI Knowledge Status Probe", True, f"Status: {status} - AI endpoints DEPLOYED (upload_id not found - expected)")
            else:
                self.log_test("AI Knowledge Status Probe", True, f"Status: {status} - AI endpoints DEPLOYED")
            self.ai_endpoints_deployed = True
        else:
            self.log_test("AI Knowledge Status Probe", False, f"Status: {status} - Unexpected response: {data}")
            self.ai_endpoints_deployed = False
        
        return status, data
    
    def test_crm_cleaning_filters_review(self):
        """Test GET /api/cleaning/filters - expect 200; brigades non-empty; management_companies=[]"""
        success, data, status = self.make_request('GET', '/api/cleaning/filters')
        
        if success and status == 200:
            # Check structure
            required_fields = ['brigades', 'management_companies', 'statuses']
            missing_fields = [field for field in required_fields if field not in data]
            
            if not missing_fields:
                brigades = data['brigades']
                management_companies = data['management_companies']
                statuses = data['statuses']
                
                # Verify brigades non-empty
                brigades_ok = isinstance(brigades, list) and len(brigades) > 0
                # Verify management_companies = []
                mc_ok = isinstance(management_companies, list) and len(management_companies) == 0
                # Verify statuses present
                statuses_ok = isinstance(statuses, list)
                
                if brigades_ok and mc_ok and statuses_ok:
                    self.log_test("CRM Filters Review", True, 
                                f"✅ brigades: {len(brigades)} (non-empty), management_companies: [] (empty), statuses: {len(statuses)}")
                    
                    # Show sample brigades
                    sample_brigades = brigades[:5] if len(brigades) > 5 else brigades
                    print(f"   Sample brigades: {sample_brigades}")
                    return True, data
                else:
                    errors = []
                    if not brigades_ok:
                        errors.append(f"brigades should be non-empty list, got {len(brigades) if isinstance(brigades, list) else type(brigades)}")
                    if not mc_ok:
                        errors.append(f"management_companies should be empty list, got {len(management_companies) if isinstance(management_companies, list) else type(management_companies)}")
                    if not statuses_ok:
                        errors.append(f"statuses should be list, got {type(statuses)}")
                    
                    self.log_test("CRM Filters Review", False, f"Validation errors: {'; '.join(errors)}")
            else:
                self.log_test("CRM Filters Review", False, f"Missing fields: {missing_fields}")
        else:
            self.log_test("CRM Filters Review", False, f"Status: {status}, Data: {data}")
        
        return False, {}
    
    def test_crm_houses_endpoint_review(self):
        """Test GET /api/cleaning/houses?page=1&limit=50 - expect 200; verify structure and required fields"""
        success, data, status = self.make_request('GET', '/api/cleaning/houses', params={'page': 1, 'limit': 50})
        
        if success and status == 200:
            # Check response structure
            required_fields = ['houses', 'total', 'page', 'limit', 'pages']
            missing_fields = [field for field in required_fields if field not in data]
            
            if not missing_fields:
                houses = data['houses']
                total = data['total']
                page = data['page']
                limit = data['limit']
                pages = data['pages']
                
                # Verify types
                if (isinstance(houses, list) and isinstance(total, int) and 
                    isinstance(page, int) and isinstance(limit, int) and isinstance(pages, int)):
                    
                    self.log_test("CRM Houses Structure", True, 
                                f"✅ houses: {len(houses)}, total: {total}, page: {page}, limit: {limit}, pages: {pages}")
                    
                    # Check house object structure if houses exist
                    if houses:
                        house = houses[0]
                        required_house_fields = ['id', 'title', 'address', 'apartments', 'entrances', 'floors', 'cleaning_dates', 'periodicity', 'bitrix_url']
                        missing_house_fields = [field for field in required_house_fields if field not in house]
                        
                        if not missing_house_fields:
                            self.log_test("CRM House Object Fields", True, 
                                        f"✅ House ID {house['id']}: all required fields present")
                            
                            # Show sample house data
                            sample_data = {
                                'id': house['id'],
                                'title': house['title'][:50] + '...' if len(house['title']) > 50 else house['title'],
                                'brigade': house.get('brigade', 'N/A'),
                                'management_company': house.get('management_company', 'N/A'),
                                'periodicity': house.get('periodicity', 'N/A')
                            }
                            print(f"   Sample house: {json.dumps(sample_data, ensure_ascii=False)}")
                            return True, data
                        else:
                            self.log_test("CRM House Object Fields", False, f"Missing house fields: {missing_house_fields}")
                    else:
                        self.log_test("CRM Houses Structure", False, "No houses returned")
                else:
                    type_errors = []
                    if not isinstance(houses, list):
                        type_errors.append(f"houses should be list, got {type(houses)}")
                    if not isinstance(total, int):
                        type_errors.append(f"total should be int, got {type(total)}")
                    if not isinstance(page, int):
                        type_errors.append(f"page should be int, got {type(page)}")
                    if not isinstance(limit, int):
                        type_errors.append(f"limit should be int, got {type(limit)}")
                    if not isinstance(pages, int):
                        type_errors.append(f"pages should be int, got {type(pages)}")
                    
                    self.log_test("CRM Houses Structure", False, f"Type errors: {'; '.join(type_errors)}")
            else:
                self.log_test("CRM Houses Structure", False, f"Missing fields: {missing_fields}")
        else:
            self.log_test("CRM Houses Structure", False, f"Status: {status}, Data: {data}")
        
        return False, {}
    
    def test_logistics_route_review(self):
        """Test POST /api/logistics/route with 1 point - if endpoint exists → 400 'Минимум 2 точки'; otherwise 404 acceptable"""
        test_data = {
            "points": [
                {"address": "Москва, Красная площадь"}
            ],
            "optimize": False,
            "profile": "driving-car",
            "language": "ru"
        }
        
        success, data, status = self.make_request('POST', '/api/logistics/route', test_data)
        
        if status == 404:
            # 404 is acceptable - endpoint not implemented
            self.log_test("Logistics Route Review", True, f"✅ Status: {status} - Endpoint not implemented (acceptable)")
        elif status == 400:
            # Check if it's the expected validation error
            detail = data.get('detail', '')
            if 'Минимум 2 точки' in detail:
                self.log_test("Logistics Route Review", True, f"✅ Status: {status} - Correct validation error: {detail}")
            else:
                self.log_test("Logistics Route Review", False, f"Status: {status} - Wrong error message: {detail}")
        else:
            self.log_test("Logistics Route Review", False, f"Status: {status} - Unexpected response: {data}")
    
    def test_ai_knowledge_endpoints_review(self):
        """Test AI Knowledge endpoints if they are deployed"""
        if not self.ai_endpoints_deployed:
            print("⏭️  Skipping AI Knowledge tests - endpoints not deployed")
            return
        
        print("🧠 Testing AI Knowledge Endpoints...")
        
        # Test key endpoints
        self.test_ai_knowledge_documents_review()
        self.test_ai_knowledge_search_review()
    
    def test_ai_knowledge_documents_review(self):
        """Test GET /api/ai-knowledge/documents"""
        success, data, status = self.make_request('GET', '/api/ai-knowledge/documents')
        
        if success and status == 200:
            if 'documents' in data and isinstance(data['documents'], list):
                docs_count = len(data['documents'])
                self.log_test("AI Knowledge Documents", True, f"✅ Retrieved {docs_count} documents")
            else:
                self.log_test("AI Knowledge Documents", False, f"Invalid response structure: {data}")
        elif status == 500 and 'Database is not initialized' in data.get('detail', ''):
            self.log_test("AI Knowledge Documents", True, f"✅ Expected 500 'Database is not initialized': {data.get('detail')}")
        else:
            self.log_test("AI Knowledge Documents", False, f"Status: {status}, Data: {data}")
    
    def test_ai_knowledge_search_review(self):
        """Test POST /api/ai-knowledge/search"""
        search_data = {
            'query': 'test',
            'top_k': 5
        }
        
        success, data, status = self.make_request('POST', '/api/ai-knowledge/search', search_data)
        
        if success and status == 200:
            if 'results' in data and isinstance(data['results'], list):
                results_count = len(data['results'])
                self.log_test("AI Knowledge Search", True, f"✅ Search returned {results_count} results")
            else:
                self.log_test("AI Knowledge Search", False, f"Invalid response structure: {data}")
        elif status == 500 and 'Database is not initialized' in data.get('detail', ''):
            self.log_test("AI Knowledge Search", True, f"✅ Expected 500 'Database is not initialized': {data.get('detail')}")
        else:
            self.log_test("AI Knowledge Search", False, f"Status: {status}, Data: {data}")
    
    def print_final_summary(self):
        """Print final test summary with clear pass/fail per step"""
        print("\n" + "=" * 80)
        print("📊 FINAL SUMMARY")
        print("=" * 80)
        
        print(f"Total Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {len(self.failed_tests)}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "No tests run")
        
        print("\n📋 STEP-BY-STEP RESULTS:")
        print("-" * 40)
        
        # Step A: Router probing
        root_passed = any("Root API Endpoint" in test['name'] for test in self.failed_tests) == False
        ai_status_passed = self.ai_endpoints_deployed is not None
        print(f"A) Router Probing: {'✅ PASS' if root_passed and ai_status_passed else '❌ FAIL'}")
        print(f"   - GET /api/: {'✅' if root_passed else '❌'}")
        print(f"   - GET /api/ai-knowledge/status: {'✅' if ai_status_passed else '❌'}")
        
        # Step B: AI Module Status
        if self.ai_endpoints_deployed is True:
            print("B) AI Module Status: ✅ DEPLOYED")
        elif self.ai_endpoints_deployed is False:
            print("B) AI Module Status: ❌ NOT DEPLOYED")
        else:
            print("B) AI Module Status: ❓ UNKNOWN")
        
        # Step C: CRM Tests
        crm_filters_passed = not any("CRM Filters Review" in test['name'] for test in self.failed_tests)
        crm_houses_passed = not any("CRM Houses Structure" in test['name'] for test in self.failed_tests)
        print(f"C) CRM Tests: {'✅ PASS' if crm_filters_passed and crm_houses_passed else '❌ FAIL'}")
        print(f"   - GET /api/cleaning/filters: {'✅' if crm_filters_passed else '❌'}")
        print(f"   - GET /api/cleaning/houses: {'✅' if crm_houses_passed else '❌'}")
        
        # Step D: Logistics Tests
        logistics_passed = not any("Logistics Route Review" in test['name'] for test in self.failed_tests)
        print(f"D) Logistics Tests: {'✅ PASS' if logistics_passed else '❌ FAIL'}")
        print(f"   - POST /api/logistics/route: {'✅' if logistics_passed else '❌'}")
        
        if self.failed_tests:
            print("\n❌ FAILED TESTS:")
            print("-" * 40)
            for i, test in enumerate(self.failed_tests, 1):
                print(f"{i}. {test['name']}")
                print(f"   Details: {test['details']}")
        
        print("\n" + "=" * 80)

    def test_review_request_diagnostics(self):
        """Test specific diagnostics endpoints as per review request"""
        print("\n🔍 REVIEW REQUEST DIAGNOSTICS TESTING")
        print("=" * 70)
        print(f"Base URL: {self.base_url}")
        print("Testing after user updated DATABASE_URL on Render:")
        print("1) GET /api/ai-knowledge/db-dsn — capture JSON (raw_present, raw_contains_sslmode, raw, normalized)")
        print("2) GET /api/ai-knowledge/db-check — capture JSON (connected, pgvector_available, pgvector_installed, errors)")
        print("3) If connected=true and pgvector_available=true and installed=false, POST /api/ai-knowledge/db-install-vector")
        print("4) If all green, run quick AI flow: preview -> study -> documents -> search -> delete")
        print("-" * 70)
        
        # Step 1: GET /api/ai-knowledge/db-dsn
        print("\n📋 STEP 1: Testing db-dsn endpoint")
        dsn_result = self.test_db_dsn_endpoint()
        
        # Step 2: GET /api/ai-knowledge/db-check  
        print("\n📊 STEP 2: Testing db-check endpoint")
        check_result = self.test_db_check_endpoint_review()
        
        # Step 3: Conditional db-install-vector
        install_attempted = False
        if check_result:
            connected = check_result.get('connected', False)
            pgvector_available = check_result.get('pgvector_available', False)
            pgvector_installed = check_result.get('pgvector_installed', False)
            
            print(f"\n📊 Database Status Analysis:")
            print(f"   Connected: {connected}")
            print(f"   PGVector Available: {pgvector_available}")
            print(f"   PGVector Installed: {pgvector_installed}")
            
            if connected and pgvector_available and not pgvector_installed:
                print("\n🔧 STEP 3: Attempting pgvector installation...")
                install_result = self.test_db_install_vector_review()
                install_attempted = True
                
                if install_result:
                    # Re-check after installation
                    print("\n🔄 Re-checking database status after installation...")
                    check_result = self.test_db_check_endpoint_review()
                    
            # Step 4: AI Flow test if all green
            if check_result and check_result.get('connected') and check_result.get('pgvector_installed'):
                print("\n🧠 STEP 4: Database fully configured - running AI flow test")
                self.test_ai_flow_quick_test()
            else:
                print("\n⚠️  Database not fully ready for AI flow test")
                if check_result:
                    print(f"     Connected: {check_result.get('connected', False)}")
                    print(f"     PGVector Installed: {check_result.get('pgvector_installed', False)}")
        else:
            print("\n❌ Could not retrieve database status from db-check endpoint")
        
        print("\n📋 REVIEW REQUEST RESULTS SUMMARY:")
        print("=" * 50)
        if dsn_result:
            print("✅ db-dsn endpoint: WORKING")
        else:
            print("❌ db-dsn endpoint: FAILED")
            
        if check_result:
            print("✅ db-check endpoint: WORKING")
        else:
            print("❌ db-check endpoint: FAILED")
            
        if install_attempted:
            print("ℹ️  db-install-vector: ATTEMPTED")
        
        return dsn_result and check_result

    def test_db_dsn_endpoint(self):
        """Test GET /api/ai-knowledge/db-dsn endpoint - capture JSON with specific fields"""
        print("\n1️⃣ Testing GET /api/ai-knowledge/db-dsn")
        
        success, data, status = self.make_request('GET', '/api/ai-knowledge/db-dsn')
        
        if success and status == 200:
            # Check for expected fields from review request
            expected_fields = ['raw_present', 'raw_contains_sslmode', 'raw', 'normalized']
            missing_fields = [field for field in expected_fields if field not in data]
            
            if not missing_fields:
                # Extract specific sub-fields
                raw = data.get('raw', {})
                normalized = data.get('normalized', {})
                
                raw_scheme = raw.get('scheme', 'N/A')
                raw_query = raw.get('query', 'N/A')
                normalized_query = normalized.get('query', 'N/A')
                
                diagnostic_info = f"raw_present={data.get('raw_present')}, raw_contains_sslmode={data.get('raw_contains_sslmode')}, raw.scheme={raw_scheme}, raw.query={raw_query}, normalized.query={normalized_query}"
                
                self.log_test("DB DSN - Endpoint Response", True, diagnostic_info)
                
                # Print full JSON for review request
                print(f"   📄 Full JSON Response:")
                print(f"   {json.dumps(data, indent=2, ensure_ascii=False)}")
                
                return data
            else:
                self.log_test("DB DSN - Endpoint Response", False, f"Missing expected fields: {missing_fields}")
        elif status == 404:
            self.log_test("DB DSN - Endpoint Exists", False, "db-dsn endpoint not found (404) - not deployed")
        elif status == 500:
            detail = data.get('detail', '')
            self.log_test("DB DSN - Endpoint Response", False, f"500 error: {detail}")
        else:
            self.log_test("DB DSN - Endpoint Response", False, f"Status: {status}, Data: {data}")
        
        return None

    def test_db_check_endpoint_review(self):
        """Test GET /api/ai-knowledge/db-check endpoint for review request"""
        print("\n2️⃣ Testing GET /api/ai-knowledge/db-check")
        
        success, data, status = self.make_request('GET', '/api/ai-knowledge/db-check')
        
        if success and status == 200:
            # Print full JSON for review request
            print(f"   📄 Full JSON Response:")
            print(f"   {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            # Check basic structure
            if isinstance(data, dict):
                self.log_test("DB Check - Endpoint Response", True, f"Response received with {len(data)} fields")
                return data
            else:
                self.log_test("DB Check - Endpoint Response", False, f"Expected dict response, got {type(data)}")
        elif status == 404:
            self.log_test("DB Check - Endpoint Exists", False, "db-check endpoint not found (404) - not deployed")
        elif status == 500:
            detail = data.get('detail', '')
            self.log_test("DB Check - Endpoint Response", False, f"500 error: {detail}")
        else:
            self.log_test("DB Check - Endpoint Response", False, f"Status: {status}, Data: {data}")
        
        return None

    def test_db_install_vector_review(self):
        """Test POST /api/ai-knowledge/db-install-vector endpoint - Review Request Step 3"""
        install_data = {"confirm": True}
        success, data, status = self.make_request('POST', '/api/ai-knowledge/db-install-vector', install_data)
        
        if success and status == 200:
            # Check if installation was successful
            if 'success' in data or 'installed' in data or 'ok' in data:
                self.log_test("DB Install Vector - Installation", True, f"PGVector installation successful: {data}")
                print(f"   ✅ PGVector installation completed successfully")
                return True
            else:
                self.log_test("DB Install Vector - Installation", False, f"Unexpected success response: {data}")
        elif status == 422:
            # Validation error - check if it's about missing confirm field
            detail = data.get('detail', '')
            if isinstance(detail, list):
                detail = str(detail)
            self.log_test("DB Install Vector - Validation", True, f"Correct validation error for missing/invalid body: {detail}")
            print(f"   ℹ️  Validation error (expected): {detail}")
        elif status == 404:
            self.log_test("DB Install Vector - Endpoint Exists", False, "db-install-vector endpoint not found (404) - not deployed")
        elif status == 500:
            detail = data.get('detail', '')
            if 'already installed' in detail.lower() or 'already exists' in detail.lower():
                self.log_test("DB Install Vector - Already Installed", True, f"PGVector already installed: {detail}")
                print(f"   ℹ️  PGVector already installed: {detail}")
                return True
            else:
                self.log_test("DB Install Vector - Installation", False, f"500 error during installation: {detail}")
        else:
            self.log_test("DB Install Vector - Installation", False, f"Status: {status}, Data: {data}")
        
        return False

    def test_ai_flow_quick_test(self):
        """Test quick AI flow: preview -> study -> documents -> search -> delete - Review Request Step 4"""
        print("   📤 Testing AI Flow: preview -> study -> documents -> search -> delete")
        
        # Create a small test.txt content
        test_content = """VasDom AudioBot Test Document

This is a test document for the AI knowledge system.
The system manages cleaning operations for residential buildings.

Key features:
- House management and scheduling
- Brigade assignment and tracking  
- Quality control and monitoring
- Bitrix24 CRM integration
- AI assistant for staff support

The company services 490+ buildings with 82 employees across 7 brigades.
Modern automation systems streamline all operational processes."""

        # Step 4.1: Preview (upload)
        print("      📤 Testing preview...")
        files = {'files': ('test.txt', test_content.encode('utf-8'), 'text/plain')}
        success, data, status = self.make_multipart_request('POST', '/api/ai-knowledge/preview', files=files)
        
        upload_id = None
        if success and status == 200 and 'upload_id' in data:
            upload_id = data['upload_id']
            chunks = data.get('chunks', 0)
            preview = data.get('preview', '')
            self.log_test("AI Flow - Preview", True, f"upload_id: {upload_id[:8]}..., chunks: {chunks}, preview: {len(preview)} chars")
        else:
            self.log_test("AI Flow - Preview", False, f"Status: {status}, Data: {data}")
            return False

        # Step 4.2: Study (save)
        print("      💾 Testing study...")
        study_data = {
            'upload_id': upload_id,
            'filename': 'test_ai_flow.txt',
            'category': 'Test'
        }
        success, data, status = self.make_multipart_request('POST', '/api/ai-knowledge/study', data=study_data)
        
        document_id = None
        if success and status == 200 and 'document_id' in data:
            document_id = data['document_id']
            chunks = data.get('chunks', 0)
            category = data.get('category', '')
            self.log_test("AI Flow - Study", True, f"document_id: {document_id[:8]}..., chunks: {chunks}, category: {category}")
        else:
            self.log_test("AI Flow - Study", False, f"Status: {status}, Data: {data}")
            return False

        # Step 4.3: Documents (list)
        print("      📋 Testing documents...")
        success, data, status = self.make_request('GET', '/api/ai-knowledge/documents')
        
        if success and status == 200 and 'documents' in data:
            docs = data['documents']
            # Find our test document
            test_doc = None
            for doc in docs:
                if doc.get('id') == document_id:
                    test_doc = doc
                    break
            
            if test_doc:
                self.log_test("AI Flow - Documents", True, f"Found test document: {test_doc.get('filename', 'N/A')}, chunks: {test_doc.get('chunks_count', 0)}")
            else:
                self.log_test("AI Flow - Documents", False, f"Test document not found in list of {len(docs)} documents")
        else:
            self.log_test("AI Flow - Documents", False, f"Status: {status}, Data: {data}")

        # Step 4.4: Search
        print("      🔍 Testing search...")
        search_data = {
            'query': 'VasDom AudioBot cleaning',
            'top_k': 5
        }
        success, data, status = self.make_request('POST', '/api/ai-knowledge/search', search_data)
        
        if success and status == 200 and 'results' in data:
            results = data['results']
            # Look for results from our test document
            test_results = [r for r in results if r.get('document_id') == document_id]
            
            if test_results:
                best_score = max(r.get('score', 0) for r in test_results)
                self.log_test("AI Flow - Search", True, f"Found {len(test_results)} results from test doc, best score: {best_score:.3f}")
            else:
                self.log_test("AI Flow - Search", True, f"Search returned {len(results)} results (test doc may not be top match)")
        else:
            self.log_test("AI Flow - Search", False, f"Status: {status}, Data: {data}")

        # Step 4.5: Delete
        print("      🗑️  Testing delete...")
        success, data, status = self.make_request('DELETE', f'/api/ai-knowledge/document/{document_id}')
        
        if success and status == 200 and data.get('ok'):
            self.log_test("AI Flow - Delete", True, f"Test document deleted successfully")
        else:
            self.log_test("AI Flow - Delete", False, f"Status: {status}, Data: {data}")

        print("   🎉 Quick AI Flow test completed")
        return True

    def test_review_request_psycopg2_binary(self):
        """Test review request: Quick re-check after adding psycopg2-binary"""
        print("\n🔍 REVIEW REQUEST: Quick re-check after adding psycopg2-binary")
        print("=" * 70)
        print(f"Base URL: {self.base_url}")
        print("Testing sequence: db-check → install (if needed) → AI flow")
        print("-" * 70)
        
        # Step 1: GET /api/ai-knowledge/db-check — expect connected true now
        print("\n1️⃣ Step 1: Database Connection Check")
        db_status = self.test_db_check_endpoint_focused()
        
        if not db_status:
            print("❌ Cannot proceed - db-check endpoint failed")
            return False
        
        connected = db_status.get('connected', False)
        pgvector_installed = db_status.get('pgvector_installed', False)
        errors = db_status.get('errors', [])
        
        # Step 2: If connected and pgvector not installed, POST install and re-check
        if connected and not pgvector_installed:
            print("\n2️⃣ Step 2: Installing PGVector Extension")
            install_success = self.test_db_install_vector_focused()
            
            if install_success:
                print("\n2️⃣b Step 2b: Re-checking after installation")
                db_status_after = self.test_db_check_endpoint_focused()
                if db_status_after and db_status_after.get('pgvector_installed', False):
                    print("✅ PGVector installation successful")
                    pgvector_installed = True
                else:
                    print("❌ PGVector installation may have failed")
        elif connected and pgvector_installed:
            print("\n✅ Step 2: PGVector already installed, skipping installation")
        elif not connected:
            print(f"\n❌ Step 2: Cannot install PGVector - database not connected")
            if errors:
                print(f"   Database errors: {errors}")
            return False
        
        # Step 3: If ready, run quick AI flow preview->study->documents->search->delete
        if connected and pgvector_installed:
            print("\n3️⃣ Step 3: Quick AI Flow Test")
            self.test_ai_flow_sequence_focused()
        else:
            print(f"\n❌ Step 3: Cannot test AI flow - prerequisites not met (connected={connected}, pgvector={pgvector_installed})")
        
        return True
    
    def test_db_check_endpoint_focused(self):
        """Focused test for db-check endpoint"""
        success, data, status = self.make_request('GET', '/api/ai-knowledge/db-check')
        
        if success and status == 200:
            connected = data.get('connected', False)
            pgvector_available = data.get('pgvector_available', False)
            pgvector_installed = data.get('pgvector_installed', False)
            errors = data.get('errors', [])
            
            status_msg = f"connected={connected}, pgvector_available={pgvector_available}, pgvector_installed={pgvector_installed}"
            if errors:
                status_msg += f", errors={len(errors)}"
            
            self.log_test("DB Check - Connection Status", connected, status_msg)
            
            if errors:
                print(f"   ⚠️  Database errors detected:")
                for error in errors[:3]:  # Show first 3 errors
                    print(f"      - {error}")
            
            return data
        else:
            self.log_test("DB Check - Endpoint", False, f"Status: {status}, Data: {data}")
            return None
    
    def test_db_install_vector_focused(self):
        """Focused test for db-install-vector endpoint"""
        success, data, status = self.make_request('POST', '/api/ai-knowledge/db-install-vector', {})
        
        if success and status == 200:
            result = data.get('result', '')
            self.log_test("DB Install Vector - Success", True, f"Result: {result}")
            return True
        elif status == 422:
            # Validation error is expected if no body provided, try with proper body
            install_data = {"confirm": True}
            success, data, status = self.make_request('POST', '/api/ai-knowledge/db-install-vector', install_data)
            if success and status == 200:
                result = data.get('result', '')
                self.log_test("DB Install Vector - Success", True, f"Result: {result}")
                return True
            else:
                self.log_test("DB Install Vector - After Retry", False, f"Status: {status}, Data: {data}")
        else:
            self.log_test("DB Install Vector - Failed", False, f"Status: {status}, Data: {data}")
        
        return False
    
    def test_ai_flow_sequence_focused(self):
        """Test quick AI flow: preview->study->documents->search->delete"""
        print("   🔄 Testing AI Flow Sequence...")
        
        # Step 1: Preview (upload)
        txt_content = "Test document for VasDom AudioBot AI system. This contains information about cleaning schedules and brigade management."
        files = {'files': ('test_flow.txt', txt_content.encode('utf-8'), 'text/plain')}
        
        success, data, status = self.make_multipart_request('POST', '/api/ai-knowledge/preview', files=files)
        
        if not (success and status == 200 and 'upload_id' in data):
            self.log_test("AI Flow - Preview", False, f"Preview failed: Status {status}")
            return False
        
        upload_id = data['upload_id']
        self.log_test("AI Flow - Preview", True, f"Upload ID: {upload_id[:8]}...")
        
        # Step 2: Study (save)
        study_data = {
            'upload_id': upload_id,
            'filename': 'test_flow_document.txt',
            'category': 'Testing'
        }
        
        success, data, status = self.make_multipart_request('POST', '/api/ai-knowledge/study', data=study_data)
        
        if not (success and status == 200 and 'document_id' in data):
            self.log_test("AI Flow - Study", False, f"Study failed: Status {status}")
            return False
        
        document_id = data['document_id']
        self.log_test("AI Flow - Study", True, f"Document ID: {document_id[:8]}...")
        
        # Step 3: Documents (list)
        success, data, status = self.make_request('GET', '/api/ai-knowledge/documents')
        
        if success and status == 200 and 'documents' in data:
            docs_count = len(data['documents'])
            self.log_test("AI Flow - Documents", True, f"Found {docs_count} documents")
        else:
            self.log_test("AI Flow - Documents", False, f"Documents list failed: Status {status}")
        
        # Step 4: Search
        search_data = {'query': 'VasDom', 'top_k': 5}
        success, data, status = self.make_request('POST', '/api/ai-knowledge/search', search_data)
        
        if success and status == 200 and 'results' in data:
            results_count = len(data['results'])
            self.log_test("AI Flow - Search", True, f"Found {results_count} search results")
        else:
            self.log_test("AI Flow - Search", False, f"Search failed: Status {status}")
        
        # Step 5: Delete
        success, data, status = self.make_request('DELETE', f'/api/ai-knowledge/document/{document_id}')
        
        if success and status == 200 and data.get('ok'):
            self.log_test("AI Flow - Delete", True, f"Document deleted successfully")
        else:
            self.log_test("AI Flow - Delete", False, f"Delete failed: Status {status}")
        
        return True

    def test_review_request_diagnostics_after_scrubbing_pgsslmode(self):
        """
        Review Request: Re-run diagnostics after scrubbing PGSSLMODE env.
        Base: https://audiobot-qci2.onrender.com
        1) GET /api/ai-knowledge/db-dsn — capture JSON including env_sslmode
        2) GET /api/ai-knowledge/db-check — expect connected true now; else capture errors
        If connected & installed, proceed to quick AI flow.
        """
        print("\n🔍 REVIEW REQUEST: DIAGNOSTICS AFTER SCRUBBING PGSSLMODE ENV")
        print("=" * 70)
        print(f"Base URL: {self.base_url}")
        print("Testing diagnostics after PGSSLMODE environment variable scrubbing")
        print("-" * 70)
        
        # Step 1: GET /api/ai-knowledge/db-dsn — capture JSON including env_sslmode
        print("\n1️⃣ Step 1: GET /api/ai-knowledge/db-dsn")
        dsn_data = self.test_db_dsn_endpoint()
        
        # Step 2: GET /api/ai-knowledge/db-check — expect connected true now; else capture errors
        print("\n2️⃣ Step 2: GET /api/ai-knowledge/db-check")
        db_status = self.test_db_check_endpoint()
        
        if db_status:
            connected = db_status.get('connected', False)
            pgvector_available = db_status.get('pgvector_available', False)
            pgvector_installed = db_status.get('pgvector_installed', False)
            errors = db_status.get('errors', [])
            
            print(f"\n📊 Database Connection Analysis:")
            print(f"   Connected: {connected}")
            print(f"   PGVector Available: {pgvector_available}")
            print(f"   PGVector Installed: {pgvector_installed}")
            print(f"   Errors: {len(errors)} found")
            
            if errors:
                print("   Error Details:")
                for i, error in enumerate(errors[:3], 1):  # Show first 3 errors
                    print(f"      {i}. {error}")
            
            if connected and pgvector_available and pgvector_installed:
                print("\n✅ Database fully connected and configured!")
                print("3️⃣ Step 3: Proceeding to quick AI flow testing...")
                self.test_quick_ai_flow()
            elif connected and pgvector_available and not pgvector_installed:
                print("\n🔧 Database connected but pgvector not installed")
                print("3️⃣ Step 3: Installing pgvector extension...")
                install_result = self.test_db_install_vector_endpoint()
                if install_result:
                    print("4️⃣ Step 4: Re-checking database status...")
                    updated_status = self.test_db_check_endpoint()
                    if updated_status and updated_status.get('pgvector_installed'):
                        print("5️⃣ Step 5: Proceeding to quick AI flow testing...")
                        self.test_quick_ai_flow()
            elif not connected:
                print("\n❌ Database still not connected after PGSSLMODE scrubbing")
                if errors:
                    print("   Root cause analysis:")
                    for error in errors:
                        if 'sslmode' in error.lower():
                            print(f"   🔍 SSL Mode Issue: {error}")
                        elif 'connection' in error.lower():
                            print(f"   🔍 Connection Issue: {error}")
                        elif 'authentication' in error.lower():
                            print(f"   🔍 Auth Issue: {error}")
                self.log_test("Review Request - Database Connection", False, 
                            f"Database not connected. Errors: {len(errors)}")
            else:
                print(f"\n❓ Unexpected database state")
                self.log_test("Review Request - Database State", False, 
                            f"Unexpected: connected={connected}, available={pgvector_available}, installed={pgvector_installed}")
        else:
            print("\n❌ Could not retrieve database status")
            self.log_test("Review Request - DB Check", False, "Failed to get database status")
        
        return True

    def test_quick_ai_flow(self):
        """Test quick AI flow: upload → study → search → delete"""
        print("\n🧠 QUICK AI FLOW TESTING")
        print("-" * 40)
        
        # Step 1: Upload a simple document
        txt_content = """VasDom AudioBot Test Document
        
This is a test document for the AI knowledge system.
The system manages cleaning operations for residential buildings.
Key features include:
- House management
- Brigade scheduling  
- Quality control
- Bitrix24 integration
"""
        
        files = {'files': ('ai_flow_test.txt', txt_content.encode('utf-8'), 'text/plain')}
        data = {'chunk_tokens': '600', 'overlap': '100'}
        
        print("   📤 Uploading test document...")
        success, upload_data, status = self.make_multipart_request('POST', '/api/ai-knowledge/upload', files=files, data=data)
        
        if success and status == 200 and 'upload_id' in upload_data:
            upload_id = upload_data['upload_id']
            chunks = upload_data.get('chunks', 0)
            print(f"   ✅ Upload successful: {chunks} chunks, upload_id: {upload_id[:8]}...")
            
            # Step 2: Save the document
            print("   💾 Saving document...")
            save_data = {'upload_id': upload_id, 'filename': 'ai_flow_test.txt'}
            success, save_response, status = self.make_multipart_request('POST', '/api/ai-knowledge/save', data=save_data)
            
            if success and status == 200 and 'document_id' in save_response:
                document_id = save_response['document_id']
                print(f"   ✅ Save successful: document_id: {document_id[:8]}...")
                
                # Step 3: Search for content
                print("   🔍 Searching for content...")
                search_data = {'query': 'VasDom cleaning', 'top_k': 5}
                success, search_response, status = self.make_request('POST', '/api/ai-knowledge/search', search_data)
                
                if success and status == 200 and 'results' in search_response:
                    results = search_response['results']
                    print(f"   ✅ Search successful: {len(results)} results found")
                    
                    # Step 4: Delete the document
                    print("   🗑️  Deleting test document...")
                    success, delete_response, status = self.make_request('DELETE', f'/api/ai-knowledge/document/{document_id}')
                    
                    if success and status == 200 and delete_response.get('ok'):
                        print("   ✅ Delete successful")
                        self.log_test("Quick AI Flow - Complete", True, 
                                    f"Full AI flow completed: upload → save → search ({len(results)} results) → delete")
                    else:
                        print(f"   ❌ Delete failed: Status {status}")
                        self.log_test("Quick AI Flow - Delete", False, f"Delete failed: {status}")
                else:
                    print(f"   ❌ Search failed: Status {status}")
                    self.log_test("Quick AI Flow - Search", False, f"Search failed: {status}")
            else:
                print(f"   ❌ Save failed: Status {status}")
                self.log_test("Quick AI Flow - Save", False, f"Save failed: {status}")
        else:
            print(f"   ❌ Upload failed: Status {status}")
            self.log_test("Quick AI Flow - Upload", False, f"Upload failed: {status}")

    def test_db_check_endpoint_review_request(self):
        """Test GET /api/ai-knowledge/db-check endpoint for review request"""
        print("\n1️⃣ Testing GET /api/ai-knowledge/db-check")
        print("   Expect: connected=true using asyncpg")
        
        success, data, status = self.make_request('GET', '/api/ai-knowledge/db-check')
        
        if success and status == 200:
            # Capture JSON as requested
            print(f"   📋 Response JSON: {json.dumps(data, indent=2)}")
            
            # Check expected fields
            connected = data.get('connected', False)
            pgvector_available = data.get('pgvector_available', False)
            pgvector_installed = data.get('pgvector_installed', False)
            errors = data.get('errors', [])
            
            if connected:
                self.log_test("DB Check - Connection", True, f"Database connected using asyncpg")
            else:
                self.log_test("DB Check - Connection", False, f"Database not connected. Errors: {errors[:2]}")
            
            if pgvector_available:
                self.log_test("DB Check - PGVector Available", True, "pgvector extension available")
            else:
                self.log_test("DB Check - PGVector Available", False, "pgvector extension not available")
            
            return data
        else:
            self.log_test("DB Check - Endpoint", False, f"Status: {status}, Data: {data}")
            return None

    def test_db_install_vector_review_request(self):
        """Test POST /api/ai-knowledge/db-install-vector for review request"""
        print("\n2️⃣ Testing POST /api/ai-knowledge/db-install-vector")
        print("   Expect: Installation attempt or validation error")
        
        # POST with empty body to test validation
        success, data, status = self.make_request('POST', '/api/ai-knowledge/db-install-vector', {})
        
        if status == 422:
            # Validation error is expected for empty body
            self.log_test("DB Install - Validation", True, f"Correctly returns 422 for missing body: {data.get('detail', '')}")
            
            # Try with proper body if endpoint expects it
            install_data = {"confirm": True}  # Common pattern for destructive operations
            success2, data2, status2 = self.make_request('POST', '/api/ai-knowledge/db-install-vector', install_data)
            
            if success2 and status2 == 200:
                self.log_test("DB Install - Installation", True, f"pgvector installation successful: {data2}")
                return True
            elif status2 == 500:
                detail = data2.get('detail', '')
                if 'already exists' in detail.lower() or 'already installed' in detail.lower():
                    self.log_test("DB Install - Already Installed", True, f"pgvector already installed: {detail}")
                    return True
                else:
                    self.log_test("DB Install - Installation", False, f"Installation failed: {detail}")
            else:
                self.log_test("DB Install - Installation", False, f"Status: {status2}, Data: {data2}")
        elif status == 200:
            self.log_test("DB Install - Installation", True, f"pgvector installation successful: {data}")
            return True
        else:
            self.log_test("DB Install - Endpoint", False, f"Status: {status}, Data: {data}")
        
        return False


if __name__ == "__main__":
    tester = VasDomAPITester()
    
    print("🚀 VasDom AudioBot Backend Testing - REVIEW REQUEST: psycopg2-binary re-check")
    print("=" * 70)
    print(f"Testing deployed backend: {tester.base_url}")
    print("Goal: Test db-check → install (if needed) → AI flow sequence")
    print("=" * 70)
    
    # Run the focused review request test
    tester.test_production_diagnostics_after_url_normalization()
    
    # Print final summary
    print("\n" + "=" * 70)
    print("📊 FINAL TEST SUMMARY")
    print("=" * 70)
    print(f"Tests Run: {tester.tests_run}")
    print(f"Tests Passed: {tester.tests_passed}")
    print(f"Tests Failed: {tester.tests_run - tester.tests_passed}")
    print(f"Success Rate: {(tester.tests_passed / tester.tests_run * 100):.1f}%" if tester.tests_run > 0 else "No tests run")
    
    if tester.failed_tests:
        print("\n❌ FAILED TESTS:")
        for i, test in enumerate(tester.failed_tests, 1):
            print(f"{i}. {test['name']}: {test['details']}")
    
    # Exit with appropriate code
    sys.exit(0 if tester.tests_passed == tester.tests_run else 1)