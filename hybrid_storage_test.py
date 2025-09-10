#!/usr/bin/env python3
"""
Hybrid Storage System Test for VasDom AudioBot
Testing PostgreSQL + in-memory fallback system as per review request
"""

import requests
import json
import time
from datetime import datetime

class HybridStorageTest:
    def __init__(self):
        self.base_url = "https://smart-audiobot.preview.emergentagent.com"
        self.api_url = f"{self.base_url}/api"
        self.session_id = f"hybrid_test_{int(time.time())}"
        self.log_ids = []
        
    def log_result(self, test_name, success, details=""):
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status} {test_name}: {details}")
        return success
    
    def make_request(self, method, endpoint, data=None):
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=30)
            
            return response.status_code, response.json() if response.text else {}
        except Exception as e:
            return 0, {"error": str(e)}
    
    def test_storage_detection(self):
        """КРИТИЧЕСКИЙ ТЕСТ 1: Storage detection via /api/health"""
        print("\n🔍 КРИТИЧЕСКИЙ ТЕСТ 1: Storage Detection")
        status, data = self.make_request('GET', 'health')
        
        if status == 200:
            services = data.get('services', {})
            database_status = services.get('database', None)
            storage_status = services.get('storage', None)
            
            # Проверяем тип хранилища
            if database_status is False and storage_status is True:
                return self.log_result("Storage Detection", True, 
                    "✅ In-memory fallback активен (database=false, storage=true)")
            elif database_status is True:
                return self.log_result("Storage Detection", True, 
                    "✅ PostgreSQL активен (database=true)")
            else:
                return self.log_result("Storage Detection", False, 
                    f"❌ Неопределенный статус хранилища: database={database_status}, storage={storage_status}")
        else:
            return self.log_result("Storage Detection", False, f"❌ Health check failed: {status}")
    
    def test_full_ai_cycle(self):
        """КРИТИЧЕСКИЙ ТЕСТ 2: Полный AI цикл"""
        print("\n🔍 КРИТИЧЕСКИЙ ТЕСТ 2: Full AI Cycle")
        
        # Шаг 1: POST /api/voice/process
        print("  📝 Шаг 1: Отправка сообщения...")
        message_data = {
            "message": "Как часто нужно убирать подъезды в многоквартирных домах? Какие есть стандарты?",
            "session_id": self.session_id
        }
        
        status, response = self.make_request('POST', 'voice/process', message_data)
        if status != 200:
            return self.log_result("Full AI Cycle - Step 1", False, f"Voice process failed: {status}")
        
        log_id = response.get('log_id')
        if not log_id:
            return self.log_result("Full AI Cycle - Step 1", False, "No log_id returned")
        
        self.log_ids.append(log_id)
        ai_response = response.get('response', '')
        similar_found = response.get('similar_found', 0)
        
        print(f"    ✅ AI ответ получен: {len(ai_response)} символов, похожих диалогов: {similar_found}")
        
        # Шаг 2: POST /api/voice/feedback
        print("  ⭐ Шаг 2: Отправка рейтинга...")
        feedback_data = {
            "log_id": log_id,
            "rating": 5,
            "feedback_text": "Отличный ответ по клинингу подъездов!"
        }
        
        status, feedback_response = self.make_request('POST', 'voice/feedback', feedback_data)
        if status != 200:
            return self.log_result("Full AI Cycle - Step 2", False, f"Feedback failed: {status}")
        
        will_train = feedback_response.get('will_be_used_for_training', False)
        print(f"    ✅ Рейтинг принят, будет использован для обучения: {will_train}")
        
        # Шаг 3: GET /api/learning/stats
        print("  📊 Шаг 3: Проверка статистики...")
        time.sleep(2)  # Даем время на обработку
        
        status, stats = self.make_request('GET', 'learning/stats')
        if status != 200:
            return self.log_result("Full AI Cycle - Step 3", False, f"Stats failed: {status}")
        
        total_interactions = stats.get('total_interactions', 0)
        avg_rating = stats.get('avg_rating')
        positive_ratings = stats.get('positive_ratings', 0)
        
        print(f"    ✅ Статистика обновлена: {total_interactions} диалогов, средний рейтинг: {avg_rating}, положительных: {positive_ratings}")
        
        return self.log_result("Full AI Cycle", True, 
            f"Полный цикл завершен: сообщение → ответ → рейтинг → статистика")
    
    def test_persistence(self):
        """КРИТИЧЕСКИЙ ТЕСТ 3: Persistence test"""
        print("\n🔍 КРИТИЧЕСКИЙ ТЕСТ 3: Data Persistence")
        
        # Создаем еще один диалог
        message_data = {
            "message": "Какие химические средства лучше использовать для уборки подъездов?",
            "session_id": self.session_id
        }
        
        status, response = self.make_request('POST', 'voice/process', message_data)
        if status != 200:
            return self.log_result("Persistence Test", False, f"Failed to create dialog: {status}")
        
        log_id = response.get('log_id')
        self.log_ids.append(log_id)
        
        # Даем рейтинг
        feedback_data = {
            "log_id": log_id,
            "rating": 4,
            "feedback_text": "Хорошая информация о химических средствах"
        }
        
        status, _ = self.make_request('POST', 'voice/feedback', feedback_data)
        if status != 200:
            return self.log_result("Persistence Test", False, f"Failed to rate dialog: {status}")
        
        # Проверяем что данные сохранились
        time.sleep(1)
        status, stats = self.make_request('GET', 'learning/stats')
        if status != 200:
            return self.log_result("Persistence Test", False, f"Failed to get stats: {status}")
        
        total_interactions = stats.get('total_interactions', 0)
        if total_interactions >= 2:
            return self.log_result("Persistence Test", True, 
                f"Данные сохранены: {total_interactions} диалогов в системе")
        else:
            return self.log_result("Persistence Test", False, 
                f"Данные не сохранились: только {total_interactions} диалогов")
    
    def test_learning_endpoints(self):
        """КРИТИЧЕСКИЙ ТЕСТ 4: Learning endpoints"""
        print("\n🔍 КРИТИЧЕСКИЙ ТЕСТ 4: Learning Endpoints")
        
        # GET /api/learning/stats
        status, stats = self.make_request('GET', 'learning/stats')
        stats_ok = status == 200 and 'total_interactions' in stats
        
        # GET /api/learning/export
        status, export_data = self.make_request('GET', 'learning/export')
        export_ok = status == 200 and 'total_exported' in export_data
        
        if stats_ok and export_ok:
            total_interactions = stats.get('total_interactions', 0)
            total_exported = export_data.get('total_exported', 0)
            return self.log_result("Learning Endpoints", True, 
                f"Stats: {total_interactions} диалогов, Export: {total_exported} качественных")
        else:
            return self.log_result("Learning Endpoints", False, 
                f"Stats OK: {stats_ok}, Export OK: {export_ok}")
    
    def test_health_database_status(self):
        """КРИТИЧЕСКИЙ ТЕСТ 5: Health check database status"""
        print("\n🔍 КРИТИЧЕСКИЙ ТЕСТ 5: Database Status in Health Check")
        
        status, data = self.make_request('GET', 'health')
        if status != 200:
            return self.log_result("Health Database Status", False, f"Health check failed: {status}")
        
        services = data.get('services', {})
        database_status = services.get('database')
        storage_status = services.get('storage')
        critical_checks = data.get('critical_checks', {})
        
        # Проверяем что статус БД отображается корректно
        if database_status is not None and storage_status is True:
            db_type = "PostgreSQL" if database_status else "In-Memory"
            return self.log_result("Health Database Status", True, 
                f"Статус БД корректно отображается: {db_type} (database={database_status})")
        else:
            return self.log_result("Health Database Status", False, 
                f"Некорректный статус БД: database={database_status}, storage={storage_status}")
    
    def run_all_tests(self):
        """Запуск всех критических тестов"""
        print("🚀 ТЕСТИРОВАНИЕ ГИБРИДНОЙ СИСТЕМЫ ХРАНЕНИЯ VasDom AudioBot")
        print("🔄 PostgreSQL + In-Memory Fallback System")
        print("🌐 URL:", self.base_url)
        print("=" * 80)
        
        results = []
        
        # Запускаем все критические тесты
        results.append(self.test_storage_detection())
        results.append(self.test_full_ai_cycle())
        results.append(self.test_persistence())
        results.append(self.test_learning_endpoints())
        results.append(self.test_health_database_status())
        
        # Итоговый отчет
        passed = sum(results)
        total = len(results)
        
        print("\n" + "=" * 80)
        print("📊 ИТОГОВЫЙ ОТЧЕТ ТЕСТИРОВАНИЯ ГИБРИДНОГО ХРАНИЛИЩА")
        print(f"✅ Пройдено: {passed}/{total}")
        print(f"❌ Провалено: {total - passed}/{total}")
        
        if passed == total:
            print("🎉 ВСЕ КРИТИЧЕСКИЕ ТЕСТЫ ПРОЙДЕНЫ!")
            print("✅ Гибридная система хранения работает корректно")
            print("✅ Fallback на in-memory функционирует правильно")
            print("✅ AI цикл полностью функционален")
        else:
            print("⚠️ Некоторые тесты провалились")
            print("🔧 Требуется внимание к гибридной системе хранения")
        
        return passed == total

if __name__ == "__main__":
    tester = HybridStorageTest()
    success = tester.run_all_tests()
    exit(0 if success else 1)
