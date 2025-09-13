#!/usr/bin/env python3
"""
AudioBot Backend API Testing Suite
Tests the specific functionality mentioned in the review request
"""

import requests
import json
import sys
import time
from datetime import datetime

class AudioBotAPITester:
    def __init__(self, base_url="http://localhost:8001"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []

    def log_test(self, name, success, details=""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED")
        else:
            self.failed_tests.append({"name": name, "details": details})
            print(f"❌ {name} - FAILED: {details}")

    def test_health_endpoint(self):
        """Test health check endpoint"""
        try:
            response = requests.get(f"{self.api_url}/health", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                print(f"   🏥 Health response: {data}")
                
            self.log_test("Health Check (/api/health)", success, 
                         f"Status: {response.status_code}")
            return success
        except Exception as e:
            self.log_test("Health Check (/api/health)", False, str(e))
            return False

    def test_dashboard_stats(self):
        """Test dashboard statistics - should show 490 houses, 50,960 apartments, 1,592 entrances"""
        try:
            response = requests.get(f"{self.api_url}/dashboard", timeout=15)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                success = (data.get("status") == "success" and 
                          "stats" in data and
                          isinstance(data["stats"], dict))
                
                if success:
                    stats = data["stats"]
                    houses_count = stats.get('houses', 0)
                    apartments_count = stats.get('apartments', 0)
                    entrances_count = stats.get('entrances', 0)
                    
                    print(f"   📊 Houses: {houses_count}")
                    print(f"   📊 Apartments: {apartments_count}")
                    print(f"   📊 Entrances: {entrances_count}")
                    print(f"   📊 Data source: {data.get('data_source', 'Unknown')}")
                    
                    # Check if numbers match expected values
                    expected_houses = 490
                    expected_apartments = 50960
                    expected_entrances = 1592
                    
                    houses_match = houses_count == expected_houses
                    apartments_match = apartments_count == expected_apartments
                    entrances_match = entrances_count == expected_entrances
                    
                    if houses_match and apartments_match and entrances_match:
                        print(f"   ✅ PERFECT MATCH: All numbers match expected values!")
                    else:
                        print(f"   ⚠️ Numbers don't match exactly:")
                        print(f"      Houses: {houses_count} (expected {expected_houses})")
                        print(f"      Apartments: {apartments_count} (expected {expected_apartments})")
                        print(f"      Entrances: {entrances_count} (expected {expected_entrances})")
                
            self.log_test("Dashboard Stats (490 houses, 50,960 apartments, 1,592 entrances)", success, 
                         f"Status: {response.status_code}, Houses: {stats.get('houses', 'N/A') if success else 'N/A'}")
            return success
        except Exception as e:
            self.log_test("Dashboard Stats", False, str(e))
            return False

    def test_cleaning_houses_fixed(self):
        """Test the main endpoint for improved house cards - /api/cleaning/houses-fixed"""
        try:
            response = requests.get(f"{self.api_url}/cleaning/houses-fixed?limit=10", timeout=25)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                success = (data.get("status") == "success" and 
                          "houses" in data and
                          isinstance(data["houses"], list))
                
                if success:
                    houses = data["houses"]
                    total = data.get("total", len(houses))
                    source = data.get("source", "Unknown")
                    
                    print(f"   🏠 Loaded houses: {len(houses)}")
                    print(f"   🏠 Total available: {total}")
                    print(f"   🏠 Data source: {source}")
                    
                    if len(houses) > 0:
                        sample_house = houses[0]
                        print(f"   🏠 Sample house:")
                        print(f"      - Address: {sample_house.get('address', 'No address')}")
                        print(f"      - Management Company: {sample_house.get('management_company', 'Not set')}")
                        print(f"      - Brigade: {sample_house.get('brigade', 'Not set')}")
                        print(f"      - Apartments: {sample_house.get('apartments_count', 0)}")
                        print(f"      - Entrances: {sample_house.get('entrances_count', 0)}")
                        print(f"      - September Schedule: {bool(sample_house.get('september_schedule'))}")
                        
                        # Check for management companies without errors
                        houses_with_mc = [h for h in houses if h.get('management_company') and h.get('management_company') != 'Не определена']
                        print(f"   🏢 Houses with management companies: {len(houses_with_mc)}/{len(houses)}")
                        
                        # Check for cleaning schedules
                        houses_with_schedule = [h for h in houses if h.get('september_schedule')]
                        print(f"   📅 Houses with cleaning schedules: {len(houses_with_schedule)}/{len(houses)}")
                        
                        if len(houses_with_mc) > 0 and len(houses_with_schedule) > 0:
                            print(f"   ✅ Management companies and cleaning schedules are loading correctly!")
                        else:
                            print(f"   ❌ Issues with management companies or cleaning schedules")
                            success = False
                
            self.log_test("Cleaning Houses Fixed (/api/cleaning/houses-fixed)", success, 
                         f"Status: {response.status_code}, Houses: {len(data.get('houses', [])) if success else 0}")
            return success
        except Exception as e:
            self.log_test("Cleaning Houses Fixed (/api/cleaning/houses-fixed)", False, str(e))
            return False

    def test_bitrix24_integration(self):
        """Test Bitrix24 integration for house data"""
        try:
            response = requests.get(f"{self.api_url}/bitrix24/test", timeout=15)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                success = data.get("status") == "success"
                print(f"   🔗 Bitrix24 connection: {data.get('connection', 'Unknown')}")
                print(f"   🔗 Sample deals: {data.get('sample_deals', 0)}")
                
            self.log_test("Bitrix24 Integration", success, 
                         f"Status: {response.status_code}")
            return success
        except Exception as e:
            self.log_test("Bitrix24 Integration", False, str(e))
            return False

    def test_production_debug(self):
        """Test production debug endpoint to check code version"""
        try:
            response = requests.get(f"{self.api_url}/cleaning/production-debug", timeout=15)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                success = data.get("status") == "success"
                
                if success:
                    code_check = data.get("code_version_check", {})
                    print(f"   🔍 Code version check:")
                    print(f"      - Has optimized loading: {code_check.get('has_optimized_loading', False)}")
                    print(f"      - Has enrichment method: {code_check.get('has_enrichment_method', False)}")
                    print(f"      - Has cache methods: {code_check.get('has_cache_methods', False)}")
                    
                    recommendations = data.get("recommendations", [])
                    if recommendations:
                        print(f"   ⚠️ Recommendations: {recommendations[:2]}")
                
            self.log_test("Production Debug", success, 
                         f"Status: {response.status_code}")
            return success
        except Exception as e:
            self.log_test("Production Debug", False, str(e))
            return False

    def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting AudioBot Backend API Tests...")
        print(f"🔗 Testing against: {self.base_url}")
        print("=" * 60)
        
        # Core API tests
        self.test_health_endpoint()
        self.test_dashboard_stats()
        self.test_cleaning_houses_fixed()
        self.test_bitrix24_integration()
        self.test_production_debug()
        
        # Print summary
        print("\n" + "=" * 60)
        print(f"📊 TEST SUMMARY:")
        print(f"   Tests run: {self.tests_run}")
        print(f"   Tests passed: {self.tests_passed}")
        print(f"   Tests failed: {len(self.failed_tests)}")
        print(f"   Success rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if self.failed_tests:
            print(f"\n❌ FAILED TESTS:")
            for test in self.failed_tests:
                print(f"   - {test['name']}: {test['details']}")
        
        return len(self.failed_tests) == 0

def main():
    # Test with localhost first
    tester = AudioBotAPITester("http://localhost:8001")
    success = tester.run_all_tests()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())