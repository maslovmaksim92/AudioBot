#!/usr/bin/env python3
"""
VasDom AudioBot Backend API Testing
Тестирование всех API endpoints для системы управления клининговой компанией
"""

import requests
import sys
import json
from datetime import datetime
from typing import Dict, Any

class VasDomAPITester:
    def __init__(self, base_url="https://audio-inspector-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []

    def log_test(self, name: str, success: bool, details: str = ""):
        """Логирование результатов тестов"""
        self.tests_run += 1
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"\n{status} - {name}")
        if details:
            print(f"   Details: {details}")
        
        if success:
            self.tests_passed += 1
        else:
            self.failed_tests.append(f"{name}: {details}")

    def test_api_root(self) -> bool:
        """Тест корневого API endpoint"""
        try:
            response = requests.get(f"{self.api_url}/", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                expected_message = "VasDom AudioBot API активна"
                if expected_message in data.get("message", ""):
                    self.log_test("API Root Status", True, f"Message: {data.get('message')}")
                    return True
                else:
                    self.log_test("API Root Status", False, f"Unexpected message: {data}")
                    return False
            else:
                self.log_test("API Root Status", False, f"Status code: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("API Root Status", False, f"Exception: {str(e)}")
            return False

    def test_dashboard_stats(self) -> bool:
        """Тест статистики дашборда - должен возвращать 348 домов, 25812 квартир, 82 сотрудника"""
        try:
            response = requests.get(f"{self.api_url}/dashboard", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                
                # Проверяем ожидаемые значения
                expected_values = {
                    "houses": 348,
                    "apartments": 25812,
                    "employees": 82,
                    "brigades": 6,
                    "completed_objects": 147,
                    "problem_objects": 25
                }
                
                all_correct = True
                details = []
                
                for key, expected in expected_values.items():
                    actual = data.get(key, 0)
                    if actual == expected:
                        details.append(f"{key}: {actual} ✓")
                    else:
                        details.append(f"{key}: {actual} (expected {expected}) ✗")
                        all_correct = False
                
                self.log_test("Dashboard Statistics", all_correct, "; ".join(details))
                return all_correct
            else:
                self.log_test("Dashboard Statistics", False, f"Status code: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Dashboard Statistics", False, f"Exception: {str(e)}")
            return False

    def test_bitrix24_integration(self) -> bool:
        """Тест интеграции с Bitrix24"""
        try:
            response = requests.get(f"{self.api_url}/bitrix24/test", timeout=15)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                status = data.get("status")
                houses_count = data.get("houses_count", 0)
                sample_houses = data.get("sample_houses", [])
                
                if status == "success" and houses_count > 0:
                    details = f"Status: {status}, Houses: {houses_count}, Sample: {len(sample_houses)} houses"
                    self.log_test("Bitrix24 Integration", True, details)
                    return True
                else:
                    details = f"Status: {status}, Houses: {houses_count}"
                    self.log_test("Bitrix24 Integration", False, details)
                    return False
            else:
                self.log_test("Bitrix24 Integration", False, f"Status code: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Bitrix24 Integration", False, f"Exception: {str(e)}")
            return False

    def test_cleaning_houses(self) -> bool:
        """Тест получения домов из воронки уборки"""
        try:
            response = requests.get(f"{self.api_url}/cleaning/houses?limit=5", timeout=15)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                houses = data.get("houses", [])
                count = data.get("count", 0)
                total_in_system = data.get("total_in_system", 0)
                
                # Проверяем что есть дома и правильное общее количество
                houses_ok = len(houses) > 0 and count > 0
                total_ok = total_in_system == 348
                
                # Проверяем что в домах есть реальные адреса Калуги
                kaluga_addresses = ["Пролетарская", "Никитиной", "Хрустальная", "Жилетово", "Кондрово", "Гагарина", "Ленина"]
                has_real_addresses = False
                
                for house in houses[:3]:  # Проверяем первые 3 дома
                    title = house.get("TITLE", "")
                    if any(addr in title for addr in kaluga_addresses):
                        has_real_addresses = True
                        break
                
                all_ok = houses_ok and total_ok and has_real_addresses
                details = f"Houses: {count}, Total: {total_in_system}, Real addresses: {has_real_addresses}"
                
                self.log_test("Cleaning Houses List", all_ok, details)
                return all_ok
            else:
                self.log_test("Cleaning Houses List", False, f"Status code: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Cleaning Houses List", False, f"Exception: {str(e)}")
            return False

    def test_voice_processing(self) -> bool:
        """Тест AI обработки голосовых запросов"""
        try:
            # Тестируем с русским запросом о компании
            test_request = {
                "text": "Сколько домов обслуживает компания VasDom?",
                "user_id": "test_user_1"
            }
            
            response = requests.post(
                f"{self.api_url}/voice/process", 
                json=test_request, 
                timeout=30,
                headers={"Content-Type": "application/json"}
            )
            
            success = response.status_code == 200
            
            if success:
                data = response.json()
                ai_response = data.get("response", "")
                confidence = data.get("confidence", 0)
                
                # Проверяем что ответ на русском и содержит информацию о компании
                has_russian = any(char in "абвгдеёжзийклмнопрстуфхцчшщъыьэюя" for char in ai_response.lower())
                mentions_vasdom = "VasDom" in ai_response or "васдом" in ai_response.lower()
                mentions_houses = any(word in ai_response.lower() for word in ["дом", "348", "калуг"])
                
                response_ok = has_russian and (mentions_vasdom or mentions_houses) and len(ai_response) > 20
                confidence_ok = confidence > 0.8
                
                all_ok = response_ok and confidence_ok
                details = f"Russian: {has_russian}, VasDom context: {mentions_vasdom or mentions_houses}, Confidence: {confidence}"
                
                self.log_test("AI Voice Processing", all_ok, details)
                return all_ok
            else:
                self.log_test("AI Voice Processing", False, f"Status code: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("AI Voice Processing", False, f"Exception: {str(e)}")
            return False

    def test_meetings_endpoints(self) -> bool:
        """Тест endpoints для планерок"""
        try:
            # Тест получения списка планерок
            response = requests.get(f"{self.api_url}/meetings", timeout=10)
            meetings_ok = response.status_code == 200
            
            if meetings_ok:
                data = response.json()
                meetings = data.get("meetings", [])
                meetings_ok = len(meetings) > 0
            
            # Тест начала записи планерки
            meeting_request = {
                "meeting_type": "планерка",
                "participants": ["user1", "user2"]
            }
            
            response = requests.post(
                f"{self.api_url}/meetings/start-recording",
                json=meeting_request,
                timeout=10,
                headers={"Content-Type": "application/json"}
            )
            
            recording_ok = response.status_code == 200
            if recording_ok:
                data = response.json()
                meeting_id = data.get("meeting_id")
                recording_ok = meeting_id is not None and "meeting_" in meeting_id
            
            all_ok = meetings_ok and recording_ok
            details = f"Meetings list: {meetings_ok}, Recording start: {recording_ok}"
            
            self.log_test("Meetings Endpoints", all_ok, details)
            return all_ok
            
        except Exception as e:
            self.log_test("Meetings Endpoints", False, f"Exception: {str(e)}")
            return False

    def run_all_tests(self) -> bool:
        """Запуск всех тестов"""
        print("🚀 Начинаем тестирование VasDom AudioBot API")
        print(f"📡 Base URL: {self.base_url}")
        print(f"🔗 API URL: {self.api_url}")
        print("=" * 60)
        
        # Запускаем все тесты
        tests = [
            self.test_api_root,
            self.test_dashboard_stats,
            self.test_bitrix24_integration,
            self.test_cleaning_houses,
            self.test_voice_processing,
            self.test_meetings_endpoints
        ]
        
        for test in tests:
            test()
        
        # Итоговый отчет
        print("\n" + "=" * 60)
        print(f"📊 ИТОГИ ТЕСТИРОВАНИЯ:")
        print(f"✅ Пройдено: {self.tests_passed}/{self.tests_run}")
        print(f"❌ Провалено: {len(self.failed_tests)}/{self.tests_run}")
        
        if self.failed_tests:
            print(f"\n🚨 ПРОБЛЕМЫ:")
            for i, failure in enumerate(self.failed_tests, 1):
                print(f"   {i}. {failure}")
        
        success_rate = (self.tests_passed / self.tests_run) * 100 if self.tests_run > 0 else 0
        print(f"\n📈 Успешность: {success_rate:.1f}%")
        
        return len(self.failed_tests) == 0

def main():
    """Основная функция"""
    tester = VasDomAPITester()
    
    try:
        all_passed = tester.run_all_tests()
        
        if all_passed:
            print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ! Backend API работает корректно.")
            return 0
        else:
            print(f"\n⚠️  ОБНАРУЖЕНЫ ПРОБЛЕМЫ! {len(tester.failed_tests)} тестов провалено.")
            return 1
            
    except KeyboardInterrupt:
        print("\n⏹️  Тестирование прервано пользователем")
        return 1
    except Exception as e:
        print(f"\n💥 Критическая ошибка: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())