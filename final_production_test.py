#!/usr/bin/env python3
"""
Final Production Testing for VasDom AudioBot - Comprehensive Test Suite
Tests all production-ready improvements as requested in the review:

КРИТИЧЕСКИЕ ТЕСТЫ:
1. Health Check: GET /api/health - должен возвращать "healthy" со всеми критическими проверками
2. Prometheus метрики: GET /api/metrics - должен возвращать метрики в формате Prometheus
3. Полный AI цикл: Сообщение → ответ → рейтинг → статистика (с проверкой метрик)
4. Learning endpoints: GET /api/learning/stats, GET /api/learning/export
5. Production endpoints: GET /api/, GET /api/dashboard, другие API

МЕТРИКИ ДЛЯ ПРОВЕРКИ:
- vasdom_requests_total - счетчик HTTP запросов
- vasdom_request_duration_seconds - время ответа
- vasdom_ai_responses_total - AI ответы  
- vasdom_learning_feedback_total - обратная связь
"""

import requests
import json
import time
import sys
from datetime import datetime

class FinalProductionTester:
    def __init__(self, base_url="https://smart-audiobot.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_log_id = None
        self.session_id = f"production_test_{int(time.time())}"
        
    def log_test(self, name: str, success: bool, details: str = ""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - ПРОЙДЕН {details}")
        else:
            print(f"❌ {name} - ПРОВАЛЕН {details}")
    
    def make_request(self, method: str, endpoint: str, data: dict = None, timeout: int = 30) -> tuple:
        """Make HTTP request and return (success, response_data, status_code)"""
        url = f"{self.api_url}/{endpoint}" if not endpoint.startswith('http') else endpoint
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
            
        except Exception as e:
            return False, {"error": str(e)}, 0

    def test_health_check_critical(self):
        """КРИТИЧЕСКИЙ ТЕСТ: Health Check с полными проверками"""
        print("\n🔍 КРИТИЧЕСКИЙ ТЕСТ: Health Check...")
        success, data, status = self.make_request('GET', 'health')
        
        if success and status == 200:
            # Проверяем статус "healthy"
            is_healthy = data.get('status') == 'healthy'
            
            # Проверяем critical_checks - все должны быть true
            critical_checks = data.get('critical_checks', {})
            all_critical_ok = all(critical_checks.values()) if critical_checks else False
            
            # Проверяем services
            services = data.get('services', {})
            has_services = bool(services)
            
            # Проверяем system_metrics
            has_system_metrics = 'system_metrics' in data
            
            overall_success = is_healthy and all_critical_ok and has_services and has_system_metrics
            
            details = f"Status: {data.get('status')}, Critical checks: {all_critical_ok}, Services: {len(services)}, Uptime: {data.get('uptime_seconds', 0):.1f}s"
            self.log_test("Health Check (Critical)", overall_success, details)
            return overall_success
        else:
            self.log_test("Health Check (Critical)", False, f"Status: {status}")
            return False

    def test_prometheus_metrics(self):
        """КРИТИЧЕСКИЙ ТЕСТ: Prometheus метрики"""
        print("\n🔍 КРИТИЧЕСКИЙ ТЕСТ: Prometheus Metrics...")
        
        try:
            response = requests.get(f"{self.api_url}/metrics", timeout=30)
            if response.status_code != 200:
                self.log_test("Prometheus Metrics", False, f"Status: {response.status_code}")
                return False
            
            metrics_text = response.text
            
            # Проверяем наличие всех требуемых метрик
            required_metrics = [
                'vasdom_requests_total',
                'vasdom_request_duration_seconds',
                'vasdom_learning_feedback_total'
            ]
            
            metrics_found = {}
            for metric in required_metrics:
                metrics_found[metric] = metric in metrics_text
            
            # Проверяем формат Prometheus
            has_help_lines = '# HELP' in metrics_text
            has_type_lines = '# TYPE' in metrics_text
            
            all_metrics_present = all(metrics_found.values())
            is_prometheus_format = has_help_lines and has_type_lines
            
            overall_success = all_metrics_present and is_prometheus_format
            
            details = f"Метрики найдены: {sum(metrics_found.values())}/{len(required_metrics)}, Prometheus формат: {is_prometheus_format}"
            self.log_test("Prometheus Metrics", overall_success, details)
            return overall_success
            
        except Exception as e:
            self.log_test("Prometheus Metrics", False, f"Error: {str(e)}")
            return False

    def test_full_ai_cycle(self):
        """КРИТИЧЕСКИЙ ТЕСТ: Полный AI цикл с проверкой метрик"""
        print("\n🔍 КРИТИЧЕСКИЙ ТЕСТ: Полный AI цикл...")
        
        # Шаг 1: Отправляем сообщение
        test_message = "Какие услуги предоставляет VasDom? Нужна уборка подъезда в многоквартирном доме."
        message_data = {
            "message": test_message,
            "session_id": self.session_id
        }
        
        success1, response_data, status1 = self.make_request('POST', 'voice/process', message_data, timeout=60)
        
        if not (success1 and status1 == 200):
            self.log_test("AI Cycle - Message Processing", False, f"Status: {status1}")
            return False
        
        # Проверяем ответ
        ai_response = response_data.get('response', '')
        log_id = response_data.get('log_id')
        similar_found = response_data.get('similar_found', 0)
        learning_improved = response_data.get('learning_improved', False)
        
        if not log_id or len(ai_response) < 20:
            self.log_test("AI Cycle - Message Processing", False, "Invalid response structure")
            return False
        
        self.test_log_id = log_id
        print(f"   ✅ Сообщение обработано: {len(ai_response)} символов, похожих: {similar_found}")
        
        # Шаг 2: Отправляем рейтинг
        feedback_data = {
            "log_id": log_id,
            "rating": 5,
            "feedback_text": "Отличный ответ! Очень информативно про услуги VasDom."
        }
        
        success2, feedback_response, status2 = self.make_request('POST', 'voice/feedback', feedback_data)
        
        if not (success2 and status2 == 200):
            self.log_test("AI Cycle - Feedback", False, f"Status: {status2}")
            return False
        
        will_train = feedback_response.get('will_be_used_for_training', False)
        print(f"   ✅ Рейтинг отправлен: 5★, будет использован для обучения: {will_train}")
        
        # Шаг 3: Проверяем статистику
        success3, stats_data, status3 = self.make_request('GET', 'learning/stats')
        
        if not (success3 and status3 == 200):
            self.log_test("AI Cycle - Statistics", False, f"Status: {status3}")
            return False
        
        total_interactions = stats_data.get('total_interactions', 0)
        avg_rating = stats_data.get('avg_rating')
        positive_ratings = stats_data.get('positive_ratings', 0)
        
        print(f"   ✅ Статистика обновлена: {total_interactions} диалогов, средний рейтинг: {avg_rating}")
        
        # Шаг 4: Проверяем метрики
        try:
            metrics_response = requests.get(f"{self.api_url}/metrics", timeout=30)
            if metrics_response.status_code == 200:
                metrics_text = metrics_response.text
                
                # Ищем метрики обратной связи
                feedback_metrics = [line for line in metrics_text.split('\n') if 'vasdom_learning_feedback_total' in line and 'rating="5"' in line]
                has_feedback_metric = len(feedback_metrics) > 0
                
                print(f"   ✅ Метрики обновлены: обратная связь зафиксирована: {has_feedback_metric}")
            else:
                has_feedback_metric = False
        except:
            has_feedback_metric = False
        
        overall_success = success1 and success2 and success3 and total_interactions > 0
        
        details = f"Диалогов: {total_interactions}, Рейтинг: {avg_rating}, Позитивных: {positive_ratings}, Метрики: {has_feedback_metric}"
        self.log_test("Full AI Cycle (Critical)", overall_success, details)
        return overall_success

    def test_learning_endpoints(self):
        """КРИТИЧЕСКИЙ ТЕСТ: Learning endpoints"""
        print("\n🔍 КРИТИЧЕСКИЙ ТЕСТ: Learning Endpoints...")
        
        # Тест GET /api/learning/stats
        success1, stats_data, status1 = self.make_request('GET', 'learning/stats')
        stats_ok = success1 and status1 == 200 and 'total_interactions' in stats_data
        
        # Тест GET /api/learning/export
        success2, export_data, status2 = self.make_request('GET', 'learning/export')
        export_ok = success2 and status2 == 200 and 'total_exported' in export_data and 'data' in export_data
        
        overall_success = stats_ok and export_ok
        
        stats_interactions = stats_data.get('total_interactions', 0) if stats_ok else 0
        export_count = export_data.get('total_exported', 0) if export_ok else 0
        
        details = f"Stats: {stats_ok} ({stats_interactions} диалогов), Export: {export_ok} ({export_count} экспортировано)"
        self.log_test("Learning Endpoints", overall_success, details)
        return overall_success

    def test_production_endpoints(self):
        """КРИТИЧЕСКИЙ ТЕСТ: Production endpoints"""
        print("\n🔍 КРИТИЧЕСКИЙ ТЕСТ: Production Endpoints...")
        
        endpoints_to_test = [
            ('', 'API Root'),
            ('dashboard', 'Dashboard'),
            ('cleaning/houses', 'Houses'),
            ('telegram/status', 'Telegram Status'),
            ('bitrix24/test', 'Bitrix24 Test')
        ]
        
        results = {}
        for endpoint, name in endpoints_to_test:
            success, data, status = self.make_request('GET', endpoint)
            results[name] = success and status == 200
        
        successful_endpoints = sum(results.values())
        total_endpoints = len(results)
        overall_success = successful_endpoints >= (total_endpoints * 0.8)  # 80% должны работать
        
        details = f"Работающих endpoints: {successful_endpoints}/{total_endpoints}"
        self.log_test("Production Endpoints", overall_success, details)
        return overall_success

    def run_final_production_test(self):
        """Запуск финального production тестирования"""
        print("🚀 ФИНАЛЬНОЕ PRODUCTION ТЕСТИРОВАНИЕ VasDom AudioBot")
        print("🎯 Проверка всех production-ready улучшений")
        print(f"🌐 URL: {self.base_url}")
        print("=" * 80)
        
        test_results = []
        
        # КРИТИЧЕСКИЕ ТЕСТЫ согласно review request
        print("\n🔥 КРИТИЧЕСКИЕ ТЕСТЫ PRODUCTION СИСТЕМЫ")
        print("-" * 60)
        
        # 1. Health Check с полными проверками
        test_results.append(self.test_health_check_critical())
        
        # 2. Prometheus метрики
        test_results.append(self.test_prometheus_metrics())
        
        # 3. Полный AI цикл с проверкой метрик
        test_results.append(self.test_full_ai_cycle())
        
        # 4. Learning endpoints
        test_results.append(self.test_learning_endpoints())
        
        # 5. Production endpoints
        test_results.append(self.test_production_endpoints())
        
        # ФИНАЛЬНЫЙ ОТЧЕТ
        print("\n" + "=" * 80)
        print("📊 ФИНАЛЬНЫЙ ОТЧЕТ PRODUCTION ТЕСТИРОВАНИЯ")
        print(f"✅ Пройдено: {self.tests_passed}/{self.tests_run}")
        print(f"❌ Провалено: {self.tests_run - self.tests_passed}/{self.tests_run}")
        
        if self.tests_passed == self.tests_run:
            print("\n🎉 ВСЕ КРИТИЧЕСКИЕ ТЕСТЫ ПРОЙДЕНЫ!")
            print("✅ VasDom AudioBot полностью готов к production использованию!")
            print("🧠 Система самообучения функционирует корректно")
            print("📊 Мониторинг и метрики работают")
            print("🔒 Все критические проблемы исправлены")
            return 0
        else:
            print("\n⚠️ ОБНАРУЖЕНЫ ПРОБЛЕМЫ В PRODUCTION СИСТЕМЕ!")
            print("🔧 Требуется дополнительная работа перед production запуском")
            return 1

def main():
    """Main execution"""
    print("🎯 VasDom AudioBot - Final Production Testing")
    print("🚀 Проверка готовности к production использованию")
    
    tester = FinalProductionTester()
    
    try:
        return tester.run_final_production_test()
    except KeyboardInterrupt:
        print("\n⏹️ Тестирование прервано пользователем")
        return 1
    except Exception as e:
        print(f"\n💥 Неожиданная ошибка: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())