#!/usr/bin/env python3
"""
Final Production Testing for VasDom AudioBot - Bitrix24 Integration
Testing all endpoints mentioned in the review request with real Bitrix24 data
"""

import requests
import sys
import json
import time
from datetime import datetime
from typing import Dict, Any

class FinalBitrix24Tester:
    def __init__(self, base_url="https://autobot-learning.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.performance_results = {}
        
    def log_test(self, name: str, success: bool, details: str = ""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED {details}")
        else:
            print(f"❌ {name} - FAILED {details}")
    
    def make_request(self, method: str, endpoint: str, data: Dict = None, timeout: int = 30) -> tuple:
        """Make HTTP request and return (success, response_data, status_code, response_time)"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        start_time = time.time()
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=timeout)
            else:
                return False, {}, 0, 0
            
            response_time = time.time() - start_time
            
            try:
                response_data = response.json()
            except:
                response_data = {"raw_response": response.text}
                
            return response.status_code < 400, response_data, response.status_code, response_time
            
        except requests.exceptions.Timeout:
            response_time = time.time() - start_time
            return False, {"error": "Request timeout"}, 0, response_time
        except requests.exceptions.ConnectionError:
            response_time = time.time() - start_time
            return False, {"error": "Connection error"}, 0, response_time
        except Exception as e:
            response_time = time.time() - start_time
            return False, {"error": str(e)}, 0, response_time

    def test_bitrix24_connection(self):
        """Test GET /api/bitrix24/test - Critical Bitrix24 CRM connection"""
        print("\n🔍 Testing Bitrix24 CRM Connection...")
        success, data, status, response_time = self.make_request('GET', 'bitrix24/test')
        
        self.performance_results['bitrix24_test'] = response_time
        
        if success and status == 200:
            has_status = 'status' in data
            is_connected = data.get('status') == 'connected'
            has_deals = 'deals' in data
            has_employees = 'employees' in data
            has_companies = 'companies' in data
            
            # Check for expected data volumes
            deals_count = data.get('deals', 0)
            employees_count = data.get('employees', 0)
            companies_count = data.get('companies', 0)
            
            is_production_ready = (
                deals_count >= 300 and  # Expected ~348 deals
                employees_count >= 80 and  # Expected 82 employees
                companies_count >= 25  # Expected 29 companies
            )
            
            overall_success = has_status and is_connected and has_deals and has_employees and has_companies
            performance_ok = response_time < 2.0  # Performance requirement
            
            self.log_test("Bitrix24 CRM Connection", overall_success and performance_ok, 
                         f"Status: {data.get('status')}, Deals: {deals_count}, Employees: {employees_count}, Companies: {companies_count}, Time: {response_time:.2f}s")
            return overall_success and performance_ok
        else:
            self.log_test("Bitrix24 CRM Connection", False, f"Status: {status}, Time: {response_time:.2f}s")
            return False

    def test_cleaning_houses_real_data(self):
        """Test GET /api/cleaning/houses - Load 490 real houses from Bitrix24"""
        print("\n🔍 Testing Real Houses Data from Bitrix24...")
        success, data, status, response_time = self.make_request('GET', 'cleaning/houses', timeout=60)
        
        self.performance_results['cleaning_houses'] = response_time
        
        if success and status == 200:
            houses = data.get('houses', [])
            total_in_system = data.get('total_in_system', 0)
            source = data.get('source', '')
            
            # Check for real Bitrix24 data
            is_real_data = 'Bitrix24' in source
            has_expected_total = total_in_system >= 490  # Expected 490 houses
            has_houses_data = len(houses) > 0
            
            # Check house data structure
            valid_structure = True
            if houses and len(houses) > 0:
                sample_house = houses[0]
                required_fields = ['deal_id', 'address', 'house_address', 'apartments_count', 
                                 'floors_count', 'entrances_count', 'brigade', 'management_company', 
                                 'status_text', 'status_color', 'tariff', 'region']
                valid_structure = all(field in sample_house for field in required_fields)
            
            # Check for real Kaluga addresses
            has_real_addresses = False
            if houses:
                addresses = [h.get('address', '') for h in houses[:5]]
                kaluga_streets = ['Пролетарская', 'Чижевского', 'Молодежная', 'Аллейная']
                has_real_addresses = any(street in ' '.join(addresses) for street in kaluga_streets)
            
            performance_ok = response_time < 2.0  # Performance requirement
            
            overall_success = (is_real_data and has_expected_total and has_houses_data and 
                             valid_structure and has_real_addresses)
            
            self.log_test("Real Houses Data (Bitrix24)", overall_success and performance_ok, 
                         f"Houses shown: {len(houses)}, Total in system: {total_in_system}, Real data: {is_real_data}, Valid structure: {valid_structure}, Time: {response_time:.2f}s")
            return overall_success and performance_ok
        else:
            self.log_test("Real Houses Data (Bitrix24)", False, f"Status: {status}, Time: {response_time:.2f}s")
            return False

    def test_cleaning_stats_real(self):
        """Test GET /api/cleaning/stats - Statistics with 29 УК and 7 brigades"""
        print("\n🔍 Testing Real Cleaning Statistics...")
        success, data, status, response_time = self.make_request('GET', 'cleaning/stats')
        
        self.performance_results['cleaning_stats'] = response_time
        
        if success and status == 200:
            # Check expected statistics from review request
            total_houses = data.get('total_houses', 0)
            total_apartments = data.get('total_apartments', 0)
            total_entrances = data.get('total_entrances', 0)
            total_floors = data.get('total_floors', 0)
            management_companies = data.get('management_companies', 0)
            active_brigades = data.get('active_brigades', 0)
            employees = data.get('employees', 0)
            
            # Expected values from review request
            expected_houses = 490
            expected_apartments = 36750  # 75 per house
            expected_entrances = 1470   # 3 per house
            expected_floors = 2450      # 5 per house
            expected_companies = 29
            expected_brigades = 7
            expected_employees = 82
            
            # Check if values are close to expected (allow some variance)
            houses_ok = abs(total_houses - expected_houses) <= 50
            apartments_ok = abs(total_apartments - expected_apartments) <= 5000
            entrances_ok = abs(total_entrances - expected_entrances) <= 200
            floors_ok = abs(total_floors - expected_floors) <= 300
            companies_ok = management_companies == expected_companies
            brigades_ok = active_brigades == expected_brigades
            employees_ok = employees == expected_employees
            
            # Check for Bitrix24 integration info
            has_bitrix_integration = 'bitrix24_integration' in data
            
            performance_ok = response_time < 2.0  # Performance requirement
            
            overall_success = (houses_ok and apartments_ok and entrances_ok and floors_ok and 
                             companies_ok and brigades_ok and employees_ok)
            
            self.log_test("Real Cleaning Statistics", overall_success and performance_ok, 
                         f"Houses: {total_houses}, Apartments: {total_apartments}, Entrances: {total_entrances}, Floors: {total_floors}, УК: {management_companies}, Brigades: {active_brigades}, Time: {response_time:.2f}s")
            return overall_success and performance_ok
        else:
            self.log_test("Real Cleaning Statistics", False, f"Status: {status}, Time: {response_time:.2f}s")
            return False

    def test_create_house_bitrix24(self):
        """Test POST /api/cleaning/houses - Create house in Bitrix24"""
        print("\n🔍 Testing House Creation in Bitrix24...")
        
        test_house = {
            "address": "Тестовая ул. д. 999",
            "house_address": "г. Калуга, ул. Тестовая, д. 999",
            "apartments_count": 120,
            "floors_count": 10,
            "entrances_count": 4,
            "brigade": "Тестовая бригада",
            "management_company": "ООО \"Тест УК\"",
            "tariff": "25000 руб/мес",
            "region": "Центральный"
        }
        
        success, data, status, response_time = self.make_request('POST', 'cleaning/houses', test_house)
        
        self.performance_results['create_house'] = response_time
        
        if success and status == 200:
            has_success = data.get('success', False)
            has_message = 'message' in data
            has_deal_id = 'deal_id' in data
            
            # Check if house was created with correct data
            created_house = data.get('house', {})
            data_preserved = (
                created_house.get('address') == test_house['address'] and
                created_house.get('apartments_count') == test_house['apartments_count']
            ) if created_house else False
            
            performance_ok = response_time < 2.0  # Performance requirement
            
            overall_success = has_success and has_message and has_deal_id and data_preserved
            
            self.log_test("House Creation (Bitrix24)", overall_success and performance_ok, 
                         f"Success: {has_success}, Deal ID: {data.get('deal_id', 'N/A')}, Data preserved: {data_preserved}, Time: {response_time:.2f}s")
            return overall_success and performance_ok
        else:
            self.log_test("House Creation (Bitrix24)", False, f"Status: {status}, Time: {response_time:.2f}s")
            return False

    def test_cache_clear(self):
        """Test POST /api/cleaning/cache/clear - Cache management"""
        print("\n🔍 Testing Cache Management...")
        success, data, status, response_time = self.make_request('POST', 'cleaning/cache/clear')
        
        self.performance_results['cache_clear'] = response_time
        
        if success and status == 200:
            has_success = data.get('success', False)
            has_message = 'message' in data
            has_timestamp = 'timestamp' in data
            
            performance_ok = response_time < 2.0  # Performance requirement
            
            overall_success = has_success and has_message and has_timestamp
            
            self.log_test("Cache Management", overall_success and performance_ok, 
                         f"Success: {has_success}, Message: {data.get('message', '')[:50]}..., Time: {response_time:.2f}s")
            return overall_success and performance_ok
        else:
            self.log_test("Cache Management", False, f"Status: {status}, Time: {response_time:.2f}s")
            return False

    def test_cleaning_schedule_september(self):
        """Test GET /api/cleaning/schedule/september - Schedule from 24 CRM fields"""
        print("\n🔍 Testing September Cleaning Schedule...")
        success, data, status, response_time = self.make_request('GET', 'cleaning/schedule/september')
        
        self.performance_results['schedule_september'] = response_time
        
        if success and status == 200:
            month = data.get('month', '')
            year = data.get('year', 0)
            schedule = data.get('schedule', {})
            total_houses = data.get('total_houses', 0)
            source = data.get('source', '')
            fields_used = data.get('fields_used', 0)
            
            # Check schedule structure
            has_valid_schedule = len(schedule) > 0
            is_september = month == 'september' and year == 2025
            is_bitrix_source = 'Bitrix24' in source
            has_crm_fields = fields_used > 20  # Expected 24 fields
            
            # Check schedule entries structure
            valid_entries = True
            frequency_patterns = []
            if schedule:
                for house_id, house_schedule in list(schedule.items())[:3]:
                    required_fields = ['house_address', 'frequency', 'next_cleaning', 'brigade']
                    if not all(field in house_schedule for field in required_fields):
                        valid_entries = False
                        break
                    frequency_patterns.append(house_schedule.get('frequency', ''))
            
            # Check for expected frequency patterns from review request
            expected_patterns = ['раза в неделю', 'раз в неделю', 'Ежедневно']
            has_expected_patterns = any(pattern in ' '.join(frequency_patterns) for pattern in expected_patterns)
            
            performance_ok = response_time < 2.0  # Performance requirement
            
            overall_success = (has_valid_schedule and is_september and is_bitrix_source and 
                             has_crm_fields and valid_entries and has_expected_patterns)
            
            self.log_test("September Cleaning Schedule", overall_success and performance_ok, 
                         f"Houses: {total_houses}, Source: Bitrix24, Fields: {fields_used}, Valid entries: {valid_entries}, Time: {response_time:.2f}s")
            return overall_success and performance_ok
        else:
            self.log_test("September Cleaning Schedule", False, f"Status: {status}, Time: {response_time:.2f}s")
            return False

    def test_performance_optimization(self):
        """Test 6x optimization and caching performance"""
        print("\n🔍 Testing Performance Optimization (6x)...")
        
        # Test caching by making the same request twice
        print("   First request (cold cache)...")
        success1, data1, status1, time1 = self.make_request('GET', 'cleaning/houses')
        
        time.sleep(0.5)  # Small delay
        
        print("   Second request (warm cache)...")
        success2, data2, status2, time2 = self.make_request('GET', 'cleaning/houses')
        
        if success1 and success2:
            # Second request should be faster (cached)
            cache_improvement = time1 > time2
            both_fast = time1 < 2.0 and time2 < 2.0
            
            # Check for cache indicators in response
            has_cache_info = (
                'performance' in data1 and '6x' in str(data1.get('performance', '')) or
                'cache' in str(data1).lower()
            )
            
            overall_success = cache_improvement and both_fast and has_cache_info
            
            self.log_test("Performance Optimization (6x)", overall_success, 
                         f"Cold: {time1:.2f}s, Warm: {time2:.2f}s, Cache improvement: {cache_improvement}, Cache info: {has_cache_info}")
            return overall_success
        else:
            self.log_test("Performance Optimization (6x)", False, "Failed to test caching")
            return False

    def test_data_integrity(self):
        """Test data integrity - 490 houses, 29 УК, 36,750 apartments, etc."""
        print("\n🔍 Testing Data Integrity...")
        
        # Get statistics
        success_stats, stats_data, _, _ = self.make_request('GET', 'cleaning/stats')
        
        # Get houses sample
        success_houses, houses_data, _, _ = self.make_request('GET', 'cleaning/houses')
        
        if success_stats and success_houses:
            # Check expected totals from review request
            total_houses = stats_data.get('total_houses', 0)
            total_apartments = stats_data.get('total_apartments', 0)
            total_entrances = stats_data.get('total_entrances', 0)
            total_floors = stats_data.get('total_floors', 0)
            management_companies = stats_data.get('management_companies', 0)
            
            # Expected values
            houses_correct = total_houses == 490
            apartments_correct = total_apartments == 36750
            entrances_correct = total_entrances == 1470
            floors_correct = total_floors == 2450
            companies_correct = management_companies == 29
            
            # Check house sample data quality
            houses = houses_data.get('houses', [])
            sample_quality = True
            if houses:
                sample = houses[0]
                # Check for realistic data
                apartments = sample.get('apartments_count', 0)
                floors = sample.get('floors_count', 0)
                entrances = sample.get('entrances_count', 0)
                
                # Realistic ranges
                apartments_realistic = 20 <= apartments <= 200
                floors_realistic = 1 <= floors <= 20
                entrances_realistic = 1 <= entrances <= 10
                
                sample_quality = apartments_realistic and floors_realistic and entrances_realistic
            
            overall_success = (houses_correct and apartments_correct and entrances_correct and 
                             floors_correct and companies_correct and sample_quality)
            
            self.log_test("Data Integrity", overall_success, 
                         f"Houses: {total_houses}/490, Apartments: {total_apartments}/36750, Entrances: {total_entrances}/1470, Floors: {total_floors}/2450, УК: {management_companies}/29")
            return overall_success
        else:
            self.log_test("Data Integrity", False, "Failed to get data for integrity check")
            return False

    def run_final_production_test(self):
        """Run complete final production testing"""
        print("🚀 FINAL PRODUCTION TESTING - VasDom AudioBot Bitrix24 Integration")
        print("🎯 Testing for production readiness with real Bitrix24 CRM data")
        print(f"🌐 Backend URL: {self.base_url}")
        print("=" * 80)
        
        test_results = []
        
        # Critical Bitrix24 Integration Tests
        print("\n🏢 BITRIX24 CRM INTEGRATION TESTS")
        print("-" * 50)
        test_results.append(self.test_bitrix24_connection())
        test_results.append(self.test_cleaning_houses_real_data())
        test_results.append(self.test_cleaning_stats_real())
        test_results.append(self.test_create_house_bitrix24())
        test_results.append(self.test_cache_clear())
        test_results.append(self.test_cleaning_schedule_september())
        
        # Performance and Optimization Tests
        print("\n⚡ PERFORMANCE & OPTIMIZATION TESTS")
        print("-" * 50)
        test_results.append(self.test_performance_optimization())
        test_results.append(self.test_data_integrity())
        
        # Performance Summary
        print("\n📊 PERFORMANCE SUMMARY")
        print("-" * 30)
        for endpoint, response_time in self.performance_results.items():
            status = "✅ FAST" if response_time < 2.0 else "⚠️ SLOW"
            print(f"{endpoint}: {response_time:.2f}s {status}")
        
        avg_response_time = sum(self.performance_results.values()) / len(self.performance_results) if self.performance_results else 0
        performance_grade = "✅ EXCELLENT" if avg_response_time < 1.0 else "✅ GOOD" if avg_response_time < 2.0 else "⚠️ NEEDS IMPROVEMENT"
        print(f"Average response time: {avg_response_time:.2f}s {performance_grade}")
        
        # Final Summary
        print("\n" + "=" * 80)
        print(f"🎯 FINAL PRODUCTION TEST SUMMARY")
        print(f"✅ Passed: {self.tests_passed}/{self.tests_run}")
        print(f"❌ Failed: {self.tests_run - self.tests_passed}/{self.tests_run}")
        
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        
        if success_rate >= 90:
            print("🎉 PRODUCTION READY! All critical systems working perfectly!")
            print("🏢 Bitrix24 integration fully operational")
            print("⚡ Performance meets 6x optimization requirements")
            print("📊 Data integrity confirmed - 490 houses, 29 УК, 7 brigades")
            return 0
        elif success_rate >= 75:
            print("⚠️ MOSTLY READY - Some minor issues detected")
            print("🔧 Review failed tests before production deployment")
            return 1
        else:
            print("❌ NOT READY FOR PRODUCTION")
            print("🚨 Critical issues detected - requires immediate attention")
            return 2

def main():
    """Main test execution"""
    print("🏢 VasDom AudioBot - Final Production Testing")
    print("🎯 Bitrix24 CRM Integration & Performance Verification")
    print("📋 Testing requirements from review request:")
    print("   • Real Bitrix24 connection with 490 houses")
    print("   • 29 управляющих компаний, 7 brigades")
    print("   • Performance < 2 seconds per request")
    print("   • 6x optimization with caching")
    print("   • September cleaning schedule from 24 CRM fields")
    print("   • Data integrity: 36,750 apartments, 1,470 entrances, 2,450 floors")
    
    # Use the correct backend URL from frontend/.env
    tester = FinalBitrix24Tester("https://autobot-learning.preview.emergentagent.com")
    
    try:
        return tester.run_final_production_test()
    except KeyboardInterrupt:
        print("\n⏹️ Testing interrupted by user")
        return 1
    except Exception as e:
        print(f"\n💥 Unexpected error during testing: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())