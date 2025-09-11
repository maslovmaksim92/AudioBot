#!/usr/bin/env python3
"""
Comprehensive Testing for VasDom AudioBot - Cleaning Houses API Endpoints
Tests all NEW cleaning/houses API endpoints mentioned in the review request:
- GET /api/cleaning/houses - получение списка домов с детальной информацией
- GET /api/cleaning/stats - статистика по домам и уборке  
- GET /api/cleaning/schedule/september - график уборки на сентябрь
- POST /api/cleaning/houses - создание нового дома в Bitrix24
"""

import requests
import sys
import json
import time
from datetime import datetime
from typing import Dict, Any, List

class CleaningHousesAPITester:
    def __init__(self, base_url="https://autobot-learning.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        
    def log_test(self, name: str, success: bool, details: str = ""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED {details}")
        else:
            print(f"❌ {name} - FAILED {details}")
    
    def make_request(self, method: str, endpoint: str, data: Dict = None, timeout: int = 30) -> tuple:
        """Make HTTP request and return (success, response_data, status_code)"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=timeout)
            else:
                return False, {}, 0
                
            try:
                response_data = response.json()
            except:
                response_data = {"raw_response": response.text}
                
            return response.status_code < 400, response_data, response.status_code
            
        except requests.exceptions.Timeout:
            return False, {"error": "Request timeout"}, 0
        except requests.exceptions.ConnectionError:
            return False, {"error": "Connection error"}, 0
        except Exception as e:
            return False, {"error": str(e)}, 0

    def test_cleaning_houses_list(self):
        """Test GET /api/cleaning/houses - получение списка домов с детальной информацией"""
        print("\n🏠 Testing Cleaning Houses List API...")
        success, data, status = self.make_request('GET', 'cleaning/houses')
        
        if success and status == 200:
            # Check main structure
            required_fields = ['houses', 'total', 'message']
            has_required = all(field in data for field in required_fields)
            
            houses = data.get('houses', [])
            total = data.get('total', 0)
            
            # Check specific houses mentioned in review request
            expected_addresses = [
                "Тестовая улица д. 123",
                "Аллейная 6 п.1", 
                "Чичерина 14"
            ]
            
            found_addresses = [house.get('address', '') for house in houses]
            has_expected_houses = all(addr in found_addresses for addr in expected_addresses)
            
            # Check house structure - all required fields
            house_fields_valid = True
            if houses:
                required_house_fields = [
                    'deal_id', 'address', 'house_address', 'apartments_count', 
                    'floors_count', 'entrances_count', 'brigade', 'management_company',
                    'status_text', 'status_color', 'tariff', 'region'
                ]
                sample_house = houses[0]
                house_fields_valid = all(field in sample_house for field in required_house_fields)
            
            overall_success = has_required and has_expected_houses and house_fields_valid and total > 0
            self.log_test("Cleaning Houses List", overall_success, 
                         f"Total: {total}, Expected houses found: {has_expected_houses}, Valid structure: {house_fields_valid}")
            return overall_success
        else:
            self.log_test("Cleaning Houses List", False, f"Status: {status}, Error: {data.get('error', 'Unknown')}")
            return False

    def test_cleaning_stats(self):
        """Test GET /api/cleaning/stats - статистика по домам и уборке"""
        print("\n📊 Testing Cleaning Statistics API...")
        success, data, status = self.make_request('GET', 'cleaning/stats')
        
        if success and status == 200:
            # Check expected metrics from review request
            expected_metrics = {
                'total_houses': 450,
                'total_apartments': 43308,
                'total_entrances': 1123,
                'total_floors': 3372
            }
            
            metrics_match = True
            for metric, expected_value in expected_metrics.items():
                actual_value = data.get(metric, 0)
                if actual_value != expected_value:
                    metrics_match = False
                    print(f"   ⚠️ {metric}: expected {expected_value}, got {actual_value}")
            
            # Check regions structure
            has_regions = 'regions' in data
            regions_valid = False
            if has_regions:
                regions = data.get('regions', {})
                expected_regions = ['Центральный', 'Никитинский', 'Жилетово', 'Северный', 'Пригород', 'Окраины']
                regions_valid = all(region in regions for region in expected_regions)
            
            overall_success = metrics_match and has_regions and regions_valid
            self.log_test("Cleaning Statistics", overall_success, 
                         f"Metrics match: {metrics_match}, Regions valid: {regions_valid}")
            return overall_success
        else:
            self.log_test("Cleaning Statistics", False, f"Status: {status}")
            return False

    def test_cleaning_schedule(self):
        """Test GET /api/cleaning/schedule/september - график уборки на сентябрь"""
        print("\n📅 Testing Cleaning Schedule API...")
        success, data, status = self.make_request('GET', 'cleaning/schedule/september')
        
        if success and status == 200:
            required_fields = ['month', 'year', 'schedule', 'total_houses']
            has_required = all(field in data for field in required_fields)
            
            month = data.get('month')
            year = data.get('year')
            schedule = data.get('schedule', {})
            total_houses = data.get('total_houses', 0)
            
            # Check schedule structure
            schedule_valid = True
            if schedule:
                # Check a sample schedule entry
                sample_key = list(schedule.keys())[0] if schedule else None
                if sample_key:
                    sample_entry = schedule[sample_key]
                    required_schedule_fields = ['house_address', 'frequency', 'next_cleaning', 'brigade']
                    schedule_valid = all(field in sample_entry for field in required_schedule_fields)
                    
                    # Check frequency formats mentioned in review
                    frequency = sample_entry.get('frequency', '')
                    has_valid_frequency = any(pattern in frequency for pattern in [
                        'раза в неделю', 'раз в неделю', 'Ежедневно'
                    ])
            
            overall_success = (has_required and month == 'september' and year == 2025 and 
                             schedule_valid and total_houses > 0)
            self.log_test("Cleaning Schedule", overall_success, 
                         f"Month: {month}, Houses: {total_houses}, Schedule valid: {schedule_valid}")
            return overall_success
        else:
            self.log_test("Cleaning Schedule", False, f"Status: {status}")
            return False

    def test_create_house(self):
        """Test POST /api/cleaning/houses - создание нового дома в Bitrix24"""
        print("\n🏗️ Testing Create House API...")
        
        # Test data for creating a new house
        test_house_data = {
            "address": "Тестовая улица д. 999",
            "house_address": "г. Калуга, ул. Тестовая, д. 999",
            "apartments_count": 50,
            "floors_count": 5,
            "entrances_count": 2,
            "brigade": "Бригада Тестовая",
            "management_company": "ООО Тест-УК",
            "tariff": "10,000 руб/мес",
            "region": "Центральный"
        }
        
        success, data, status = self.make_request('POST', 'cleaning/houses', test_house_data)
        
        if success and status == 200:
            required_fields = ['success', 'message', 'house', 'deal_id']
            has_required = all(field in data for field in required_fields)
            
            is_successful = data.get('success', False)
            has_deal_id = 'deal_id' in data and data['deal_id']
            created_house = data.get('house', {})
            
            # Check if created house contains our test data
            house_data_preserved = True
            if created_house:
                for key, value in test_house_data.items():
                    if created_house.get(key) != value:
                        house_data_preserved = False
                        break
            
            overall_success = has_required and is_successful and has_deal_id and house_data_preserved
            self.log_test("Create House", overall_success, 
                         f"Success: {is_successful}, Deal ID: {data.get('deal_id', 'N/A')}, Data preserved: {house_data_preserved}")
            return overall_success
        else:
            self.log_test("Create House", False, f"Status: {status}, Error: {data.get('error', 'Unknown')}")
            return False

    def test_data_consistency(self):
        """Test data consistency across different endpoints"""
        print("\n🔍 Testing Data Consistency Across Endpoints...")
        
        # Get houses list
        houses_success, houses_data, _ = self.make_request('GET', 'cleaning/houses')
        # Get stats
        stats_success, stats_data, _ = self.make_request('GET', 'cleaning/stats')
        
        if houses_success and stats_success:
            houses_count = houses_data.get('total', 0)
            stats_houses = stats_data.get('total_houses', 0)
            
            # Note: houses endpoint shows sample data (6 houses), stats shows total (450)
            # This is expected behavior - houses endpoint shows detailed sample, stats shows totals
            houses_endpoint_shows_sample = houses_count < stats_houses
            
            # Check regions consistency
            regions_consistent = True
            if 'regions' in stats_data:
                stats_regions = set(stats_data['regions'].keys())
                expected_regions = {'Центральный', 'Никитинский', 'Жилетово', 'Северный', 'Пригород', 'Окраины'}
                regions_consistent = stats_regions == expected_regions
            
            overall_success = houses_endpoint_shows_sample and regions_consistent
            self.log_test("Data Consistency", overall_success, 
                         f"Houses sample: {houses_count}, Total houses: {stats_houses}, Regions consistent: {regions_consistent}")
            return overall_success
        else:
            self.log_test("Data Consistency", False, "Could not fetch data from both endpoints")
            return False

    def run_comprehensive_test(self):
        """Run all cleaning houses API tests"""
        print("🚀 Starting VasDom AudioBot - Cleaning Houses API Testing")
        print("🏠 Testing NEW API endpoints for house management")
        print(f"🌐 Testing against: {self.base_url}")
        print("=" * 70)
        
        test_results = []
        
        # Test all cleaning houses endpoints
        print("\n🏠 TESTING CLEANING HOUSES API ENDPOINTS")
        print("-" * 50)
        
        test_results.append(self.test_cleaning_houses_list())
        test_results.append(self.test_cleaning_stats())
        test_results.append(self.test_cleaning_schedule())
        test_results.append(self.test_create_house())
        test_results.append(self.test_data_consistency())
        
        # Summary
        print("\n" + "=" * 70)
        print(f"📊 CLEANING HOUSES API TEST SUMMARY")
        print(f"✅ Passed: {self.tests_passed}/{self.tests_run}")
        print(f"❌ Failed: {self.tests_run - self.tests_passed}/{self.tests_run}")
        
        if self.tests_passed == self.tests_run:
            print("🎉 ALL CLEANING HOUSES API TESTS PASSED!")
            print("🏠 All house management endpoints are working correctly!")
            return 0
        else:
            print("⚠️  Some tests failed. Check the details above.")
            return 1

def main():
    """Main test execution for Cleaning Houses API"""
    print("🏠 VasDom AudioBot - Cleaning Houses API Tester")
    print("🚀 Testing NEW house management endpoints")
    print("📋 Testing endpoints:")
    print("   • GET /api/cleaning/houses - список домов")
    print("   • GET /api/cleaning/stats - статистика домов")
    print("   • GET /api/cleaning/schedule/september - график уборки")
    print("   • POST /api/cleaning/houses - создание дома")
    
    # Use the correct URL from frontend/.env
    tester = CleaningHousesAPITester("https://autobot-learning.preview.emergentagent.com")
    
    try:
        return tester.run_comprehensive_test()
    except KeyboardInterrupt:
        print("\n⏹️  Testing interrupted by user")
        return 1
    except Exception as e:
        print(f"\n💥 Unexpected error during testing: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())