#!/usr/bin/env python3
"""
VasDom AudioBot Dashboard API Testing
Comprehensive testing based on the review request in Russian

Testing endpoints:
1. Dashboard endpoints: /api/dashboard, /api/health, /api/cleaning/houses, /api/employees/stats
2. AI functionality: /api/voice/process, /api/voice/feedback, /api/learning/stats, /api/learning/export, /api/learning/train
3. Additional APIs: /api/telegram/status, /api/bitrix24/test

Backend URL: https://audiobot-qci2.onrender.com
"""

import requests
import sys
import json
import time
from datetime import datetime
from typing import Dict, Any, Tuple

class VasDomAudioBotDashboardTester:
    def __init__(self, base_url="https://autobot-learning.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_log_id = None  # Store log_id for feedback testing
        self.session_id = f"test_session_{int(time.time())}"
        self.test_results = []
        
    def log_test(self, name: str, success: bool, details: str = "", critical: bool = False):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED {details}")
            self.test_results.append({"name": name, "status": "PASSED", "details": details, "critical": critical})
        else:
            print(f"❌ {name} - FAILED {details}")
            self.test_results.append({"name": name, "status": "FAILED", "details": details, "critical": critical})
    
    def make_request(self, method: str, endpoint: str, data: Dict = None, timeout: int = 30) -> Tuple[bool, Dict, int]:
        """Make HTTP request and return (success, response_data, status_code)"""
        url = f"{self.api_url}/{endpoint}" if not endpoint.startswith('http') else endpoint
        headers = {'Content-Type': 'application/json'}
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=timeout)
            else:
                return False, {"error": "Unsupported method"}, 0
                
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

    # ========== ОСНОВНЫЕ ENDPOINTS ДАШБОРДА ==========
    
    def test_dashboard_stats(self):
        """Test GET /api/dashboard - статистика дашборда"""
        print("\n🔍 Testing Dashboard Statistics...")
        success, data, status = self.make_request('GET', 'dashboard')
        
        if success and status == 200:
            # Проверяем ключевые метрики из review request
            expected_metrics = ['employees', 'houses', 'entrances', 'apartments']
            has_metrics = all(metric in data for metric in expected_metrics)
            
            # Проверяем конкретные значения из review request
            employees = data.get('employees', 0)
            houses = data.get('houses', 0)
            entrances = data.get('entrances', 0)
            
            # Ожидаемые значения: 82 сотрудника, 450 домов, 1123 подъездов
            metrics_correct = (
                employees == 82 and 
                houses == 450 and 
                entrances == 1123
            )
            
            overall_success = has_metrics and metrics_correct
            self.log_test("Dashboard Statistics", overall_success, 
                         f"Employees: {employees}/82, Houses: {houses}/450, Entrances: {entrances}/1123", 
                         critical=True)
            return overall_success
        else:
            self.log_test("Dashboard Statistics", False, f"Status: {status}, Error: {data.get('error', 'Unknown')}", critical=True)
            return False

    def test_health_check(self):
        """Test GET /api/health - проверка здоровья системы"""
        print("\n🔍 Testing System Health Check...")
        success, data, status = self.make_request('GET', 'health')
        
        if success and status == 200:
            has_status = 'status' in data and data['status'] == 'healthy'
            has_services = 'services' in data
            has_learning_data = 'learning_data' in data
            
            services = data.get('services', {})
            learning_data = data.get('learning_data', {})
            
            # Проверяем ключевые сервисы
            emergent_llm = services.get('emergent_llm', False)
            embeddings = services.get('embeddings', False)
            storage = services.get('storage', False)
            
            overall_success = has_status and has_services and has_learning_data
            self.log_test("System Health Check", overall_success, 
                         f"Status: {data.get('status')}, LLM: {emergent_llm}, Embeddings: {embeddings}, Storage: {storage}", 
                         critical=True)
            return overall_success
        else:
            self.log_test("System Health Check", False, f"Status: {status}", critical=True)
            return False

    def test_cleaning_houses(self):
        """Test GET /api/cleaning/houses - информация о домах по районам"""
        print("\n🔍 Testing Cleaning Houses by Districts...")
        success, data, status = self.make_request('GET', 'cleaning/houses')
        
        if success and status == 200:
            has_total = 'total' in data
            has_regions = 'regions' in data
            
            total_houses = data.get('total', 0)
            regions = data.get('regions', {})
            
            # Проверяем что есть данные по районам Калуги
            expected_regions = ['Центральный', 'Никитинский', 'Жилетово', 'Северный', 'Пригород', 'Окраины']
            has_expected_regions = all(region in regions for region in expected_regions)
            
            # Проверяем общее количество домов (450)
            total_correct = total_houses == 450
            
            overall_success = has_total and has_regions and has_expected_regions and total_correct
            self.log_test("Cleaning Houses by Districts", overall_success, 
                         f"Total: {total_houses}/450, Regions: {len(regions)}/6, Expected regions: {has_expected_regions}", 
                         critical=True)
            return overall_success
        else:
            self.log_test("Cleaning Houses by Districts", False, f"Status: {status}", critical=True)
            return False

    def test_employees_stats(self):
        """Test GET /api/employees/stats - статистика по сотрудникам"""
        print("\n🔍 Testing Employee Statistics...")
        success, data, status = self.make_request('GET', 'employees/stats')
        
        if success and status == 200:
            has_total = 'total' in data
            has_brigades = 'brigades' in data
            has_by_region = 'by_region' in data
            has_roles = 'roles' in data
            
            total_employees = data.get('total', 0)
            brigades = data.get('brigades', 0)
            by_region = data.get('by_region', {})
            roles = data.get('roles', {})
            
            # Проверяем ожидаемые значения: 82 сотрудника, 6 бригад
            total_correct = total_employees == 82
            brigades_correct = brigades == 6
            
            # Проверяем распределение по ролям
            expected_roles = ['Уборщики', 'Бригадиры', 'Контролёры', 'Администраторы']
            has_expected_roles = all(role in roles for role in expected_roles)
            
            overall_success = has_total and has_brigades and has_by_region and has_roles and total_correct and brigades_correct
            self.log_test("Employee Statistics", overall_success, 
                         f"Total: {total_employees}/82, Brigades: {brigades}/6, Roles: {has_expected_roles}", 
                         critical=True)
            return overall_success
        else:
            self.log_test("Employee Statistics", False, f"Status: {status}", critical=True)
            return False

    # ========== AI ФУНКЦИОНАЛ ==========
    
    def test_voice_process(self):
        """Test POST /api/voice/process - обработка голосовых сообщений с самообучением"""
        print("\n🔍 Testing Voice Processing with Self-Learning...")
        
        # Используем реалистичное сообщение на русском языке для клининговой компании
        test_message = "Как часто нужно убирать подъезды в многоквартирных домах? Какие есть рекомендации по графику уборки?"
        test_data = {
            "message": test_message,
            "session_id": self.session_id
        }
        
        success, data, status = self.make_request('POST', 'voice/process', test_data, timeout=60)
        
        if success and status == 200:
            required_fields = ['response', 'log_id', 'session_id', 'model_used', 'response_time']
            has_required = all(field in data for field in required_fields)
            
            # Store log_id for feedback testing
            if 'log_id' in data:
                self.test_log_id = data['log_id']
            
            response_text = data.get('response', '')
            response_length = len(response_text)
            
            # Проверяем что ответ на русском языке и содержательный
            is_meaningful_response = response_length > 50
            is_russian_response = any(char in response_text for char in 'абвгдеёжзийклмнопрстуфхцчшщъыьэюя')
            
            # Проверяем метрики самообучения
            similar_found = data.get('similar_found', 0)
            learning_improved = data.get('learning_improved', False)
            model_used = data.get('model_used', '')
            
            overall_success = has_required and is_meaningful_response and is_russian_response
            self.log_test("Voice Processing with Self-Learning", overall_success, 
                         f"Response: {response_length} chars, Russian: {is_russian_response}, Similar found: {similar_found}, Learning: {learning_improved}, Model: {model_used}", 
                         critical=True)
            return overall_success
        else:
            self.log_test("Voice Processing with Self-Learning", False, f"Status: {status}, Error: {data.get('error', 'Unknown')}", critical=True)
            return False

    def test_voice_feedback(self):
        """Test POST /api/voice/feedback - система рейтингов"""
        print("\n🔍 Testing Voice Feedback Rating System...")
        
        if not self.test_log_id:
            self.log_test("Voice Feedback Rating System", False, "No log_id available from previous test", critical=True)
            return False
        
        feedback_data = {
            "log_id": self.test_log_id,
            "rating": 5,
            "feedback_text": "Отличный ответ! Очень полезная информация для управления клининговой компанией."
        }
        
        success, data, status = self.make_request('POST', 'voice/feedback', feedback_data)
        
        if success and status == 200:
            has_success_field = 'success' in data
            is_successful = data.get('success', False)
            has_message = 'message' in data
            will_be_used = data.get('will_be_used_for_training', False)
            
            # Проверяем что система понимает высокий рейтинг
            message = data.get('message', '')
            is_russian_message = any(char in message for char in 'абвгдеёжзийклмнопрстуфхцчшщъыьэюя')
            
            overall_success = has_success_field and is_successful and has_message and is_russian_message
            self.log_test("Voice Feedback Rating System", overall_success, 
                         f"Success: {is_successful}, Will train: {will_be_used}, Russian message: {is_russian_message}", 
                         critical=True)
            return overall_success
        else:
            self.log_test("Voice Feedback Rating System", False, f"Status: {status}", critical=True)
            return False

    def test_learning_stats(self):
        """Test GET /api/learning/stats - статистика обучения"""
        print("\n🔍 Testing Learning Statistics...")
        success, data, status = self.make_request('GET', 'learning/stats')
        
        if success and status == 200:
            required_fields = ['total_interactions', 'positive_ratings', 'negative_ratings', 'improvement_rate']
            has_required = all(field in data for field in required_fields)
            
            # Проверяем метрики обучения
            total_interactions = data.get('total_interactions', 0)
            avg_rating = data.get('avg_rating')
            positive_ratings = data.get('positive_ratings', 0)
            negative_ratings = data.get('negative_ratings', 0)
            improvement_rate = data.get('improvement_rate', 0)
            last_learning_update = data.get('last_learning_update')
            
            # Проверяем что данные имеют смысл
            has_meaningful_data = isinstance(total_interactions, int) and isinstance(improvement_rate, (int, float))
            
            overall_success = has_required and has_meaningful_data
            self.log_test("Learning Statistics", overall_success, 
                         f"Interactions: {total_interactions}, Avg rating: {avg_rating}, Positive: {positive_ratings}, Improvement: {improvement_rate:.2f}", 
                         critical=True)
            return overall_success
        else:
            self.log_test("Learning Statistics", False, f"Status: {status}", critical=True)
            return False

    def test_learning_export(self):
        """Test GET /api/learning/export - экспорт данных для дообучения"""
        print("\n🔍 Testing Learning Data Export...")
        success, data, status = self.make_request('GET', 'learning/export')
        
        if success and status == 200:
            required_fields = ['total_exported', 'min_rating_used', 'data', 'export_timestamp']
            has_required = all(field in data for field in required_fields)
            
            exported_data = data.get('data', [])
            total_exported = data.get('total_exported', 0)
            min_rating = data.get('min_rating_used', 0)
            export_timestamp = data.get('export_timestamp', '')
            
            # Проверяем формат данных для fine-tuning
            is_valid_format = True
            if exported_data and len(exported_data) > 0:
                sample = exported_data[0]
                is_valid_format = 'messages' in sample and 'metadata' in sample
                
                # Проверяем структуру messages
                if 'messages' in sample:
                    messages = sample['messages']
                    if isinstance(messages, list) and len(messages) >= 2:
                        has_user_assistant = any(msg.get('role') == 'user' for msg in messages) and any(msg.get('role') == 'assistant' for msg in messages)
                        is_valid_format = is_valid_format and has_user_assistant
            
            overall_success = has_required and is_valid_format
            self.log_test("Learning Data Export", overall_success, 
                         f"Exported: {total_exported} conversations, Min rating: {min_rating}, Valid format: {is_valid_format}", 
                         critical=True)
            return overall_success
        else:
            self.log_test("Learning Data Export", False, f"Status: {status}", critical=True)
            return False

    def test_learning_train(self):
        """Test POST /api/learning/train - запуск обучения"""
        print("\n🔍 Testing Learning Training Trigger...")
        success, data, status = self.make_request('POST', 'learning/train')
        
        if success and status == 200:
            has_status = 'status' in data
            has_message = 'message' in data
            has_timestamp = 'timestamp' in data
            
            status_value = data.get('status', '')
            message = data.get('message', '')
            
            # Проверяем что обучение запущено
            training_started = status_value == 'training_started'
            is_russian_message = any(char in message for char in 'абвгдеёжзийклмнопрстуфхцчшщъыьэюя')
            
            overall_success = has_status and has_message and has_timestamp and training_started
            self.log_test("Learning Training Trigger", overall_success, 
                         f"Status: {status_value}, Russian message: {is_russian_message}", 
                         critical=True)
            return overall_success
        else:
            self.log_test("Learning Training Trigger", False, f"Status: {status}", critical=True)
            return False

    # ========== ДОПОЛНИТЕЛЬНЫЕ API ==========
    
    def test_telegram_status(self):
        """Test GET /api/telegram/status - статус телеграм бота"""
        print("\n🔍 Testing Telegram Bot Status...")
        success, data, status = self.make_request('GET', 'telegram/status')
        
        if success and status == 200:
            has_status = 'status' in data
            has_bot = 'bot' in data
            has_features = 'features' in data
            
            status_value = data.get('status', '')
            bot_name = data.get('bot', '')
            features = data.get('features', [])
            
            # Проверяем что бот настроен
            is_configured = status_value in ['configured', 'active', 'working']
            is_vasdom_bot = 'VasDom' in bot_name or 'AudioBot' in bot_name
            has_expected_features = len(features) > 0
            
            overall_success = has_status and has_bot and has_features and is_configured
            self.log_test("Telegram Bot Status", overall_success, 
                         f"Status: {status_value}, Bot: {bot_name}, Features: {len(features)}")
            return overall_success
        else:
            self.log_test("Telegram Bot Status", False, f"Status: {status}")
            return False

    def test_bitrix24_integration(self):
        """Test GET /api/bitrix24/test - тест интеграции с Bitrix24"""
        print("\n🔍 Testing Bitrix24 Integration...")
        success, data, status = self.make_request('GET', 'bitrix24/test')
        
        if success and status == 200:
            has_status = 'status' in data
            has_integration = 'integration' in data
            
            status_value = data.get('status', '')
            integration_status = data.get('integration', '')
            deals = data.get('deals', 0)
            employees = data.get('employees', 0)
            companies = data.get('companies', 0)
            
            # Проверяем что интеграция работает
            is_connected = status_value in ['connected', 'active', 'working']
            is_working = integration_status in ['working', 'active', 'connected']
            
            # Проверяем данные из Bitrix24
            has_meaningful_data = deals > 0 and employees > 0 and companies > 0
            
            overall_success = has_status and has_integration and is_connected and is_working
            self.log_test("Bitrix24 Integration", overall_success, 
                         f"Status: {status_value}, Integration: {integration_status}, Deals: {deals}, Employees: {employees}, Companies: {companies}")
            return overall_success
        else:
            self.log_test("Bitrix24 Integration", False, f"Status: {status}")
            return False

    def run_comprehensive_test(self):
        """Run comprehensive testing based on review request"""
        print("🚀 VasDom AudioBot Dashboard API Comprehensive Testing")
        print("🎯 Based on Russian review request requirements")
        print(f"🌐 Testing against: {self.base_url}")
        print("=" * 80)
        
        test_results = []
        
        # ========== ОСНОВНЫЕ ENDPOINTS ДАШБОРДА ==========
        print("\n" + "📊 TESTING MAIN DASHBOARD ENDPOINTS" + " 📊")
        print("-" * 60)
        
        test_results.append(self.test_dashboard_stats())
        test_results.append(self.test_health_check())
        test_results.append(self.test_cleaning_houses())
        test_results.append(self.test_employees_stats())
        
        # ========== AI ФУНКЦИОНАЛ ==========
        print("\n" + "🧠 TESTING AI FUNCTIONALITY WITH SELF-LEARNING" + " 🧠")
        print("-" * 60)
        
        test_results.append(self.test_voice_process())
        test_results.append(self.test_voice_feedback())
        test_results.append(self.test_learning_stats())
        test_results.append(self.test_learning_export())
        test_results.append(self.test_learning_train())
        
        # ========== ДОПОЛНИТЕЛЬНЫЕ API ==========
        print("\n" + "🔗 TESTING ADDITIONAL INTEGRATIONS" + " 🔗")
        print("-" * 60)
        
        test_results.append(self.test_telegram_status())
        test_results.append(self.test_bitrix24_integration())
        
        # ========== SUMMARY ==========
        print("\n" + "=" * 80)
        print(f"📊 VASDOM AUDIOBOT DASHBOARD API TEST SUMMARY")
        print(f"✅ Passed: {self.tests_passed}/{self.tests_run}")
        print(f"❌ Failed: {self.tests_run - self.tests_passed}/{self.tests_run}")
        
        # Detailed results
        print("\n📋 DETAILED RESULTS:")
        critical_failures = []
        for result in self.test_results:
            if result["status"] == "FAILED" and result["critical"]:
                critical_failures.append(result["name"])
        
        if critical_failures:
            print(f"🚨 CRITICAL FAILURES: {len(critical_failures)}")
            for failure in critical_failures:
                print(f"   ❌ {failure}")
        
        # Overall assessment
        success_rate = (self.tests_passed / self.tests_run) * 100 if self.tests_run > 0 else 0
        
        if success_rate >= 90:
            print("🎉 EXCELLENT! VasDom AudioBot Dashboard API is working correctly!")
            print("🧠 All key metrics and self-learning features are operational!")
            return 0
        elif success_rate >= 70:
            print("✅ GOOD! Most features are working, but some need attention.")
            print("🔧 Check the failed tests above for improvement areas.")
            return 0
        else:
            print("⚠️  NEEDS ATTENTION! Multiple critical features are not working.")
            print("🔧 Significant issues detected that need immediate fixing.")
            return 1

def main():
    """Main test execution"""
    print("🧠 VasDom AudioBot Dashboard API Comprehensive Tester")
    print("📋 Testing based on Russian review request:")
    print("   • Dashboard statistics (82 employees, 450 houses, 1123 entrances)")
    print("   • AI self-learning functionality with Russian responses")
    print("   • Rating system and continuous learning")
    print("   • Telegram bot and Bitrix24 integrations")
    print("   • Complete learning cycle: message → processing → rating → training")
    
    # Use the backend URL from the review request
    tester = VasDomAudioBotDashboardTester("https://audiobot-qci2.onrender.com")
    
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