#!/usr/bin/env python3
"""
VasDom AudioBot Backend API Testing Suite
Tests all critical API endpoints for the cleaning company management system
"""

import requests
import json
import sys
import time
from datetime import datetime
from io import BytesIO

class VasDomAPITester:
    def __init__(self, base_url="https://smart-facility-ai.preview.emergentagent.com"):
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

    def test_api_root(self):
        """Test API root endpoint"""
        try:
            response = requests.get(f"{self.api_url}/", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                expected_keys = ["message", "version", "status", "features"]
                has_keys = all(key in data for key in expected_keys)
                success = has_keys and "VasDom AudioBot API" in data.get("message", "")
                
            self.log_test("API Root", success, 
                         f"Status: {response.status_code}, Response: {response.text[:100]}")
            return success
        except Exception as e:
            self.log_test("API Root", False, str(e))
            return False

    def test_dashboard_stats(self):
        """Test dashboard statistics endpoint - должен показывать 491 дом"""
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
                    required_stats = ["employees", "houses", "entrances", "apartments", "floors"]
                    success = all(stat in stats for stat in required_stats)
                    
                    houses_count = stats.get('houses', 0)
                    print(f"   📊 Houses: {houses_count}, Employees: {stats.get('employees', 0)}")
                    print(f"   📊 Data source: {data.get('data_source', 'Unknown')}")
                    
                    # КРИТИЧЕСКИЙ ТЕСТ: должно быть 491 дом, не 348
                    if houses_count == 491:
                        print(f"   ✅ CORRECT: Shows 491 houses as expected from CSV data")
                    elif houses_count == 348:
                        print(f"   ❌ WRONG: Shows old 348 houses instead of updated 491")
                        success = False
                    else:
                        print(f"   ⚠️ UNEXPECTED: Shows {houses_count} houses (expected 491)")
                
            self.log_test("Dashboard Stats (491 Houses Check)", success, 
                         f"Status: {response.status_code}, Houses: {data.get('stats', {}).get('houses', 'N/A')}")
            return success
        except Exception as e:
            self.log_test("Dashboard Stats (491 Houses Check)", False, str(e))
            return False

    def test_bitrix24_connection(self):
        """Test Bitrix24 integration"""
        try:
            response = requests.get(f"{self.api_url}/bitrix24/test", timeout=15)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                success = data.get("status") == "success"
                print(f"   🔗 Bitrix24 connection: {data.get('bitrix_info', {})}")
                
            self.log_test("Bitrix24 Connection", success, 
                         f"Status: {response.status_code}, Response: {response.text[:150]}")
            return success
        except Exception as e:
            self.log_test("Bitrix24 Connection", False, str(e))
            return False

    def test_cleaning_houses(self):
        """Test cleaning houses data from Bitrix24 CRM - должен загружать все дома"""
        try:
            response = requests.get(f"{self.api_url}/cleaning/houses", timeout=25)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                success = (data.get("status") == "success" and 
                          "houses" in data and
                          isinstance(data["houses"], list))
                
                if success:
                    houses_count = len(data["houses"])
                    total_from_api = data.get("total", houses_count)
                    print(f"   🏠 Loaded {houses_count} houses from {data.get('source', 'Unknown')}")
                    print(f"   🏠 Total reported: {total_from_api}")
                    
                    if houses_count > 0:
                        sample_house = data["houses"][0]
                        print(f"   🏠 Sample: {sample_house.get('address', 'No address')}")
                        print(f"   🏠 Brigade: {sample_house.get('brigade', 'No brigade')}")
                        print(f"   🏠 Bitrix24 ID: {sample_house.get('bitrix24_deal_id', 'No ID')}")
                        
                        # Проверяем что данные реально из Bitrix24
                        has_bitrix_fields = (sample_house.get('bitrix24_deal_id') and 
                                           sample_house.get('stage') and
                                           sample_house.get('brigade'))
                        
                        if has_bitrix_fields:
                            print("   ✅ Real Bitrix24 CRM data detected")
                        else:
                            print("   ❌ May be using mock data instead of real Bitrix24")
                            success = False
                    
                    # Проверяем что загружается достаточно домов (должно быть много)
                    if houses_count >= 400:
                        print(f"   ✅ Good amount of houses loaded: {houses_count}")
                    elif houses_count >= 50:
                        print(f"   ⚠️ Moderate amount of houses: {houses_count} (may be limited)")
                    else:
                        print(f"   ❌ Too few houses: {houses_count} (likely mock data)")
                        success = False
                
            self.log_test("Bitrix24 CRM Houses Loading", success, 
                         f"Status: {response.status_code}, Houses: {len(data.get('houses', []))}")
            return success
        except Exception as e:
            self.log_test("Bitrix24 CRM Houses Loading", False, str(e))
            return False

    def test_voice_ai_processing(self):
        """Test AI voice processing with GPT-4 mini через Emergent LLM"""
        try:
            test_message = {
                "text": "Сколько домов у нас в работе и какие бригады работают?",
                "user_id": "test_manager"
            }
            
            response = requests.post(f"{self.api_url}/voice/process", 
                                   json=test_message, timeout=30)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                success = ("response" in data and 
                          len(data["response"]) > 10 and
                          "timestamp" in data)
                
                if success:
                    ai_response = data["response"]
                    print(f"   🤖 AI Response: {ai_response[:150]}...")
                    
                    # Проверяем что AI отвечает с контекстом VasDom
                    vasdom_keywords = ["491", "дом", "бригад", "калуг", "vasdom", "клининг", "подъезд"]
                    has_vasdom_context = any(keyword.lower() in ai_response.lower() for keyword in vasdom_keywords)
                    
                    if has_vasdom_context:
                        print("   ✅ AI response contains VasDom context (GPT-4 mini working)")
                    else:
                        print("   ❌ AI response lacks VasDom context - may not be using GPT-4 mini properly")
                        success = False
                    
                    # Проверяем упоминание правильного количества домов
                    if "491" in ai_response:
                        print("   ✅ AI correctly mentions 491 houses")
                    elif "348" in ai_response:
                        print("   ❌ AI mentions old 348 houses instead of 491")
                        success = False
                
            self.log_test("GPT-4 Mini AI Processing", success, 
                         f"Status: {response.status_code}, Context check: {'✅' if success else '❌'}")
            return success
        except Exception as e:
            self.log_test("GPT-4 Mini AI Processing", False, str(e))
            return False

    def test_meetings_functionality(self):
        """Test meetings recording functionality"""
        try:
            # Start recording
            start_response = requests.post(f"{self.api_url}/meetings/start-recording", timeout=10)
            success = start_response.status_code == 200
            
            if success:
                start_data = start_response.json()
                success = (start_data.get("status") == "success" and 
                          "meeting_id" in start_data)
                
                if success:
                    meeting_id = start_data["meeting_id"]
                    print(f"   🎤 Started meeting: {meeting_id}")
                    
                    # Wait a moment then stop recording
                    time.sleep(2)
                    
                    stop_response = requests.post(f"{self.api_url}/meetings/stop-recording?meeting_id={meeting_id}", 
                                                timeout=15)
                    success = stop_response.status_code == 200
                    
                    if success:
                        stop_data = stop_response.json()
                        success = stop_data.get("status") == "success"
                        print(f"   ⏹️ Stopped meeting successfully")
                
            self.log_test("Meetings Functionality", success, 
                         f"Start: {start_response.status_code}, Stop: {stop_response.status_code if 'stop_response' in locals() else 'N/A'}")
            return success
        except Exception as e:
            self.log_test("Meetings Functionality", False, str(e))
            return False

    def test_meetings_list(self):
        """Test meetings list functionality"""
        try:
            response = requests.get(f"{self.api_url}/meetings", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                success = (data.get("status") == "success" and 
                          "meetings" in data)
                
                if success:
                    meetings_count = len(data["meetings"])
                    print(f"   📋 Meetings: {meetings_count}")
                
            self.log_test("Meetings List", success, 
                         f"Status: {response.status_code}, Meetings: {len(data.get('meetings', []))}")
            return success
        except Exception as e:
            self.log_test("Meetings List", False, str(e))
            return False

    def test_system_logs(self):
        """Test system logs endpoint"""
        try:
            response = requests.get(f"{self.api_url}/logs", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                success = (data.get("status") == "success" and 
                          "voice_logs" in data)
                
                if success:
                    voice_logs = len(data["voice_logs"])
                    print(f"   📋 Voice logs: {voice_logs}")
                
            self.log_test("System Logs", success, 
                         f"Status: {response.status_code}")
            return success
        except Exception as e:
            self.log_test("System Logs", False, str(e))
            return False

    def run_all_tests(self):
        """Run all API tests"""
        print("🚀 Starting VasDom AudioBot API Tests")
        print(f"🔗 Testing API at: {self.api_url}")
        print("=" * 60)
        
        # Core API tests
        self.test_api_root()
        self.test_dashboard_stats()
        
        # Integration tests
        self.test_bitrix24_connection()
        self.test_cleaning_houses()
        
        # AI functionality tests
        self.test_voice_ai_processing()
        
        # Feature tests
        self.test_meetings_functionality()
        self.test_meetings_list()
        self.test_system_logs()
        
        # Print results
        print("=" * 60)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} passed")
        
        if self.failed_tests:
            print("\n❌ Failed Tests:")
            for test in self.failed_tests:
                print(f"   • {test['name']}: {test['details']}")
        
        success_rate = (self.tests_passed / self.tests_run) * 100 if self.tests_run > 0 else 0
        print(f"✅ Success Rate: {success_rate:.1f}%")
        
        return self.tests_passed == self.tests_run

def main():
    """Main test execution"""
    tester = VasDomAPITester()
    
    try:
        all_passed = tester.run_all_tests()
        return 0 if all_passed else 1
    except KeyboardInterrupt:
        print("\n⏹️ Tests interrupted by user")
        return 1
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())