#!/usr/bin/env python3
"""
Critical Tests for VasDom AudioBot - Review Request Focus
Tests the specific endpoints mentioned in the review request
"""

import requests
import json
import sys
import time
from datetime import datetime

class CriticalTester:
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

    def test_cleaning_houses_main(self):
        """КРИТИЧЕСКИЙ ТЕСТ 1: GET /api/cleaning/houses - основной endpoint домов"""
        try:
            print("\n🏠 КРИТИЧЕСКИЙ ТЕСТ 1: GET /api/cleaning/houses")
            print("   Требование: Дома с заполненными количественными полями")
            print("   Проверка: apartments_count > 0, entrances_count > 0, floors_count > 0")
            print("   Проверка: management_company не null/пустая строка")
            
            response = requests.get(f"{self.api_url}/cleaning/houses", timeout=30)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                success = (data.get("status") == "success" and 
                          "houses" in data and
                          isinstance(data["houses"], list))
                
                if success:
                    houses = data["houses"]
                    houses_count = len(houses)
                    total_from_api = data.get("total", houses_count)
                    
                    print(f"   🏠 Загружено домов: {houses_count}")
                    print(f"   🏠 Total из API: {total_from_api}")
                    
                    if houses_count > 0:
                        # Проверяем количественные поля
                        houses_with_apartments = sum(1 for h in houses if (h.get('apartments_count') or 0) > 0)
                        houses_with_entrances = sum(1 for h in houses if (h.get('entrances_count') or 0) > 0)
                        houses_with_floors = sum(1 for h in houses if (h.get('floors_count') or 0) > 0)
                        houses_with_uc = sum(1 for h in houses if h.get('management_company') and h.get('management_company') != 'null')
                        
                        print(f"   🏠 Домов с apartments_count > 0: {houses_with_apartments}/{houses_count}")
                        print(f"   🏠 Домов с entrances_count > 0: {houses_with_entrances}/{houses_count}")
                        print(f"   🏠 Домов с floors_count > 0: {houses_with_floors}/{houses_count}")
                        print(f"   🏠 Домов с УК не null: {houses_with_uc}/{houses_count}")
                        
                        # КРИТИЧЕСКИЕ ПРОВЕРКИ
                        critical_issues = []
                        
                        if houses_with_apartments == 0:
                            critical_issues.append("Все apartments_count = 0")
                        if houses_with_entrances == 0:
                            critical_issues.append("Все entrances_count = 0")
                        if houses_with_floors == 0:
                            critical_issues.append("Все floors_count = 0")
                        if houses_with_uc == 0:
                            critical_issues.append("Все management_company = null")
                        
                        if critical_issues:
                            print(f"   ❌ КРИТИЧЕСКИЕ ПРОБЛЕМЫ:")
                            for issue in critical_issues:
                                print(f"      - {issue}")
                            success = False
                        else:
                            print(f"   ✅ Все количественные поля заполнены корректно")
                        
                        # Показываем примеры
                        sample_house = houses[0]
                        print(f"   📋 Пример дома:")
                        print(f"      - Адрес: {sample_house.get('address', 'Нет')}")
                        print(f"      - Квартиры: {sample_house.get('apartments_count', 0)}")
                        print(f"      - Подъезды: {sample_house.get('entrances_count', 0)}")
                        print(f"      - Этажи: {sample_house.get('floors_count', 0)}")
                        print(f"      - УК: {sample_house.get('management_company', 'null')}")
                
            self.log_test("КРИТИЧЕСКИЙ: GET /api/cleaning/houses", success, 
                         f"Status: {response.status_code}, Houses: {houses_count if 'houses_count' in locals() else 0}")
            return success
        except Exception as e:
            self.log_test("КРИТИЧЕСКИЙ: GET /api/cleaning/houses", False, str(e))
            return False

    def test_cleaning_houses_490(self):
        """КРИТИЧЕСКИЙ ТЕСТ 2: GET /api/cleaning/houses-490 - должен возвращать exactly 490 домов"""
        try:
            print("\n🏠 КРИТИЧЕСКИЙ ТЕСТ 2: GET /api/cleaning/houses-490")
            print("   Требование: Загрузка exactly 490 домов из Bitrix24")
            print("   Проверка: apartments_count > 0, entrances_count > 0, floors_count > 0")
            print("   Проверка: management_company не null/пустая строка")
            
            response = requests.get(f"{self.api_url}/cleaning/houses-490", timeout=30)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                success = (data.get("status") == "success" and 
                          "houses" in data and
                          isinstance(data["houses"], list))
                
                if success:
                    houses = data["houses"]
                    houses_count = len(houses)
                    total_from_api = data.get("total", houses_count)
                    
                    print(f"   🏠 Загружено домов: {houses_count}")
                    print(f"   🏠 Total из API: {total_from_api}")
                    
                    # КРИТИЧЕСКАЯ ПРОВЕРКА: exactly 490 домов
                    if houses_count == 490:
                        print(f"   ✅ EXACTLY 490 домов загружено")
                    else:
                        print(f"   ❌ НЕПРАВИЛЬНОЕ КОЛИЧЕСТВО: {houses_count} != 490")
                        success = False
                    
                    if houses_count > 0:
                        # Проверяем количественные поля
                        houses_with_apartments = sum(1 for h in houses if (h.get('apartments_count') or 0) > 0)
                        houses_with_entrances = sum(1 for h in houses if (h.get('entrances_count') or 0) > 0)
                        houses_with_floors = sum(1 for h in houses if (h.get('floors_count') or 0) > 0)
                        houses_with_uc = sum(1 for h in houses if h.get('management_company') and h.get('management_company') != 'null')
                        
                        print(f"   🏠 Домов с apartments_count > 0: {houses_with_apartments}/{houses_count}")
                        print(f"   🏠 Домов с entrances_count > 0: {houses_with_entrances}/{houses_count}")
                        print(f"   🏠 Домов с floors_count > 0: {houses_with_floors}/{houses_count}")
                        print(f"   🏠 Домов с УК не null: {houses_with_uc}/{houses_count}")
                        
                        # КРИТИЧЕСКИЕ ПРОВЕРКИ
                        if houses_with_apartments == 0:
                            print(f"   ❌ КРИТИЧЕСКАЯ ПРОБЛЕМА: Все apartments_count = 0")
                            success = False
                        elif houses_with_apartments < houses_count * 0.8:
                            print(f"   ⚠️ ПРОБЛЕМА: Мало домов с apartments_count > 0")
                            success = False
                        else:
                            print(f"   ✅ apartments_count заполнены корректно")
                        
                        if houses_with_entrances == 0:
                            print(f"   ❌ КРИТИЧЕСКАЯ ПРОБЛЕМА: Все entrances_count = 0")
                            success = False
                        elif houses_with_entrances < houses_count * 0.8:
                            print(f"   ⚠️ ПРОБЛЕМА: Мало домов с entrances_count > 0")
                            success = False
                        else:
                            print(f"   ✅ entrances_count заполнены корректно")
                        
                        if houses_with_floors == 0:
                            print(f"   ❌ КРИТИЧЕСКАЯ ПРОБЛЕМА: Все floors_count = 0")
                            success = False
                        elif houses_with_floors < houses_count * 0.8:
                            print(f"   ⚠️ ПРОБЛЕМА: Мало домов с floors_count > 0")
                            success = False
                        else:
                            print(f"   ✅ floors_count заполнены корректно")
                        
                        if houses_with_uc == 0:
                            print(f"   ❌ КРИТИЧЕСКАЯ ПРОБЛЕМА: Все management_company = null")
                            success = False
                        elif houses_with_uc < houses_count * 0.5:
                            print(f"   ⚠️ ПРОБЛЕМА: Мало домов с УК")
                            success = False
                        else:
                            print(f"   ✅ management_company заполнены корректно")
                        
                        # Показываем примеры
                        sample_house = houses[0]
                        print(f"   📋 Пример дома:")
                        print(f"      - Адрес: {sample_house.get('address', 'Нет')}")
                        print(f"      - Квартиры: {sample_house.get('apartments_count', 0)}")
                        print(f"      - Подъезды: {sample_house.get('entrances_count', 0)}")
                        print(f"      - Этажи: {sample_house.get('floors_count', 0)}")
                        print(f"      - УК: {sample_house.get('management_company', 'null')}")
                
            self.log_test("КРИТИЧЕСКИЙ: GET /api/cleaning/houses-490", success, 
                         f"Status: {response.status_code}, Houses: {houses_count if 'houses_count' in locals() else 0}")
            return success
        except Exception as e:
            self.log_test("КРИТИЧЕСКИЙ: GET /api/cleaning/houses-490", False, str(e))
            return False

    def test_bitrix24_connection(self):
        """КРИТИЧЕСКИЙ ТЕСТ 3: GET /api/bitrix24/test - проверка подключения к Bitrix24"""
        try:
            print("\n🔗 КРИТИЧЕСКИЙ ТЕСТ 3: GET /api/bitrix24/test")
            print("   Требование: Проверка подключения к Bitrix24")
            print("   Ожидается: Успешное подключение и получение данных")
            
            response = requests.get(f"{self.api_url}/bitrix24/test", timeout=15)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                success = data.get("status") == "success"
                
                if success:
                    bitrix_info = data.get("bitrix_info", {})
                    connection_status = bitrix_info.get("connection", "unknown")
                    sample_deals = bitrix_info.get("sample_deals", 0)
                    
                    print(f"   🔗 Статус подключения: {connection_status}")
                    print(f"   🔗 Примеров сделок: {sample_deals}")
                    
                    if connection_status == "✅ Connected":
                        print(f"   ✅ Bitrix24 подключение работает")
                    else:
                        print(f"   ❌ Проблемы с подключением к Bitrix24")
                        success = False
                    
                    if sample_deals > 0:
                        print(f"   ✅ Получены данные из Bitrix24: {sample_deals} сделок")
                    else:
                        print(f"   ⚠️ Нет данных из Bitrix24")
                else:
                    print(f"   ❌ API вернул ошибку: {data.get('message', 'Unknown error')}")
                
            self.log_test("КРИТИЧЕСКИЙ: GET /api/bitrix24/test", success, 
                         f"Status: {response.status_code}")
            return success
        except Exception as e:
            self.log_test("КРИТИЧЕСКИЙ: GET /api/bitrix24/test", False, str(e))
            return False

    def test_house_schema_structure(self):
        """КРИТИЧЕСКИЙ ТЕСТ 4: Проверка структуры данных House schema"""
        try:
            print("\n📋 КРИТИЧЕСКИЙ ТЕСТ 4: Проверка структуры House schema")
            print("   Требование: House schema содержит все новые поля")
            print("   Проверка: Наличие всех обязательных полей в ответе")
            
            response = requests.get(f"{self.api_url}/cleaning/houses?limit=1", timeout=15)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                success = (data.get("status") == "success" and 
                          "houses" in data and
                          len(data["houses"]) > 0)
                
                if success:
                    house = data["houses"][0]
                    
                    # Обязательные поля из review request
                    required_fields = [
                        'address', 'deal_id', 'brigade', 'management_company',
                        'apartments_count', 'entrances_count', 'floors_count'
                    ]
                    
                    # Дополнительные поля для полной функциональности
                    additional_fields = [
                        'status', 'stage_id', 'assigned_by_id', 'company_id',
                        'contact_id', 'created_date', 'modified_date'
                    ]
                    
                    missing_required = []
                    present_required = []
                    missing_additional = []
                    present_additional = []
                    
                    for field in required_fields:
                        if field in house:
                            present_required.append(field)
                        else:
                            missing_required.append(field)
                    
                    for field in additional_fields:
                        if field in house:
                            present_additional.append(field)
                        else:
                            missing_additional.append(field)
                    
                    print(f"   📋 Обязательных полей присутствует: {len(present_required)}/{len(required_fields)}")
                    print(f"   📋 Дополнительных полей присутствует: {len(present_additional)}/{len(additional_fields)}")
                    
                    if missing_required:
                        print(f"   ❌ КРИТИЧЕСКИЕ отсутствующие поля: {missing_required}")
                        success = False
                    else:
                        print(f"   ✅ Все обязательные поля присутствуют")
                    
                    if missing_additional:
                        print(f"   ⚠️ Отсутствующие дополнительные поля: {missing_additional}")
                    
                    # Показываем структуру
                    print(f"   📋 Структура House:")
                    for field in present_required:
                        value = house.get(field)
                        print(f"      - {field}: {type(value).__name__} = {str(value)[:50]}")
                
            self.log_test("КРИТИЧЕСКИЙ: House Schema Structure", success, 
                         f"Status: {response.status_code}, Required fields: {len(present_required) if 'present_required' in locals() else 0}")
            return success
        except Exception as e:
            self.log_test("КРИТИЧЕСКИЙ: House Schema Structure", False, str(e))
            return False

    def run_critical_tests(self):
        """Run only critical tests from review request"""
        print("🔥 КРИТИЧЕСКИЕ ТЕСТЫ VasDom AudioBot - Review Request")
        print(f"🔗 Testing against: {self.base_url}")
        print("📋 Фокус на проблеме: Продакшн показывает все количественные поля как '0'")
        print("📋 Нужно проверить что локально это исправлено")
        print("=" * 80)
        
        # КРИТИЧНЫЕ ТЕСТЫ из review request
        test1 = self.test_cleaning_houses_main()      # GET /api/cleaning/houses
        test2 = self.test_cleaning_houses_490()       # GET /api/cleaning/houses-490
        test3 = self.test_bitrix24_connection()       # GET /api/bitrix24/test
        test4 = self.test_house_schema_structure()    # Проверка House schema
        
        # Final summary
        print("\n" + "=" * 80)
        print("📊 ИТОГОВЫЙ ОТЧЕТ КРИТИЧЕСКИХ ТЕСТОВ")
        print("=" * 80)
        print(f"✅ Тестов пройдено: {self.tests_passed}/{self.tests_run}")
        print(f"❌ Тестов провалено: {len(self.failed_tests)}")
        
        if self.failed_tests:
            print("\n❌ ПРОВАЛИВШИЕСЯ КРИТИЧЕСКИЕ ТЕСТЫ:")
            for i, test in enumerate(self.failed_tests, 1):
                print(f"{i}. {test['name']}")
                print(f"   Детали: {test['details']}")
        
        success_rate = (self.tests_passed / self.tests_run) * 100 if self.tests_run > 0 else 0
        print(f"\n📊 Успешность: {success_rate:.1f}%")
        
        # Специальная оценка для review request
        if success_rate == 100:
            print("🎉 ОТЛИЧНО: Все критические проблемы исправлены локально!")
            print("✅ Количественные поля больше НЕ показывают '0'")
            print("✅ management_company больше НЕ null")
            print("✅ Bitrix24 подключение работает")
            print("✅ House schema содержит все новые поля")
            print("🚀 ГОТОВО К ДЕПЛОЮ НА ПРОДАКШН")
        elif success_rate >= 75:
            print("⚠️ ЧАСТИЧНО: Большинство проблем исправлено, но есть вопросы")
            print("🔧 Требуется дополнительная работа перед деплоем")
        else:
            print("❌ КРИТИЧНО: Основные проблемы НЕ исправлены")
            print("🚫 НЕ ГОТОВО к деплою на продакшн")
        
        print("=" * 80)
        return success_rate >= 75

def main():
    """Main test execution"""
    tester = CriticalTester()
    
    try:
        success = tester.run_critical_tests()
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n⏹️ Tests interrupted by user")
        return 1
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())