#!/usr/bin/env python3
"""
КРИТИЧЕСКИЙ ТЕСТ для Review Request - Проверка готовности к деплою на Render
"""

import requests
import json
import sys
from datetime import datetime

class CriticalReviewTester:
    def __init__(self):
        # Используем локальный backend
        self.base_url = "http://localhost:8001"
        self.api_url = f"{self.base_url}/api"
        self.results = {
            "management_companies": {"status": "unknown", "details": []},
            "cleaning_types": {"status": "unknown", "details": []},
            "quantitative_fields": {"status": "unknown", "details": []}
        }

    def test_critical_houses_490(self):
        """КРИТИЧЕСКИЙ ТЕСТ: GET /api/cleaning/houses-490"""
        print("🔥 КРИТИЧЕСКИЙ ТЕСТ: GET /api/cleaning/houses-490")
        print("=" * 60)
        
        try:
            response = requests.get(f"{self.api_url}/cleaning/houses-490", timeout=120)
            
            if response.status_code != 200:
                print(f"❌ ОШИБКА: Status code {response.status_code}")
                print(f"Response: {response.text[:500]}")
                return False
            
            data = response.json()
            houses = data.get("houses", [])
            
            if len(houses) != 490:
                print(f"❌ ОШИБКА: Загружено {len(houses)} домов, ожидалось 490")
                return False
            
            print(f"✅ Загружено exactly 490 домов")
            
            # Тест 1: УК (Management Companies)
            self.test_management_companies(houses[:10])  # Проверяем первые 10
            
            # Тест 2: Типы уборки
            self.test_cleaning_types(houses[:5])  # Проверяем первые 5
            
            # Тест 3: Количественные поля
            self.test_quantitative_fields(houses)
            
            return True
            
        except Exception as e:
            print(f"❌ КРИТИЧЕСКАЯ ОШИБКА: {str(e)}")
            return False

    def test_management_companies(self, houses):
        """Тест 1: УК должны показывать РЕАЛЬНЫЕ названия из Bitrix24"""
        print("\n1️⃣ ТЕСТ УК (Management Companies):")
        print("-" * 40)
        
        real_uc_count = 0
        fake_uc_count = 0
        null_uc_count = 0
        
        for i, house in enumerate(houses, 1):
            uc = house.get('management_company')
            
            if not uc or uc == 'null':
                null_uc_count += 1
                print(f"   Дом {i}: УК = null")
            elif any(keyword in uc for keyword in ['ООО', 'ЖИЛИЩНОЕ', 'РЭУ', 'ЕТЦ', 'УК']):
                real_uc_count += 1
                print(f"   Дом {i}: УК = {uc} ✅")
            else:
                fake_uc_count += 1
                print(f"   Дом {i}: УК = {uc} ❓")
        
        print(f"\nРЕЗУЛЬТАТ УК:")
        print(f"   Реальные УК: {real_uc_count}/10")
        print(f"   Fake УК: {fake_uc_count}/10") 
        print(f"   Null УК: {null_uc_count}/10")
        
        if real_uc_count >= 5:
            self.results["management_companies"]["status"] = "success"
            print("   ✅ УК ТЕСТ ПРОЙДЕН")
        else:
            self.results["management_companies"]["status"] = "failed"
            print("   ❌ УК ТЕСТ НЕ ПРОЙДЕН")
        
        self.results["management_companies"]["details"] = {
            "real": real_uc_count,
            "fake": fake_uc_count,
            "null": null_uc_count
        }

    def test_cleaning_types(self, houses):
        """Тест 2: Типы уборки должны показывать ПОЛНЫЕ описания, НЕ "Тип 2468" """
        print("\n2️⃣ ТЕСТ ТИПОВ УБОРКИ (Cleaning Types):")
        print("-" * 40)
        
        full_descriptions = 0
        type_ids = 0
        missing_types = 0
        
        for i, house in enumerate(houses, 1):
            september = house.get('september_schedule', {})
            cleaning_type_1 = september.get('cleaning_type_1', '')
            
            if not cleaning_type_1:
                missing_types += 1
                print(f"   Дом {i}: Тип уборки = отсутствует")
            elif cleaning_type_1.startswith('Тип '):
                type_ids += 1
                print(f"   Дом {i}: Тип уборки = {cleaning_type_1} ❌")
            elif len(cleaning_type_1) > 20:  # Полное описание
                full_descriptions += 1
                print(f"   Дом {i}: Тип уборки = {cleaning_type_1[:50]}... ✅")
            else:
                print(f"   Дом {i}: Тип уборки = {cleaning_type_1} ❓")
        
        print(f"\nРЕЗУЛЬТАТ ТИПОВ УБОРКИ:")
        print(f"   Полные описания: {full_descriptions}/5")
        print(f"   ID типов (Тип XXXX): {type_ids}/5")
        print(f"   Отсутствуют: {missing_types}/5")
        
        if full_descriptions >= 3:
            self.results["cleaning_types"]["status"] = "success"
            print("   ✅ ТИПЫ УБОРКИ ТЕСТ ПРОЙДЕН")
        else:
            self.results["cleaning_types"]["status"] = "failed"
            print("   ❌ ТИПЫ УБОРКИ ТЕСТ НЕ ПРОЙДЕН")
        
        self.results["cleaning_types"]["details"] = {
            "full_descriptions": full_descriptions,
            "type_ids": type_ids,
            "missing": missing_types
        }

    def test_quantitative_fields(self, houses):
        """Тест 3: Количественные поля должны быть > 0 для большинства домов"""
        print("\n3️⃣ ТЕСТ КОЛИЧЕСТВЕННЫХ ПОЛЕЙ:")
        print("-" * 40)
        
        apartments_positive = 0
        entrances_positive = 0
        floors_positive = 0
        
        total_apartments = 0
        total_entrances = 0
        total_floors = 0
        
        for house in houses:
            apt_count = house.get('apartments_count', 0) or 0
            ent_count = house.get('entrances_count', 0) or 0
            floor_count = house.get('floors_count', 0) or 0
            
            if apt_count > 0:
                apartments_positive += 1
                total_apartments += apt_count
            
            if ent_count > 0:
                entrances_positive += 1
                total_entrances += ent_count
                
            if floor_count > 0:
                floors_positive += 1
                total_floors += floor_count
        
        print(f"   Квартиры > 0: {apartments_positive}/490 ({apartments_positive/490*100:.1f}%)")
        print(f"   Подъезды > 0: {entrances_positive}/490 ({entrances_positive/490*100:.1f}%)")
        print(f"   Этажи > 0: {floors_positive}/490 ({floors_positive/490*100:.1f}%)")
        
        print(f"\n   Общие суммы:")
        print(f"   Всего квартир: {total_apartments}")
        print(f"   Всего подъездов: {total_entrances}")
        print(f"   Всего этажей: {total_floors}")
        
        # Проверяем что большинство домов имеют количественные данные > 0
        success_rate = (apartments_positive + entrances_positive + floors_positive) / (490 * 3)
        
        if success_rate >= 0.8:  # 80% полей должны быть > 0
            self.results["quantitative_fields"]["status"] = "success"
            print("   ✅ КОЛИЧЕСТВЕННЫЕ ПОЛЯ ТЕСТ ПРОЙДЕН")
        else:
            self.results["quantitative_fields"]["status"] = "failed"
            print("   ❌ КОЛИЧЕСТВЕННЫЕ ПОЛЯ ТЕСТ НЕ ПРОЙДЕН")
        
        self.results["quantitative_fields"]["details"] = {
            "apartments_positive": apartments_positive,
            "entrances_positive": entrances_positive,
            "floors_positive": floors_positive,
            "success_rate": success_rate
        }

    def print_final_results(self):
        """Печать финальных результатов"""
        print("\n" + "="*60)
        print("🚀 ФИНАЛЬНЫЕ РЕЗУЛЬТАТЫ ГОТОВНОСТИ К ДЕПЛОЮ:")
        print("="*60)
        
        all_passed = True
        
        # УК
        uc_status = self.results["management_companies"]["status"]
        if uc_status == "success":
            print("✅ УК: ГОТОВЫ - показывают реальные названия из Bitrix24")
        else:
            print("❌ УК: НЕ ГОТОВЫ - показывают fake данные или null")
            all_passed = False
        
        # Типы уборки
        types_status = self.results["cleaning_types"]["status"]
        if types_status == "success":
            print("✅ ТИПЫ УБОРКИ: ГОТОВЫ - показывают полные описания")
        else:
            print("❌ ТИПЫ УБОРКИ: НЕ ГОТОВЫ - показывают 'Тип 2468'")
            all_passed = False
        
        # Количественные поля
        quant_status = self.results["quantitative_fields"]["status"]
        if quant_status == "success":
            print("✅ КОЛИЧЕСТВЕННЫЕ ПОЛЯ: ГОТОВЫ - большинство > 0")
        else:
            print("❌ КОЛИЧЕСТВЕННЫЕ ПОЛЯ: НЕ ГОТОВЫ - много нулей")
            all_passed = False
        
        print("\n" + "="*60)
        if all_passed:
            print("🎉 СИСТЕМА ГОТОВА К ДЕПЛОЮ НА RENDER!")
        else:
            print("⚠️ СИСТЕМА НЕ ГОТОВА К ДЕПЛОЮ - ЕСТЬ КРИТИЧЕСКИЕ ПРОБЛЕМЫ")
        print("="*60)
        
        return all_passed

def main():
    tester = CriticalReviewTester()
    
    print("🔥 КРИТИЧЕСКАЯ ПРОВЕРКА ГОТОВНОСТИ К ДЕПЛОЮ")
    print("Проверяем исправления согласно review request")
    print("URL:", tester.base_url)
    print()
    
    success = tester.test_critical_houses_490()
    
    if success:
        ready_for_deploy = tester.print_final_results()
        sys.exit(0 if ready_for_deploy else 1)
    else:
        print("\n❌ КРИТИЧЕСКИЙ ТЕСТ НЕ ПРОШЕЛ - СИСТЕМА НЕ ГОТОВА")
        sys.exit(1)

if __name__ == "__main__":
    main()