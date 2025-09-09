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
                
            self.log_test("API Root (/api/)", success, 
                         f"Status: {response.status_code}, Response: {response.text[:100]}")
            return success
        except Exception as e:
            self.log_test("API Root (/api/)", False, str(e))
            return False

    def test_health_endpoint(self):
        """Test health check endpoint"""
        try:
            response = requests.get(f"{self.api_url}/health", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                success = (data.get("status") == "healthy" and 
                          "service" in data and
                          "VasDom AudioBot" in data.get("service", ""))
                print(f"   🏥 Health status: {data.get('status')}")
                print(f"   🏥 Service: {data.get('service')}")
                print(f"   🏥 AI mode: {data.get('ai_mode', 'unknown')}")
                
            self.log_test("Health Check (/api/health)", success, 
                         f"Status: {response.status_code}")
            return success
        except Exception as e:
            self.log_test("Health Check (/api/health)", False, str(e))
            return False

    def test_dashboard_html(self):
        """Test dashboard HTML page"""
        try:
            response = requests.get(f"{self.base_url}/dashboard", timeout=10)
            success = response.status_code == 200
            
            if success:
                html_content = response.text
                success = ("VasDom AudioBot" in html_content and 
                          "<!DOCTYPE html>" in html_content and
                          "491" in html_content)
                print(f"   📄 HTML length: {len(html_content)} chars")
                print(f"   📄 Contains VasDom title: {'✅' if 'VasDom AudioBot' in html_content else '❌'}")
                print(f"   📄 Contains 491 houses: {'✅' if '491' in html_content else '❌'}")
                
            self.log_test("Dashboard HTML (/dashboard)", success, 
                         f"Status: {response.status_code}, HTML: {'✅' if success else '❌'}")
            return success
        except Exception as e:
            self.log_test("Dashboard HTML (/dashboard)", False, str(e))
            return False

    def test_dashboard_html_typo(self):
        """Test dashboard HTML page with typo"""
        try:
            response = requests.get(f"{self.base_url}/dashbord", timeout=10)
            success = response.status_code == 200
            
            if success:
                html_content = response.text
                success = ("VasDom AudioBot" in html_content and 
                          "<!DOCTYPE html>" in html_content)
                print(f"   📄 Typo URL works: {'✅' if success else '❌'}")
                
            self.log_test("Dashboard HTML with typo (/dashbord)", success, 
                         f"Status: {response.status_code}")
            return success
        except Exception as e:
            self.log_test("Dashboard HTML with typo (/dashbord)", False, str(e))
            return False

    def test_telegram_status(self):
        """Test Telegram bot status"""
        try:
            response = requests.get(f"{self.api_url}/telegram/status", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                success = "status" in data
                print(f"   📱 Telegram status: {data.get('status')}")
                print(f"   📱 Bot token: {data.get('bot_token')}")
                print(f"   📱 Webhook URL: {data.get('webhook_url', 'not configured')}")
                
            self.log_test("Telegram Status (/api/telegram/status)", success, 
                         f"Status: {response.status_code}")
            return success
        except Exception as e:
            self.log_test("Telegram Status (/api/telegram/status)", False, str(e))
            return False

    def test_telegram_webhook(self):
        """Test Telegram webhook endpoint"""
        try:
            # Test with sample webhook data
            webhook_data = {
                "update_id": 123456789,
                "message": {
                    "message_id": 1,
                    "from": {"id": 123, "first_name": "Test"},
                    "chat": {"id": 123, "type": "private"},
                    "date": 1234567890,
                    "text": "Test message"
                }
            }
            
            response = requests.post(f"{self.api_url}/telegram/webhook", 
                                   json=webhook_data, timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                success = data.get("status") == "received"
                print(f"   📱 Webhook response: {data.get('message', 'No message')}")
                print(f"   📱 Update ID: {data.get('update_id')}")
                
            self.log_test("Telegram Webhook (/api/telegram/webhook)", success, 
                         f"Status: {response.status_code}, No 404: {'✅' if response.status_code != 404 else '❌'}")
            return success
        except Exception as e:
            self.log_test("Telegram Webhook (/api/telegram/webhook)", False, str(e))
            return False

    def test_self_learning_status(self):
        """Test AI self-learning status endpoint"""
        try:
            response = requests.get(f"{self.api_url}/self-learning/status", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                success = "status" in data
                print(f"   🧠 Self-learning status: {data.get('status')}")
                print(f"   🧠 AI interactions: {data.get('ai_interactions', 0)}")
                print(f"   🧠 Database: {data.get('database', 'unknown')}")
                
                emergent_info = data.get('emergent_llm', {})
                print(f"   🧠 Emergent LLM available: {emergent_info.get('package_available', False)}")
                print(f"   🧠 AI mode: {emergent_info.get('mode', 'unknown')}")
                
            self.log_test("Self-Learning Status (/api/self-learning/status)", success, 
                         f"Status: {response.status_code}")
            return success
        except Exception as e:
            self.log_test("Self-Learning Status (/api/self-learning/status)", False, str(e))
            return False

    def test_dashboard_stats(self):
        """Test dashboard statistics endpoint - должен показывать ТОЛЬКО CRM данные (348 домов), НЕ CSV fallback"""
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
                    data_source = data.get('data_source', 'Unknown')
                    print(f"   📊 Houses: {houses_count}, Employees: {stats.get('employees', 0)}")
                    print(f"   📊 Data source: {data_source}")
                    
                    # КРИТИЧЕСКИЙ ТЕСТ: должно быть 348 домов из CRM, НЕ 491 из CSV fallback
                    if houses_count == 348:
                        print(f"   ✅ CORRECT: Shows 348 houses from CRM Bitrix24 (no CSV fallback)")
                        # Проверяем что источник данных указывает на CRM
                        if "CRM" in data_source or "Bitrix24" in data_source:
                            print(f"   ✅ Data source correctly indicates CRM: {data_source}")
                        else:
                            print(f"   ⚠️ Data source unclear: {data_source}")
                    elif houses_count == 491:
                        print(f"   ❌ WRONG: Shows 491 houses - using CSV fallback instead of CRM-only data")
                        success = False
                    else:
                        print(f"   ⚠️ UNEXPECTED: Shows {houses_count} houses (expected 348 from CRM)")
                        success = False
                
            self.log_test("Dashboard CRM-Only Data (348 Houses)", success, 
                         f"Status: {response.status_code}, Houses: {data.get('stats', {}).get('houses', 'N/A')}")
            return success
        except Exception as e:
            self.log_test("Dashboard CRM-Only Data (348 Houses)", False, str(e))
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

    def test_self_learning_system(self):
        """Test AI self-learning system - логи должны сохраняться в PostgreSQL"""
        try:
            # Сначала отправляем сообщение AI для создания лога
            test_message = {
                "text": "Тест системы самообучения VasDom",
                "user_id": "self_learning_test"
            }
            
            ai_response = requests.post(f"{self.api_url}/voice/process", 
                                      json=test_message, timeout=30)
            
            if ai_response.status_code != 200:
                self.log_test("Self-Learning System", False, "AI processing failed")
                return False
            
            # Ждем немного чтобы лог сохранился
            time.sleep(3)
            
            # Проверяем что логи сохраняются
            logs_response = requests.get(f"{self.api_url}/logs", timeout=10)
            success = logs_response.status_code == 200
            
            if success:
                data = logs_response.json()
                success = (data.get("status") == "success" and 
                          "voice_logs" in data and
                          isinstance(data["voice_logs"], list))
                
                if success:
                    voice_logs = data["voice_logs"]
                    logs_count = len(voice_logs)
                    print(f"   🧠 Voice logs in PostgreSQL: {logs_count}")
                    
                    # Проверяем что наш тестовый лог сохранился
                    test_log_found = False
                    for log in voice_logs:
                        if (log.get("user_message") and 
                            "самообучения" in log["user_message"].lower()):
                            test_log_found = True
                            print(f"   ✅ Self-learning test log found in PostgreSQL")
                            print(f"   🧠 Log context: {log.get('context', 'No context')}")
                            break
                    
                    if not test_log_found and logs_count > 0:
                        print(f"   ⚠️ Test log not found, but {logs_count} other logs exist")
                    elif not test_log_found:
                        print(f"   ❌ No logs found - self-learning may not be working")
                        success = False
                    
                    # Проверяем что есть GPT4mini логи
                    gpt4_logs = [log for log in voice_logs if 
                               log.get("context", "").startswith("GPT4mini_")]
                    if gpt4_logs:
                        print(f"   ✅ Found {len(gpt4_logs)} GPT-4 mini learning logs")
                    else:
                        print(f"   ⚠️ No GPT-4 mini specific logs found")
                
            self.log_test("Self-Learning System (PostgreSQL)", success, 
                         f"Logs: {logs_response.status_code}, Count: {len(data.get('voice_logs', []))}")
            return success
        except Exception as e:
            self.log_test("Self-Learning System (PostgreSQL)", False, str(e))
            return False

    def run_all_tests(self):
        """Run all API tests according to review requirements"""
        print("🚀 Starting VasDom AudioBot API Tests - Review Requirements")
        print(f"🔗 Testing API at: {self.api_url}")
        print("📋 Review Requirements:")
        print("   1. Главные endpoints - /api/, /api/dashboard, /api/health")
        print("   2. Dashboard HTML - /dashboard, /dashbord (с опечаткой)")
        print("   3. Telegram - /api/telegram/status, /api/telegram/webhook")
        print("   4. AI система - /api/voice/process и /api/self-learning/status")
        print("   5. Bitrix24 - /api/cleaning/houses")
        print("   ОЖИДАЕМЫЕ РЕЗУЛЬТАТЫ:")
        print("   - Все маршруты работают (статус 200)")
        print("   - Dashboard HTML возвращается корректно")
        print("   - Telegram webhook не выдает 404")
        print("   - AI fallback режим активен")
        print("   - 491 дом в статистике")
        print("=" * 80)
        
        # 1. Главные endpoints
        self.test_api_root()
        self.test_dashboard_stats()
        self.test_health_endpoint()
        
        # 2. Dashboard HTML
        self.test_dashboard_html()
        self.test_dashboard_html_typo()
        
        # 3. Telegram endpoints
        self.test_telegram_status()
        self.test_telegram_webhook()
        
        # 4. AI система
        self.test_voice_ai_processing()
        self.test_self_learning_status()
        
        # 5. Bitrix24
        self.test_bitrix24_connection()
        self.test_cleaning_houses()
        
        # Additional functionality tests
        self.test_meetings_functionality()
        self.test_meetings_list()
        self.test_self_learning_system()
        
        # Print results
        print("=" * 80)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} passed")
        
        if self.failed_tests:
            print("\n❌ Failed Tests:")
            for test in self.failed_tests:
                print(f"   • {test['name']}: {test['details']}")
        
        success_rate = (self.tests_passed / self.tests_run) * 100 if self.tests_run > 0 else 0
        print(f"✅ Success Rate: {success_rate:.1f}%")
        
        # Review requirements summary
        print("\n📋 Review Requirements Status:")
        
        # Check main endpoints
        main_endpoints_tests = [test for test in self.failed_tests if any(endpoint in test["name"] for endpoint in ["API Root", "Dashboard Stats", "Health Check"])]
        main_endpoints_passed = len(main_endpoints_tests) == 0
        
        # Check dashboard HTML
        dashboard_html_tests = [test for test in self.failed_tests if "Dashboard HTML" in test["name"]]
        dashboard_html_passed = len(dashboard_html_tests) == 0
        
        # Check telegram endpoints
        telegram_tests = [test for test in self.failed_tests if "Telegram" in test["name"]]
        telegram_passed = len(telegram_tests) == 0
        
        # Check AI system
        ai_tests = [test for test in self.failed_tests if any(ai_test in test["name"] for ai_test in ["GPT-4 Mini", "Self-Learning Status"])]
        ai_passed = len(ai_tests) == 0
        
        # Check Bitrix24
        bitrix_tests = [test for test in self.failed_tests if "Bitrix24" in test["name"]]
        bitrix_passed = len(bitrix_tests) == 0
        
        print(f"   1. Главные endpoints (/api/, /dashboard, /health): {'✅' if main_endpoints_passed else '❌'}")
        print(f"   2. Dashboard HTML (/dashboard, /dashbord): {'✅' if dashboard_html_passed else '❌'}")
        print(f"   3. Telegram (/telegram/status, /webhook): {'✅' if telegram_passed else '❌'}")
        print(f"   4. AI система (/voice/process, /self-learning/status): {'✅' if ai_passed else '❌'}")
        print(f"   5. Bitrix24 (/cleaning/houses): {'✅' if bitrix_passed else '❌'}")
        
        # Check specific issues mentioned in review
        print("\n🔍 Проблемы для проверки:")
        no_404_errors = not any("404" in test["details"] for test in self.failed_tests if test["details"])
        print(f"   - Исправлены ли все 404 Not Found ошибки? {'✅' if no_404_errors else '❌'}")
        print(f"   - Работает ли dashboard на /dashboard? {'✅' if dashboard_html_passed else '❌'}")
        print(f"   - Telegram webhook /api/telegram/webhook отвечает? {'✅' if telegram_passed else '❌'}")
        
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