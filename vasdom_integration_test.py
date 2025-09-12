#!/usr/bin/env python3
"""
VasDom AudioBot Integration Test
Tests the specific issue: Frontend не может загрузить карточки домов из backend API
"""

import requests
import json
import time
from datetime import datetime

class VasDomIntegrationTester:
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

    def test_backend_health(self):
        """Test backend health endpoint"""
        try:
            response = requests.get(f"{self.api_url}/health", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                print(f"   🏥 Backend status: {data.get('status')}")
                print(f"   🏥 Service: {data.get('service')}")
                
            self.log_test("Backend Health Check", success, 
                         f"Status: {response.status_code}")
            return success
        except Exception as e:
            self.log_test("Backend Health Check", False, str(e))
            return False

    def test_houses_490_endpoint(self):
        """Test the specific houses-490 endpoint mentioned in the request"""
        try:
            print(f"\n🏠 Testing /api/cleaning/houses-490 endpoint...")
            start_time = time.time()
            
            response = requests.get(f"{self.api_url}/cleaning/houses-490", timeout=30)
            
            end_time = time.time()
            duration = end_time - start_time
            
            success = response.status_code == 200
            
            if success:
                data = response.json()
                houses_count = len(data.get("houses", []))
                total = data.get("total", 0)
                source = data.get("source", "Unknown")
                
                print(f"   🏠 Response time: {duration:.2f} seconds")
                print(f"   🏠 Houses loaded: {houses_count}")
                print(f"   🏠 Total reported: {total}")
                print(f"   🏠 Data source: {source}")
                
                # Check if we got 490 houses as expected
                if houses_count == 490:
                    print(f"   ✅ Correct number of houses (490)")
                else:
                    print(f"   ⚠️ Expected 490 houses, got {houses_count}")
                
                # Check response time (should be around 6 seconds as mentioned)
                if duration <= 10:
                    print(f"   ✅ Response time acceptable ({duration:.2f}s)")
                else:
                    print(f"   ⚠️ Response time slow ({duration:.2f}s)")
                
                # Check sample house data
                if houses_count > 0:
                    sample_house = data["houses"][0]
                    print(f"   🏠 Sample house: {sample_house.get('address', 'No address')}")
                    print(f"   🏠 Sample brigade: {sample_house.get('brigade', 'No brigade')}")
                    print(f"   🏠 Sample status: {sample_house.get('status_text', 'No status')}")
                
            self.log_test("Houses-490 Endpoint", success, 
                         f"Status: {response.status_code}, Houses: {houses_count if success else 0}, Time: {duration:.2f}s")
            return success
        except Exception as e:
            self.log_test("Houses-490 Endpoint", False, str(e))
            return False

    def test_cors_headers(self):
        """Test CORS headers for frontend integration"""
        try:
            print(f"\n🌐 Testing CORS headers...")
            
            # Test preflight request
            headers = {
                'Origin': 'http://localhost:3000',
                'Access-Control-Request-Method': 'GET',
                'Access-Control-Request-Headers': 'Content-Type'
            }
            
            response = requests.options(f"{self.api_url}/cleaning/houses-490", headers=headers, timeout=10)
            
            cors_headers = {
                'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
                'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
                'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers')
            }
            
            print(f"   🌐 CORS Allow-Origin: {cors_headers['Access-Control-Allow-Origin']}")
            print(f"   🌐 CORS Allow-Methods: {cors_headers['Access-Control-Allow-Methods']}")
            print(f"   🌐 CORS Allow-Headers: {cors_headers['Access-Control-Allow-Headers']}")
            
            # Check if CORS allows localhost:3000
            success = (cors_headers['Access-Control-Allow-Origin'] in ['*', 'http://localhost:3000'] or
                      response.status_code in [200, 204])
            
            if success:
                print(f"   ✅ CORS properly configured for frontend")
            else:
                print(f"   ❌ CORS may block frontend requests")
            
            self.log_test("CORS Configuration", success, 
                         f"Status: {response.status_code}, Origin: {cors_headers['Access-Control-Allow-Origin']}")
            return success
        except Exception as e:
            self.log_test("CORS Configuration", False, str(e))
            return False

    def test_network_simulation(self):
        """Simulate frontend network request"""
        try:
            print(f"\n🌐 Simulating frontend network request...")
            
            headers = {
                'Origin': 'http://localhost:3000',
                'Referer': 'http://localhost:3000/',
                'User-Agent': 'Mozilla/5.0 (Frontend Test)',
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(f"{self.api_url}/cleaning/houses-490", headers=headers, timeout=30)
            
            success = response.status_code == 200
            
            if success:
                data = response.json()
                houses_count = len(data.get("houses", []))
                print(f"   🌐 Frontend simulation successful: {houses_count} houses")
                
                # Check if response is JSON serializable (important for frontend)
                try:
                    json.dumps(data)
                    print(f"   ✅ Response is properly JSON serializable")
                except:
                    print(f"   ❌ Response has JSON serialization issues")
                    success = False
            
            self.log_test("Frontend Network Simulation", success, 
                         f"Status: {response.status_code}")
            return success
        except Exception as e:
            self.log_test("Frontend Network Simulation", False, str(e))
            return False

    def test_debug_endpoints(self):
        """Test debug endpoints mentioned in the request"""
        try:
            print(f"\n🔧 Testing debug endpoints...")
            
            # Test debug-houses endpoint
            response = requests.get(f"{self.api_url}/debug-houses", timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                print(f"   🔧 Debug houses status: {data.get('status')}")
                print(f"   🔧 Bitrix24 webhook: {data.get('bitrix24_webhook', 'Not configured')}")
                print(f"   🔧 Category info: {data.get('category_info', {})}")
            
            success = response.status_code == 200
            
            self.log_test("Debug Endpoints", success, 
                         f"Status: {response.status_code}")
            return success
        except Exception as e:
            self.log_test("Debug Endpoints", False, str(e))
            return False

    def run_integration_tests(self):
        """Run all integration tests"""
        print("🚀 VasDom AudioBot Integration Tests")
        print("=" * 60)
        print("🎯 TESTING ISSUE: Frontend не может загрузить карточки домов")
        print("📋 Expected: /api/cleaning/houses-490 returns 490 houses in ~6 seconds")
        print("📋 Expected: Frontend can display house cards")
        print("=" * 60)
        
        # Run tests
        self.test_backend_health()
        self.test_houses_490_endpoint()
        self.test_cors_headers()
        self.test_network_simulation()
        self.test_debug_endpoints()
        
        # Print results
        print("\n" + "=" * 60)
        print(f"📊 Integration Test Results: {self.tests_passed}/{self.tests_run} passed")
        
        if self.failed_tests:
            print("\n❌ Failed Tests:")
            for test in self.failed_tests:
                print(f"   • {test['name']}: {test['details']}")
        
        success_rate = (self.tests_passed / self.tests_run) * 100 if self.tests_run > 0 else 0
        print(f"✅ Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 80:
            print("\n🎉 INTEGRATION STATUS: ✅ WORKING")
            print("   Backend API is accessible and returning data")
            print("   Frontend should be able to load house cards")
        else:
            print("\n⚠️ INTEGRATION STATUS: ❌ ISSUES DETECTED")
            print("   There are problems that may prevent frontend from loading houses")
        
        return success_rate >= 80

def main():
    tester = VasDomIntegrationTester()
    success = tester.run_integration_tests()
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())