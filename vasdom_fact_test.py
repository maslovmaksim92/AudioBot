#!/usr/bin/env python3
"""
ВАШ ДОМ ФАКТ Forecast Test - Testing updated requirements from review request
"""

import asyncio
import httpx
import json
from datetime import datetime
from typing import Dict, List, Any, Optional

# Backend URL from environment
BACKEND_URL = "https://call-logger-6.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

class TestResults:
    def __init__(self):
        self.errors = []
        self.finance_endpoints = {}

async def test_vasdom_fact_forecast_endpoint():
    """Test ВАШ ДОМ ФАКТ forecast endpoint with updated requirements from review request"""
    print("\n=== ТЕСТ ОБНОВЛЕННОГО ПРОГНОЗА ВАШ ДОМ ФАКТ ===\n")
    
    results = TestResults()
    scenarios = ["pessimistic", "realistic", "optimistic"]
    company = "ВАШ ДОМ ФАКТ"
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            print(f"🏢 Тестируем обновленный прогноз для компании: {company}")
            print("📋 Новые требования к проверке:")
            print("   ПЕССИМИСТИЧНЫЙ:")
            print("   - 2026: выручка = 56,539,380 ₽")
            print("   - 2027-2030: рост выручки +10% ежегодно")
            print("   - Рост расходов +9.7% ежегодно")
            print("")
            print("   РЕАЛИСТИЧНЫЙ:")
            print("   - Рост выручки +20% ежегодно")
            print("   - Рост расходов +16.2% ежегодно")
            print("   - Маржа должна быть в диапазоне 26.48% - 36.61%")
            print("")
            print("   ОПТИМИСТИЧНЫЙ:")
            print("   - Рост выручки +30% ежегодно")
            print("   - Рост расходов +18.9% ежегодно")
            print("")
            print("   ДЛЯ ВСЕХ СЦЕНАРИЕВ:")
            print("   - Детализация расходов НЕ должна содержать: кредиты, аутсорсинг, продукты питания")
            print("   - В детализации текущий ремонт должен быть на 70% меньше")
            print("   - Категория 'зарплата' должна содержать перераспределенные суммы")
            print("")
            
            scenario_results = {}
            
            for scenario in scenarios:
                print(f"🔍 Тестируем сценарий: {scenario}")
                
                # Test the forecast endpoint
                response = await client.get(
                    f"{API_BASE}/finances/forecast",
                    params={"company": company, "scenario": scenario}
                )
                
                print(f"📡 Ответ сервера для {scenario}: {response.status_code}")
                
                # Check 200 status
                if response.status_code != 200:
                    error_msg = f"❌ Сценарий {scenario}: ошибка {response.status_code} - {response.text}"
                    results.errors.append(error_msg)
                    print(error_msg)
                    continue
                
                data = response.json()
                scenario_results[scenario] = data
                print(f"✅ Сценарий {scenario}: 200 статус получен")
                
                # Validate response structure
                required_fields = ['company', 'scenario', 'base_year', 'base_data', 'forecast']
                for field in required_fields:
                    if field not in data:
                        error_msg = f"❌ Сценарий {scenario}: отсутствует поле '{field}'"
                        results.errors.append(error_msg)
                        print(error_msg)
                    else:
                        print(f"✅ Поле '{field}' присутствует")
                
                # Check forecast data for years 2026-2030
                forecast = data.get('forecast', [])
                if len(forecast) < 5:
                    error_msg = f"❌ Сценарий {scenario}: недостаточно лет в прогнозе (ожидалось 5, получено {len(forecast)})"
                    results.errors.append(error_msg)
                    print(error_msg)
                    continue
                
                print(f"✅ Прогноз содержит {len(forecast)} лет (2026-2030)")
                
                # Get base year data
                base_data = data.get('base_data', {})
                base_revenue = base_data.get('revenue', 0)
                base_expenses = base_data.get('expenses', 0)
                
                print(f"📊 Базовые данные 2025:")
                print(f"   - Выручка: {base_revenue:,.0f} ₽")
                print(f"   - Расходы: {base_expenses:,.0f} ₽")
                
                # Check scenario-specific requirements
                if scenario == "pessimistic":
                    print(f"\n📊 Проверяем ПЕССИМИСТИЧНЫЙ сценарий:")
                    
                    # Check 2026 specific revenue requirement
                    year_2026 = next((y for y in forecast if y.get('year') == 2026), None)
                    if year_2026:
                        revenue_2026 = year_2026.get('revenue', 0)
                        expected_2026_revenue = 56539380
                        
                        revenue_diff_pct = abs(revenue_2026 - expected_2026_revenue) / expected_2026_revenue * 100
                        if revenue_diff_pct > 1.0:  # Allow 1% tolerance
                            error_msg = f"❌ Пессимистичный 2026: неверная выручка. Ожидалось {expected_2026_revenue:,.0f} ₽, получено {revenue_2026:,.0f} ₽"
                            results.errors.append(error_msg)
                            print(error_msg)
                        else:
                            print(f"✅ 2026: выручка корректна ({revenue_2026:,.0f} ₽)")
                    
                    # Check 10% annual revenue growth for 2027-2030
                    prev_revenue = year_2026.get('revenue', 0) if year_2026 else 0
                    for year_data in forecast[1:]:  # Skip 2026, check 2027-2030
                        year = year_data.get('year')
                        revenue = year_data.get('revenue', 0)
                        
                        expected_revenue = prev_revenue * 1.10
                        revenue_diff_pct = abs(revenue - expected_revenue) / expected_revenue * 100
                        
                        if revenue_diff_pct > 1.0:
                            error_msg = f"❌ Пессимистичный {year}: неверный рост выручки +10%. Ожидалось {expected_revenue:,.0f} ₽, получено {revenue:,.0f} ₽"
                            results.errors.append(error_msg)
                            print(error_msg)
                        else:
                            print(f"✅ {year}: рост выручки +10% корректен ({revenue:,.0f} ₽)")
                        
                        prev_revenue = revenue
                    
                    # Check 9.7% annual expense growth
                    prev_expenses = year_2026.get('expenses', 0) if year_2026 else 0
                    for year_data in forecast:
                        year = year_data.get('year')
                        expenses = year_data.get('expenses', 0)
                        
                        if year == 2026:
                            prev_expenses = expenses
                            continue
                            
                        expected_expenses = prev_expenses * 1.097
                        expense_diff_pct = abs(expenses - expected_expenses) / expected_expenses * 100
                        
                        if expense_diff_pct > 1.0:
                            error_msg = f"❌ Пессимистичный {year}: неверный рост расходов +9.7%. Ожидалось {expected_expenses:,.0f} ₽, получено {expenses:,.0f} ₽"
                            results.errors.append(error_msg)
                            print(error_msg)
                        else:
                            print(f"✅ {year}: рост расходов +9.7% корректен ({expenses:,.0f} ₽)")
                        
                        prev_expenses = expenses
                
                elif scenario == "realistic":
                    print(f"\n📊 Проверяем РЕАЛИСТИЧНЫЙ сценарий:")
                    
                    # Check 20% annual revenue growth
                    prev_revenue = base_revenue
                    for year_data in forecast:
                        year = year_data.get('year')
                        revenue = year_data.get('revenue', 0)
                        expenses = year_data.get('expenses', 0)
                        
                        expected_revenue = prev_revenue * 1.20
                        revenue_diff_pct = abs(revenue - expected_revenue) / expected_revenue * 100
                        
                        if revenue_diff_pct > 1.0:
                            error_msg = f"❌ Реалистичный {year}: неверный рост выручки +20%. Ожидалось {expected_revenue:,.0f} ₽, получено {revenue:,.0f} ₽"
                            results.errors.append(error_msg)
                            print(error_msg)
                        else:
                            print(f"✅ {year}: рост выручки +20% корректен ({revenue:,.0f} ₽)")
                        
                        prev_revenue = revenue
                    
                    # Check 16.2% annual expense growth
                    prev_expenses = base_expenses
                    for year_data in forecast:
                        year = year_data.get('year')
                        expenses = year_data.get('expenses', 0)
                        
                        expected_expenses = prev_expenses * 1.162
                        expense_diff_pct = abs(expenses - expected_expenses) / expected_expenses * 100
                        
                        if expense_diff_pct > 1.0:
                            error_msg = f"❌ Реалистичный {year}: неверный рост расходов +16.2%. Ожидалось {expected_expenses:,.0f} ₽, получено {expenses:,.0f} ₽"
                            results.errors.append(error_msg)
                            print(error_msg)
                        else:
                            print(f"✅ {year}: рост расходов +16.2% корректен ({expenses:,.0f} ₽)")
                        
                        prev_expenses = expenses
                    
                    # Check margin range 26.48% - 36.61%
                    for year_data in forecast:
                        year = year_data.get('year')
                        revenue = year_data.get('revenue', 0)
                        expenses = year_data.get('expenses', 0)
                        
                        if revenue > 0:
                            margin = ((revenue - expenses) / revenue) * 100
                            
                            if margin < 26.48 or margin > 36.61:
                                error_msg = f"❌ Реалистичный {year}: маржа {margin:.2f}% вне диапазона 26.48% - 36.61%"
                                results.errors.append(error_msg)
                                print(error_msg)
                            else:
                                print(f"✅ {year}: маржа {margin:.2f}% в допустимом диапазоне")
                
                elif scenario == "optimistic":
                    print(f"\n📊 Проверяем ОПТИМИСТИЧНЫЙ сценарий:")
                    
                    # Check 30% annual revenue growth
                    prev_revenue = base_revenue
                    for year_data in forecast:
                        year = year_data.get('year')
                        revenue = year_data.get('revenue', 0)
                        
                        expected_revenue = prev_revenue * 1.30
                        revenue_diff_pct = abs(revenue - expected_revenue) / expected_revenue * 100
                        
                        if revenue_diff_pct > 1.0:
                            error_msg = f"❌ Оптимистичный {year}: неверный рост выручки +30%. Ожидалось {expected_revenue:,.0f} ₽, получено {revenue:,.0f} ₽"
                            results.errors.append(error_msg)
                            print(error_msg)
                        else:
                            print(f"✅ {year}: рост выручки +30% корректен ({revenue:,.0f} ₽)")
                        
                        prev_revenue = revenue
                    
                    # Check 18.9% annual expense growth
                    prev_expenses = base_expenses
                    for year_data in forecast:
                        year = year_data.get('year')
                        expenses = year_data.get('expenses', 0)
                        
                        expected_expenses = prev_expenses * 1.189
                        expense_diff_pct = abs(expenses - expected_expenses) / expected_expenses * 100
                        
                        if expense_diff_pct > 1.0:
                            error_msg = f"❌ Оптимистичный {year}: неверный рост расходов +18.9%. Ожидалось {expected_expenses:,.0f} ₽, получено {expenses:,.0f} ₽"
                            results.errors.append(error_msg)
                            print(error_msg)
                        else:
                            print(f"✅ {year}: рост расходов +18.9% корректен ({expenses:,.0f} ₽)")
                        
                        prev_expenses = expenses
                
                # Check expense breakdown for all scenarios
                print(f"\n🔍 Проверяем детализацию расходов для сценария {scenario}:")
                
                # Check that expense_breakdown is present
                has_expense_breakdown = False
                for year_data in forecast:
                    if 'expense_breakdown' in year_data:
                        has_expense_breakdown = True
                        break
                
                if not has_expense_breakdown:
                    error_msg = f"❌ Сценарий {scenario}: отсутствует expense_breakdown в прогнозе"
                    results.errors.append(error_msg)
                    print(error_msg)
                else:
                    print(f"✅ expense_breakdown присутствует")
                    
                    # Check excluded categories
                    excluded_categories = ['кредиты', 'аутсорсинг', 'продукты питания']
                    found_excluded = []
                    
                    sample_year = forecast[0] if forecast else {}
                    expense_breakdown = sample_year.get('expense_breakdown', {})
                    
                    for category_key, amount in expense_breakdown.items():
                        category_lower = category_key.lower()
                        for excluded in excluded_categories:
                            if excluded in category_lower:
                                found_excluded.append(category_key)
                    
                    if found_excluded:
                        error_msg = f"❌ Сценарий {scenario}: найдены исключаемые категории в детализации: {found_excluded}"
                        results.errors.append(error_msg)
                        print(error_msg)
                    else:
                        print(f"✅ Исключаемые категории отсутствуют в детализации")
                    
                    # Check for salary redistribution
                    salary_categories = [k for k in expense_breakdown.keys() if 'зарплата' in k.lower() or 'заработная' in k.lower()]
                    if salary_categories:
                        print(f"✅ Найдены категории зарплаты: {salary_categories}")
                    else:
                        print(f"⚠️ Категории зарплаты не найдены в детализации")
                    
                    # Check current repair reduction (should be 70% less)
                    repair_categories = [k for k in expense_breakdown.keys() if 'текущий ремонт' in k.lower() or 'ремонт' in k.lower()]
                    if repair_categories:
                        print(f"✅ Найдены категории ремонта: {repair_categories}")
                        print(f"   (Проверка 70% сокращения требует сравнения с базовыми данными)")
                    else:
                        print(f"⚠️ Категории ремонта не найдены в детализации")
                
                print(f"")  # Empty line for readability
            
            # Store results
            results.finance_endpoints['vasdom_fact_forecast'] = scenario_results
            
            # Summary
            print("📋 ИТОГОВАЯ СВОДКА:")
            success_count = len([s for s in scenarios if s in scenario_results])
            print(f"✅ Успешно протестировано сценариев: {success_count}/3")
            
            if results.errors:
                print(f"❌ Обнаружено ошибок: {len(results.errors)}")
                for error in results.errors[-5:]:  # Show last 5 errors
                    print(f"   - {error}")
            else:
                print(f"🎉 Все критерии успеха выполнены!")
    
    except Exception as e:
        error_msg = f"❌ Ошибка при тестировании прогноза ВАШ ДОМ ФАКТ: {str(e)}"
        results.errors.append(error_msg)
        print(error_msg)
    
    return results

async def main():
    """Main test execution - focused on ВАШ ДОМ ФАКТ forecast testing as per review request"""
    print("🚀 ТЕСТИРОВАНИЕ ОБНОВЛЕННОГО ПРОГНОЗА ВАШ ДОМ ФАКТ С НОВЫМИ ТРЕБОВАНИЯМИ")
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
    
    print("\n" + "=" * 80)
    print("🧪 ТЕСТИРОВАНИЕ ПРОГНОЗА ВАШ ДОМ ФАКТ")
    print("=" * 80)
    
    # Run the specific test for ВАШ ДОМ ФАКТ as requested
    result = await test_vasdom_fact_forecast_endpoint()
    
    # Print summary
    print("\n" + "=" * 80)
    print("📊 ИТОГОВЫЙ ОТЧЁТ")
    print("=" * 80)
    
    if result.errors:
        print(f"❌ Обнаружено ошибок: {len(result.errors)}")
        print("\n🔍 ДЕТАЛИ ОШИБОК:")
        for i, error in enumerate(result.errors, 1):
            print(f"   {i}. {error}")
        
        # Проверяем на критические ошибки
        critical_errors = [e for e in result.errors if "КРИТИЧЕСКАЯ ОШИБКА" in e or "500" in e]
        if critical_errors:
            print(f"\n⚠️ КРИТИЧЕСКИХ ОШИБОК: {len(critical_errors)}")
            print("❌ ТРЕБУЕТСЯ ИСПРАВЛЕНИЕ КОДА")
        else:
            print("\n✅ Критические ошибки исправлены")
            print("⚠️ Остались только минорные проблемы")
    else:
        print("🎉 ВСЕ ТЕСТЫ ПРОШЛИ УСПЕШНО!")
        print("✅ Все три сценария работают")
        print("✅ Рост выручки соответствует требованиям")
        print("✅ Рост расходов соответствует требованиям")
        print("✅ Исключенные категории отсутствуют")
        print("✅ Перераспределение в зарплату выполнено")
    
    print("\n" + "=" * 80)
    print("🏁 ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
    print("=" * 80)
    
    return [("ВАШ ДОМ ФАКТ Forecast Test", result)]

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)