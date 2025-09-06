#!/usr/bin/env python3
"""
VasDom AI System - Final Comprehensive Testing
Testing all critical endpoints for production readiness as per review request
"""

import requests
import sys
import json
from datetime import datetime
from typing import Dict, Any, List

class VasDomComprehensiveTester:
    def __init__(self, base_url="https://telegram-bitrix.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []
        self.test_results = {}

    def log_result(self, test_name: str, success: bool, response_data: Any = None, error: str = None):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {test_name} - PASSED")
        else:
            self.failed_tests.append({"test": test_name, "error": error})
            print(f"❌ {test_name} - FAILED: {error}")
        
        self.test_results[test_name] = {
            "success": success,
            "response": response_data,
            "error": error
        }

    def run_test(self, name: str, method: str, endpoint: str, expected_status: int = 200, 
                 data: Dict = None, timeout: int = 30) -> tuple:
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}" if not endpoint.startswith('http') else endpoint
        headers = {'Content-Type': 'application/json'}

        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=timeout)

            success = response.status_code == expected_status
            response_data = None
            
            try:
                response_data = response.json()
            except:
                response_data = response.text

            if success:
                self.log_result(name, True, response_data)
                return True, response_data
            else:
                error_msg = f"Expected {expected_status}, got {response.status_code}"
                if response_data:
                    error_msg += f" - {str(response_data)[:200]}"
                self.log_result(name, False, response_data, error_msg)
                return False, response_data

        except requests.exceptions.Timeout:
            error_msg = f"Request timeout after {timeout}s"
            self.log_result(name, False, None, error_msg)
            return False, {}
        except Exception as e:
            error_msg = f"Request error: {str(e)}"
            self.log_result(name, False, None, error_msg)
            return False, {}

    def test_critical_backend_apis(self):
        """Test all critical backend APIs as specified in review request"""
        print("\n" + "="*80)
        print("🚀 TESTING CRITICAL BACKEND APIs - PRODUCTION READINESS")
        print("="*80)

        # 1. GET /api/ - главная информация
        success, data = self.run_test(
            "GET /api/ - Main Information", 
            "GET", 
            ""
        )
        if success and data:
            print(f"   Service: {data.get('service', 'Unknown')}")
            print(f"   Version: {data.get('version', 'Unknown')}")
            print(f"   Telegram Bot: {data.get('telegram_bot', 'Unknown')}")

        # 2. GET /api/dashboard - дашборд данные
        success, data = self.run_test(
            "GET /api/dashboard - Dashboard Data",
            "GET",
            "dashboard"
        )
        if success and data:
            metrics = data.get('metrics', {})
            print(f"   Total Employees: {metrics.get('total_employees', 0)}")
            print(f"   Total Houses: {metrics.get('total_houses', 0)}")
            print(f"   Recent Activities: {len(data.get('recent_activities', []))}")
            print(f"   AI Insights: {len(data.get('ai_insights', []))}")

        # 3. GET /api/system/health - статус всех сервисов
        success, data = self.run_test(
            "GET /api/system/health - System Health",
            "GET",
            "system/health"
        )
        if success and data:
            print(f"   Status: {data.get('status', 'Unknown')}")
            services = data.get('services', {})
            for service, status in services.items():
                print(f"   {service}: {status}")

        # 4. GET /api/bitrix24/test - тест Bitrix24 (должен вернуть "Максим Маслов")
        success, data = self.run_test(
            "GET /api/bitrix24/test - Bitrix24 Test (Максим Маслов)",
            "GET",
            "bitrix24/test"
        )
        if success and data:
            print(f"   Integration Status: {data.get('integration_status', 'Unknown')}")
            user_name = data.get('user_name', 'Unknown')
            print(f"   User Found: {user_name}")
            if user_name == 'Максим Маслов':
                print("   ✅ CORRECT USER FOUND!")
            elif 'Максим' in user_name:
                print("   ✅ CORRECT USER FOUND (partial match)!")
            else:
                print("   ⚠️ Different user found")

        # 5. GET /api/bitrix24/deals - получить сделки (должно быть 50 сделок)
        success, data = self.run_test(
            "GET /api/bitrix24/deals - Get Deals (50 expected)",
            "GET",
            "bitrix24/deals"
        )
        if success and data:
            deal_count = data.get('count', 0)
            print(f"   Deals Count: {deal_count} (Expected: 50)")
            print(f"   Data Source: {data.get('data_source', 'Unknown')}")
            if deal_count >= 45:  # Allow some tolerance
                print("   ✅ SUFFICIENT DEALS FOUND!")
            else:
                print("   ⚠️ Less deals than expected")

        # 6. GET /api/bitrix24/cleaning-houses - дома для уборки из воронки "Уборка подъездов"
        success, data = self.run_test(
            "GET /api/bitrix24/cleaning-houses - Cleaning Houses Pipeline",
            "GET",
            "bitrix24/cleaning-houses"
        )
        if success and data:
            houses_count = data.get('count', 0)
            print(f"   Cleaning Houses: {houses_count}")

        # 7. POST /api/ai/chat - AI чат (тест: "Покажи статистику по сделкам VasDom")
        test_message = "Покажи статистику по сделкам VasDom"
        success, data = self.run_test(
            "POST /api/ai/chat - AI Chat (VasDom Statistics)",
            "POST",
            "ai/chat",
            data={
                "message": test_message,
                "session_id": "production_test",
                "user_id": "test_user"
            },
            timeout=45  # AI responses can be slow
        )
        if success and data:
            response_text = data.get('response', '')
            print(f"   AI Response Length: {len(response_text)} chars")
            if len(response_text) > 50:
                print("   ✅ AI PROVIDED DETAILED RESPONSE")
                # Check if response contains VasDom context
                if any(word in response_text.lower() for word in ['васдом', 'сделк', 'статистик']):
                    print("   ✅ AI RESPONSE CONTAINS VASDOM CONTEXT")
            else:
                print("   ⚠️ AI response seems short")

        # 8. GET /api/telegram/set-webhook - установка webhook
        success, data = self.run_test(
            "GET /api/telegram/set-webhook - Webhook Setup",
            "GET",
            "telegram/set-webhook"
        )
        if success and data:
            print(f"   Status: {data.get('status', 'Unknown')}")
            print(f"   Bot: {data.get('bot', 'Unknown')}")
            if data.get('status') == '✅ SUCCESS!':
                print("   ✅ WEBHOOK SETUP SUCCESSFUL!")

        # 9. GET /api/employees - список сотрудников
        success, data = self.run_test(
            "GET /api/employees - Employee List",
            "GET",
            "employees"
        )
        if success and isinstance(data, list):
            print(f"   Employees Count: {len(data)}")

        # 10. GET /api/company/info - информация о компании
        success, data = self.run_test(
            "GET /api/company/info - Company Information",
            "GET",
            "company/info"
        )
        if success and data:
            company = data.get('company', {})
            print(f"   Company Name: {company.get('name', 'Unknown')}")
            print(f"   Cities: {company.get('cities', [])}")

    def test_business_functions(self):
        """Test business functions as specified in review request"""
        print("\n" + "="*80)
        print("💼 TESTING BUSINESS FUNCTIONS")
        print("="*80)

        # Test AI analysis of Bitrix24 deals
        success, data = self.run_test(
            "AI Analysis of Bitrix24 Deals",
            "POST",
            "ai/chat",
            data={
                "message": "Проанализируй наши 50 сделок из Bitrix24 и дай рекомендации",
                "session_id": "business_test",
                "user_id": "business_user"
            },
            timeout=45
        )
        if success and data:
            response = data.get('response', '')
            if any(word in response.lower() for word in ['сделк', 'bitrix', 'рекомендац', 'анализ']):
                print("   ✅ AI CAN ANALYZE BITRIX24 DEALS")

        # Test cleaning pipeline recognition
        success, data = self.run_test(
            "Cleaning Pipeline Recognition (ID: 34)",
            "GET",
            "bitrix24/pipeline"
        )
        if success and data:
            pipeline = data.get('pipeline', {})
            if pipeline and 'уборк' in pipeline.get('NAME', '').lower():
                print("   ✅ CLEANING PIPELINE RECOGNIZED")
                pipeline_id = pipeline.get('ID')
                if pipeline_id:
                    print(f"   Pipeline ID: {pipeline_id}")

        # Test financial analytics
        success, data = self.run_test(
            "Financial Analytics Calculation",
            "GET",
            "financial/monthly-data?months=3"
        )
        if success and data:
            if data.get('success') and 'summary' in data:
                summary = data['summary']
                print(f"   Revenue Achievement: {summary.get('revenue_achievement', 0)}%")
                print("   ✅ FINANCIAL ANALYTICS WORKING")

        # Test dashboard KPIs
        success, data = self.run_test(
            "Dashboard Real KPIs",
            "GET",
            "dashboard"
        )
        if success and data:
            metrics = data.get('metrics', {})
            if metrics.get('total_employees', 0) > 0 or metrics.get('total_houses', 0) > 0:
                print("   ✅ DASHBOARD SHOWS REAL KPIs")

    def test_integrations(self):
        """Test all integrations"""
        print("\n" + "="*80)
        print("🔗 TESTING INTEGRATIONS")
        print("="*80)

        # Test Telegram Bot integration
        success, data = self.run_test(
            "Telegram Bot Integration (@aitest123432_bot)",
            "GET",
            "telegram/bot-info"
        )
        if success and data:
            bot_username = data.get('bot_username', '')
            if '@aitest123432_bot' in bot_username:
                print("   ✅ TELEGRAM BOT CONFIGURED CORRECTLY")

        # Test Bitrix24 real data
        success, data = self.run_test(
            "Bitrix24 Real Data Integration",
            "GET",
            "bitrix24/test"
        )
        if success and data:
            integration_status = data.get('integration_status', '')
            if '✅ РЕАЛЬНЫЕ ДАННЫЕ' in integration_status:
                print("   ✅ BITRIX24 REAL DATA INTEGRATION")
            elif '⚠️ ДЕМО-ДАННЫЕ' in integration_status:
                print("   ⚠️ BITRIX24 DEMO DATA (fallback)")

        # Test AI Assistant responsiveness
        success, data = self.run_test(
            "AI Assistant Responsiveness",
            "POST",
            "ai/chat",
            data={
                "message": "Привет! Как дела?",
                "session_id": "integration_test"
            },
            timeout=30
        )
        if success and data:
            response = data.get('response', '')
            if len(response) > 10:
                print("   ✅ AI ASSISTANT RESPONSIVE")

    def run_comprehensive_test(self):
        """Run all comprehensive tests"""
        print("🚀 STARTING COMPREHENSIVE VASDOM AI SYSTEM TEST")
        print(f"Testing against: {self.base_url}")
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Run all test suites
        self.test_critical_backend_apis()
        self.test_business_functions()
        self.test_integrations()

        # Print final results
        self.print_final_results()

    def print_final_results(self):
        """Print comprehensive test results"""
        print("\n" + "="*80)
        print("📊 FINAL COMPREHENSIVE TEST RESULTS - VASDOM AI SYSTEM")
        print("="*80)
        
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        
        print(f"📈 Overall Success Rate: {success_rate:.1f}% ({self.tests_passed}/{self.tests_run})")
        
        if success_rate >= 95:
            print("🎉 EXCELLENT! System ready for production")
            production_ready = True
        elif success_rate >= 80:
            print("✅ GOOD! Minor issues to address")
            production_ready = False
        elif success_rate >= 60:
            print("⚠️ MODERATE! Several issues need fixing")
            production_ready = False
        else:
            print("❌ CRITICAL! Major issues require immediate attention")
            production_ready = False

        # Print failed tests
        if self.failed_tests:
            print(f"\n❌ FAILED TESTS ({len(self.failed_tests)}):")
            for i, failed in enumerate(self.failed_tests, 1):
                print(f"   {i}. {failed['test']}")
                print(f"      Error: {failed['error']}")

        # Critical system checks
        print(f"\n🔍 CRITICAL SYSTEM CHECKS:")
        
        # Check Bitrix24 integration
        bitrix_test = self.test_results.get("GET /api/bitrix24/test - Bitrix24 Test (Максим Маслов)", {})
        if bitrix_test.get("success"):
            response = bitrix_test.get("response", {})
            user_name = response.get("user_name", "")
            if "Максим" in user_name:
                print("   ✅ Bitrix24: Real integration with Максим Маслов")
            else:
                print("   ⚠️ Bitrix24: Working but different user")
        else:
            print("   ❌ Bitrix24: Integration failed")

        # Check deals count
        deals_test = self.test_results.get("GET /api/bitrix24/deals - Get Deals (50 expected)", {})
        if deals_test.get("success"):
            response = deals_test.get("response", {})
            deal_count = response.get("count", 0)
            if deal_count >= 45:
                print(f"   ✅ Deals: {deal_count} deals found (target: 50)")
            else:
                print(f"   ⚠️ Deals: Only {deal_count} deals found (target: 50)")
        else:
            print("   ❌ Deals: Failed to retrieve deals")

        # Check AI integration
        ai_test = self.test_results.get("POST /api/ai/chat - AI Chat (VasDom Statistics)", {})
        if ai_test.get("success"):
            print("   ✅ AI Assistant: Working and responsive")
        else:
            print("   ❌ AI Assistant: Not responding properly")

        # Check Telegram
        telegram_test = self.test_results.get("GET /api/telegram/set-webhook - Webhook Setup", {})
        if telegram_test.get("success"):
            response = telegram_test.get("response", {})
            if response.get("status") == "✅ SUCCESS!":
                print("   ✅ Telegram Bot: Webhook configured successfully")
            else:
                print("   ⚠️ Telegram Bot: Partial configuration")
        else:
            print("   ❌ Telegram Bot: Webhook setup failed")

        print(f"\n⏰ Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Final verdict
        print(f"\n🎯 PRODUCTION READINESS: {'✅ READY' if production_ready else '❌ NOT READY'}")
        
        return success_rate >= 95

def main():
    """Main test execution"""
    tester = VasDomComprehensiveTester()
    
    try:
        success = tester.run_comprehensive_test()
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())