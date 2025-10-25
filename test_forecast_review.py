#!/usr/bin/env python3
"""
Test script for forecast endpoints according to review request
"""

import asyncio
import httpx
import json
from typing import Dict, List, Any

# Backend URL from environment
BACKEND_URL = "https://finreport-dashboard.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

class TestResults:
    def __init__(self):
        self.errors = []
        self.finance_endpoints = {}

async def test_forecast_updates_review():
    """Test forecast endpoints according to review request requirements"""
    print("\n=== ТЕСТ ОБНОВЛЕНИЙ ПРОГНОЗА (REVIEW REQUEST) ===\n")
    
    results = TestResults()
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            print("🎯 Тестируем обновления прогноза согласно review request:")
            print("1. GET /api/finances/forecast?company=ВАШ ДОМ ФАКТ&scenario=optimistic")
            print("2. GET /api/finances/forecast?company=УФИЦ модель&scenario=realistic")
            print("")
            
            # Test 1: ВАШ ДОМ ФАКТ - Оптимистичный
            print("🏢 1. ТЕСТИРУЕМ ВАШ ДОМ ФАКТ - ОПТИМИСТИЧНЫЙ СЦЕНАРИЙ")
            print("-" * 60)
            
            response = await client.get(
                f"{API_BASE}/finances/forecast",
                params={"company": "ВАШ ДОМ ФАКТ", "scenario": "optimistic"}
            )
            
            print(f"📡 Ответ сервера: {response.status_code}")
            
            if response.status_code != 200:
                error_msg = f"❌ ВАШ ДОМ ФАКТ optimistic: ошибка {response.status_code} - {response.text}"
                results.errors.append(error_msg)
                print(error_msg)
            else:
                data = response.json()
                results.finance_endpoints['vasdom_fact_optimistic'] = data
                print("✅ ВАШ ДОМ ФАКТ optimistic: 200 статус получен")
                
                # Check forecast data
                forecast = data.get('forecast', [])
                scenario_info = data.get('scenario_info', {})
                
                print(f"📊 Проверяем требования для ВАШ ДОМ ФАКТ - Оптимистичный:")
                
                # 1. Маржа 2026-2030 в диапазоне 27.58%-36.42%
                print("\n1️⃣ Проверяем маржу 2026-2030 (диапазон 27.58%-36.42%):")
                margin_errors = []
                for year_data in forecast:
                    year = year_data.get('year')
                    if year and 2026 <= year <= 2030:
                        margin = year_data.get('margin', 0)
                        if not (27.58 <= margin <= 36.42):
                            margin_errors.append(f"   ❌ {year}: маржа {margin:.2f}% вне диапазона")
                        else:
                            print(f"   ✅ {year}: маржа {margin:.2f}% в диапазоне")
                
                if margin_errors:
                    results.errors.extend(margin_errors)
                else:
                    print("   ✅ Все маржи в требуемом диапазоне")
                
                # 2. Детализация расходов НЕ содержит "юридические услуги"
                print("\n2️⃣ Проверяем отсутствие 'юридические услуги' в детализации:")
                legal_services_found = False
                for year_data in forecast:
                    expense_breakdown = year_data.get('expense_breakdown', {})
                    for category, amount in expense_breakdown.items():
                        if 'юридические' in category.lower() or 'юридическ' in category.lower():
                            legal_services_found = True
                            results.errors.append(f"   ❌ Найдена категория '{category}' в детализации")
                            break
                
                if not legal_services_found:
                    print("   ✅ 'Юридические услуги' отсутствуют в детализации")
                
                # 3. Категория "зарплата" увеличена (включает перераспределенные суммы)
                print("\n3️⃣ Проверяем категорию 'зарплата' (должна быть увеличена):")
                salary_found = False
                for year_data in forecast:
                    expense_breakdown = year_data.get('expense_breakdown', {})
                    for category, amount in expense_breakdown.items():
                        if 'зарплата' in category.lower() or 'зп' in category.lower():
                            salary_found = True
                            print(f"   ✅ Найдена категория '{category}': {amount:,.0f} ₽")
                            break
                
                if not salary_found:
                    results.errors.append("   ❌ Категория 'зарплата' не найдена в детализации")
                
                # 4. Рост расходов обновлен до +22.5% (вместо +18.9%)
                print("\n4️⃣ Проверяем рост расходов +22.5%:")
                if len(forecast) >= 2:
                    year_2026 = next((y for y in forecast if y.get('year') == 2026), None)
                    year_2027 = next((y for y in forecast if y.get('year') == 2027), None)
                    
                    if year_2026 and year_2027:
                        expenses_2026 = year_2026.get('expenses', 0)
                        expenses_2027 = year_2027.get('expenses', 0)
                        
                        if expenses_2026 > 0:
                            growth_rate = ((expenses_2027 - expenses_2026) / expenses_2026) * 100
                            expected_growth = 22.5
                            
                            if abs(growth_rate - expected_growth) > 1.0:  # Allow 1% tolerance
                                results.errors.append(f"   ❌ Рост расходов {growth_rate:.1f}%, ожидался {expected_growth}%")
                            else:
                                print(f"   ✅ Рост расходов {growth_rate:.1f}% (ожидался {expected_growth}%)")
                
                # 5. Поле detailed_description присутствует в scenario_info
                print("\n5️⃣ Проверяем поле 'detailed_description' в scenario_info:")
                detailed_description = scenario_info.get('detailed_description')
                if not detailed_description:
                    results.errors.append("   ❌ Поле 'detailed_description' отсутствует в scenario_info")
                else:
                    print("   ✅ Поле 'detailed_description' присутствует")
                    
                    # 6. detailed_description содержит: summary, revenue_factors, expense_factors
                    print("\n6️⃣ Проверяем структуру detailed_description:")
                    required_fields = ['summary', 'revenue_factors', 'expense_factors']
                    for field in required_fields:
                        if field not in detailed_description:
                            results.errors.append(f"   ❌ Отсутствует поле '{field}' в detailed_description")
                        else:
                            content = detailed_description[field]
                            print(f"   ✅ Поле '{field}' присутствует ({len(str(content))} символов)")
            
            print("\n" + "=" * 60)
            
            # Test 2: УФИЦ модель - Реалистичный
            print("🏢 2. ТЕСТИРУЕМ УФИЦ МОДЕЛЬ - РЕАЛИСТИЧНЫЙ СЦЕНАРИЙ")
            print("-" * 60)
            
            response = await client.get(
                f"{API_BASE}/finances/forecast",
                params={"company": "УФИЦ модель", "scenario": "realistic"}
            )
            
            print(f"📡 Ответ сервера: {response.status_code}")
            
            if response.status_code != 200:
                error_msg = f"❌ УФИЦ модель realistic: ошибка {response.status_code} - {response.text}"
                results.errors.append(error_msg)
                print(error_msg)
            else:
                data = response.json()
                results.finance_endpoints['ufic_realistic'] = data
                print("✅ УФИЦ модель realistic: 200 статус получен")
                
                scenario_info = data.get('scenario_info', {})
                
                print(f"📊 Проверяем требования для УФИЦ модель - Реалистичный:")
                
                # 1. Поле detailed_description присутствует в scenario_info
                print("\n1️⃣ Проверяем поле 'detailed_description' в scenario_info:")
                detailed_description = scenario_info.get('detailed_description')
                if not detailed_description:
                    results.errors.append("   ❌ Поле 'detailed_description' отсутствует в scenario_info")
                else:
                    print("   ✅ Поле 'detailed_description' присутствует")
                    
                    # 2. detailed_description содержит: summary, revenue_factors, expense_factors
                    print("\n2️⃣ Проверяем структуру detailed_description:")
                    required_fields = ['summary', 'revenue_factors', 'expense_factors']
                    for field in required_fields:
                        if field not in detailed_description:
                            results.errors.append(f"   ❌ Отсутствует поле '{field}' в detailed_description")
                        else:
                            content = detailed_description[field]
                            print(f"   ✅ Поле '{field}' присутствует ({len(str(content))} символов)")
            
            print("\n" + "=" * 60)
            print("📋 ИТОГИ ТЕСТИРОВАНИЯ ОБНОВЛЕНИЙ ПРОГНОЗА:")
            
            if not results.errors:
                print("🎉 ВСЕ КРИТЕРИИ УСПЕХА ВЫПОЛНЕНЫ!")
                print("✅ Юридические услуги исключены")
                print("✅ Маржа оптимистичного в диапазоне 27.58%-36.42%")
                print("✅ Детальные описания присутствуют")
                print("✅ Структура detailed_description корректна")
            else:
                print(f"⚠️ ОБНАРУЖЕНО {len(results.errors)} ПРОБЛЕМ:")
                for error in results.errors:
                    print(f"   {error}")
            
    except Exception as e:
        error_msg = f"❌ Ошибка при тестировании обновлений прогноза: {str(e)}"
        results.errors.append(error_msg)
        print(error_msg)
    
    return results

async def main():
    """Main test execution"""
    print("🚀 ТЕСТИРОВАНИЕ ОБНОВЛЕНИЙ ПРОГНОЗА (REVIEW REQUEST)")
    print("=" * 80)
    print(f"🌐 Backend URL: {BACKEND_URL}")
    print(f"🔗 API Base: {API_BASE}")
    print("=" * 80)
    
    # Check basic connectivity
    print("\n🔍 Проверяем доступность backend...")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{API_BASE}/health")
            if response.status_code == 200:
                print("✅ Backend доступен")
            else:
                print(f"⚠️ Backend недоступен: {response.status_code}")
                return
    except Exception as e:
        print(f"❌ Ошибка подключения к backend: {str(e)}")
        return
    
    # Run the test
    result = await test_forecast_updates_review()
    
    # Print summary
    print("\n" + "=" * 80)
    print("📊 ИТОГОВЫЙ ОТЧЁТ")
    print("=" * 80)
    
    if result.errors:
        print(f"❌ Обнаружено ошибок: {len(result.errors)}")
        print("\n🔍 ДЕТАЛИ ОШИБОК:")
        for i, error in enumerate(result.errors, 1):
            print(f"   {i}. {error}")
    else:
        print("🎉 ВСЕ ТЕСТЫ ПРОШЛИ УСПЕШНО!")
        print("✅ Все критерии успеха выполнены")
        print("✅ Юридические услуги исключены")
        print("✅ Маржа оптимистичного в диапазоне 27.58%-36.42%")
        print("✅ Детальные описания присутствуют")
        print("✅ Структура detailed_description корректна")
    
    print("\n" + "=" * 80)
    print("🏁 ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main())